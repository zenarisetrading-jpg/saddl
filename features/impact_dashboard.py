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

@st.cache_data(ttl=300, show_spinner=False)
def _fetch_impact_data(client_id: str, test_mode: bool, window_days: int = 7, cache_version: str = "v1") -> Tuple[pd.DataFrame, Dict[str, Any]]:
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
        full_summary = db.get_impact_summary(client_id)
        return impact_df, full_summary
    except Exception as e:
        # Return empty structures on failure to prevent UI crash
        print(f"Cache miss error: {e}")
        return pd.DataFrame(), {'total_actions': 0, 'net_sales_impact': 0, 'net_spend_change': 0}




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
        # Ensure time_frame is never None
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
        # Use data upload timestamp as cache version to invalidate on re-upload
        cache_version = str(st.session_state.get('data_upload_timestamp', 'v1'))
        # Parse time frame to days for the before/after comparison window
        time_frame_days = {"7D": 7, "14D": 14, "30D": 30, "60D": 60, "90D": 90}
        window_days = time_frame_days.get(time_frame, 7)
        impact_df, full_summary = _fetch_impact_data(selected_client, test_mode, window_days, cache_version)
    
    if full_summary['total_actions'] == 0:
        st.info("No actions with matching 'next week' performance data found. This means either:\n"
                "- Actions were logged but no performance data for the following week exists yet.\n"
                "- Upload next week's Search Term Report and run the optimizer to see impact.")
        return
        
    
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
    
    # Get latest available date for reference (matches Home page logic)
    available_dates = db_manager.get_available_dates(selected_client)
    ref_date = pd.to_datetime(available_dates[0]) if available_dates else pd.Timestamp.now()
    
    # Filter actions to selected time period
    if not impact_df.empty and 'action_date' in impact_df.columns:
        cutoff_date = ref_date - pd.Timedelta(days=days)
        impact_df['action_date_dt'] = pd.to_datetime(impact_df['action_date'], errors='coerce')
        impact_df = impact_df[impact_df['action_date_dt'] >= cutoff_date].copy()
        
        # Apply 'active' filter (only show actions with spend data) to match Home Page
        active_mask = (impact_df['before_spend'].fillna(0) + impact_df['after_spend'].fillna(0)) > 0
        impact_df = impact_df[active_mask].copy()
        
        # Recalculate summary for filtered actions
        if not impact_df.empty:
            # Use impact_score for main metric (rule-based)
            impact_col = 'impact_score' if 'impact_score' in impact_df.columns else 'delta_sales'
            full_summary = {
                'total_actions': len(impact_df),
                'net_sales_impact': impact_df[impact_col].sum(),  # This is now impact_score
                'net_spend_change': impact_df['delta_spend'].sum() if 'delta_spend' in impact_df.columns else 0,
                'winners': (impact_df['is_winner'] == True).sum() if 'is_winner' in impact_df.columns else 0,
                'losers': (impact_df['is_winner'] == False).sum() if 'is_winner' in impact_df.columns else 0,
                'win_rate': ((impact_df['is_winner'] == True).sum() / len(impact_df) * 100) if len(impact_df) > 0 and 'is_winner' in impact_df.columns else 0
            }
        else:
            full_summary = {'total_actions': 0, 'net_sales_impact': 0, 'net_spend_change': 0, 'winners': 0, 'losers': 0, 'win_rate': 0}
    
    # ==========================================
    # DATE RANGE CALLOUT
    # ==========================================
    if not impact_df.empty and 'action_date' in impact_df.columns:
        action_dates = pd.to_datetime(impact_df['action_date'], errors='coerce').dropna()
        if not action_dates.empty:
            min_date = action_dates.min().strftime('%b %d, %Y')
            max_date = action_dates.max().strftime('%b %d, %Y')
            unique_weeks = impact_df['action_date'].nunique()
            
            # Handle single date vs range
            if min_date == max_date:
                date_text = f"from <strong>{min_date}</strong>"
            else:
                date_text = f"from <strong>{min_date}</strong> to <strong>{max_date}</strong>"
            
            # Dynamic Title based on filter
            title_text = f"{time_frame} Impact Summary"
            
            # Theme-aware calendar icon
            theme_mode = st.session_state.get('theme_mode', 'dark')
            cal_color = "#60a5fa" if theme_mode == 'dark' else "#3b82f6"
            calendar_icon = f'<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="{cal_color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 6px;"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>'
            
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, rgba(59, 130, 246, 0.2) 0%, rgba(59, 130, 246, 0.05) 100%);
                        border: 1px solid rgba(59, 130, 246, 0.3);
                        border-radius: 8px;
                        padding: 12px 16px;
                        margin-bottom: 16px;">
                {calendar_icon}<strong>{title_text}</strong> — Showing data {date_text} 
                ({len(impact_df)} actions across {unique_weeks} optimization run{'s' if unique_weeks > 1 else ''})
            </div>
            """, unsafe_allow_html=True)
    
    # ==========================================
    # SPLIT: ACTIVE vs DORMANT ACTIONS
    # ==========================================
    if not impact_df.empty:
        # Active: rows where (before_spend + after_spend) > 0
        active_mask = (impact_df['before_spend'].fillna(0) + impact_df['after_spend'].fillna(0)) > 0
        active_df = impact_df[active_mask].copy()
        dormant_df = impact_df[~active_mask].copy()
        
        # Add migration tracking indicator for HARVEST with before_spend > 0
        if 'action_type' in active_df.columns:
            active_df['is_migration'] = (
                (active_df['action_type'] == 'HARVEST') & 
                (active_df['before_spend'].fillna(0) > 0)
            )
    else:
        active_df = impact_df
        dormant_df = pd.DataFrame()
    
    # Recalculate summary for ACTIVE ONLY to ensure consistency
    active_count = len(active_df)
    dormant_count = len(dormant_df)
    
    # Calculate active-only summary metrics
    if not active_df.empty:
        # Use impact_score for the main metric (rule-based expected outcome)
        # impact_score = cost saved (for NEGATIVE) + lift (for HARVEST) + delta (for BID_CHANGE)
        impact_col = 'impact_score' if 'impact_score' in active_df.columns else 'delta_sales'
        spend_col = 'delta_spend' if 'delta_spend' in active_df.columns else 'delta_spend'
        
        impact_scores = active_df[impact_col].fillna(0)
        delta_spend = active_df[spend_col].fillna(0)
        is_winner = active_df['is_winner'].fillna(False)
        
        # Build by_action_type with correct nested structure
        by_action_type = {}
        for action_type in active_df['action_type'].unique():
            action_data = active_df[active_df['action_type'] == action_type]
            by_action_type[action_type] = {
                'net_sales': action_data[impact_col].fillna(0).sum(),  # Use impact_score
                'net_spend': action_data[spend_col].fillna(0).sum()
            }
        
        active_summary = {
            'total_actions': active_count,
            'net_sales_impact': impact_scores.sum(),  # Use impact_score for main metric
            'net_spend_change': delta_spend.sum(),
            'winners': is_winner.sum(),
            'losers': (~is_winner).sum() if 'is_winner' in active_df.columns else 0,
            'win_rate': (is_winner.sum() / active_count * 100) if active_count > 0 else 0,
            'roi': impact_scores.sum() / abs(delta_spend.sum()) if delta_spend.sum() != 0 else 0,
            'by_action_type': by_action_type
        }
    else:
        # Fallback if active_df is empty
        if time_frame:  # Always apply time frame filter
             # If filtering and no active data, show Zeros (don't fallback to lifetime)
             active_summary = {
                'total_actions': 0,
                'net_sales_impact': 0,
                'net_spend_change': 0,
                'winners': 0,
                'losers': 0,
                'win_rate': 0,
                'roi': 0,
                'by_action_type': {}
            }
        else:
             active_summary = full_summary
    
    # ==========================================
    # HERO TILES (Based on Active Only)
    # ==========================================
    _render_hero_tiles(active_summary, active_count, dormant_count)
    
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
            if active_df.empty:
                st.info("No measured impact data (all actions have $0 spend)")
            else:
                # Charts for active data - USE ACTIVE SUMMARY
                col1, col2 = st.columns(2)
                with col1:
                    _render_waterfall_chart(active_summary)
                with col2:
                    _render_winners_losers_chart(active_df)
                
                st.divider()
                
                # Drill-down table with migration badges
                _render_drill_down_table(active_df, show_migration_badge=True)
        
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
    """Render the hero metric tiles with glassmorphism style."""
    
    # Custom CSS for glassmorphism tiles
    # Theme-aware colors for subtle accents
    theme_mode = st.session_state.get('theme_mode', 'dark')
    
    # Brand-aligned color palette (true Saddle logo colors)
    if theme_mode == 'dark':
        positive_accent = "rgba(91, 85, 111, 0.3)"  # Logo purple
        positive_glow = "rgba(91, 85, 111, 0.15)"
        positive_text = "#B6B4C2"  # Soft lavender gray
        
        negative_accent = "rgba(136, 19, 55, 0.25)"  # Muted wine
        negative_glow = "rgba(136, 19, 55, 0.12)"
        negative_text = "#fda4af"  # Rose-300 (softer)
        
        neutral_accent = "rgba(148, 163, 184, 0.25)"  # Muted slate
        neutral_text = "#cbd5e1"  # Slate-300
    else:
        positive_accent = "rgba(91, 85, 111, 0.25)"  # Logo purple (lighter)
        positive_glow = "rgba(91, 85, 111, 0.10)"
        positive_text = "#5B556F"  # Direct logo color
        
        negative_accent = "rgba(136, 19, 55, 0.2)"  # Deep muted wine
        negative_glow = "rgba(136, 19, 55, 0.08)"
        negative_text = "#be123c"  # Rose-700
        
        neutral_accent = "rgba(100, 116, 139, 0.2)"
        neutral_text = "#475569"  # Slate-600
    
    # SVG Icons (Saddle Brand Palette)
    icon_color = "#8F8CA3"
    
    sales_icon = f'<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="{icon_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 6px;"><line x1="12" y1="2" x2="12" y2="22"></line><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>'
    spend_icon = f'<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="{icon_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 6px;"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline><polyline points="17 6 23 6 23 12"></polyline></svg>'
    target_icon = f'<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="{icon_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 6px;"><circle cx="12" cy="12" r="10"></circle><circle cx="12" cy="12" r="6"></circle><circle cx="12" cy="12" r="2"></circle></svg>'
    profit_icon = f'<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="{icon_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 6px;"><rect x="1" y="4" width="22" height="16" rx="2" ry="2"></rect><line x1="1" y1="10" x2="23" y2="10"></line></svg>'
    
    st.markdown("""
    <style>
    .hero-tile {
        background: linear-gradient(135deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.03) 100%);
        backdrop-filter: blur(10px);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 24px rgba(0,0,0,0.08);
        transition: all 0.3s ease;
    }
    .hero-tile:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 32px rgba(0,0,0,0.12);
    }
    .hero-value {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 6px;
        margin-top: 8px;
    }
    .hero-label {
        font-size: 0.75rem;
        opacity: 0.7;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # ==========================================
    # WATERFALL STORY: Actions → Components → Result
    # ==========================================
    
    # Extract component impacts from by_action_type
    by_type = summary.get('by_action_type', {})
    
    # Get impacts by action category
    cost_saved = sum(v['net_sales'] for k, v in by_type.items() if 'NEGATIVE' in k.upper())
    harvest_gains = sum(v['net_sales'] for k, v in by_type.items() if 'HARVEST' in k.upper())
    bid_changes = sum(v['net_sales'] for k, v in by_type.items() if 'BID' in k.upper())
    net_result = summary['net_sales_impact']
    total_actions = summary['total_actions']
    win_rate = summary['win_rate']
    
    # Identify biggest contributor
    components = [
        ('Cost Saved (Negatives)', cost_saved),
        ('Harvest Efficiency', harvest_gains),
        ('Bid Adjustments', bid_changes)
    ]
    sorted_components = sorted(components, key=lambda x: abs(x[1]), reverse=True)
    biggest_name, biggest_value = sorted_components[0]
    
    # Story callout
    if net_result >= 0:
        story_icon = "✅"
        story_color = positive_text
        story_text = f"Net positive! {biggest_name} contributed ${biggest_value:+,.0f}"
    else:
        # Find the biggest negative contributor
        negative_components = [(n, v) for n, v in components if v < 0]
        if negative_components:
            drag_name, drag_value = min(negative_components, key=lambda x: x[1])
            story_icon = "⚠️"
            story_color = negative_text
            story_text = f"{drag_name} dragged down results by ${abs(drag_value):,.0f}"
        else:
            story_icon = "📊"
            story_color = neutral_text
            story_text = "Impact below expectations"
    
    # Row 1: 5 tiles showing the waterfall
    col1, col2, col3, col4, col5 = st.columns(5)
    
    small_tile_style = "padding: 16px; border-radius: 10px; text-align: center;"
    label_style = "font-size: 0.7rem; color: #8F8CA3; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; display: flex; align-items: center; justify-content: center; gap: 6px;"
    value_style = "font-size: 1.4rem; font-weight: 700;"
    
    # SVG Icons (consistent with brand)
    icon_color = "#8F8CA3"
    bar_chart_icon = f'<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="{icon_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>'
    shield_icon = f'<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>'
    leaf_icon = f'<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"></path><path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"></path></svg>'
    trending_icon = f'<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="{icon_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline><polyline points="17 6 23 6 23 12"></polyline></svg>'
    dollar_icon = f'<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="{icon_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="1" x2="12" y2="23"></line><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>'
    target_icon = f'<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="{icon_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><circle cx="12" cy="12" r="6"></circle><circle cx="12" cy="12" r="2"></circle></svg>'
    activity_icon = f'<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="{icon_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>'
    check_icon = f'<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>'
    alert_icon = f'<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>'
    
    with col1:
        st.markdown(f"""
        <div style="{small_tile_style} background: rgba(143, 140, 163, 0.08); border: 1px solid rgba(143, 140, 163, 0.15);">
            <div style="{label_style}">{bar_chart_icon} Actions</div>
            <div style="{value_style} color: {neutral_text};">{total_actions:,}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        color = positive_text if cost_saved > 0 else negative_text if cost_saved < 0 else neutral_text
        prefix = '+' if cost_saved > 0 else ''
        st.markdown(f"""
        <div style="{small_tile_style} background: rgba(34, 197, 94, 0.08); border: 1px solid rgba(34, 197, 94, 0.2);">
            <div style="{label_style}">{shield_icon} Cost Saved</div>
            <div style="{value_style} color: {color};">{prefix}${cost_saved:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        color = positive_text if harvest_gains > 0 else negative_text if harvest_gains < 0 else neutral_text
        prefix = '+' if harvest_gains > 0 else ''
        st.markdown(f"""
        <div style="{small_tile_style} background: rgba(59, 130, 246, 0.08); border: 1px solid rgba(59, 130, 246, 0.2);">
            <div style="{label_style}">{leaf_icon} Harvest Gains</div>
            <div style="{value_style} color: {color};">{prefix}${harvest_gains:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        color = positive_text if bid_changes > 0 else negative_text if bid_changes < 0 else neutral_text
        prefix = '+' if bid_changes > 0 else ''
        bg_color = "rgba(34, 197, 94, 0.08)" if bid_changes > 0 else "rgba(239, 68, 68, 0.08)" if bid_changes < 0 else "rgba(143, 140, 163, 0.08)"
        border_color = "rgba(34, 197, 94, 0.2)" if bid_changes > 0 else "rgba(239, 68, 68, 0.2)" if bid_changes < 0 else "rgba(143, 140, 163, 0.15)"
        st.markdown(f"""
        <div style="{small_tile_style} background: {bg_color}; border: 1px solid {border_color};">
            <div style="{label_style}">{trending_icon} Bid Changes</div>
            <div style="{value_style} color: {color};">{prefix}${bid_changes:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        color = positive_text if net_result > 0 else negative_text if net_result < 0 else neutral_text
        prefix = '+' if net_result > 0 else ''
        bg_color = positive_glow if net_result > 0 else negative_glow if net_result < 0 else "rgba(143, 140, 163, 0.08)"
        border_color = positive_accent if net_result > 0 else negative_accent if net_result < 0 else neutral_accent
        st.markdown(f"""
        <div style="{small_tile_style} background: linear-gradient(135deg, {bg_color} 0%, rgba(255,255,255,0.03) 100%); border-left: 4px solid {border_color};">
            <div style="{label_style}">{dollar_icon} Net Result</div>
            <div style="{value_style} color: {color};">{prefix}${net_result:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Story callout row with SVG icons
    story_svg = check_icon if net_result >= 0 else alert_icon
    
    st.markdown(f"""
    <div style="background: rgba(143, 140, 163, 0.05); border: 1px solid rgba(143, 140, 163, 0.1); border-radius: 8px; 
                padding: 12px 20px; margin-top: 16px; display: flex; align-items: center; justify-content: space-between;">
        <div style="display: flex; align-items: center; gap: 10px;">
            {story_svg}
            <span style="color: {story_color}; font-weight: 600;">{story_text}</span>
        </div>
        <div style="display: flex; gap: 24px; color: #8F8CA3; font-size: 0.85rem;">
            <span style="display: flex; align-items: center; gap: 4px;">{target_icon} Win Rate: <strong style="color: {positive_text if win_rate >= 60 else negative_text if win_rate < 40 else neutral_text};">{win_rate:.0f}%</strong></span>
            <span style="display: flex; align-items: center; gap: 4px;">{activity_icon} Measured: <strong>{active_count}</strong> | Pending: <strong>{dormant_count}</strong></span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _render_waterfall_chart(summary: Dict[str, Any]):
    """Render waterfall chart showing impact by action type."""
    
    # Target icon for action type
    icon_color = "#8F8CA3"
    target_icon = f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{icon_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 8px;"><circle cx="12" cy="12" r="10"></circle><circle cx="12" cy="12" r="6"></circle><circle cx="12" cy="12" r="2"></circle></svg>'
    st.markdown(f"### {target_icon}Impact by Action Type", unsafe_allow_html=True)
    
    by_type = summary.get('by_action_type', {})
    
    if not by_type:
        st.info("No action type breakdown available")
        return
    
    # Prepare data
    action_types = list(by_type.keys())
    net_impacts = [by_type[t]['net_sales'] - by_type[t]['net_spend'] for t in action_types]
    
    # Sort by impact
    sorted_data = sorted(zip(action_types, net_impacts), key=lambda x: x[1], reverse=True)
    action_types = [x[0] for x in sorted_data]
    net_impacts = [x[1] for x in sorted_data]
    
    # Create waterfall chart - using analytical palette with transparency
    # Brand-aligned colors: Muted violet for positive, muted wine for negative
    fig = go.Figure(go.Waterfall(
        name="Impact",
        orientation="v",
        measure=["relative"] * len(net_impacts) + ["total"],
        x=action_types + ['Total'],
        y=net_impacts + [sum(net_impacts)],
        connector={"line": {"color": "rgba(148, 163, 184, 0.2)"}},
        decreasing={"marker": {"color": "rgba(136, 19, 55, 0.5)"}}, # Muted Wine
        increasing={"marker": {"color": "rgba(91, 85, 111, 0.6)"}}, # Logo purple
        totals={"marker": {"color": "rgba(30, 41, 59, 0.8)"}},
        textposition="outside",
        text=[f"${v:+,.0f}" for v in net_impacts] + [f"${sum(net_impacts):+,.0f}"]
    ))
    
    fig.update_layout(
        showlegend=False,
        height=350,
        margin=dict(t=20, b=20, l=20, r=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)'),
        xaxis=dict(showgrid=False)
    )
    
    st.plotly_chart(fig, use_container_width=True)


def _render_winners_losers_chart(impact_df: pd.DataFrame):
    """Render top winners and losers based on raw performance aggregated by target."""
    
    # Chart icon 
    icon_color = "#8F8CA3"
    chart_icon = f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="{icon_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 8px;"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>'
    st.markdown(f"### {chart_icon}Biggest Winners & Losers", unsafe_allow_html=True)
    
    if impact_df.empty:
        st.info("No impact data available")
        return
    
    # AGGREGATE BY TARGET: This is critical.
    # impact_df has one row per ACTION. We need one bar per TARGET.
    target_perf = impact_df.groupby('target_text').agg({
        'delta_sales': 'first', # These are target-level metrics already
        'delta_spend': 'first',
        'before_spend': 'first',
        'after_spend': 'first'
    }).reset_index()
    
    # Calculate RAW individual performance (not prorated)
    target_perf['raw_perf'] = target_perf['delta_sales'].fillna(0) - target_perf['delta_spend'].fillna(0)
    
    # Filter to targets that actually had activity
    target_perf = target_perf[(target_perf['before_spend'] > 0) | (target_perf['after_spend'] > 0)]
    
    if target_perf.empty:
        st.info("No matched targets with performance data found")
        return
    
    # Get top 5 winners and bottom 5 losers
    winners = target_perf.sort_values('raw_perf', ascending=False).head(5)
    losers = target_perf.sort_values('raw_perf', ascending=True).head(5)
    
    # Combine for chart
    chart_df = pd.concat([winners, losers]).drop_duplicates().sort_values('raw_perf', ascending=False)
    chart_df['target_short'] = chart_df['target_text'].str[:25] + '...'
    
    # Brand-aligned palette: Muted violet for positive, muted wine for negative
    chart_df['color'] = chart_df['raw_perf'].apply(
        lambda x: "rgba(91, 85, 111, 0.6)" if x > 0 else "rgba(136, 19, 55, 0.5)"
    )
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=chart_df['target_short'],
        x=chart_df['raw_perf'],
        orientation='h',
        marker_color=chart_df['color'],
        text=[f"${v:+,.0f}" for v in chart_df['raw_perf']],
        textposition='outside'
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
    """Render detailed drill-down table with optional migration badges."""
    
    with st.expander("📋 Detailed Action Log", expanded=False):
        if impact_df.empty:
            st.info("No actions to display")
            return
        
        # Create display dataframe
        display_df = impact_df.copy()
        
        # Add migration badge for HARVEST with before_spend > 0
        if show_migration_badge and 'is_migration' in display_df.columns:
            # Create a formatted action column with badge
            display_df['action_display'] = display_df.apply(
                lambda r: f"🔄 {r['action_type']}" if r.get('is_migration', False) else r['action_type'],
                axis=1
            )
        else:
            display_df['action_display'] = display_df['action_type']
        
        # Select columns for display (include validation_status for rule-based impact)
        display_cols = [
            'action_display', 'target_text', 'reason',
            'before_spend', 'after_spend', 'delta_spend',
            'before_sales', 'after_sales', 'delta_sales',
            'impact_score', 'validation_status', 'is_winner'
        ]
        
        available_cols = [c for c in display_cols if c in display_df.columns]
        display_df = display_df[available_cols].copy()
        
        # Format numeric columns
        for col in ['before_spend', 'after_spend', 'delta_spend', 'before_sales', 'after_sales', 'delta_sales', 'impact_score']:
            if col in display_df.columns:
                display_df[col] = display_df[col].apply(
                    lambda x: f"${x:,.2f}" if pd.notna(x) else "-"
                )
        
        # Format is_winner mapping to be more descriptive
        if 'is_winner' in display_df.columns:
            def format_result(row):
                val = row['is_winner']
                if pd.isna(val) or val is None: return "-"
                
                # Check raw performance for labeling
                # We use raw delta_sales/spend from the original impact_df if available
                # or just use the is_winner boolean if it's already calculated correctly
                if val == True:
                    return "📈 Positive Impact"
                
                # If we're here, is_winner is False. 
                # We need to distinguish between "Negative Impact" and "No Change"
                # Using the raw delta_sales and delta_spend before being formatted to strings
                dsales = row['_delta_sales_raw']
                dspend = row['_delta_spend_raw']
                
                if abs(dsales) < 0.01 and abs(dspend) < 0.01:
                    return "➖ No Measurable Impact"
                return "📉 Negative Impact"

            # Create temporary raw columns for logic
            display_df['_delta_sales_raw'] = impact_df.loc[display_df.index, 'delta_sales'].fillna(0)
            display_df['_delta_spend_raw'] = impact_df.loc[display_df.index, 'delta_spend'].fillna(0)
            
            display_df['is_winner'] = display_df.apply(format_result, axis=1)
            
            # Drop temporary columns
            display_df = display_df.drop(columns=['_delta_sales_raw', '_delta_spend_raw'])
        
        display_df = display_df.rename(columns={
            'action_display': 'Action',
            'target_text': 'Target',
            'reason': 'Reason',
            'before_spend': 'Before Spend',
            'after_spend': 'After Spend',
            'delta_spend': 'Δ Spend',
            'before_sales': 'Before Sales',
            'after_sales': 'After Sales',
            'delta_sales': 'Δ Sales',
            'impact_score': 'Impact',
            'validation_status': 'Status',
            'is_winner': 'Result'
        })
        
        # Show migration legend if applicable
        if show_migration_badge and 'is_migration' in impact_df.columns and impact_df['is_migration'].any():
            st.caption("🔄 = **Migration Tracking**: This search term's performance is tracked across ALL campaigns "
                      "(e.g., Auto → Exact). Shows efficiency gain from your harvest.")
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
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
    Returns the EXACT same metrics as Impact tab's 30D view.
    Reuses identical calculation logic - no separate path.
    """
    from datetime import timedelta
    
    db_manager = st.session_state.get('db_manager')
    selected_client = (
        st.session_state.get('active_account_id') or 
        st.session_state.get('active_account_name') or 
        st.session_state.get('last_stats_save', {}).get('client_id')
    )
    
    if not db_manager or not selected_client:
        return None
        
    try:
        # USE CACHED DATA FETCHER
        test_mode = st.session_state.get('test_mode', False)
        # Use data upload timestamp as cache version
        cv = str(st.session_state.get('data_upload_timestamp', 'v1'))
        impact_df, _ = _fetch_impact_data(selected_client, test_mode, window_days=7, cache_version=cv)
        
        if impact_df.empty:
            return None
            
        # Get available dates (fast, usually cached internally by DB manager if needed, but cheap query)
        available_dates = db_manager.get_available_dates(selected_client)
        if not available_dates:
            return None
        
        # Apply 30D filter (same as Impact tab lines 120-130)
        impact_df['action_date_dt'] = pd.to_datetime(impact_df['action_date'], errors='coerce')
        latest_data_date = pd.to_datetime(available_dates[0])
        cutoff_date = latest_data_date - timedelta(days=30)
        impact_df = impact_df[impact_df['action_date_dt'] >= cutoff_date].copy()
        
        if impact_df.empty:
            return None
        
        # Active filter (same as Impact tab lines 172-174)
        active_mask = (impact_df['before_spend'].fillna(0) + impact_df['after_spend'].fillna(0)) > 0
        active_df = impact_df[active_mask].copy()
        
        if active_df.empty:
            return None
        
        # Calculate exactly like Impact tab using impact_score (rule-based)
        impact_col = 'impact_score' if 'impact_score' in active_df.columns else 'delta_sales'
        spend_col = 'delta_spend' if 'delta_spend' in active_df.columns else 'delta_spend'
        
        impact_scores = active_df[impact_col].fillna(0)
        delta_spend = active_df[spend_col].fillna(0)
        is_winner = active_df['is_winner'].fillna(False)
        active_count = len(active_df)
        
        # Find top action type by net impact
        top_action_type = None
        if 'action_type' in active_df.columns:
            by_type = active_df.groupby('action_type')[impact_col].sum()
            if not by_type.empty:
                top_action_type = by_type.idxmax()
        
        return {
            'sales': impact_scores.sum(),  # Use impact_score, not delta_sales
            'roi': impact_scores.sum() / abs(delta_spend.sum()) if delta_spend.sum() != 0 else 0,
            'win_rate': (is_winner.sum() / active_count * 100) if active_count > 0 else 0,
            'top_action_type': top_action_type
        }
    except:
        pass
        
    return None

