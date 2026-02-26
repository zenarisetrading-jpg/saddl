#!/usr/bin/env python3
"""
Saddle Backfill Worker
======================
Watches client_settings for newly-connected accounts and automatically
runs the SP-API historical backfill — no user or admin action needed.

Flow:
  OAuth completes  →  onboarding_status = 'connected'
  Worker detects it  →  runs backfill (sets status → 'backfilling')
  Backfill completes  →  onboarding_status = 'active'
  Data is live in the app

Run alongside the Streamlit app:
  Terminal 1:  streamlit run ppcsuite_v4_ui_experiment.py
  Terminal 2:  python worker.py

Cloud (Railway / Render / Fly.io):
  Deploy as a second service with the same env vars.
  No extra config needed — same DATABASE_URL, same SP-API keys.
"""

from __future__ import annotations

import logging
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
log = logging.getLogger("saddl.worker")

POLL_INTERVAL_SECONDS = 30   # How often to scan for new accounts
BACKFILL_DAYS         = 90   # Historical window to pull


def _get_db_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        sys.exit("❌  DATABASE_URL is not set.")
    return url


def _connect():
    import psycopg2  # type: ignore
    return psycopg2.connect(_get_db_url())


def _find_pending_clients() -> list[dict]:
    """
    Return accounts that:
      - have onboarding_status = 'connected'  (OAuth done, backfill not yet run)
      - have an lwa_refresh_token stored
      - have NO rows yet in sc_raw.fba_inventory for their client_id
        (proxy for "backfill has never completed successfully")
    """
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT cs.client_id, cs.lwa_refresh_token
                FROM client_settings cs
                WHERE cs.onboarding_status = 'connected'
                  AND cs.lwa_refresh_token IS NOT NULL
                  AND NOT EXISTS (
                      SELECT 1 FROM sc_raw.fba_inventory fi
                      WHERE fi.client_id = cs.client_id
                      LIMIT 1
                  )
            """)
            rows = cur.fetchall()
    return [{"client_id": r[0], "refresh_token": r[1]} for r in rows]


def _run_backfill_for(client_id: str, refresh_token: str) -> None:
    """Run the full backfill for one client. Mirrors _backfill_thread_fn in data_hub.py."""
    from datetime import date, timedelta

    log.info("▶  Starting backfill  client=%s", client_id)

    marketplace_id = os.getenv("MARKETPLACE_ID_UAE", "A2VIGQ35RCS4UG")
    prev_token     = os.environ.get("LWA_REFRESH_TOKEN_UAE")
    os.environ["LWA_REFRESH_TOKEN_UAE"] = refresh_token

    # Clear cached access token so we auth with this client's token
    try:
        from pipelines import sp_api_client as _spc  # type: ignore
        _spc._token_cache.update({"access_token": None, "expires_at": None})
    except Exception:
        pass

    # Mark as in-progress immediately so we don't double-pick
    _set_status(client_id, "backfilling")

    try:
        from pipelines.sp_api_client import get_settings, get_token  # type: ignore
        from pipelines.spapi_pipeline import (  # type: ignore
            build_sales_traffic_query, create_data_kiosk_query,
            poll_query_status, download_query_document,
            upsert_sales_traffic, pull_fba_inventory,
        )

        settings     = get_settings()
        access_token = get_token(force_refresh=True)
        today        = date.today()
        start_dt     = (today - timedelta(days=BACKFILL_DAYS)).strftime("%Y-%m-%d")
        end_dt       = (today - timedelta(days=1)).strftime("%Y-%m-%d")

        log.info("  Date range  : %s → %s", start_dt, end_dt)

        # Step 1 — Sales & Traffic (raw rows, tagged with client_id)
        log.info("  [1/4] Submitting Data Kiosk query…")
        qbody    = build_sales_traffic_query(start_dt, end_dt, settings.marketplace_id)
        qid      = create_data_kiosk_query(access_token, qbody)
        payload  = poll_query_status(access_token, qid, poll_seconds=30, max_wait_minutes=30)
        doc_id   = payload.get("dataDocumentId")
        if not doc_id:
            raise RuntimeError(f"No dataDocumentId for queryId={qid}")
        payloads = download_query_document(access_token, doc_id)
        rows_sc  = upsert_sales_traffic(
            payloads, end_dt, settings.marketplace_id, account_id=client_id
        )
        log.info("  [1/4] ✓ %d rows written (account_id=%s)", rows_sc, client_id)

        # Step 1b — Aggregate raw rows → sc_analytics.account_daily
        log.info("  [2/4] Aggregating sales/traffic → account_daily…")
        try:
            from pipeline.aggregator import upsert_account_daily, upsert_osi_index  # type: ignore
            db_url      = _get_db_url()
            agg_start   = date.fromisoformat(start_dt)
            agg_end     = date.fromisoformat(end_dt)
            agg_current = agg_start
            agg_count   = 0
            while agg_current <= agg_end:
                upsert_account_daily(
                    db_url,
                    agg_current.isoformat(),
                    settings.marketplace_id,
                    client_id=client_id,
                    account_id=client_id,
                )
                upsert_osi_index(
                    db_url,
                    agg_current.isoformat(),
                    settings.marketplace_id,
                    account_id=client_id,
                )
                agg_current += timedelta(days=1)
                agg_count   += 1
            log.info("  [2/4] ✓ %d days aggregated (account_daily + osi_index)", agg_count)
        except Exception as agg_exc:
            log.warning("  [2/4] Aggregation failed (non-fatal): %s", agg_exc)

        # Step 3 — FBA Inventory
        log.info("  [3/4] FBA inventory snapshot…")
        rows_inv = pull_fba_inventory(client_id)
        log.info("  [3/4] ✓ %s rows written", rows_inv)

        # Step 4 — BSR (best-effort)
        log.info("  [4/4] Best Seller Rank snapshot…")
        try:
            import psycopg2 as _pg  # type: ignore
            from pipeline.bsr_pipeline import fetch_bsr_batch, upsert_bsr_history  # type: ignore
            db_url = _get_db_url()
            with _pg.connect(db_url) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT DISTINCT child_asin FROM sc_raw.sales_traffic "
                        "WHERE marketplace_id = %s AND report_date >= %s "
                        "AND account_id = %s AND child_asin IS NOT NULL LIMIT 500",
                        (settings.marketplace_id, start_dt, client_id),
                    )
                    asins = [r[0] for r in cur.fetchall()]
            if asins:
                cfg = {
                    "lwa_client_id":     os.getenv("LWA_CLIENT_ID", ""),
                    "lwa_client_secret": os.getenv("LWA_CLIENT_SECRET", ""),
                    "refresh_token_uae": refresh_token,
                    "aws_access_key":    os.getenv("AWS_ACCESS_KEY_ID", ""),
                    "aws_secret_key":    os.getenv("AWS_SECRET_ACCESS_KEY", ""),
                    "aws_region":        os.getenv("AWS_REGION", "eu-west-1"),
                    "marketplace_uae":   settings.marketplace_id,
                    "spapi_account_id":  client_id,
                    "endpoint":          "https://sellingpartnerapi-eu.amazon.com",
                    "database_url":      db_url,
                }
                bsr_rows = fetch_bsr_batch(cfg, token=access_token,
                                           asins=asins, report_date=today.strftime("%Y-%m-%d"))
                rows_bsr = upsert_bsr_history(bsr_rows, db_url)
                log.info("  [4/4] ✓ %d rows written", rows_bsr)
            else:
                log.info("  [4/4] No ASINs found — skipping")
        except Exception as bsr_exc:
            log.warning("  [4/4] BSR failed (non-fatal): %s", bsr_exc)

        _set_status(client_id, "active")
        log.info("✅  Backfill complete  client=%s", client_id)

    except Exception as exc:
        log.error("❌  Backfill FAILED  client=%s  error=%s", client_id, exc)
        _set_status(client_id, "connected")   # Reset so worker retries next cycle

    finally:
        if prev_token is not None:
            os.environ["LWA_REFRESH_TOKEN_UAE"] = prev_token
        else:
            os.environ.pop("LWA_REFRESH_TOKEN_UAE", None)
        try:
            from pipelines import sp_api_client as _spc  # type: ignore
            _spc._token_cache.update({"access_token": None, "expires_at": None})
        except Exception:
            pass


def _set_status(client_id: str, status: str) -> None:
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE client_settings SET onboarding_status = %s, updated_at = NOW() "
                "WHERE client_id = %s",
                (status, client_id),
            )
        conn.commit()


def main() -> None:
    # Load .env for local dev
    try:
        from dotenv import load_dotenv  # type: ignore
        load_dotenv(ROOT / ".env")
    except ImportError:
        pass

    log.info("═══════════════════════════════════════════")
    log.info("Saddle Backfill Worker started")
    log.info("Poll interval : %ds", POLL_INTERVAL_SECONDS)
    log.info("Backfill window: %d days", BACKFILL_DAYS)
    log.info("═══════════════════════════════════════════")

    while True:
        try:
            pending = _find_pending_clients()
            if pending:
                log.info("Found %d account(s) needing backfill", len(pending))
                for client in pending:
                    _run_backfill_for(client["client_id"], client["refresh_token"])
        except Exception as exc:
            log.error("Worker poll error (will retry): %s", exc)

        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
