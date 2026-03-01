"""
Tier 1 Campaign Recommendation Panel

Renders campaign-level action recommendations ABOVE the row-level optimizer results.
The user reviews and acts on these first, then scrolls to individual bid adjustments.

Accepted campaigns are stored in st.session_state["tier1_accepted_campaigns"] and
excluded from Tier 2 (bid table) and Downloads (bulk file export).

Styling: uses the exact same CSS classes and patterns already defined in runner.py
(.v2-kpi, .v2-kpi-label, .v2-kpi-value, .v2-flag-panel, .v2-flag-title, .v2-flag-line).
No new color values, component types, or CSS classes are introduced.
"""

from __future__ import annotations

import streamlit as st
import pandas as pd


_REC_EMOJI = {
    "PAUSE":           "🔴",
    "REDUCE_BUDGET":   "🟠",
    "RESTRUCTURE":     "🟡",
    "INCREASE_BUDGET": "🟢",
    "SCALE":           "🟢",
    "MAINTAIN":        "⚪",
}

_ACTIONABLE = {"PAUSE", "REDUCE_BUDGET", "RESTRUCTURE", "INCREASE_BUDGET", "SCALE"}


def render_tier1_campaign_panel(campaign_recs: pd.DataFrame) -> list[str]:
    """
    Render Tier 1 campaign-level recommendations.

    Parameters
    ----------
    campaign_recs : pd.DataFrame
        Output of generate_campaign_recommendations().

    Returns
    -------
    list[str]
        Campaign names the user accepted for Tier 1 action.
        These are EXCLUDED from Tier 2 bid table and Downloads.
        Also stored in st.session_state["tier1_accepted_campaigns"].
    """
    if campaign_recs is None or campaign_recs.empty:
        return []

    actionable = campaign_recs[campaign_recs["recommendation"].isin(_ACTIONABLE)].copy()
    maintain   = campaign_recs[campaign_recs["recommendation"] == "MAINTAIN"].copy()

    if actionable.empty:
        st.markdown(
            "<div class='v2-flag-panel'>"
            "<div class='v2-flag-title'>Tier 1: Campaign Review</div>"
            "<div class='v2-flag-line'>✓ All campaigns performing within acceptable range "
            "— no campaign-level actions needed.</div>"
            "</div>",
            unsafe_allow_html=True,
        )
        return []

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown(
        "<div class='v2-flag-title' style='font-size:1.1rem;margin-bottom:4px;'>"
        "Tier 1 — Campaign Actions</div>"
        "<div class='v2-flag-line' style='margin-bottom:12px;'>"
        "Review these before looking at individual bid adjustments. "
        "Checked campaigns are excluded from the bid table below.</div>",
        unsafe_allow_html=True,
    )

    # ── Summary KPI cards ─────────────────────────────────────────────────────
    pause_count    = int((actionable["recommendation"] == "PAUSE").sum())
    scale_count    = int(actionable["recommendation"].isin(["SCALE", "INCREASE_BUDGET"]).sum())
    restructure_c  = int(actionable["recommendation"].isin(["RESTRUCTURE", "REDUCE_BUDGET"]).sum())
    total_impact   = float(actionable["estimated_monthly_impact"].sum())

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f"<div class='v2-kpi'>"
            f"<div class='v2-kpi-label'>Campaigns Flagged</div>"
            f"<div class='v2-kpi-value'>{len(actionable)} of {len(campaign_recs)}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"<div class='v2-kpi'>"
            f"<div class='v2-kpi-label'>Pause Candidates</div>"
            f"<div class='v2-kpi-value'>{pause_count}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"<div class='v2-kpi'>"
            f"<div class='v2-kpi-label'>Scale Candidates</div>"
            f"<div class='v2-kpi-value'>{scale_count}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            f"<div class='v2-kpi'>"
            f"<div class='v2-kpi-label'>Est. Monthly Impact</div>"
            f"<div class='v2-kpi-value'>${total_impact:,.0f}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown("<div style='margin-top:6px;'></div>", unsafe_allow_html=True)

    # ── Per-campaign rows with checkboxes ─────────────────────────────────────
    st.markdown(
        "<div class='v2-flag-line' style='margin-bottom:6px;'>"
        "<strong>Check campaigns to act on</strong> — unchecked campaigns flow to "
        "Tier 2 bid optimization below.</div>",
        unsafe_allow_html=True,
    )

    accepted: list[str] = []

    for _, row in actionable.iterrows():
        emoji      = _REC_EMOJI.get(row["recommendation"], "⚪")
        camp_name  = row["campaign_name"]
        default_on = row["recommendation"] == "PAUSE" and row.get("confidence") == "HIGH"

        col_cb, col_body = st.columns([0.04, 0.96])
        with col_cb:
            checked = st.checkbox(
                label=" ",
                value=bool(default_on),
                key=f"tier1_cb_{camp_name}",
                label_visibility="collapsed",
            )
        with col_body:
            st.markdown(
                f"<div class='v2-flag-line'>"
                f"{emoji} <strong>{row['recommendation']}</strong> — {camp_name}<br>"
                f"<span style='color:#94a3b8;font-size:0.88rem;'>"
                f"ROAS {row['roas']:.1f}× &nbsp;·&nbsp; "
                f"{row['orders']} orders &nbsp;·&nbsp; "
                f"${row['spend']:,.0f} spend &nbsp;·&nbsp; "
                f"{row['efficiency_ratio']:.2f}× efficiency"
                f"</span><br>"
                f"<span style='color:#94a3b8;font-size:0.85rem;font-style:italic;'>"
                f"{row['reason']}"
                f"</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

        if checked:
            accepted.append(camp_name)

    # ── MAINTAIN campaigns in collapsed expander ──────────────────────────────
    if not maintain.empty:
        with st.expander(f"✓ {len(maintain)} campaign(s) performing normally", expanded=False):
            display_cols = [
                c for c in ["campaign_name", "roas", "orders", "efficiency_ratio", "reason"]
                if c in maintain.columns
            ]
            st.dataframe(
                maintain[display_cols],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "campaign_name":  st.column_config.TextColumn("Campaign"),
                    "roas":           st.column_config.NumberColumn("ROAS", format="%.2f×"),
                    "efficiency_ratio": st.column_config.NumberColumn("Efficiency", format="%.2f×"),
                    "reason":         st.column_config.TextColumn("Notes", width="large"),
                },
            )

    # ── Status lines ──────────────────────────────────────────────────────────
    skipped = len(actionable) - len(accepted)
    if accepted:
        st.success(
            f"✓ {len(accepted)} campaign(s) accepted for Tier 1 action — "
            f"excluded from bid table and bulk file below."
        )
    if skipped > 0:
        st.info(
            f"↓ {skipped} campaign(s) skipped — flowing to Tier 2 row-level "
            f"optimization with full cascade intelligence applied."
        )

    st.divider()

    # Persist to session state so Downloads tab can read it
    st.session_state["tier1_accepted_campaigns"] = accepted

    return accepted
