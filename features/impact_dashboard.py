"""
Impact Dashboard Module

Sleek before/after analysis dashboard showing the ROI of optimization actions.
Features:
- Hero tiles with key metrics
- Waterfall chart by action type
- Winners/Losers bar chart
- Detailed drill-down table
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from core.db_manager import get_db_manager

@st.cache_data(ttl=3600, show_spinner=False)  # Restored production TTL
def _fetch_impact_data(client_id: str, test_mode: bool, window_days: int = 7, cache_version: str = "v4_dedup") -> Tuple[pd.DataFrame, Dict[str, Any]]:

    """
    Cached data fetcher for impact analysis.
    Prevents re-querying the DB on every rerun or tab switch.
    
    Args:
        client_id: Account ID
        test_mode: Whether using test database
        window_days: Number of days for before/after comparison window
        cache_version: Version string that changes when data is uploaded (invalidates cache)
    """
    try:
        db = get_db_manager(test_mode)
        impact_df = db.get_action_impact(client_id, window_days=window_days)
        full_summary = db.get_impact_summary(client_id, window_days=window_days)
        return impact_df, full_summary
    except Exception as e:
        # Return empty structures on failure to prevent UI crash
        print(f"Cache miss error: {e}")
        return pd.DataFrame(), {
            'total_actions': 0, 
            'roas_before': 0, 'roas_after': 0, 'roas_lift_pct': 0,
            'incremental_revenue': 0,
            'p_value': 1.0, 'is_significant': False, 'confidence_pct': 0,
            'implementation_rate': 0, 'confirmed_impact': 0, 'pending': 0,
            'win_rate': 0, 'winners': 0, 'losers': 0,
            'by_action_type': {}
        }





def render_impact_dashboard():
    """Main render function for Impact Dashboard."""
    
    # Header Layout with Toggle
    col_header, col_toggle = st.columns([3, 1])
    
    with col_header:
        st.markdown("## :material/monitoring: Impact & Results")
        st.caption("Measured impact of executed optimization actions")

    with col_toggle:
        st.write("") # Spacer
        # Use radio buttons with horizontal layout for time frame selection
        time_frame = st.radio(
            "Time Frame",
            options=["7D", "14D", "30D", "60D", "90D"],
            index=2,  # Default to 30D (index 2)
            horizontal=True,
            label_visibility="collapsed",
            key="impact_time_frame"
        )
        if time_frame is None:
            time_frame = "30D"

    
    # Dark theme compatible CSS
    st.markdown("""
    <style>
    /* Dark theme buttons */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
        color: white !important;
        border: none !important;
        font-weight: 600 !important;
    }
    .stDownloadButton > button:hover {
        background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
        transform: translateY(-1px);
    }
    /* Data table dark theme compatibility */
    .stDataFrame {
        background: transparent !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Check for database manager
    db_manager = st.session_state.get('db_manager')
    if db_manager is None:
        st.warning("⚠️ Database not initialized. Please ensure you're in the main app.")
        return
    
    # USE ACTIVE ACCOUNT from session state
    selected_client = st.session_state.get('active_account_id', 'default_client')
    
    if not selected_client:
        st.error("⚠️ No account selected! Please select an account in the sidebar.")
        return
    
    # Get available dates for selected account
    available_dates = db_manager.get_available_dates(selected_client)
    
    if not available_dates:
        st.warning(f"⚠️ No action data found for account '{st.session_state.get('active_account_name', selected_client)}'. "\
                   "Run the optimizer to log actions.")
        return
    
    # Sidebar info - show active account
    with st.sidebar:
        # Just show account info, removed comparison settings
        st.info(f"**Account:** {st.session_state.get('active_account_name', selected_client)}")
        st.caption(f"📅 Data available: {len(available_dates)} weeks")
    
    # Get impact data using auto time-lag matching (no date params needed)
    # Get impact data using auto time-lag matching (cached)
    with st.spinner("Calculating impact..."):
        # Use cached fetcher
        test_mode = st.session_state.get('test_mode', False)
        # Force cache bust with version + timestamp
        cache_version = "v8_decision_impact_" + str(st.session_state.get('data_upload_timestamp', 'init'))
        # Parse time frame to days for the before/after comparison window
        time_frame_days = {"7D": 7, "14D": 14, "30D": 30, "60D": 60, "90D": 90}
        window_days = time_frame_days.get(time_frame, 7)
        impact_df, full_summary = _fetch_impact_data(selected_client, test_mode, window_days, cache_version)
        
        # Terminal debug: Show Decision Impact metrics
        print(f"\n=== DECISION IMPACT DEBUG ({selected_client}) ===")
        for w in [7, 14, 30]:
            try:
                db = get_db_manager(test_mode)
                s = db.get_impact_summary(selected_client, window_days=w)
                val = s.get('validated', {})
                print(f"{w}D: ROAS {val.get('roas_before',0):.2f}x -> {val.get('roas_after',0):.2f}x | Lift: {val.get('roas_lift_pct',0):.1f}% | N={val.get('total_actions',0)}")
                print(f"    Decision Impact: {val.get('decision_impact',0):.0f} | Spend Avoided: {val.get('spend_avoided',0):.0f}")
                print(f"    Good: {val.get('pct_good',0):.0f}% | Neutral: {val.get('pct_neutral',0):.0f}% | Bad: {val.get('pct_bad',0):.0f}% | Market Downshift: {val.get('market_downshift_count',0)}")
            except Exception as e:
                print(f"{w}D: Error - {e}")
        print("===================================\n")


    
    # Fixed KeyError: Use 'all' summary for initial check
    if full_summary.get('all', {}).get('total_actions', 0) == 0:
        st.info("No actions with matching 'next week' performance data found. This means either:\n"
                "- Actions were logged but no performance data for the following week exists yet.\n"
                "- Upload next week's Search Term Report and run the optimizer to see impact.")
        return
        
    # Period Header Preparation
    compare_text = ""
    p = full_summary.get('period_info', {})
    if p.get('before_start'):
        try:
            def fmt(d):
                if isinstance(d, str):
                    return datetime.strptime(d[:10], "%Y-%m-%d").strftime("%b %d")
                return d.strftime("%b %d")
            
            b_range = f"{fmt(p['before_start'])} - {fmt(p['before_end'])}"
            a_range = f"{fmt(p['after_start'])} - {fmt(p['after_end'])}"
            compare_text = f"Comparing <code>{b_range}</code> (Before) vs. <code>{a_range}</code> (After)"
        except Exception as e:
            print(f"Header date error: {e}")
        
    
    # Time frame (7D, 14D, 30D) now controls the before/after comparison window in the SQL query
    # No need to filter actions here - all actions with measurable impact are returned
    time_frame_days = {
        "7D": 7,
        "14D": 14,
        "30D": 30,
        "60D": 60,
        "90D": 90
    }
    days = time_frame_days.get(time_frame, 30)
    filter_label = f"{days}-Day Window"
    
    # Get latest available date for reference
    available_dates = db_manager.get_available_dates(selected_client)
    ref_date = pd.to_datetime(available_dates[0]) if available_dates else pd.Timestamp.now()
    
    # NO ADDITIONAL FILTERING - get_action_impact already handles:
    # 1. Fixed windows based on selected days
    # 2. Only eligible actions
    # The UI uses full_summary directly from the backend for statistical rigor.

    
    # Redundant date range callout removed (merged into top header)
    
    # ==========================================
    # CONSOLIDATED PREMIUM HEADER
    # ==========================================
    if not impact_df.empty:
        theme_mode = st.session_state.get('theme_mode', 'dark')
        cal_color = "#60a5fa" if theme_mode == 'dark' else "#3b82f6"
        calendar_icon = f'<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="{cal_color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 6px;"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>'
        
        action_count = len(impact_df)
        unique_weeks = impact_df['action_date'].nunique() if 'action_date' in impact_df.columns else 1
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, rgba(59, 130, 246, 0.05) 100%);
                    border: 1px solid rgba(59, 130, 246, 0.3);
                    border-radius: 12px; padding: 16px; margin-bottom: 24px;">
            <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px;">
                <div style="display: flex; align-items: center;">
                    {calendar_icon}
                    <span style="font-weight: 600; font-size: 1.1rem; color: #60a5fa; margin-right: 12px;">{time_frame} Impact Summary</span>
                    <span style="color: #94a3b8; font-size: 0.95rem;">{compare_text}</span>
                </div>
                <div style="color: #94a3b8; font-size: 0.85rem; opacity: 0.8;">
                    {action_count} actions total across {unique_weeks} runs
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ==========================================
    # UNIVERSAL VALIDATION TOGGLE
    # ==========================================
    toggle_col1, toggle_col2 = st.columns([1, 5])
    with toggle_col1:
        show_validated_only = st.toggle(
            "Validated Only", 
            value=True, 
            help="Show only actions confirmed by actual CPC/Bid data"
        )
    with toggle_col2:
        if show_validated_only:
            st.caption("✓ Showing **validated actions only** — filtering all cards and charts.")
        else:
            st.caption("📊 Showing **all actions** — including pending and unverified.")
            
    # ==========================================
    # DATA PREPARATION: ACTIVE vs DORMANT
    # ==========================================
    # Filter based on toggle BEFORE splitting
    v_mask = impact_df['validation_status'].str.contains('✓|CPC Validated|CPC Match|Directional|Confirmed|Normalized', na=False, regex=True)
    display_df = impact_df[v_mask].copy() if show_validated_only else impact_df.copy()
    
    # Measured (Active) vs Pending (Dormant)
    # Measured if there was spend in BEFORE or AFTER window
    measured_mask = (display_df['before_spend'].fillna(0) + display_df['observed_after_spend'].fillna(0)) > 0
    active_df = display_df[measured_mask].copy()
    dormant_df = display_df[~measured_mask].copy()
    
    # Use pre-calculated summary from backend for the tiles
    display_summary = full_summary.get('validated' if show_validated_only else 'all', {})
    
    # HERO TILES (Now synchronized)
    _render_hero_tiles(display_summary, len(active_df), len(dormant_df))
    
    st.divider()

    with st.expander("🔍 View supporting evidence", expanded=True):
        # ==========================================
        # MEASURED vs PENDING IMPACT TABS
        # ==========================================
        tab_measured, tab_pending = st.tabs([
            "▸ Measured Impact", 
            "▸ Pending Impact"
        ])
        
        with tab_measured:
            # Filter active_df based on the universal toggle
            active_display = display_df[(display_df['before_spend'].fillna(0) + display_df['after_spend'].fillna(0)) > 0] if not display_df.empty else display_df
            
            if active_display.empty:
                st.info("No measured impact data for the selected filter")
            else:
                # IMPACT ANALYTICS: Attribution Waterfall + Stacked Revenue Bar
                _render_new_impact_analytics(display_summary, active_display, show_validated_only)
                
                st.divider()
                
                # Drill-down table with migration badges
                _render_drill_down_table(active_display, show_migration_badge=True)
        
        with tab_pending:
            if dormant_df.empty:
                st.success("✨ All executed optimizations have measured activity!")
            else:
                st.info("💤 **Pending Impact** — These actions were applied to keywords/targets "
                    "with $0 spend in both periods. The baseline is established and impact is pending traffic.")
                
                # Simple table for dormant
                _render_dormant_table(dormant_df)

    st.markdown("<br>", unsafe_allow_html=True)
    st.caption(
        "This view presents measured outcomes of executed actions over the selected period. "
        "Detailed diagnostics are available for deeper investigation when required."
    )


def _render_empty_state():
    """Render empty state when no data exists."""
    # Theme-aware chart icon
    icon_color = "#8F8CA3"
    empty_icon = f'<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="{icon_color}" stroke-opacity="0.2" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>'
    st.markdown(f"""
    <div style="text-align: center; padding: 60px 20px;">
        <div style="margin-bottom: 20px;">{empty_icon}</div>
        <h2 style="color: #8F8CA3; opacity: 0.5;">No Impact Data Yet</h2>
        <p style="color: #8F8CA3; opacity: 0.35; max-width: 400px; margin: 0 auto;">
            Run the optimizer and download the report to start tracking actions. 
            Then upload next week's data to see the impact.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    ### How to use Impact Analysis:
    
    1. **Week 1**: Upload Search Term Report → Run Optimizer → Download Full Report
    2. **Week 2**: Upload new Search Term Report → Come here to see before/after comparison
    """)


def _render_hero_tiles(summary: Dict[str, Any], active_count: int = 0, dormant_count: int = 0):
    """Render the hero metric tiles with ROAS analytics."""
    
    # Theme-aware colors
    theme_mode = st.session_state.get('theme_mode', 'dark')
    
    if theme_mode == 'dark':
        positive_text = "#4ade80"  # Green-400
        negative_text = "#f87171"  # Red-400
        neutral_text = "#cbd5e1"  # Slate-300
        muted_text = "#8F8CA3"
    else:
        positive_text = "#16a34a"  # Green-600
        negative_text = "#dc2626"  # Red-600
        neutral_text = "#475569"  # Slate-600
        muted_text = "#64748b"
    
    # SVG Icons
    icon_color = "#8F8CA3"
    
    # Chart bars icon (Actions)
    actions_icon = f'<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="{icon_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>'
    
    # Trending up icon (ROAS Lift)
    roas_icon = f'<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="{icon_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline><polyline points="17 6 23 6 23 12"></polyline></svg>'
    
    # Dollar sign icon (Revenue)
    revenue_icon = f'<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="{icon_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="1" x2="12" y2="23"></line><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>'
    
    # Check circle icon (Implementation)
    impl_icon = f'<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="{icon_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>'
    
    # Stat sig indicators
    sig_positive = f'<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="#22c55e" stroke="#22c55e" stroke-width="2"><circle cx="12" cy="12" r="10"></circle></svg>'
    sig_negative = f'<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#64748b" stroke-width="2"><circle cx="12" cy="12" r="10"></circle></svg>'
    
    # Extract metrics
    total_actions = summary.get('total_actions', 0)
    roas_lift = summary.get('roas_lift_pct', 0)
    incr_revenue = summary.get('incremental_revenue', 0)
    impl_rate = summary.get('implementation_rate', 0)
    is_sig = summary.get('is_significant', False)
    p_value = summary.get('p_value', 1.0)
    confidence = summary.get('confidence_pct', 0)
    

    
    # By action type for callout
    by_type = summary.get('by_action_type', {})
    cost_saved = sum(v['net_sales'] for k, v in by_type.items() if 'NEGATIVE' in k.upper())
    harvest_gains = sum(v['net_sales'] for k, v in by_type.items() if 'HARVEST' in k.upper())
    bid_changes = sum(v['net_sales'] for k, v in by_type.items() if 'BID' in k.upper())
    
    # CSS
    st.markdown("""
    <style>
    .hero-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.06) 0%, rgba(255,255,255,0.02) 100%);
        border: 1px solid rgba(143, 140, 163, 0.15);
        border-radius: 12px;
        padding: 20px 16px;
        text-align: center;
    }
    .hero-label {
        font-size: 0.7rem;
        color: #8F8CA3;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
    }
    .hero-value {
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 4px;
    }
    .hero-sub {
        font-size: 0.75rem;
        color: #8F8CA3;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 4px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # ==========================================
    # PRIMARY METRICS CARDS (Row 1) - Decision-Focused
    # ==========================================
    # Extract new Decision Impact metrics
    decision_impact = summary.get('decision_impact', 0)
    spend_avoided = summary.get('spend_avoided', 0)
    pct_good = summary.get('pct_good', 0)
    pct_neutral = summary.get('pct_neutral', 0)
    pct_bad = summary.get('pct_bad', 0)
    market_downshift = summary.get('market_downshift_count', 0)
    
    # NPS-style Decision Quality Score = Good% - Bad%
    decision_quality_score = pct_good - pct_bad
    
    from utils.formatters import get_account_currency
    currency = get_account_currency()
    
    # Icons for new cards
    target_icon = f'<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="{icon_color}" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><circle cx="12" cy="12" r="6"></circle><circle cx="12" cy="12" r="2"></circle></svg>'
    shield_icon = f'<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="{icon_color}" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>'
    score_icon = f'<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="{icon_color}" stroke-width="2"><path d="M12 20V10"></path><path d="M18 20V4"></path><path d="M6 20v-4"></path></svg>'
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        di_color = positive_text if decision_impact > 0 else negative_text if decision_impact < 0 else neutral_text
        di_prefix = '+' if decision_impact > 0 else ''
        st.markdown(f"""
        <div class="hero-card">
            <div class="hero-label">{target_icon} Decision Impact</div>
            <div class="hero-value" style="color: {di_color};">{di_prefix}{currency}{decision_impact:,.0f}</div>
            <div class="hero-sub">market-adjusted</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        sa_color = positive_text if spend_avoided > 0 else neutral_text
        st.markdown(f"""
        <div class="hero-card">
            <div class="hero-label">{shield_icon} Spend Avoided</div>
            <div class="hero-value" style="color: {sa_color};">{currency}{spend_avoided:,.0f}</div>
            <div class="hero-sub">capital protected</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        # NPS-style bands: +40 to +100 Exceptional, +10 to +39 Strong, -10 to +9 Neutral, <-10 Needs review
        if decision_quality_score >= 40:
            score_color = positive_text
            score_label = "Exceptional"
        elif decision_quality_score >= 10:
            score_color = positive_text
            score_label = "Strong"
        elif decision_quality_score >= -10:
            score_color = neutral_text
            score_label = "Neutral"
        else:
            score_color = negative_text
            score_label = "Needs review"
        
        score_prefix = '+' if decision_quality_score > 0 else ''
        st.markdown(f"""
        <div class="hero-card">
            <div class="hero-label">{score_icon} Decision Quality</div>
            <div class="hero-value" style="color: {score_color};">{score_prefix}{decision_quality_score:.0f}</div>
            <div class="hero-sub">{score_label}</div>
            <div class="hero-sub" style="margin-top: 4px;">
                <span style="color: {positive_text};">{pct_good:.0f}%</span> / 
                <span style="color: {neutral_text};">{pct_neutral:.0f}%</span> / 
                <span style="color: {negative_text};">{pct_bad:.0f}%</span>
                <span style="color: #64748b; font-size: 0.65rem; margin-left: 4px;">Good / Neutral / Bad</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        impl_color = positive_text if impl_rate >= 70 else negative_text if impl_rate < 40 else neutral_text
        st.markdown(f"""
        <div class="hero-card">
            <div class="hero-label">{impl_icon} Implementation</div>
            <div class="hero-value" style="color: {impl_color};">{impl_rate:.0f}%</div>
            <div class="hero-sub">confirmed applied</div>
        </div>
        """, unsafe_allow_html=True)
    
    # ==========================================
    # SINGLE COMBINED CALLOUT (Context + Stats)
    # ==========================================
    win_rate = summary.get('win_rate', 0)
    confirmed = summary.get('confirmed_impact', 0)
    pending = summary.get('pending', 0)
    wr_color = positive_text if win_rate >= 60 else negative_text if win_rate < 40 else neutral_text
    
    market_context = f" ({market_downshift} market shifts detected)" if market_downshift > 0 else ""
    
    st.markdown(f"""
    <div style="background: rgba(143, 140, 163, 0.08); border: 1px solid rgba(143, 140, 163, 0.15); border-radius: 8px; 
                padding: 12px 20px; margin-top: 16px; display: flex; align-items: center; justify-content: space-between;">
        <div style="display: flex; align-items: center; gap: 10px;">
            <span style="font-size: 1.1rem;">💡</span>
            <span style="color: #8F8CA3; font-size: 0.85rem;">
                Results adjust for market changes. We measure whether <strong>your decisions</strong> helped.{market_context}
            </span>
        </div>
        <div style="display: flex; gap: 24px; color: #8F8CA3; font-size: 0.85rem;">
            <span>Win Rate: <strong style="color: {wr_color};">{win_rate:.0f}%</strong></span>
            <span>Measured: <strong>{confirmed}</strong> | Pending: <strong>{pending}</strong></span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _render_new_impact_analytics(summary: Dict[str, Any], impact_df: pd.DataFrame, validated_only: bool = True):
    """Render new impact analytics: 3 Core Charts."""
    
    from utils.formatters import get_account_currency
    currency = get_account_currency()
    
    # Chart 1: Decision Outcome Matrix (full width)
    _render_decision_outcome_matrix(impact_df, summary)
    
    # Charts 2 & 3 side by side
    col1, col2 = st.columns(2)
    
    with col1:
        _render_decision_quality_distribution(summary)
    
    with col2:
        _render_capital_allocation_flow(impact_df, currency)


def _render_decision_outcome_matrix(impact_df: pd.DataFrame, summary: Dict[str, Any]):
    """Chart 1: Decision Outcome Matrix - The visual backbone."""
    
    import plotly.graph_objects as go
    import numpy as np
    
    st.markdown("#### 🎯 Decision Outcome Matrix")
    st.caption("Were decisions correct given market conditions?")
    
    if impact_df.empty:
        st.info("No data to display")
        return
    
    # Filter to confirmed actions with valid data
    df = impact_df.copy()
    df = df[df['before_spend'] > 0]
    
    # Calculate CPC before and after
    df['cpc_before'] = df['before_spend'] / df['before_clicks'].replace(0, np.nan)
    df['cpc_after'] = df['observed_after_spend'] / df['after_clicks'].replace(0, np.nan)
    df['cpc_change_pct'] = ((df['cpc_after'] - df['cpc_before']) / df['cpc_before'] * 100).fillna(0)
    
    # Calculate Decision Impact (market-adjusted)
    df['spc_before'] = df['before_sales'] / df['before_clicks'].replace(0, np.nan)
    df['expected_clicks'] = df['observed_after_spend'] / df['cpc_before']
    df['expected_sales'] = df['expected_clicks'] * df['spc_before']
    df['decision_impact'] = df['observed_after_sales'] - df['expected_sales']
    
    # Clean infinite/nan values
    df = df[np.isfinite(df['cpc_change_pct']) & np.isfinite(df['decision_impact'])]
    df = df[df['cpc_change_pct'].abs() < 200]  # Filter extreme outliers
    
    if len(df) < 3:
        st.info("Insufficient data for matrix")
        return
    
    # Color by action type (including NEGATIVE)
    action_colors = {
        'BID_UP': '#22c55e',      # Green
        'BID_DOWN': '#3b82f6',    # Blue
        'BID': '#6366f1',         # Indigo (generic bid)
        'HOLD': '#8b5cf6',        # Purple
        'PAUSE': '#f59e0b',       # Orange
        'NEGATIVE': '#ef4444',    # Red (negatives stand out)
        'BID_CHANGE': '#6366f1',  # Indigo
    }
    
    # Normalize action types
    df['action_clean'] = df['action_type'].str.upper().str.replace('_CHANGE', '').str.replace('ADJUSTMENT', '').str.replace('_ADD', '')
    
    # Determine if point is in "neutral zone" (close to 0,0)
    impact_threshold = max(df['decision_impact'].abs().quantile(0.25), 50)
    cpc_threshold = 10  # ±10% CPC change is neutral zone
    df['is_neutral_zone'] = (df['decision_impact'].abs() < impact_threshold) & (df['cpc_change_pct'].abs() < cpc_threshold)
    
    fig = go.Figure()
    
    # Add dots for each action type
    for action_type in df['action_clean'].unique():
        type_df = df[df['action_clean'] == action_type]
        color = action_colors.get(action_type, '#8F8CA3')
        
        # Different opacity based on zone
        neutral_mask = type_df['is_neutral_zone']
        
        # Non-neutral points (full opacity)
        if (~neutral_mask).any():
            non_neutral = type_df[~neutral_mask]
            fig.add_trace(go.Scatter(
                x=non_neutral['cpc_change_pct'],
                y=non_neutral['decision_impact'],
                mode='markers',
                name=action_type.replace('_', ' ').title(),
                marker=dict(size=10, color=color, opacity=0.8),
                hovertemplate='CPC: %{x:.1f}%<br>Impact: %{y:,.0f}<extra></extra>',
                legendgroup=action_type
            ))
        
        # Neutral zone points (muted opacity)
        if neutral_mask.any():
            neutral = type_df[neutral_mask]
            fig.add_trace(go.Scatter(
                x=neutral['cpc_change_pct'],
                y=neutral['decision_impact'],
                mode='markers',
                name=action_type.replace('_', ' ').title(),
                marker=dict(size=8, color=color, opacity=0.35),  # Smaller, more muted
                hovertemplate='CPC: %{x:.1f}%<br>Impact: %{y:,.0f} (neutral)<extra></extra>',
                legendgroup=action_type,
                showlegend=False  # Don't duplicate legend
            ))
    
    # Add quadrant lines
    fig.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.3)")
    fig.add_vline(x=0, line_dash="dash", line_color="rgba(255,255,255,0.3)")
    
    # Add quadrant labels
    x_range = max(abs(df['cpc_change_pct'].min()), abs(df['cpc_change_pct'].max()), 20)
    y_range = max(abs(df['decision_impact'].min()), abs(df['decision_impact'].max()), 100)
    
    annotations = [
        dict(x=-x_range*0.5, y=y_range*0.7, text="🟢 Good Defense", showarrow=False, font=dict(color='#22c55e', size=11)),
        dict(x=x_range*0.5, y=y_range*0.7, text="🟢 Good Offense", showarrow=False, font=dict(color='#22c55e', size=11)),
        dict(x=-x_range*0.5, y=-y_range*0.7, text="🟡 Market-Driven Loss", showarrow=False, font=dict(color='#f59e0b', size=11)),
        dict(x=x_range*0.5, y=-y_range*0.7, text="🔴 Decision Error", showarrow=False, font=dict(color='#ef4444', size=11)),
    ]
    
    fig.update_layout(
        height=400,
        margin=dict(t=30, b=50, l=50, r=30),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            title=dict(text="CPC Change %", font=dict(color='#94a3b8')),
            showgrid=True, gridcolor='rgba(128,128,128,0.1)',
            tickfont=dict(color='#94a3b8'),
            zeroline=False
        ),
        yaxis=dict(
            title=dict(text="Decision Impact", font=dict(color='#94a3b8')),
            showgrid=True, gridcolor='rgba(128,128,128,0.1)',
            tickfont=dict(color='#94a3b8'),
            zeroline=False
        ),
        legend=dict(
            orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5,
            font=dict(color='#94a3b8', size=11)
        ),
        annotations=annotations
    )
    
    st.plotly_chart(fig, use_container_width=True)


def _render_decision_quality_distribution(summary: Dict[str, Any]):
    """Chart 2: Decision Quality Distribution (NPS-Style Donut)."""
    
    import plotly.graph_objects as go
    
    st.markdown("#### 📊 Decision Quality Distribution")
    
    pct_good = summary.get('pct_good', 0)
    pct_neutral = summary.get('pct_neutral', 0)
    pct_bad = summary.get('pct_bad', 0)
    
    # NPS-style score
    decision_quality_score = pct_good - pct_bad
    
    if pct_good + pct_neutral + pct_bad == 0:
        st.info("No outcome data")
        return
    
    # Donut chart
    fig = go.Figure(data=[go.Pie(
        values=[pct_good, pct_neutral, pct_bad],
        labels=['Good', 'Neutral', 'Bad'],
        hole=0.6,
        marker=dict(colors=['#22c55e', '#64748b', '#ef4444']),
        textinfo='label+percent',
        textfont=dict(size=12, color='#e2e8f0'),
        hovertemplate='%{label}: %{value:.1f}%<extra></extra>',
        sort=False
    )])
    
    # Add score in center
    score_color = '#22c55e' if decision_quality_score > 0 else '#ef4444' if decision_quality_score < 0 else '#64748b'
    score_prefix = '+' if decision_quality_score > 0 else ''
    
    fig.add_annotation(
        text=f"<b style='font-size:28px; color:{score_color};'>{score_prefix}{decision_quality_score:.0f}</b><br><span style='font-size:11px; color:#8F8CA3;'>Quality Score</span>",
        showarrow=False,
        font=dict(size=14, color='#e2e8f0')
    )
    
    fig.update_layout(
        height=350,
        margin=dict(t=30, b=60, l=30, r=30),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Important copy
    st.caption("*Neutrals excluded to focus on signal, not noise.*")


def _render_capital_allocation_flow(impact_df: pd.DataFrame, currency: str):
    """Chart 3: Capital Allocation Flow (Spend Lens)."""
    
    import plotly.graph_objects as go
    import numpy as np
    
    st.markdown("#### 💰 Capital Allocation Flow")
    
    if impact_df.empty:
        st.info("No data to display")
        return
    
    df = impact_df.copy()
    
    # Calculate spend categories
    df['spend_maintained'] = df[['before_spend', 'observed_after_spend']].min(axis=1)
    df['spend_avoided'] = (df['before_spend'] - df['observed_after_spend']).clip(lower=0)
    df['spend_added'] = (df['observed_after_spend'] - df['before_spend']).clip(lower=0)
    
    # Aggregate by action type
    action_map = {
        'BID_DOWN': 'Bid Down',
        'BID_UP': 'Bid Up',
        'PAUSE': 'Pause',
        'HOLD': 'Hold',
        'BID_CHANGE': 'Bid Change',
    }
    
    df['action_clean'] = df['action_type'].str.upper().map(
        lambda x: next((v for k, v in action_map.items() if k in str(x)), 'Other')
    )
    
    # Aggregate totals
    total_original = df['before_spend'].sum()
    total_maintained = df['spend_maintained'].sum()
    total_avoided = df['spend_avoided'].sum()
    total_reallocated = df['spend_added'].sum()
    
    if total_original == 0:
        st.info("No spend data")
        return
    
    # Sankey diagram
    fig = go.Figure(go.Sankey(
        node=dict(
            pad=20,
            thickness=25,
            line=dict(color='rgba(0,0,0,0)', width=0),
            label=[
                f"Original<br>{currency}{total_original:,.0f}",
                f"Maintained<br>{currency}{total_maintained:,.0f}",
                f"Avoided<br>{currency}{total_avoided:,.0f}",
                f"Reallocated<br>{currency}{total_reallocated:,.0f}"
            ],
            color=['#5B556F', '#64748b', '#22c55e', '#3b82f6'],
        ),
        link=dict(
            source=[0, 0, 0],
            target=[1, 2, 3],
            value=[total_maintained, total_avoided, total_reallocated],
            color=['rgba(100,116,139,0.4)', 'rgba(34,197,94,0.4)', 'rgba(59,130,246,0.4)']
        )
    ))
    
    fig.update_layout(
        height=350,
        margin=dict(t=30, b=30, l=30, r=30),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(size=11, color='#e2e8f0')
    )
    
    st.plotly_chart(fig, use_container_width=True)


# Legacy chart functions (kept for backward compatibility but not called)
def _render_attribution_waterfall(summary: Dict[str, Any], impact_df: pd.DataFrame, currency: str, validated_only: bool):
    """Render attribution-based waterfall showing ROAS contribution by action type."""
    
    label = "📊 ROAS Contribution by Type" if validated_only else "📊 Sales Change by Type"
    st.markdown(f"#### {label}")
    
    if impact_df.empty:
        st.info("No data to display")
        return
    
    # Break down by MATCH TYPE for more granular attribution (instead of action type)
    # This shows AUTO, BROAD, EXACT, etc. contributions like the Account Overview donut
    match_type_col = 'match_type' if 'match_type' in impact_df.columns else None
    
    contributions = {}
    
    if match_type_col and impact_df[match_type_col].notna().any():
        # Group by match type for richer breakdown
        for match_type in impact_df[match_type_col].dropna().unique():
            type_df = impact_df[impact_df[match_type_col] == match_type]
            type_df = type_df[(type_df['before_spend'] > 0) & (type_df['observed_after_spend'] > 0)]
            
            if len(type_df) == 0:
                continue
            
            # Calculate this type's ROAS contribution
            before_spend = type_df['before_spend'].sum()
            before_sales = type_df['before_sales'].sum()
            after_spend = type_df['observed_after_spend'].sum()
            after_sales = type_df['observed_after_sales'].sum()
            
            roas_before = before_sales / before_spend if before_spend > 0 else 0
            roas_after = after_sales / after_spend if after_spend > 0 else 0
            
            contribution = before_spend * (roas_after - roas_before)
            
            # Clean match type name
            name = str(match_type).upper() if match_type else 'OTHER'
            contributions[name] = contributions.get(name, 0) + contribution
    else:
        # Fallback to action type if no match type
        display_names = {
            'BID_CHANGE': 'Bid Optim.',
            'NEGATIVE': 'Cost Saved',
            'HARVEST': 'Harvest Gains',
            'BID_ADJUSTMENT': 'Bid Optim.'
        }
        
        for action_type in impact_df['action_type'].unique():
            type_df = impact_df[impact_df['action_type'] == action_type]
            type_df = type_df[(type_df['before_spend'] > 0) & (type_df['observed_after_spend'] > 0)]
            
            if len(type_df) == 0:
                continue
            
            before_spend = type_df['before_spend'].sum()
            before_sales = type_df['before_sales'].sum()
            after_spend = type_df['observed_after_spend'].sum()
            after_sales = type_df['observed_after_sales'].sum()
            
            roas_before = before_sales / before_spend if before_spend > 0 else 0
            roas_after = after_sales / after_spend if after_spend > 0 else 0
            
            contribution = before_spend * (roas_after - roas_before)
            
            name = display_names.get(action_type, action_type.replace('_', ' ').title())
            contributions[name] = contributions.get(name, 0) + contribution
    
    if not contributions:
        st.info("Insufficient data for attribution")
        return
    
    # Get the authoritative total from summary (must match hero tile)
    target_total = summary.get('incremental_revenue', 0)
    calculated_total = sum(contributions.values())
    
    # Scale contributions proportionally so they sum to the hero tile's incremental_revenue
    if calculated_total != 0 and target_total != 0:
        scale_factor = target_total / calculated_total
        contributions = {k: v * scale_factor for k, v in contributions.items()}
    
    # Sort and create chart
    sorted_data = sorted(contributions.items(), key=lambda x: x[1], reverse=True)
    names = [x[0] for x in sorted_data]
    impacts = [x[1] for x in sorted_data]
    
    # Color palette matching donut chart (purple-slate-gray scale, cyan only for total)
    bar_colors = ['#5B556F', '#8F8CA3', '#475569', '#334155', '#64748b']  # Purple to slate
    colors = [bar_colors[i % len(bar_colors)] for i in range(len(impacts))]
    colors.append('#22d3ee')  # Cyan for total only
    
    # Total must match hero tile exactly
    final_total = target_total if target_total != 0 else sum(impacts)
    
    # Brand colors from Account Overview: Purple (#5B556F), Cyan (#22d3ee)
    fig = go.Figure(go.Waterfall(
        name="Contribution",
        orientation="v",
        measure=["relative"] * len(impacts) + ["total"],
        x=names + ['Total'],
        y=impacts + [final_total],
        connector={"line": {"color": "rgba(143, 140, 163, 0.3)"}},  # #8F8CA3
        decreasing={"marker": {"color": "#8F8CA3"}},   # Neutral slate (for negatives)
        increasing={"marker": {"color": "#5B556F"}},   # Brand Purple (for positives)
        totals={"marker": {"color": "#22d3ee"}},       # Accent Cyan
        textposition="outside",
        textfont=dict(size=14, color="#e2e8f0"),
        text=[f"{currency}{v:+,.0f}" for v in impacts] + [f"{currency}{final_total:+,.0f}"]
    ))
    
    fig.update_layout(
        showlegend=False,
        height=380,
        margin=dict(t=60, b=40, l=30, r=30),  # Much more space for labels
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.15)', tickformat=',.0f', tickfont=dict(color='#94a3b8', size=12)),
        xaxis=dict(showgrid=False, tickfont=dict(color='#cbd5e1', size=12))
    )
    
    st.plotly_chart(fig, use_container_width=True)


def _render_stacked_revenue_bar(summary: Dict[str, Any], currency: str, validated_only: bool = True):
    """Render stacked bar showing Before Revenue vs After (Baseline + Incremental)."""
    
    title = "#### 📈 Baseline vs. Incremental Sales" if validated_only else "#### 📈 Revenue Comparison"
    st.markdown(title)
    
    # Get actual values from summary
    before_sales = summary.get('before_sales', 0)
    after_sales = summary.get('after_sales', 0)
    incremental = summary.get('incremental_revenue', 0)
    roas_before = summary.get('roas_before', 0)
    roas_after = summary.get('roas_after', 0)
    
    # If we have actual sales values, use them
    if before_sales > 0 and after_sales > 0:
        fig = go.Figure()
        
        # Before bar - Brand Purple
        fig.add_trace(go.Bar(
            name='Sales (Before)',
            x=['Before'],
            y=[before_sales],
            marker_color='#5B556F',  # Brand Purple
            text=[f"{currency}{before_sales:,.0f}"],
            textposition='auto',
            textfont=dict(color='#e2e8f0', size=13),
        ))
        
        # After bar with incremental highlight
        fig.add_trace(go.Bar(
            name='Baseline (Expected)',
            x=['After'],
            y=[before_sales],  # Same as before (baseline)
            marker_color='#5B556F',  # Brand Purple
            showlegend=True,
        ))
        
        # Use ROAS-based incremental from summary (matches waterfall and hero tile)
        # This is: before_spend × (roas_after - roas_before)
        lift = incremental  # Use the calculated incremental, not raw sales delta
        lift_color = '#22d3ee'  # Accent Cyan for incremental
        fig.add_trace(go.Bar(
            name='Incremental (Lift)',
            x=['After'],
            y=[lift],
            marker_color=lift_color,
            text=[f"{'+' if lift >= 0 else ''}{currency}{lift:,.0f}"],
            textposition='outside',
            textfont=dict(color='#e2e8f0', size=14),
        ))
        
        fig.update_layout(
            barmode='stack',
            showlegend=True,
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5, font=dict(color='#94a3b8', size=11)),
            height=380,
            margin=dict(t=60, b=40, l=30, r=30),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.15)', tickfont=dict(color='#94a3b8', size=12)),
            xaxis=dict(showgrid=False, tickfont=dict(color='#cbd5e1', size=12))
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    elif roas_before > 0 or roas_after > 0:
        # Fallback: Show ROAS comparison bars with brand colors
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=['Before', 'After'],
            y=[roas_before, roas_after],
            marker_color=['#5B556F', '#22d3ee'],  # Brand Purple to Cyan
            text=[f"{roas_before:.2f}x", f"{roas_after:.2f}x"],
            textposition='auto',
            textfont=dict(color='#e2e8f0', size=14),
        ))
        fig.update_layout(
            showlegend=False,
            height=380,
            margin=dict(t=40, b=40, l=30, r=30),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.1)', title="ROAS", tickfont=dict(color='#94a3b8', size=12)),
            xaxis=dict(showgrid=False)
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No comparative data")


def _render_impact_analytics(summary: Dict[str, Any], impact_df: pd.DataFrame):
    """Render the dual-chart impact analytics section."""
    
    col1, col2 = st.columns([1.2, 0.8])
    
    with col1:
        _render_waterfall_chart(summary)
    
    with col2:
        _render_roas_comparison(summary)


def _render_waterfall_chart(summary: Dict[str, Any]):
    """Render waterfall chart showing incremental revenue by action type."""
    
    # Target icon for action type
    icon_color = "#8F8CA3"
    target_icon = f'<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="{icon_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 8px;"><circle cx="12" cy="12" r="10"></circle><circle cx="12" cy="12" r="6"></circle><circle cx="12" cy="12" r="2"></circle></svg>'
    st.markdown(f"#### {target_icon}Revenue Impact by Type", unsafe_allow_html=True)
    
    by_type = summary.get('by_action_type', {})
    if not by_type:
        st.info("No action type breakdown available")
        return
    
    # Map raw types to display names
    display_names = {
        'BID_CHANGE': 'Bid Optim.',
        'NEGATIVE': 'Cost Saved',
        'HARVEST': 'Harvest Gains',
        'BID_ADJUSTMENT': 'Bid Optim.'
    }
    
    # Aggregate data
    agg_data = {}
    for t, data in by_type.items():
        name = display_names.get(t, t.replace('_', ' ').title())
        agg_data[name] = agg_data.get(name, 0) + data['net_sales']
    
    # Sort
    sorted_data = sorted(agg_data.items(), key=lambda x: x[1], reverse=True)
    names = [x[0] for x in sorted_data]
    impacts = [x[1] for x in sorted_data]
    
    from utils.formatters import get_account_currency
    chart_currency = get_account_currency()
    
    fig = go.Figure(go.Waterfall(
        name="Impact",
        orientation="v",
        measure=["relative"] * len(impacts) + ["total"],
        x=names + ['Total'],
        y=impacts + [sum(impacts)],
        connector={"line": {"color": "rgba(148, 163, 184, 0.2)"}},
        decreasing={"marker": {"color": "rgba(248, 113, 113, 0.5)"}}, 
        increasing={"marker": {"color": "rgba(74, 222, 128, 0.6)"}}, 
        totals={"marker": {"color": "rgba(143, 140, 163, 0.6)"}},
        textposition="outside",
        text=[f"{chart_currency}{v:+,.0f}" for v in impacts] + [f"{chart_currency}{sum(impacts):+,.0f}"]
    ))
    
    fig.update_layout(
        showlegend=False,
        height=320,
        margin=dict(t=10, b=10, l=10, r=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.1)', tickformat=',.0f'),
        xaxis=dict(showgrid=False)
    )
    
    st.plotly_chart(fig, use_container_width=True)


def _render_roas_comparison(summary: Dict[str, Any]):
    """Render side-by-side ROAS before/after comparison."""
    
    icon_color = "#8F8CA3"
    trend_icon = f'<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="{icon_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 8px;"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline><polyline points="17 6 23 6 23 12"></polyline></svg>'
    st.markdown(f"#### {trend_icon}Account ROAS Shift", unsafe_allow_html=True)
    
    r_before = summary.get('roas_before', 0)
    r_after = summary.get('roas_after', 0)
    
    if r_before == 0 and r_after == 0:
        st.info("No comparative ROAS data")
        return
        
    fig = go.Figure()
    
    # Before Bar
    fig.add_trace(go.Bar(
        x=['Before Optim.'],
        y=[r_before],
        name="Before",
        marker_color="rgba(148, 163, 184, 0.4)",
        text=[f"{r_before:.2f}"],
        textposition='auto',
    ))
    
    # After Bar
    color = "rgba(74, 222, 128, 0.6)" if r_after >= r_before else "rgba(248, 113, 113, 0.6)"
    fig.add_trace(go.Bar(
        x=['After Optim.'],
        y=[r_after],
        name="After",
        marker_color=color,
        text=[f"{r_after:.2f}"],
        textposition='auto',
    ))
    
    fig.update_layout(
        showlegend=False,
        height=320,
        margin=dict(t=10, b=10, l=40, r=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.1)', title="Account ROAS"),
        xaxis=dict(showgrid=False)
    )
    
    st.plotly_chart(fig, use_container_width=True)


def _render_winners_losers_chart(impact_df: pd.DataFrame):
    """Render top contributors by incremental revenue."""
    
    # Chart icon 
    icon_color = "#8F8CA3"
    chart_icon = f'<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="{icon_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 8px;"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>'
    st.markdown(f"#### {chart_icon}Top Revenue Contributors", unsafe_allow_html=True)
    
    if impact_df.empty:
        st.info("No targeting data available")
        return
    
    # AGGREGATE BY CAMPAIGN > AD GROUP > TARGET
    agg_cols = {
        'impact_score': 'sum',
        'before_spend': 'sum',
        'after_spend': 'sum'
    }
    # Include campaign and ad group to avoid merging "close-match" etc account-wide
    group_cols = ['campaign_name', 'ad_group_name', 'target_text']
    target_perf = impact_df.groupby(group_cols).agg(agg_cols).reset_index()
    
    # Filter to targets that actually had activity
    target_perf = target_perf[(target_perf['before_spend'] > 0) | (target_perf['after_spend'] > 0)]
    
    if target_perf.empty:
        st.info("No matched targets with performance data found")
        return
    
    # Get top 5 winners and bottom 5 losers by impact_score
    winners = target_perf.sort_values('impact_score', ascending=False).head(5)
    losers = target_perf.sort_values('impact_score', ascending=True).head(5)
    
    # Combine for chart
    chart_df = pd.concat([winners, losers]).drop_duplicates().sort_values('impact_score', ascending=False)
    
    # Create descriptive labels
    def create_label(row):
        target = row['target_text']
        cam = row['campaign_name'][:15] + '..' if len(row['campaign_name']) > 15 else row['campaign_name']
        adg = row['ad_group_name'][:10] + '..' if len(row['ad_group_name']) > 10 else row['ad_group_name']
        
        # If it's an auto-type, emphasize the type but show campaign
        if target.lower() in ['close-match', 'loose-match', 'substitutes', 'complements']:
            return f"{target} ({cam})"
        return f"{target[:20]}.. ({cam})"

    chart_df['display_label'] = chart_df.apply(create_label, axis=1)
    chart_df['full_context'] = chart_df.apply(lambda r: f"Cam: {r['campaign_name']}<br>Ad Group: {r['ad_group_name']}<br>Target: {r['target_text']}", axis=1)
    
    # Rename for the chart library to use
    chart_df['raw_perf'] = chart_df['impact_score']
    
    # Brand-aligned palette: Muted violet for positive, muted wine for negative
    chart_df['color'] = chart_df['raw_perf'].apply(
        lambda x: "rgba(91, 85, 111, 0.6)" if x > 0 else "rgba(136, 19, 55, 0.5)"
    )
    
    from utils.formatters import get_account_currency
    bar_currency = get_account_currency()
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=chart_df['display_label'],
        x=chart_df['raw_perf'],
        orientation='h',
        marker_color=chart_df['color'],
        text=[f"{bar_currency}{v:+,.0f}" for v in chart_df['raw_perf']],
        textposition='outside',
        hovertext=chart_df['full_context'],
        hoverinfo='text+x'
    ))
    
    fig.update_layout(
        height=350,
        margin=dict(t=20, b=20, l=20, r=60),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)', zeroline=True, zerolinecolor='rgba(128,128,128,0.5)'),
        yaxis=dict(showgrid=False, autorange='reversed')
    )

    
    st.plotly_chart(fig, use_container_width=True)


def _render_drill_down_table(impact_df: pd.DataFrame, show_migration_badge: bool = False):
    """Render detailed drill-down table with decision-adjusted metrics."""
    
    import numpy as np
    
    with st.expander("📋 Detailed Action Log", expanded=False):
        if impact_df.empty:
            st.info("No actions to display")
            return
        
        # Create display dataframe with all decision-adjusted calculations
        display_df = impact_df.copy()
        
        # Add migration badge for HARVEST with before_spend > 0
        if show_migration_badge and 'is_migration' in display_df.columns:
            display_df['action_display'] = display_df.apply(
                lambda r: f"🔄 {r['action_type']}" if r.get('is_migration', False) else r['action_type'],
                axis=1
            )
        else:
            display_df['action_display'] = display_df['action_type']
        
        # ==========================================
        # CALCULATE DECISION-ADJUSTED METRICS
        # ==========================================
        
        # Spend Avoided = max(0, Before_Spend - After_Spend)
        display_df['spend_avoided'] = (display_df['before_spend'] - display_df['observed_after_spend']).clip(lower=0)
        
        # CPC Before = Before_Spend / Before_Clicks (NULL if clicks=0)
        display_df['before_clicks'] = display_df.get('before_clicks', 0)
        display_df['after_clicks'] = display_df.get('after_clicks', 0)
        display_df['cpc_before'] = display_df['before_spend'] / display_df['before_clicks'].replace(0, np.nan)
        display_df['cpc_after'] = display_df['observed_after_spend'] / display_df['after_clicks'].replace(0, np.nan)
        
        # CPC Change % = (CPC_After - CPC_Before) / CPC_Before
        display_df['cpc_change_pct'] = ((display_df['cpc_after'] - display_df['cpc_before']) / display_df['cpc_before'] * 100).fillna(0)
        
        # Sales Per Click (proxy for CVR × AOV)
        display_df['spc_before'] = display_df['before_sales'] / display_df['before_clicks'].replace(0, np.nan)
        
        # Expected Sales = (After_Spend / CPC_Before) × SPC_Before
        display_df['expected_clicks'] = display_df['observed_after_spend'] / display_df['cpc_before']
        display_df['expected_sales'] = display_df['expected_clicks'] * display_df['spc_before']
        
        # Decision Impact = After_Sales - Expected_Sales
        display_df['decision_impact'] = display_df['observed_after_sales'] - display_df['expected_sales']
        
        # Market Tag logic
        def get_market_tag(row):
            if row['before_clicks'] == 0:
                return "Low Data"
            if pd.notna(row['cpc_after']) and pd.notna(row['cpc_before']) and row['cpc_before'] > 0:
                if row['cpc_after'] <= 0.75 * row['cpc_before']:
                    return "Market Downshift"
            return "Normal"
        display_df['market_tag'] = display_df.apply(get_market_tag, axis=1)
        
        # Decision Outcome logic
        def get_decision_outcome(row):
            action = str(row['action_type']).upper()
            di = row['decision_impact'] if pd.notna(row['decision_impact']) else 0
            sa = row['spend_avoided'] if pd.notna(row['spend_avoided']) else 0
            bs = row['before_spend'] if pd.notna(row['before_spend']) else 0
            market_tag = row['market_tag']
            
            # Low Data → Neutral
            if market_tag == "Low Data":
                return "🟡 Neutral"
            
            # Good: DI > 0 OR (defensive + significant spend avoided + market downshift)
            if di > 0:
                return "🟢 Good"
            if action in ['BID_DOWN', 'PAUSE', 'NEGATIVE'] and bs > 0 and sa >= 0.1 * bs:
                return "🟢 Good"
            
            # Neutral: small impact
            before_sales = row['before_sales'] if pd.notna(row['before_sales']) else 0
            threshold = max(0.05 * before_sales, 10)  # 5% of before_sales or $10
            if abs(di) < threshold:
                return "🟡 Neutral"
            
            # Bad: negative impact in normal market
            if di < 0 and market_tag == "Normal":
                return "🔴 Bad"
            
            # Default to Neutral for edge cases
            return "🟡 Neutral"
        
        display_df['decision_outcome'] = display_df.apply(get_decision_outcome, axis=1)
        
        # ==========================================
        # SELECT FINAL COLUMNS (per spec)
        # ==========================================
        display_cols = [
            'action_display', 'target_text', 'reason',
            'before_spend', 'observed_after_spend', 'spend_avoided',
            'before_sales', 'observed_after_sales',
            'cpc_before', 'cpc_after', 'cpc_change_pct',
            'expected_sales', 'decision_impact',
            'market_tag', 'decision_outcome', 'validation_status'
        ]
        
        # Filter to columns that actually exist
        cols_to_use = [c for c in display_cols if c in display_df.columns]
        display_df = display_df[cols_to_use].copy()
        
        # Rename for user-friendly display
        final_rename = {
            'action_display': 'Action Taken',
            'target_text': 'Target',
            'reason': 'Logic Basis',
            'before_spend': 'Before Spend',
            'observed_after_spend': 'After Spend',
            'spend_avoided': 'Spend Avoided',
            'before_sales': 'Before Sales',
            'observed_after_sales': 'After Sales',
            'cpc_before': 'CPC Before',
            'cpc_after': 'CPC After',
            'cpc_change_pct': 'CPC Change %',
            'expected_sales': 'Expected Sales',
            'decision_impact': 'Decision Impact',
            'market_tag': 'Market Tag',
            'decision_outcome': 'Decision Outcome',
            'validation_status': 'Validation Status'
        }
        display_df = display_df.rename(columns=final_rename)
        
        # Format currency columns
        from utils.formatters import get_account_currency
        df_currency = get_account_currency()
        currency_cols = ['Before Spend', 'After Spend', 'Spend Avoided', 'Before Sales', 'After Sales', 'Expected Sales', 'Decision Impact']
        for col in currency_cols:
            if col in display_df.columns:
                display_df[col] = display_df[col].apply(lambda x: f"{df_currency}{x:,.2f}" if pd.notna(x) else "-")
        
        # Format CPC columns
        cpc_cols = ['CPC Before', 'CPC After']
        for col in cpc_cols:
            if col in display_df.columns:
                display_df[col] = display_df[col].apply(lambda x: f"{df_currency}{x:.2f}" if pd.notna(x) else "-")
        
        # Format CPC Change %
        if 'CPC Change %' in display_df.columns:
            display_df['CPC Change %'] = display_df['CPC Change %'].apply(lambda x: f"{x:+.1f}%" if pd.notna(x) else "-")
        
        # Show migration legend if applicable
        if show_migration_badge and 'is_migration' in impact_df.columns and impact_df['is_migration'].any():
            st.caption("🔄 = **Migration Tracking**: Efficiency gain from harvesting search term to exact match.")
        
        st.dataframe(
            display_df,
            use_container_width=True,
            column_config={
                "Decision Impact": st.column_config.TextColumn(
                    "Decision Impact",
                    help="Market-adjusted: After_Sales - Expected_Sales (what would have happened without change)"
                ),
                "Expected Sales": st.column_config.TextColumn(
                    "Expected Sales",
                    help="Counterfactual: (After_Spend / CPC_Before) × CVR_Before × AOV_Before"
                ),
                "Market Tag": st.column_config.TextColumn(
                    "Market Tag",
                    help="Normal | Market Downshift (CPC dropped >25%) | Low Data (no baseline clicks)"
                ),
                "Decision Outcome": st.column_config.TextColumn(
                    "Decision Outcome",
                    help="Good: positive impact or successful defense | Neutral: small/ambiguous | Bad: negative impact in stable market"
                ),
                "Validation Status": st.column_config.TextColumn(
                    "Validation Status",
                    help="Verification that the action was actually applied based on subsequent spend reporting"
                )
            }
        )
        
        # Download button
        csv = impact_df.to_csv(index=False)
        st.download_button(
            "📥 Download Full Data (CSV)",
            csv,
            "impact_analysis.csv",
            "text/csv"
        )


def _render_dormant_table(dormant_df: pd.DataFrame):
    """Render simple table for dormant actions ($0 spend in both periods)."""
    
    if dormant_df.empty:
        return
    
    # Simplified view for dormant
    display_cols = ['action_type', 'target_text', 'old_value', 'new_value', 'reason']
    available_cols = [c for c in display_cols if c in dormant_df.columns]
    display_df = dormant_df[available_cols].copy()
    
    display_df = display_df.rename(columns={
        'action_type': 'Action',
        'target_text': 'Target',
        'old_value': 'Old Value',
        'new_value': 'New Value',
        'reason': 'Reason'
    })
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    st.caption(f"💡 These {len(dormant_df)} optimizations have an established baseline but are pending traffic. "
              "They will appear in Measured Impact once the targets receive impressions.")


def render_reference_data_badge():
    """Render reference data status badge for sidebar."""
    
    db_manager = st.session_state.get('db_manager')
    if db_manager is None:
        return
    
    try:
        status = db_manager.get_reference_data_status()
        
        if not status['exists']:
            st.markdown("""
            <div style="padding: 8px 12px; background: rgba(239, 68, 68, 0.1); border-radius: 8px; border-left: 3px solid #EF4444;">
                <span style="font-size: 0.85rem;">❌ <strong>No Reference Data</strong></span>
            </div>
            """, unsafe_allow_html=True)
        elif status['is_stale']:
            days = status['days_ago']
            st.markdown(f"""
            <div style="padding: 8px 12px; background: rgba(245, 158, 11, 0.1); border-radius: 8px; border-left: 3px solid #F59E0B;">
                <span style="font-size: 0.85rem;">⚠️ <strong>Data Stale</strong> ({days} days ago)</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            days = status['days_ago']
            count = status['record_count']
            st.markdown(f"""
            <div style="padding: 8px 12px; background: rgba(16, 185, 129, 0.1); border-radius: 8px; border-left: 3px solid #10B981;">
                <span style="font-size: 0.85rem;">✅ <strong>Data Loaded</strong> ({days}d ago, {count:,} records)</span>
            </div>
            """, unsafe_allow_html=True)
    except Exception as e:
        pass  # Silently handle errors

def get_recent_impact_summary() -> Optional[dict]:
    """
    Helper for Home Page cockpit.
    Returns impact summary metrics from DB for the last 30 days.
    Simple and reliable - matches get_account_health_score pattern.
    """
    from core.db_manager import get_db_manager
    
    # Check for test mode
    test_mode = st.session_state.get('test_mode', False)
    db_manager = get_db_manager(test_mode)
    
    # Fallback chain for account ID (same as health score)
    selected_client = (
        st.session_state.get('active_account_id') or 
        st.session_state.get('active_account_name') or 
        st.session_state.get('last_stats_save', {}).get('client_id')
    )
    
    if not db_manager or not selected_client:
        return None
        
    try:
        # Direct DB query - simple and reliable
        summary = db_manager.get_impact_summary(selected_client, window_days=30)
        
        if not summary:
            return None
        
        # Handle dual-summary structure (all/validated)
        active_summary = summary.get('validated', summary.get('all', summary))
        
        if active_summary.get('total_actions', 0) == 0:
            return None
        
        # Extract key metrics
        incremental_revenue = active_summary.get('incremental_revenue', 0)
        win_rate = active_summary.get('win_rate', 0)
        
        # Get top action type
        by_type = active_summary.get('by_action_type', {})
        top_action_type = None
        if by_type:
            top_action_type = max(by_type, key=lambda k: by_type[k].get('count', 0))
        
        return {
            'sales': incremental_revenue,
            'win_rate': win_rate,
            'top_action_type': top_action_type,
            'roi': active_summary.get('roas_lift_pct', 0)
        }
        
    except Exception as e:
        print(f"[Impact Summary] Error: {e}")
        return None

