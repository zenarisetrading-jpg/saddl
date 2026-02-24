import streamlit as st
import pandas as pd
import psycopg2

from features.optimizer_shared.core import (
    prepare_data,
    calculate_account_benchmarks,
    DEFAULT_CONFIG,
    OPTIMIZATION_PROFILES,
)
from utils.matchers import ExactMatcher
from features.optimizer_shared.strategies.harvest import identify_harvest_candidates
from features.optimizer_shared.strategies.negatives import identify_negative_candidates
from features.optimizer_shared.strategies.bids import calculate_bid_optimizations
from features.optimizer_shared.data_access import fetch_target_stats_cached
from features.optimizer_shared.ui.tabs.bids import render_bids_tab
from features.optimizer_shared.ui.tabs.negatives import render_negatives_tab
from features.optimizer_shared.ui.tabs.harvest import render_harvest_tab
from features.optimizer_shared.ui.tabs.downloads import render_downloads_tab


def run_pipeline_and_render_results():
    if st.session_state.get("v2_opt_state") == "running":
        success = _execute_v2_engine()
        st.session_state["v2_opt_state"] = "completed" if success else "entry"
        st.rerun()

    if st.session_state.get("v2_opt_state") == "completed":
        _render_v2_results_view()


def _execute_v2_engine():
    with st.spinner("Executing optimizer pipeline..."):
        config = DEFAULT_CONFIG.copy()
        profile_name = st.session_state.get("opt_risk_profile", "Balanced").lower()
        profile_params = OPTIMIZATION_PROFILES.get(profile_name, OPTIMIZATION_PROFILES["balanced"])["params"]
        config.update(profile_params)

        client_id = st.session_state.get("active_account_id")
        test_mode = st.session_state.get("test_mode", False)

        if client_id == "s2c_uae_test":
            config["halo_min_organic_units"] = 75

        try:
            df = fetch_target_stats_cached(client_id, test_mode)
        except psycopg2.OperationalError as e:
            msg = str(e)
            if "could not translate host name" in msg:
                st.error(
                    "Database host could not be resolved. Check network/DNS and DATABASE_URL host."
                )
            else:
                st.error(f"Database connection failed: {msg}")
            st.info(
                "If this is a local network issue, retry in a few seconds. "
                "If it persists, verify the Supabase pooler hostname in your DATABASE_URL."
            )
            return False
        except Exception as e:
            st.error(f"Failed to load optimizer data: {e}")
            return False

        if df is None or df.empty:
            st.error("No data available to optimize. Please check Data Hub.")
            return False

        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
            start_date = st.session_state.get("opt_start_date")
            end_date = st.session_state.get("opt_end_date")
            if start_date and end_date:
                mask = (df["Date"].dt.date >= start_date) & (df["Date"].dt.date <= end_date)
                df = df[mask].copy()

        df, date_info = prepare_data(df, config)
        benchmarks = calculate_account_benchmarks(df, config)
        universal_median = benchmarks.get("universal_median_roas", config.get("TARGET_ROAS", 2.5))

        matcher = ExactMatcher(df)
        harvest = identify_harvest_candidates(df, config, matcher, benchmarks)
        neg_kw, neg_pt, your_products = identify_negative_candidates(df, config, harvest, benchmarks)

        neg_set = set(zip(neg_kw["Campaign Name"], neg_kw["Ad Group Name"], neg_kw["Term"].str.lower()))
        data_days = date_info.get("days", 7) if date_info else 7

        bids_ex, bids_pt, bids_agg, bids_auto = calculate_bid_optimizations(
            df,
            config,
            set(harvest["Customer Search Term"].str.lower()),
            neg_set,
            universal_median,
            data_days=data_days,
            client_id=client_id,
        )

        st.session_state["v2_opt_results"] = {
            "config": config,
            "df": df,
            "bids_ex": bids_ex,
            "bids_pt": bids_pt,
            "bids_agg": bids_agg,
            "bids_auto": bids_auto,
            "neg_kw": neg_kw,
            "neg_pt": neg_pt,
            "harvest": harvest,
            "date_info": date_info,
            "your_products": your_products,
        }
        return True


def _current_bid_for_row(row: pd.Series) -> float:
    for col in ["Current Bid", "Bid", "Ad Group Default Bid", "CPC"]:
        val = row.get(col)
        if pd.notna(val):
            try:
                v = float(val)
                if v > 0:
                    return v
            except Exception:
                continue
    return 0.0


def _add_bid_direction(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    out = df.copy()
    out["Current_Bid_Calc"] = out.apply(_current_bid_for_row, axis=1)
    out["New Bid"] = pd.to_numeric(out.get("New Bid", 0), errors="coerce").fillna(0)
    out["Reason"] = out.get("Reason", "").astype(str)

    def _direction(row):
        reason = str(row.get("Reason", "")).lower()
        if "hold" in reason or "cooldown" in reason:
            return "hold"
        cur = float(row.get("Current_Bid_Calc", 0) or 0)
        new = float(row.get("New Bid", 0) or 0)
        if cur <= 0 or new <= 0:
            return "hold"
        if new > cur:
            return "increase"
        if new < cur:
            return "decrease"
        return "hold"

    out["direction"] = out.apply(_direction, axis=1)
    out["adjustment_pct"] = out.apply(
        lambda r: ((r["New Bid"] - r["Current_Bid_Calc"]) / r["Current_Bid_Calc"] * 100)
        if r["Current_Bid_Calc"] > 0
        else 0,
        axis=1,
    )
    return out


def _render_preview_table(df: pd.DataFrame, columns: list, reason_col: str = "Reason"):
    if df.empty:
        st.info("No rows to preview.")
        return

    table = df[[c for c in columns if c in df.columns]].copy()
    column_config = {}
    if reason_col in table.columns:
        column_config[reason_col] = st.column_config.TextColumn(reason_col, width="large")
    st.dataframe(
        table,
        use_container_width=True,
        hide_index=True,
        height=240,
        column_config=column_config,
    )


def _format_currency(value, currency="AED"):
    try:
        return f"{currency}{float(value):,.0f}"
    except Exception:
        return f"{currency}0"


def _render_v2_results_view():
    res = st.session_state.get("v2_opt_results")
    if not res:
        st.session_state["v2_opt_state"] = "entry"
        st.rerun()

    bids_ex = res["bids_ex"]
    bids_pt = res["bids_pt"]
    bids_agg = res["bids_agg"]
    bids_auto = res["bids_auto"]
    neg_kw = res["neg_kw"]
    neg_pt = res["neg_pt"]
    harvest = res["harvest"]

    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Manrope:wght@400;500;700&display=swap');

        .v2-h2 {
            font-family: 'Space Grotesk', sans-serif;
            color: #f8fafc;
            letter-spacing: 0.01em;
            margin-bottom: 6px;
        }

        div[data-testid="stDataFrame"] [data-testid="stMarkdownContainer"] p {
            white-space: normal !important;
            overflow: visible !important;
            text-overflow: clip !important;
            line-height: 1.35 !important;
        }

        .v2-flag-panel {
            border: 1px solid rgba(148, 163, 184, 0.22);
            border-radius: 14px;
            padding: 16px;
            background: rgba(15, 23, 42, 0.55);
            margin-top: 18px;
        }

        .v2-flag-title {
            color: #e2e8f0;
            font-family: 'Space Grotesk', sans-serif;
            margin-bottom: 10px;
            font-size: 1rem;
            font-weight: 700;
        }

        .v2-flag-line {
            font-family: 'Manrope', sans-serif;
            color: #cbd5e1;
            margin: 8px 0;
            font-size: 0.95rem;
        }

        .v2-pending {
            color: #94a3b8;
            font-style: italic;
        }

        .v2-kpi {
            border: 1px solid rgba(148, 163, 184, 0.2);
            border-radius: 12px;
            padding: 10px 12px;
            background: rgba(15, 23, 42, 0.52);
            margin-bottom: 12px;
        }
        .v2-kpi-label {
            color: #94a3b8;
            font-size: 0.8rem;
            letter-spacing: 0.03em;
            text-transform: uppercase;
            margin-bottom: 2px;
        }
        .v2-kpi-value {
            color: #e2e8f0;
            font-size: 1.05rem;
            font-weight: 700;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<h2 class='v2-h2'>Optimizer v2 results</h2>", unsafe_allow_html=True)

    if st.button("Back to pre-run brief"):
        st.session_state["v2_opt_state"] = "entry"
        st.rerun()

    direct_bids = pd.concat([bids_ex, bids_pt], ignore_index=True)
    agg_bids = pd.concat([bids_agg, bids_auto], ignore_index=True)
    all_bids = pd.concat([direct_bids, agg_bids], ignore_index=True)
    all_bids = _add_bid_direction(all_bids) if not all_bids.empty else all_bids

    t1, t2, t3 = st.tabs(["⚡ Decisions", "🧠 Intelligence", "⬇️ Downloads"])

    with t1:
        bid_inc = int((all_bids.get("direction") == "increase").sum()) if not all_bids.empty else 0
        bid_dec = int((all_bids.get("direction") == "decrease").sum()) if not all_bids.empty else 0
        bid_hold = int((all_bids.get("direction") == "hold").sum()) if not all_bids.empty else 0
        total_negative_actions = (len(neg_kw) if not neg_kw.empty else 0) + (len(neg_pt) if not neg_pt.empty else 0)
        harvest_count = len(harvest) if not harvest.empty else 0

        k1, k2, k3 = st.columns(3, gap="small")
        with k1:
            st.markdown(
                f"""
                <div class="v2-kpi">
                    <div class="v2-kpi-label">Bid Actions</div>
                    <div class="v2-kpi-value">{bid_inc + bid_dec + bid_hold}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with k2:
            st.markdown(
                f"""
                <div class="v2-kpi">
                    <div class="v2-kpi-label">Negative Actions</div>
                    <div class="v2-kpi-value">{total_negative_actions}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with k3:
            st.markdown(
                f"""
                <div class="v2-kpi">
                    <div class="v2-kpi-label">Harvest Candidates</div>
                    <div class="v2-kpi-value">{harvest_count}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with st.expander(f"[Bid Changes]   {bid_inc} increases · {bid_dec} decreases · {bid_hold} holds", expanded=True):
            if not all_bids.empty:
                bid_preview = all_bids.sort_values("adjustment_pct", ascending=False).head(5)
                _render_preview_table(
                    bid_preview,
                    ["Targeting", "Reason", "Campaign Name", "Match Type", "Current_Bid_Calc", "New Bid", "direction"],
                )
            else:
                st.info("No bid actions generated.")

            if st.toggle("View All", key="v2_view_all_bids"):
                render_bids_tab(bids_ex, bids_pt, bids_agg, bids_auto)

        neg_kw_count = len(neg_kw) if not neg_kw.empty else 0
        neg_asin_count = 0
        if not neg_pt.empty:
            if "Is_ASIN" in neg_pt.columns:
                neg_asin_count = int(pd.to_numeric(neg_pt["Is_ASIN"], errors="coerce").fillna(0).astype(bool).sum())
            else:
                neg_asin_count = int(neg_pt.get("Term", neg_pt.get("Targeting", pd.Series(dtype=str))).astype(str).str.contains("asin", case=False, na=False).sum())

        blocked_spend = 0.0
        if not neg_kw.empty and "Spend" in neg_kw.columns:
            blocked_spend += pd.to_numeric(neg_kw["Spend"], errors="coerce").fillna(0).sum()
        if not neg_pt.empty and "Spend" in neg_pt.columns:
            blocked_spend += pd.to_numeric(neg_pt["Spend"], errors="coerce").fillna(0).sum()

        with st.expander(f"[Negatives]   {neg_kw_count} keywords · {neg_asin_count} ASINs · {_format_currency(blocked_spend)} blocked", expanded=True):
            neg_preview_rows = []
            if not neg_kw.empty:
                k = neg_kw.copy()
                k["Type"] = "Keyword"
                neg_preview_rows.append(k)
            if not neg_pt.empty:
                p = neg_pt.copy()
                p["Type"] = "Product Targeting"
                neg_preview_rows.append(p)

            if neg_preview_rows:
                neg_preview = pd.concat(neg_preview_rows, ignore_index=True).head(5)
                _render_preview_table(
                    neg_preview,
                    ["Type", "Term", "Targeting", "Reason", "Campaign Name", "Ad Group Name", "Spend"],
                )
            else:
                st.info("No negative actions generated.")

            if st.toggle("View All", key="v2_view_all_negs"):
                render_negatives_tab(neg_kw, neg_pt)

        potential_sales = 0.0
        if not harvest.empty:
            if "Sales" in harvest.columns:
                potential_sales = pd.to_numeric(harvest["Sales"], errors="coerce").fillna(0).sum()

        with st.expander(f"[Harvest]   {len(harvest)} candidates · {_format_currency(potential_sales)} potential sales", expanded=True):
            if not harvest.empty:
                harvest_preview = harvest.head(5)
                _render_preview_table(
                    harvest_preview,
                    ["Harvest_Term", "Customer Search Term", "Campaign Name", "Ad Group Name", "ROAS", "Sales", "Orders", "New Bid"],
                    reason_col="Reason",
                )
            else:
                st.info("No harvest candidates generated.")

            if st.toggle("View All", key="v2_view_all_harvest"):
                render_harvest_tab(harvest)

    with t2:
        st.markdown("### Wasted Spend Heatmap")
        from features.optimizer_shared.ui.heatmap import create_heatmap
        from features.optimizer_shared.ui.tabs.audit import render_audit_tab

        heatmap_df = create_heatmap(
            res["df"],
            res["config"],
            harvest,
            neg_kw,
            neg_pt,
            direct_bids,
            agg_bids,
        )
        render_audit_tab(heatmap_df)

        cooldown_count = 0
        if not all_bids.empty and "Reason" in all_bids.columns:
            cooldown_count = int(all_bids["Reason"].astype(str).str.contains("cooldown", case=False, na=False).sum())

        all_flags = []
        if not all_bids.empty and "Intelligence_Flags" in all_bids.columns:
            series = all_bids["Intelligence_Flags"].replace("", pd.NA).dropna()
            for raw in series:
                all_flags.extend([x.strip() for x in str(raw).split(",") if x.strip()])

        flag_counts = pd.Series(all_flags).value_counts() if all_flags else pd.Series(dtype=int)
        inventory_count = int(flag_counts.get("INVENTORY_RISK", 0))
        halo_count = int(flag_counts.get("HALO_ACTIVE", 0))
        organic_dom_count = int(flag_counts.get("CANNIBALIZE_RISK", 0))

        has_commerce = bool(st.session_state.get("v21_commerce_fetch_ok", False))

        pending_note = ""
        if not has_commerce:
            pending_note = "<div class='v2-pending'>SP-API not connected - inventory and organic signals unavailable</div>"

        inventory_line = f"{inventory_count}" if has_commerce else "not available"
        halo_line = f"{halo_count}" if has_commerce else "not available"
        organic_line = f"{organic_dom_count}" if has_commerce else "not available"

        st.markdown(
            f"""
            <div class="v2-flag-panel">
                <div class="v2-flag-title">V2 Intelligence Layer</div>
                <div class="v2-flag-line">├── Actions blocked by cooldown: <strong>{cooldown_count}</strong></div>
                <div class="v2-flag-line">├── Actions blocked — Inventory Risk: <span class="v2-pending">{inventory_line}</span></div>
                <div class="v2-flag-line">├── Actions adjusted — Halo Active: <span class="v2-pending">{halo_line}</span></div>
                <div class="v2-flag-line">└── Actions held — Organic CVR Dominant: <span class="v2-pending">{organic_line}</span></div>
                {pending_note}
            </div>
            """,
            unsafe_allow_html=True,
        )

    with t3:
        results_for_downloads = {
            "neg_kw": neg_kw,
            "neg_pt": neg_pt,
            "harvest": harvest,
            "direct_bids": direct_bids,
            "agg_bids": agg_bids,
        }
        render_downloads_tab(results_for_downloads)
