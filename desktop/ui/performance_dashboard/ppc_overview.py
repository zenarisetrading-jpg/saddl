"""
PPC Overview Tab — SADDL AdPulse Performance Dashboard

Streamlit implementation of the PPC Overview module.
Design reference: React PPCModule component.
Styling follows business_overview.py conventions.
"""

from __future__ import annotations

import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime, timedelta
from typing import Optional, Dict, Any


# ===========================================================================
# GUARDRAILS  (PRD 6.1)
# ===========================================================================

def _safe_div(n: float, d: float) -> float:
    """Safe division — returns 0 on zero/NaN denominator."""
    if not d or pd.isna(d) or pd.isna(n):
        return 0.0
    return n / d


def _fmt_currency(v) -> str:
    if v is None or (isinstance(v, float) and (pd.isna(v) or np.isnan(v))):
        return "N/A"
    return f"${v:,.2f}"


def _fmt_roas(v) -> str:
    if v is None or (isinstance(v, float) and (pd.isna(v) or np.isnan(v))):
        return "0.00×"
    return f"{min(float(v), 99.9):.2f}×"


def _fmt_pct(v) -> str:
    if v is None or (isinstance(v, float) and (pd.isna(v) or np.isnan(v))):
        return "N/A"
    return f"{float(v) * 100:.2f}%"


def _fmt_number(v) -> str:
    if v is None or (isinstance(v, float) and (pd.isna(v) or np.isnan(v))):
        return "N/A"
    return f"{int(v):,}"


def _classify_keyword(row: pd.Series, target_roas: float) -> str:
    """Flag keywords by diagnostic category."""
    if row["sales"] == 0 and row["spend"] > 50:
        return "Zero-Conversion"
    if row["roas"] > 0 and row["roas"] > target_roas * 1.5:
        return "Under-Bidding"
    if row["roas"] < target_roas:
        return "Over-Spending"
    return "Optimized"


# ===========================================================================
# THEME
# ===========================================================================

def _inject_ppc_theme() -> None:
    """Inject CSS matching the business_overview.py dark palette."""
    st.markdown(
        """
        <style>
        /* ── PPC Overview Cards ── */
        .ppc-health-card {
            position: relative;
            border-radius: 14px;
            border: 1px solid rgba(55,65,81,0.9);
            background: rgba(17,24,39,0.92);
            padding: 16px 16px 14px 16px;
            min-height: 118px;
            overflow: hidden;
            box-shadow: 0 14px 30px rgba(0,0,0,0.25);
            margin-bottom: 4px;
        }
        .ppc-health-label {
            color: #9CA3AF;
            text-transform: uppercase;
            font-weight: 700;
            font-size: 10px;
            letter-spacing: .09em;
            margin-bottom: 6px;
        }
        .ppc-health-value {
            color: #FFFFFF;
            font-weight: 800;
            font-size: 28px;
            line-height: 1.05;
            letter-spacing: -0.02em;
            margin-bottom: 6px;
        }
        .ppc-trend-badge {
            display: inline-block;
            font-size: 10px;
            font-weight: 700;
            border-radius: 8px;
            padding: 3px 7px;
            margin-top: 2px;
        }
        .ppc-trend-up-good   { color:#34D399; background:rgba(16,185,129,0.15); }
        .ppc-trend-up-bad    { color:#FB7185; background:rgba(244,63,94,0.15); }
        .ppc-trend-down-good { color:#34D399; background:rgba(16,185,129,0.15); }
        .ppc-trend-down-bad  { color:#FB7185; background:rgba(244,63,94,0.15); }
        .ppc-trend-flat      { color:#9CA3AF; background:rgba(156,163,175,0.10); }

        /* ── Section Headers ── */
        .ppc-section {
            margin-top: 18px;
            margin-bottom: 10px;
            border-bottom: 1px solid rgba(75,85,99,0.55);
            padding-bottom: 8px;
        }
        .ppc-section h3 {
            margin: 0;
            color: #F3F4F6;
            font-size: 18px;
            font-weight: 700;
            letter-spacing: -0.01em;
        }
        .ppc-section p {
            margin: 3px 0 0 0;
            color: #9CA3AF;
            font-size: 12px;
        }

        /* ── Table Wrapper ── */
        .ppc-table-wrap {
            border: 1px solid rgba(55,65,81,0.9);
            border-radius: 12px;
            overflow: hidden;
            background: rgba(17,24,39,0.92);
            box-shadow: 0 14px 30px rgba(0,0,0,0.25);
        }
        .ppc-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }
        .ppc-table thead {
            background: rgba(3,7,18,0.55);
        }
        .ppc-table th {
            text-transform: uppercase;
            color: #9CA3AF;
            letter-spacing: .06em;
            font-size: 11px;
            padding: 11px 10px;
            border-bottom: 1px solid rgba(55,65,81,0.8);
            font-weight: 600;
        }
        .ppc-table th:first-child, .ppc-table td:first-child {
            text-align: left;
            padding-left: 16px;
        }
        .ppc-table td {
            color: #D1D5DB;
            padding: 11px 10px;
            border-bottom: 1px solid rgba(55,65,81,0.40);
            text-align: right;
            vertical-align: middle;
        }
        .ppc-table tr:last-child td { border-bottom: none; }
        .ppc-table tr:hover td { background: rgba(55,65,81,0.18); }

        /* ── ROAS Badges ── */
        .roas-green  { color:#34D399; background:rgba(16,185,129,0.12);  border:1px solid rgba(16,185,129,0.30);  border-radius:6px; padding:3px 8px; font-weight:700; font-size:12px; }
        .roas-amber  { color:#F59E0B; background:rgba(245,158,11,0.12);  border:1px solid rgba(245,158,11,0.30);  border-radius:6px; padding:3px 8px; font-weight:700; font-size:12px; }
        .roas-red    { color:#FB7185; background:rgba(244,63,94,0.12);   border:1px solid rgba(244,63,94,0.30);   border-radius:6px; padding:3px 8px; font-weight:700; font-size:12px; }

        /* ── Diagnostic Flag Chips ── */
        .flag-zero  { color:#F59E0B; background:rgba(245,158,11,0.12);  border:1px solid rgba(245,158,11,0.30);  border-radius:999px; padding:3px 9px; font-size:11px; font-weight:700; }
        .flag-over  { color:#FB7185; background:rgba(244,63,94,0.12);   border:1px solid rgba(244,63,94,0.30);   border-radius:999px; padding:3px 9px; font-size:11px; font-weight:700; }
        .flag-under { color:#818CF8; background:rgba(99,102,241,0.12);  border:1px solid rgba(99,102,241,0.30);  border-radius:999px; padding:3px 9px; font-size:11px; font-weight:700; }
        .flag-ok    { color:#6B7280; background:transparent;             border:1px solid rgba(107,114,128,0.20); border-radius:999px; padding:3px 9px; font-size:11px; font-weight:500; }

        /* ── Target ROAS Pill ── */
        .ppc-target-pill {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            background: rgba(99,102,241,0.10);
            border: 1px solid rgba(99,102,241,0.25);
            border-radius: 8px;
            padding: 4px 10px;
            font-size: 12px;
            color: #818CF8;
            font-weight: 600;
        }

        /* ── Empty State ── */
        .ppc-empty {
            border: 1px dashed rgba(55,65,81,0.7);
            border-radius: 12px;
            padding: 32px;
            text-align: center;
            color: #6B7280;
            font-size: 14px;
            background: rgba(17,24,39,0.50);
        }
        .ppc-empty-icon { font-size: 28px; margin-bottom: 8px; }

        /* ── Intelligence Log ── */
        .intel-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid rgba(55,65,81,0.40);
        }
        .intel-row:last-child { border-bottom: none; }
        .intel-date   { color: #6B7280; font-size: 11px; margin-bottom: 3px; }
        .intel-action { color: #E5E7EB; font-size: 13px; font-weight: 600; }
        .intel-count  { color: #818CF8; font-weight: 800; }
        .intel-roas-before { color: #9CA3AF; font-size: 12px; }
        .intel-roas-after-up   { color: #34D399; font-size: 12px; font-weight: 700; }
        .intel-roas-after-down { color: #FB7185; font-size: 12px; font-weight: 700; }
        .intel-pending {
            font-size: 11px; font-weight: 700;
            color: #F59E0B;
            background: rgba(245,158,11,0.10);
            border: 1px solid rgba(245,158,11,0.25);
            border-radius: 6px;
            padding: 3px 8px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ===========================================================================
# UI COMPONENTS
# ===========================================================================

def _section_header(title: str, subtitle: str = "") -> None:
    sub_html = f"<p>{subtitle}</p>" if subtitle else ""
    st.markdown(
        f'<div class="ppc-section"><h3>{title}</h3>{sub_html}</div>',
        unsafe_allow_html=True,
    )


def _health_card(title: str, value: str, delta: float, inverse: bool = False) -> str:
    """Return HTML for one KPI health card."""
    is_positive = delta > 0
    is_neutral = delta == 0

    if is_neutral:
        badge_cls = "ppc-trend-flat"
        arrow = "▶"
        pct = "Flat"
    else:
        is_good = (not inverse and is_positive) or (inverse and not is_positive)
        if is_good:
            badge_cls = "ppc-trend-up-good" if is_positive else "ppc-trend-down-good"
        else:
            badge_cls = "ppc-trend-up-bad" if is_positive else "ppc-trend-down-bad"
        arrow = "▲" if is_positive else "▼"
        pct = f"{arrow} {abs(delta):.1f}%"

    return f"""
    <div class="ppc-health-card">
        <div class="ppc-health-label">{title}</div>
        <div class="ppc-health-value">{value}</div>
        <span class="ppc-trend-badge {badge_cls}">{pct}</span>
    </div>
    """


def _empty_state(message: str = "No PPC data uploaded yet") -> None:
    st.markdown(
        f'<div class="ppc-empty">'
        f'<div class="ppc-empty-icon">📊</div>'
        f'<div>{message}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def _roas_badge(roas: float, target: float) -> str:
    val = _fmt_roas(roas)
    if roas >= target:
        return f'<span class="roas-green">{val}</span>'
    elif roas >= target * 0.8:
        return f'<span class="roas-amber">{val}</span>'
    else:
        return f'<span class="roas-red">{val}</span>'


def _flag_chip(flag: str) -> str:
    map_ = {
        "Zero-Conversion": ('flag-zero', '⚠ Zero-Conv'),
        "Over-Spending":   ('flag-over',  '↘ Over-Spend'),
        "Under-Bidding":   ('flag-under', '↑ Under-Bid'),
        "Optimized":       ('flag-ok',    '✓ Optimized'),
    }
    cls, label = map_.get(flag, ('flag-ok', flag))
    return f'<span class="{cls}">{label}</span>'


# ===========================================================================
# DATA PROCESSING
# ===========================================================================

def _filter_by_date(df: pd.DataFrame, window_days: int) -> pd.DataFrame:
    """Return rows within window_days of the most recent date in df."""
    if df is None or df.empty:
        return df
    if "start_date" not in df.columns:
        return df
    df = df.copy()
    df["start_date"] = pd.to_datetime(df["start_date"], errors="coerce")
    cutoff = df["start_date"].max() - timedelta(days=window_days)
    return df[df["start_date"] >= cutoff]


def _build_stats(df: pd.DataFrame, prev_df: pd.DataFrame) -> Dict[str, Any]:
    """Aggregate totals and compute period-over-period deltas."""
    def _totals(d):
        if d is None or d.empty:
            return dict(spend=0, sales=0, impressions=0, clicks=0, orders=0)
        return dict(
            spend=d["spend"].sum(),
            sales=d["sales"].sum(),
            impressions=d["impressions"].sum() if "impressions" in d.columns else 0,
            clicks=d["clicks"].sum() if "clicks" in d.columns else 0,
            orders=d["orders"].sum() if "orders" in d.columns else 0,
        )

    cur = _totals(df)
    prv = _totals(prev_df)

    def _delta_pct(c, p):
        if not p:
            return 0.0
        return (c - p) / p * 100

    roas = _safe_div(cur["spend"] and cur["sales"], cur["spend"])
    acos = _safe_div(cur["spend"], cur["sales"])
    ctr  = _safe_div(cur["clicks"], cur["impressions"])
    cpc  = _safe_div(cur["spend"], cur["clicks"])

    p_roas = _safe_div(prv.get("sales", 0), prv.get("spend", 0) or 1)
    p_acos = _safe_div(prv.get("spend", 0), prv.get("sales", 0) or 1)
    p_ctr  = _safe_div(prv.get("clicks", 0), prv.get("impressions", 0) or 1)
    p_cpc  = _safe_div(prv.get("spend", 0), prv.get("clicks", 0) or 1)

    active_kw = len(df["target_text"].dropna().unique()) if (df is not None and not df.empty and "target_text" in df.columns) else 0

    return dict(
        spend=cur["spend"],
        roas=_safe_div(cur["sales"], cur["spend"]),
        acos=acos,
        impressions=cur["impressions"],
        clicks=cur["clicks"],
        ctr=ctr,
        cpc=cpc,
        active_keywords=active_kw,
        # deltas (pct change)
        d_spend=_delta_pct(cur["spend"], prv["spend"]),
        d_roas=_delta_pct(roas, p_roas),
        d_acos=_delta_pct(acos, p_acos),
        d_impressions=_delta_pct(cur["impressions"], prv["impressions"]),
        d_ctr=_delta_pct(ctr, p_ctr),
        d_cpc=_delta_pct(cpc, p_cpc),
    )


def _build_campaign_df(df: pd.DataFrame, target_roas: float) -> pd.DataFrame:
    """Aggregate target_stats to campaign level with computed metrics."""
    if df is None or df.empty:
        return pd.DataFrame()

    agg_cols = {"spend": "sum", "sales": "sum"}
    if "impressions" in df.columns:
        agg_cols["impressions"] = "sum"
    if "clicks" in df.columns:
        agg_cols["clicks"] = "sum"
    if "orders" in df.columns:
        agg_cols["orders"] = "sum"

    camp = df.groupby("campaign_name", as_index=False).agg(agg_cols)
    camp = camp[camp["spend"] > 0].copy()
    camp["roas"] = camp.apply(lambda r: _safe_div(r["sales"], r["spend"]), axis=1)
    camp["acos"] = camp.apply(lambda r: _safe_div(r["spend"], r["sales"]), axis=1)
    if "clicks" in camp.columns:
        camp["cpc"] = camp.apply(lambda r: _safe_div(r["spend"], r["clicks"]), axis=1)

    # Derive match group from campaign name suffix conventions
    def _group(name):
        n = str(name).upper()
        if "EXACT" in n:  return "Exact"
        if "BROAD" in n:  return "Broad"
        if "PHRASE" in n: return "Phrase"
        if "AUTO" in n:   return "Auto"
        if "PT" in n or "PRODUCT" in n: return "Product"
        return "Mixed"

    camp["group"] = camp["campaign_name"].apply(_group)
    return camp.sort_values("spend", ascending=False).reset_index(drop=True)


def _build_keyword_df(
    df: pd.DataFrame,
    target_roas: float,
    match_type_filter: str = "All",
) -> pd.DataFrame:
    """Aggregate to keyword level, classify diagnostics, apply match type filter."""
    if df is None or df.empty:
        return pd.DataFrame()

    group_cols = ["target_text"]
    if "match_type" in df.columns:
        group_cols.append("match_type")
    if "campaign_name" in df.columns:
        group_cols.append("campaign_name")

    agg_cols = {"spend": "sum", "sales": "sum"}
    if "impressions" in df.columns:
        agg_cols["impressions"] = "sum"
    if "clicks" in df.columns:
        agg_cols["clicks"] = "sum"
    if "orders" in df.columns:
        agg_cols["orders"] = "sum"

    kw = df.groupby(group_cols, as_index=False).agg(agg_cols)
    kw = kw[kw["spend"] > 0].copy()
    kw["roas"] = kw.apply(lambda r: _safe_div(r["sales"], r["spend"]), axis=1)

    # Apply match type filter
    if match_type_filter != "All" and "match_type" in kw.columns:
        kw = kw[kw["match_type"].str.upper() == match_type_filter.upper()]

    kw["flag"] = kw.apply(lambda r: _classify_keyword(r, target_roas), axis=1)
    return kw.sort_values("spend", ascending=False).head(20).reset_index(drop=True)


# ===========================================================================
# DATA FETCHING
# ===========================================================================

@st.cache_data(ttl=300, show_spinner=False)
def _fetch_target_stats(client_id: str, test_mode: bool):
    from features.optimizer_shared.data_access import fetch_target_stats_cached
    return fetch_target_stats_cached(client_id, test_mode)


def _fetch_actions(client_id: str, test_mode: bool, limit: int = 200):
    try:
        from app_core.db_manager import get_db_manager
        db = get_db_manager(test_mode)
        if db and client_id:
            return db.get_actions_by_client(client_id, limit=limit)
    except Exception:
        pass
    return []


# ===========================================================================
# SECTION RENDERERS
# ===========================================================================

def _render_health_strip(stats: Dict[str, Any]) -> None:
    cards = [
        ("Total Ad Spend",   _fmt_currency(stats["spend"]),          stats["d_spend"],       True),
        ("Blended ROAS",     _fmt_roas(stats["roas"]),                stats["d_roas"],        False),
        ("ACOS",             _fmt_pct(stats["acos"]),                 stats["d_acos"],        True),
        ("Impressions",      _fmt_number(stats["impressions"]),       stats["d_impressions"], False),
        ("CTR",              _fmt_pct(stats["ctr"]),                  stats["d_ctr"],         False),
        ("Avg. CPC",         _fmt_currency(stats["cpc"]),             stats["d_cpc"],         True),
    ]

    cols = st.columns(7)
    for idx, (title, value, delta, inverse) in enumerate(cards):
        with cols[idx]:
            st.markdown(_health_card(title, value, delta, inverse), unsafe_allow_html=True)

    # Active keywords gets its own styled card (no delta)
    with cols[6]:
        st.markdown(
            f"""
            <div class="ppc-health-card">
                <div class="ppc-health-label">Active Keywords</div>
                <div class="ppc-health-value">{_fmt_number(stats["active_keywords"])}</div>
                <span class="ppc-trend-badge ppc-trend-flat">Unique targets</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_campaign_table(campaign_df: pd.DataFrame, target_roas: float) -> None:
    if campaign_df.empty:
        _empty_state("No campaign data for this period")
        return

    # Build HTML table
    rows_html = ""
    for _, row in campaign_df.iterrows():
        cpc_val = _fmt_currency(row.get("cpc")) if "cpc" in row else "N/A"
        rows_html += f"""
        <tr>
            <td style="text-align:left">
                <div style="font-weight:600;color:#E5E7EB;font-size:13px">{row['campaign_name']}</div>
                <div style="font-size:11px;color:#6B7280">{row.get('group','')}</div>
            </td>
            <td>{_fmt_currency(row['spend'])}</td>
            <td style="color:#34D399">{_fmt_currency(row['sales'])}</td>
            <td>{_roas_badge(row['roas'], target_roas)}</td>
            <td>{_fmt_pct(row['acos'])}</td>
            <td style="color:#6B7280">{_fmt_number(row.get('impressions', 0))}</td>
            <td style="color:#6B7280">{cpc_val}</td>
        </tr>
        """

    legend = (
        '<span class="roas-green" style="font-size:11px">▶ Above Target</span> &nbsp;'
        '<span class="roas-amber" style="font-size:11px">▶ Within 20%</span> &nbsp;'
        '<span class="roas-red"   style="font-size:11px">▶ Below Target</span>'
    )

    st.markdown(
        f"""
        <div style="display:flex;justify-content:flex-end;margin-bottom:8px">{legend}</div>
        <div class="ppc-table-wrap">
        <table class="ppc-table">
            <thead>
                <tr>
                    <th>Campaign</th>
                    <th>Spend</th>
                    <th>Sales</th>
                    <th>ROAS</th>
                    <th>ACOS</th>
                    <th>Impressions</th>
                    <th>CPC</th>
                </tr>
            </thead>
            <tbody>{rows_html}</tbody>
        </table>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_keyword_diagnostics(kw_df: pd.DataFrame, target_roas: float) -> None:
    if kw_df.empty:
        _empty_state("No keyword data for this period")
        return

    rows_html = ""
    for _, row in kw_df.iterrows():
        match_label = f"[{row['match_type']}]" if "match_type" in row and pd.notna(row.get("match_type")) else ""
        campaign = str(row.get("campaign_name", ""))[:48] + ("…" if len(str(row.get("campaign_name", ""))) > 48 else "")
        roas_str = f"{min(float(row['roas']), 99.9):.2f}×" if row["sales"] > 0 else "0.00×"

        rows_html += f"""
        <tr>
            <td style="text-align:left">
                <div style="font-weight:600;color:#E5E7EB;font-size:13px">{row['target_text']}</div>
                <div style="font-size:11px;color:#6B7280">{match_label}</div>
            </td>
            <td style="color:#9CA3AF;font-size:12px;max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{campaign}</td>
            <td>{_fmt_currency(row['spend'])}</td>
            <td style="color:#9CA3AF">{_fmt_currency(row['sales'])}</td>
            <td style="font-weight:600;color:#D1D5DB">{roas_str}</td>
            <td>{_flag_chip(row['flag'])}</td>
        </tr>
        """

    st.markdown(
        f"""
        <div class="ppc-table-wrap">
        <table class="ppc-table">
            <thead>
                <tr>
                    <th>Target Keyword</th>
                    <th>Campaign</th>
                    <th>Spend</th>
                    <th>Sales</th>
                    <th>ROAS</th>
                    <th style="text-align:center">Diagnostic Flag</th>
                </tr>
            </thead>
            <tbody>{rows_html}</tbody>
        </table>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_intelligence_log(client_id: str, test_mode: bool) -> None:
    """Render SADDL Intelligence Log from optimizer action history."""
    actions = _fetch_actions(client_id, test_mode, limit=300)

    if not actions:
        _empty_state("No optimizer runs recorded yet")
        return

    # Group by date (day) to create "run" summaries
    df = pd.DataFrame(actions)
    if df.empty:
        _empty_state("No optimizer runs recorded yet")
        return

    df["action_date"] = pd.to_datetime(df["action_date"], errors="coerce")
    df["run_day"] = df["action_date"].dt.date

    runs = (
        df.groupby("run_day")
        .agg(
            action_count=("id", "count"),
            primary_type=("action_type", lambda s: s.value_counts().index[0] if len(s) else ""),
            last_time=("action_date", "max"),
        )
        .reset_index()
        .sort_values("run_day", ascending=False)
        .head(5)
    )

    today = datetime.utcnow().date()
    yesterday = today - timedelta(days=1)

    rows_html = ""
    for _, run in runs.iterrows():
        day = run["run_day"]
        if day == today:
            date_label = f"Today, {run['last_time'].strftime('%I:%M %p') if pd.notna(run['last_time']) else ''}"
        elif day == yesterday:
            date_label = f"Yesterday, {run['last_time'].strftime('%I:%M %p') if pd.notna(run['last_time']) else ''}"
        else:
            date_label = str(day)

        action_type = str(run["primary_type"]).replace("_", " ").title()
        count = int(run["action_count"])

        rows_html += f"""
        <div class="intel-row">
            <div>
                <div class="intel-date">{date_label}</div>
                <div class="intel-action">
                    <span class="intel-count">{count}</span> actions &nbsp;·&nbsp; {action_type}
                </div>
            </div>
            <div>
                <span class="intel-pending">Pending impact</span>
            </div>
        </div>
        """

    st.markdown(
        f"""
        <div style="border:1px solid rgba(55,65,81,0.9);border-radius:12px;
                    background:rgba(17,24,39,0.92);padding:16px 18px;
                    box-shadow:0 14px 30px rgba(0,0,0,0.25)">
            {rows_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div style="margin-top:10px;text-align:center">'
        '<a href="#" style="color:#818CF8;font-size:12px;font-weight:600;'
        'text-decoration:none">View Full Impact Analysis →</a></div>',
        unsafe_allow_html=True,
    )


# ===========================================================================
# MAIN ENTRY POINT
# ===========================================================================

def render_ppc_overview() -> None:
    """Render the PPC Overview tab. Called from run_performance_hub()."""
    _inject_ppc_theme()

    # ── Session state defaults ──────────────────────────────────────────────
    if "ppc_window_days" not in st.session_state:
        st.session_state["ppc_window_days"] = 30
    if "ppc_match_filter" not in st.session_state:
        st.session_state["ppc_match_filter"] = "All"

    client_id = st.session_state.get("client_id") or st.session_state.get("selected_client_id") or ""
    test_mode = st.session_state.get("test_mode", False)
    target_roas = float(st.session_state.get("target_roas", 3.0))

    # ── Top bar ─────────────────────────────────────────────────────────────
    top_l, top_r = st.columns([5, 2])
    with top_l:
        st.markdown(
            '<div class="bo-topbar">'
            '<p class="bo-title">PPC Overview</p>'
            '<p class="bo-subtitle">Campaign and keyword-level actionability layer.</p>'
            '</div>',
            unsafe_allow_html=True,
        )
    with top_r:
        st.markdown("<div style='padding-top:12px'>", unsafe_allow_html=True)
        window_choice = st.radio(
            "Date window",
            options=[14, 30, 60],
            index=[14, 30, 60].index(st.session_state["ppc_window_days"]),
            format_func=lambda x: f"{x}D",
            horizontal=True,
            label_visibility="collapsed",
            key="ppc_window_radio",
        )
        if window_choice != st.session_state["ppc_window_days"]:
            st.session_state["ppc_window_days"] = window_choice
            st.cache_data.clear()
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    window_days: int = st.session_state["ppc_window_days"]

    # Target ROAS pill
    st.markdown(
        f'<div style="display:flex;justify-content:flex-end;margin-bottom:4px">'
        f'<span class="ppc-target-pill">⚡ Target ROAS: {target_roas:.1f}×</span></div>',
        unsafe_allow_html=True,
    )

    # ── Load data ───────────────────────────────────────────────────────────
    raw_df = _fetch_target_stats(client_id, test_mode) if client_id else None

    if raw_df is None or raw_df.empty:
        st.markdown("<br>", unsafe_allow_html=True)
        _empty_state("No PPC data found. Upload a bulk file via the Data Hub to get started.")
        return

    # Filter current window
    cur_df = _filter_by_date(raw_df, window_days)

    # Prior period (same length, immediately before current window)
    if "start_date" in raw_df.columns:
        raw_df["start_date"] = pd.to_datetime(raw_df["start_date"], errors="coerce")
        cur_cutoff = raw_df["start_date"].max() - timedelta(days=window_days)
        prev_cutoff = cur_cutoff - timedelta(days=window_days)
        prev_df = raw_df[
            (raw_df["start_date"] >= prev_cutoff) & (raw_df["start_date"] < cur_cutoff)
        ]
    else:
        prev_df = pd.DataFrame()

    stats = _build_stats(cur_df, prev_df)
    match_filter = st.session_state["ppc_match_filter"]

    # ── Section 1: PPC Health Strip ──────────────────────────────────────────
    _section_header("PPC Health", f"Last {window_days} days · vs prior {window_days}-day period")
    _render_health_strip(stats)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Sections 2 + 3: Campaign table + Intelligence Log (side by side) ────
    main_col, side_col = st.columns([2, 1])

    with main_col:
        _section_header(
            "Campaign Performance",
            "Sorted by spend · ROAS color-coded against target",
        )

        # Match type filter
        match_options = ["All", "Exact", "Broad", "Phrase", "Auto", "PT"]
        new_filter = st.segmented_control(
            "Match type",
            options=match_options,
            default=match_filter,
            key="ppc_match_seg",
            label_visibility="collapsed",
        ) if hasattr(st, "segmented_control") else st.selectbox(
            "Match type",
            options=match_options,
            index=match_options.index(match_filter) if match_filter in match_options else 0,
            key="ppc_match_sel",
            label_visibility="collapsed",
        )

        if new_filter != match_filter:
            st.session_state["ppc_match_filter"] = new_filter
            st.rerun()

        # Filter df by match type for campaign table
        filtered_df = cur_df.copy()
        if match_filter != "All" and "match_type" in filtered_df.columns:
            filtered_df = filtered_df[
                filtered_df["match_type"].str.upper() == match_filter.upper()
            ]

        campaign_df = _build_campaign_df(filtered_df, target_roas)
        _render_campaign_table(campaign_df, target_roas)

    with side_col:
        _section_header("SADDL Intelligence Log", "Optimizer run history")
        _render_intelligence_log(client_id, test_mode)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Section 4: Keyword Diagnostics ──────────────────────────────────────
    _section_header(
        "Keyword Diagnostics",
        "Top 20 by spend · automated flagging for over-spending, under-bidding, and zero-conversion terms",
    )

    kw_df = _build_keyword_df(cur_df, target_roas, match_filter)
    _render_keyword_diagnostics(kw_df, target_roas)

    st.markdown("<br>", unsafe_allow_html=True)
