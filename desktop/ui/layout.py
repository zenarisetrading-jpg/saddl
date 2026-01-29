"""
UI Layout Components

Page setup, sidebar navigation, and home page.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import timedelta

from ui.theme import ThemeManager
# Lazy imports moved inside functions to prevent circular dependencies
# from features.impact_dashboard import get_recent_impact_summary
# from features.report_card import get_account_health_score
# from core.account_utils import get_active_account_id

def setup_page():
    """Setup page CSS and styling."""
    # Apply dynamic theme CSS
    ThemeManager.apply_css()

def render_sidebar(navigate_to):
    """
    Render sidebar navigation.
    
    Args:
        navigate_to: Function to navigate between modules
        
    Returns:
        Selected module name
    """
    # Wrap navigate_to to check for pending actions when leaving optimizer
    def safe_navigate(target_module):
        current = st.session_state.get('current_module', 'home')
        
        # Check if leaving optimizer with pending actions that haven't been accepted
        if current == 'optimizer' and target_module != 'optimizer':
            pending = st.session_state.get('pending_actions')
            accepted = st.session_state.get('optimizer_actions_accepted', False)
            
            if pending and not accepted:
                # Store the target and show confirmation
                st.session_state['_pending_navigation_target'] = target_module
                st.session_state['_show_action_confirmation'] = True
                st.rerun()
                return
        
        navigate_to(target_module)
    # Sidebar Logo at TOP (theme-aware, prominent)
    theme_mode = st.session_state.get('theme_mode', 'dark')
    logo_data = ThemeManager.get_cached_logo(theme_mode)
    
    if logo_data:
        st.sidebar.markdown(
            f'<div style="text-align: center; padding: 15px 0 20px 0;"><img src="data:image/png;base64,{logo_data}" style="width: 200px;" /></div>',
            unsafe_allow_html=True
        )
        
    # Account selector
    from ui.account_manager import render_account_selector
    render_account_selector()
    
    st.sidebar.markdown("---")
    
    if st.sidebar.button("Home", use_container_width=True):
        safe_navigate('home')
    
    if st.sidebar.button("Account Overview", use_container_width=True):
        safe_navigate('performance')
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("##### SYSTEM")
    
    # Data Hub - central upload
    if st.sidebar.button("Data Hub", use_container_width=True):
        safe_navigate('data_hub')
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("##### ANALYZE")
    
    # Core features
    if st.sidebar.button("Optimizer", use_container_width=True):
        safe_navigate('optimizer')
    
    if st.sidebar.button("ASIN Shield", use_container_width=True):
        safe_navigate('asin_mapper')
    
    if st.sidebar.button("Clusters", use_container_width=True):
        safe_navigate('ai_insights')
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("##### ACTIONS")
    
    if st.sidebar.button("Launchpad", use_container_width=True):
        safe_navigate('creator')
    
    st.sidebar.markdown("---")
    
    if st.sidebar.button("Help & Support", use_container_width=True, icon="❓"):
        safe_navigate('help_center')
    
    # Show undo toast if available
    from ui.action_confirmation import show_undo_toast
    show_undo_toast()
    
    # Theme Toggle at BOTTOM
    st.sidebar.markdown("---")
    ThemeManager.render_toggle()
    
    return st.session_state.get('current_module', 'home')

def render_home():
    import streamlit as st

    from features.impact_dashboard import get_recent_impact_summary
    from features.report_card import get_account_health_score
    from core.account_utils import get_active_account_id
    from ui.components.empty_states import render_empty_state
    
    # === EMPTY STATE CHECKS ===
    # Support "Test Mode" via query params to verify empty states without deleting data
    # Usage: ?test_state=no_account or ?test_state=no_data
    test_state = st.query_params.get("test_state")


    
    # 1. Check if any accounts exist at all (No Accounts)
    db = st.session_state.get('db_manager')
    has_accounts = False
    if db:
        # Get Organization Context
        from core.auth.service import AuthService
        auth = AuthService()
        current_user = auth.get_current_user()
        org_id = str(current_user.organization_id) if current_user else None
        
        accounts = db.get_all_accounts(organization_id=org_id)
        has_accounts = len(accounts) > 0
        
    # Force empty state if requested
    if test_state == "no_account" or not has_accounts:
        render_empty_state('no_account')
        return

    # 2. Check if active account has data (No Data / Syncing)
    active_account_id = st.session_state.get('active_account_id')
    account_name = st.session_state.get('active_account_name', 'Account')
    
    # Check if data loaded in DataHub or DB has data
    from core.data_hub import DataHub
    hub = DataHub()
    
    # Try basic data existence check
    data_exists = False
    if hub.is_loaded("search_term_report"):
        data_exists = True
    elif active_account_id and db:
        # Quick DB check
        dates = db.get_available_dates(active_account_id)
        if dates and len(dates) > 0:
            data_exists = True
            
    if test_state == "no_data" or not data_exists:
        render_empty_state('no_data', context={'account_name': account_name})
        return

    st.markdown("""
        <style>
        /* Premium Cards */
        [data-testid="stColumn"]:has(.cockpit-marker) > div {
            background: linear-gradient(135deg, rgba(30, 41, 59, 0.95) 0%, rgba(15, 23, 42, 0.95) 100%);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(148, 163, 184, 0.15);
            border-radius: 16px;
            padding: 24px;
            box-shadow: 
                0 4px 16px rgba(0, 0, 0, 0.3),
                0 0 0 1px rgba(255, 255, 255, 0.05) inset;
            transition: all 0.3s ease;
            display: flex;
            flex-direction: column;
            min-height: 220px;
        }
        
        [data-testid="stColumn"]:has(.cockpit-marker) > div:hover {
            transform: translateY(-2px);
            box-shadow: 
                0 8px 24px rgba(0, 0, 0, 0.4),
                0 0 0 1px rgba(255, 255, 255, 0.08) inset;
            border-color: rgba(6, 182, 212, 0.3);
        }
        
        .cockpit-label {
            font-size: 0.75rem;
            color: #94a3b8;
            font-weight: 700;
            margin-bottom: 12px;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        .cockpit-subtext {
            font-size: 0.8rem;
            color: #94a3b8;
            margin-top: 4px;
        }
        
        /* Key Insights Cards */
        .insight-card {
            background: linear-gradient(135deg, rgba(30, 41, 59, 0.6) 0%, rgba(15, 23, 42, 0.6) 100%);
            backdrop-filter: blur(8px);
            border-radius: 12px;
            padding: 18px 20px !important;
            transition: all 0.25s ease;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
            margin-bottom: 10px;
        }
        
        .insight-card:hover {
            transform: translateX(4px) translateY(-2px);
            box-shadow: 0 6px 16px rgba(0, 0, 0, 0.3);
        }
        
        /* Key Insights - Type Colors */
        [data-testid="column"]:has(.insight-positive), [data-testid="stColumn"]:has(.insight-positive) {
            border-left: 3px solid #10B981 !important;
        }

        [data-testid="column"]:has(.insight-positive):hover, [data-testid="stColumn"]:has(.insight-positive):hover {
            box-shadow: 
                0 6px 16px rgba(0, 0, 0, 0.3),
                -3px 0 12px rgba(16, 185, 129, 0.3) !important;
        }

        [data-testid="column"]:has(.insight-warning), [data-testid="stColumn"]:has(.insight-warning) {
            border-left: 3px solid #F59E0B !important;
        }

        [data-testid="column"]:has(.insight-warning):hover, [data-testid="stColumn"]:has(.insight-warning):hover {
            box-shadow: 
                0 6px 16px rgba(0, 0, 0, 0.3),
                -3px 0 12px rgba(245, 158, 11, 0.3) !important;
        }

        [data-testid="column"]:has(.insight-info), [data-testid="stColumn"]:has(.insight-info) {
            border-left: 3px solid #06B6D4 !important;
        }

        /* Icon glow */
        .insight-icon {
            width: 40px;
            height: 40px;
            border-radius: 10px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
            margin-right: 12px;
            background: rgba(255,255,255,0.05); /* fallback */
        }

        .insight-positive .insight-icon {
            background: rgba(16, 185, 129, 0.15);
            color: #10B981;
            box-shadow: 0 0 12px rgba(16, 185, 129, 0.2);
        }

        .insight-warning .insight-icon {
            background: rgba(245, 158, 11, 0.15);
            color: #F59E0B;
            box-shadow: 0 0 12px rgba(245, 158, 11, 0.2);
        }

        .insight-info .insight-icon {
            background: rgba(6, 182, 212, 0.15);
            color: #06B6D4;
            box-shadow: 0 0 12px rgba(6, 182, 212, 0.2);
        }
        
        /* Smooth page load */
        [data-testid="stVerticalBlock"] > div {
            animation: fadeIn 0.5s ease-out;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        /* Fix for plotly height adjustment */
        .js-plotly-plot { margin-top: 10px; }
        
        /* Hide the marker itself */
        .cockpit-marker { display: none; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <h1 style="
        background: linear-gradient(135deg, #F5F5F7 0%, #22D3EE 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 8px;
    ">
        DECISION COCKPIT
    </h1>
    <p style="color: #94a3b8; font-size: 0.95rem; margin-bottom: 24px;">
        Strategic overview of your account performance
    </p>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    t1, t2, t3 = st.columns(3)
    
    with t1:
        st.markdown('<div class="cockpit-marker health-marker"></div>', unsafe_allow_html=True)
        # Determine source badge
        source = st.session_state.get('_cockpit_data_source', 'db')
        sync_badge = '<span style="font-size: 0.55rem; background: rgba(34, 197, 94, 0.15); color: #22c55e; padding: 2px 6px; border-radius: 4px; font-weight: 800;">LIVE SYNC</span>' if source == 'live' else ''
        
        # Header - LEFT ALIGNED (Removed justify-content:center)
        st.markdown(f'<div class="cockpit-label" style="justify-content: space-between;"><span>Health Score</span>{sync_badge}</div>', unsafe_allow_html=True)
        
        if active_account_id:
            health = get_account_health_score(str(active_account_id))
        else:
            health = None
        
        # Note: The column container itself is flex-column (from CSS on line 118)
        # We will render items sequentially.
        
        if health is not None:
            health = round(health)
            import plotly.graph_objects as go
            
            # Status thresholds
            if health > 75:
                status_text = "HEALTHY"
                status_color = "#22c55e"
            elif health >= 40:
                status_text = "STABLE"
                status_color = "#f59e0b"
            else:
                status_text = "ATTENTION"
                status_color = "#ef4444"
            
            # Dashboard-consistent gauge
            fig = go.Figure(go.Indicator(
                mode="gauge",  # Removed 'number' to render it with Custom HTML for Glow Effect
                value=health,
                gauge={
                    'axis': {
                        'range': [0, 100],
                        'tickwidth': 1,
                        'tickcolor': '#64748b',
                        'ticklen': 10,
                        'tickvals': [0, 25, 50, 75, 100],
                        'ticktext': ['0', '25', '50', '75', '100'],
                        'tickfont': {'size': 10, 'color': '#64748b'}
                    },
                    'bar': {'color': '#06b6d4', 'thickness': 0.7}, 
                    'bgcolor': '#374151',
                    'borderwidth': 0,
                }
            ))
            
            # Increased height for visual impact
            fig.update_layout(
                height=145, 
                margin=dict(l=30, r=30, t=15, b=0),
                paper_bgcolor="rgba(0,0,0,0)",
                font={'family': 'Inter, sans-serif'}
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            
            # Score + Status Text (Overlaid on Gauge with negative margin)
            st.markdown(f'''
            <div style="text-align: center; margin-top: -70px; margin-bottom: 25px; position: relative; z-index: 10;">
                <div style="
                    color: #06B6D4;
                    font-size: 2.8rem;
                    font-weight: 800;
                    text-shadow: 0 0 20px rgba(6, 182, 212, 0.5);
                    line-height: 1;
                    margin-bottom: 4px;
                    font-family: 'Inter', sans-serif;
                ">{health}%</div>
                <div style="
                    color: {status_color}; 
                    font-weight: 700; 
                    font-size: 0.85rem; 
                    text-transform: uppercase; 
                    letter-spacing: 1px;
                    text-shadow: 0 0 10px {status_color}40;
                ">{status_text}</div>
            </div>
            ''', unsafe_allow_html=True)
            
            # Get actual scores from stored health data
            db_manager = st.session_state.get('db_manager')
            selected_client = st.session_state.get('active_account_id') or st.session_state.get('active_account_name')
            roas_score, efficiency_score, cvr_score = 0, 0, 0
            if db_manager and selected_client:
                try:
                    health_data = db_manager.get_account_health(selected_client)
                    if health_data:
                        roas_score = health_data.get('roas_score', 0)
                        efficiency_score = health_data.get('waste_score', 0)  # DB column is waste_score
                        cvr_score = health_data.get('cvr_score', 0)
                except:
                    pass
            
            # BOTTOM ROW: Display actual scores
            # Using margin-top: 15px to ensure separation, textual alignment centered
            st.markdown(f'''<div style="display: flex; justify-content: space-around; text-align: center; width: 100%;">
                <div><div style="font-size: 0.95rem; font-weight: 700; color: #94a3b8;">{roas_score:.0f}</div><div style="font-size: 0.6rem; color: #64748b;">ROAS</div></div>
                <div><div style="font-size: 0.95rem; font-weight: 700; color: #94a3b8;">{efficiency_score:.0f}</div><div style="font-size: 0.6rem; color: #64748b;">Efficiency</div></div>
                <div><div style="font-size: 0.95rem; font-weight: 700; color: #94a3b8;">{cvr_score:.0f}</div><div style="font-size: 0.6rem; color: #64748b;">CVR</div></div>
            </div>''', unsafe_allow_html=True)
            
        else:
            st.markdown('<div class="cockpit-value" style="text-align:center; padding: 40px 0; color: #64748b;">—</div>', unsafe_allow_html=True)
            st.markdown('<div class="cockpit-subtext" style="text-align:center;">Run optimizer to calculate</div>', unsafe_allow_html=True)

    with t2:
        st.markdown('<div class="cockpit-marker"></div>', unsafe_allow_html=True)
        st.markdown('<div class="cockpit-label" style="text-align:center;">14-Day Decision Impact</div>', unsafe_allow_html=True)
        impact_data = get_recent_impact_summary()
        st.markdown('<div style="flex-grow:1; display:flex; flex-direction:column; justify-content:space-between; text-align:center;">', unsafe_allow_html=True)
        if impact_data is not None:
            impact = impact_data.get('sales', 0)
            win_rate = impact_data.get('win_rate', 0)
            top_action = impact_data.get('top_action_type', None)
            
            # Center main content
            from utils.formatters import get_account_currency
            home_currency = get_account_currency()
            st.markdown('<div style="flex-grow:1; display:flex; flex-direction:column; justify-content:center;">', unsafe_allow_html=True)
            st.markdown(f"""
            <div style="text-align: center; padding: 32px 0;">
                <div style="
                    color: #06B6D4;
                    font-size: 3.2rem;
                    font-weight: 800;
                    text-shadow: 0 0 24px rgba(6, 182, 212, 0.4);
                    margin-bottom: 8px;
                    letter-spacing: -1px;
                ">
                    {f"+{home_currency}{impact:,.0f}" if impact >= 0 else f"-{home_currency}{abs(impact):,.0f}"}
                </div>
                <div style="color: #94a3b8; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px;">
                    Net Change Last 14 Days
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Bottom row callouts - at absolute bottom
            action_display = ""
            if top_action:
                action_display = {"HARVEST": "Harvests", "NEGATIVE": "Keyword Defense", "BID_UPDATE": "Bid Changes", "BID_CHANGE": "Bid Changes"}.get(top_action, top_action.title())
            
            # Trend indicator with clearer labels and tooltip
            # Positive: Sales increased after optimizer actions - good!
            # Attention: Sales decreased - may need to review actions or wait for more data
            # Stable: No net change - actions had neutral effect
            if impact > 0:
                arrow_svg = '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2.5" style="vertical-align:middle"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"></polyline><polyline points="16 7 22 7 22 13"></polyline></svg>'
                trend_text = "Growing"
                trend_color = "#22c55e"
                trend_tooltip = "Decision Impact is positive over the last 14 days. Your optimization actions are driving value!"
            elif impact < 0:
                arrow_svg = '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2.5" style="vertical-align:middle"><polyline points="6 9 12 15 18 9"></polyline></svg>'
                trend_text = "Review Needed"
                trend_color = "#f59e0b"
                trend_tooltip = "Decision Impact is negative. This requires review to ensure actions are having the desired effect."
            else:
                arrow_svg = ''
                trend_text = "Stable"
                trend_color = "#64748b"
                trend_tooltip = "Decision Impact is neutral. Actions have stabilized performance."
            
            trend_html = f'{arrow_svg} <span style="color:{trend_color}">{trend_text}</span>'
            
            # CSS tooltip that works in Streamlit (title attribute doesn't work reliably)
            tooltip_css = '''
            <style>
            .tooltip-container { position: relative; display: inline-block; cursor: help; }
            .tooltip-container .tooltip-text {
                visibility: hidden;
                width: 220px;
                background-color: #1e293b;
                color: #e2e8f0;
                text-align: left;
                border-radius: 6px;
                padding: 8px 10px;
                position: absolute;
                z-index: 1000;
                bottom: 125%;
                left: 50%;
                margin-left: -110px;
                opacity: 0;
                transition: opacity 0.2s;
                font-size: 0.75rem;
                line-height: 1.4;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            }
            .tooltip-container:hover .tooltip-text { visibility: visible; opacity: 1; }
            .info-icon { font-size: 0.7rem; color: #64748b; margin-left: 3px; }
            </style>
            '''
            
            st.markdown(f'''{tooltip_css}
            <div style="display: flex; justify-content: space-around; text-align: center; margin-top: auto;">
                <div>
                    <div style="font-size: 0.95rem; font-weight: 700; color: #94a3b8;">{action_display or "—"}</div>
                    <div style="font-size: 0.6rem; color: #64748b;">
                        Top Driver
                        <span class="tooltip-container"><span class="info-icon">ⓘ</span><span class="tooltip-text">The action type that contributed most to your recent decision impact.</span></span>
                    </div>
                </div>
                <div>
                    <div style="font-size: 0.95rem; font-weight: 700;">{trend_html}</div>
                    <div style="font-size: 0.6rem; color: #64748b;">
                        14-Day Trend
                        <span class="tooltip-container"><span class="info-icon">ⓘ</span><span class="tooltip-text">{trend_tooltip}</span></span>
                    </div>
                </div>
            </div>''', unsafe_allow_html=True)
        else:
            st.markdown('<div class="cockpit-value" style="text-align:center;">—</div>', unsafe_allow_html=True)
            st.markdown('<div class="cockpit-subtext" style="text-align:center;">Run optimizer to track impact</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with t3:
        st.markdown('<div class="cockpit-marker"></div>', unsafe_allow_html=True)
        st.markdown('<div class="cockpit-label">Next Step</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-weight: 700; font-size: 1rem; margin-bottom: 4px;">Optimization Ready</div>', unsafe_allow_html=True)
        st.markdown('<div class="cockpit-subtext" style="margin-bottom: 20px;">Review your optimization recommendations.</div>', unsafe_allow_html=True)
        if st.button("Review Optimization Recommendations", use_container_width=True, type="primary"):
            st.session_state['current_module'] = 'optimizer'
            st.rerun()
            
        # Secondary CTA
        if st.button("Executive Summary", use_container_width=True):
            st.session_state['current_module'] = 'performance'
            st.session_state['active_perf_tab'] = 'Executive Dashboard'
            st.rerun()


    # ========================================
    # COMPUTE 6 KEY INSIGHTS
    # ========================================
    from datetime import date, timedelta
    from utils.formatters import get_account_currency
    from core.account_utils import get_active_account_id
    from features.impact_dashboard import get_recent_impact_summary
    import numpy as np
    import pandas as pd
    
    currency = get_account_currency()
    insights = []
    
    # Get DB manager and client
    db_manager = st.session_state.get('db_manager')
    client_id = get_active_account_id()
    
    # ========================================
    # ROW 1: PERFORMANCE METRICS (14d delta)
    # ========================================
    roas_delta = 0
    efficiency_delta = 0
    efficiency_current = 0
    top_campaign = "—"
    top_campaign_delta = 0
    
    if db_manager and client_id:
        try:
            # Fetch all data and filter locally (get_target_stats_df doesn't accept date params)
            df_all = db_manager.get_target_stats_df(client_id)
            


            if df_all is not None and not df_all.empty:
                # Column normalization (Case-insensitive check)
                if 'Date' not in df_all.columns:
                    # Try lowercase 'date'
                    col_map = {c.lower(): c for c in df_all.columns}
                    if 'date' in col_map:
                        df_all['Date'] = df_all[col_map['date']]
                
                if 'Date' in df_all.columns:
                    df_all['Date'] = pd.to_datetime(df_all['Date'], errors='coerce')
                    df_all = df_all.dropna(subset=['Date'])
                    
                    if not df_all.empty:
                        max_date = df_all['Date'].max().date()
                        
                        # Define windows (inclusive)
                        end_curr_date = max_date
                        start_curr_date = max_date - timedelta(days=14)
                        end_prev_date = start_curr_date - timedelta(days=1)
                        start_prev_date = end_prev_date - timedelta(days=13)
                        
                        # Convert to Timestamps for robust filtering
                        ts_start_curr = pd.Timestamp(start_curr_date)
                        ts_end_curr = pd.Timestamp(end_curr_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
                        
                        ts_start_prev = pd.Timestamp(start_prev_date)
                        ts_end_prev = pd.Timestamp(end_prev_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
                        
                        # Filter using Timestamps (more reliable than .dt.date comparison)
                        df_curr = df_all[(df_all['Date'] >= ts_start_curr) & (df_all['Date'] <= ts_end_curr)]
                        df_prev = df_all[(df_all['Date'] >= ts_start_prev) & (df_all['Date'] <= ts_end_prev)]
                        

                        
                    if not df_curr.empty:
                        # ROAS Trend
                        curr_spend = df_curr['Spend'].sum() if 'Spend' in df_curr.columns else 0
                        curr_sales = df_curr['Sales'].sum() if 'Sales' in df_curr.columns else 0
                        roas_curr = curr_sales / curr_spend if curr_spend > 0 else 0
                        
                        if not df_prev.empty:
                            prev_spend = df_prev['Spend'].sum() if 'Spend' in df_prev.columns else 0
                            prev_sales = df_prev['Sales'].sum() if 'Sales' in df_prev.columns else 0
                            roas_prev = prev_sales / prev_spend if prev_spend > 0 else 0
                            roas_delta = ((roas_curr - roas_prev) / roas_prev * 100) if roas_prev > 0 else 0
                    
                    # Spend Efficiency (Ad Group aggregation)
                    def calc_efficiency(df):
                        if 'Ad Group Name' in df.columns:
                            agg = df.groupby('Ad Group Name').agg({'Spend': 'sum', 'Sales': 'sum'}).reset_index()
                            agg['ROAS'] = (agg['Sales'] / agg['Spend']).replace([np.inf, -np.inf], 0).fillna(0)
                            eff_spend = agg[agg['ROAS'] >= 2.5]['Spend'].sum()
                            total = agg['Spend'].sum()
                            return (eff_spend / total * 100) if total > 0 else 0
                        return 0
                    
                    efficiency_current = calc_efficiency(df_curr)
                    if not df_prev.empty:
                        eff_prev = calc_efficiency(df_prev)
                        efficiency_delta = efficiency_current - eff_prev
                    

                    
                    # Top Growing Campaign
                    if not df_prev.empty and 'Campaign Name' in df_curr.columns:
                        camp_curr = df_curr.groupby('Campaign Name')['Sales'].sum()
                        camp_prev = df_prev.groupby('Campaign Name')['Sales'].sum()
                        camp_delta = camp_curr.subtract(camp_prev, fill_value=0)
                        if not camp_delta.empty and camp_delta.max() > 0:
                            top_campaign = camp_delta.idxmax()
                            top_campaign_delta = camp_delta.max()
        except Exception as e:
            import logging
            logging.warning(f"Home insight calculation error: {e}")
            st.error(f"Insight Error: {e}")
    
    # Build Row 1 insights
    arrow_up = "↑"
    arrow_down = "↓"
    
    # 1. ROAS Trend
    if roas_delta >= 0:
        insights.append({
            "title": f"ROAS {arrow_up} {abs(roas_delta):.1f}%",
            "subtitle": "vs prior 14 days",
            "icon_type": "success" if roas_delta > 3 else "info",
            "tooltip": f"ROAS (Return on Ad Spend) changed by {roas_delta:+.1f}% compared to the previous 14-day period. Higher is better."
        })
    else:
        insights.append({
            "title": f"ROAS {arrow_down} {abs(roas_delta):.1f}%",
            "subtitle": "vs prior 14 days",
            "icon_type": "warning",
            "tooltip": f"ROAS (Return on Ad Spend) changed by {roas_delta:.1f}% compared to the previous 14-day period. Consider reviewing campaigns."
        })
    
    # 2. Spend Efficiency Trend
    if efficiency_delta >= 0:
        insights.append({
            "title": f"Efficiency {arrow_up} {abs(efficiency_delta):.1f}%",
            "subtitle": f"Now {efficiency_current:.0f}% efficient",
            "icon_type": "success" if efficiency_delta > 3 else "info",
            "tooltip": f"Spend Efficiency measures % of spend going to ad groups with ROAS >= 2.5x. Currently {efficiency_current:.0f}% of spend is efficient."
        })
    else:
        insights.append({
            "title": f"Efficiency {arrow_down} {abs(efficiency_delta):.1f}%",
            "subtitle": f"Now {efficiency_current:.0f}% efficient",
            "icon_type": "warning",
            "tooltip": f"Spend Efficiency measures % of spend going to ad groups with ROAS >= 2.5x. Currently {efficiency_current:.0f}% of spend is efficient, down from prior period."
        })
    
    # 3. Top Growing Campaign
    if top_campaign != "—" and top_campaign_delta > 0:
        display_name = top_campaign[:18] + "..." if len(top_campaign) > 18 else top_campaign
        insights.append({
            "title": display_name,
            "subtitle": f"{arrow_up} {currency} {top_campaign_delta:,.0f} sales",
            "icon_type": "success",
            "tooltip": f"Campaign '{top_campaign}' showed the largest sales increase (+{currency}{top_campaign_delta:,.0f}) compared to the prior 14-day period."
        })
    else:
        insights.append({
            "title": "No Growth Leader",
            "subtitle": "All campaigns stable",
            "icon_type": "info",
            "tooltip": "No single campaign showed significant growth compared to the prior period. Performance is stable across campaigns."
        })
    
    # ========================================
    # ROW 2: DECISION METRICS (from get_recent_impact_summary)
    # ========================================
    impact_data = get_recent_impact_summary()
    decision_impact = impact_data.get('sales', 0) if impact_data else 0
    win_rate = impact_data.get('win_rate', 0) if impact_data else 0
    
    # 4. Win Rate (win_rate is a ratio 0-1, convert to percentage)
    win_rate_pct = win_rate * 100
    if win_rate_pct > 0:
        insights.append({
            "title": f"{win_rate_pct:.0f}% Win Rate",
            "subtitle": "actions beating baseline",
            "icon_type": "success" if win_rate_pct > 50 else "info",
            "tooltip": f"Win Rate measures the percentage of optimizer actions that resulted in positive impact. {win_rate_pct:.0f}% of your actions improved performance."
        })
    else:
        insights.append({
            "title": "0% Win Rate",
            "subtitle": "run optimizer to track",
            "icon_type": "note",
            "tooltip": "Win Rate measures the percentage of optimizer actions with positive impact. Run the optimizer to start tracking."
        })
    
    # 5. Quality Score (Decision Impact is already shown in hero tile, not duplicating)
    quality = impact_data.get('quality_score', 0) if impact_data else 0
    if quality > 0:
        insights.append({
            "title": f"+{quality:.0f} Quality",
            "subtitle": "net positive actions",
            "icon_type": "success",
            "tooltip": f"Quality Score = % of good actions minus % of bad actions. A score of +{quality:.0f} means your action mix is net positive."
        })
    elif quality < 0:
        insights.append({
            "title": f"{quality:.0f} Quality",
            "subtitle": "review action mix",
            "icon_type": "warning",
            "tooltip": f"Quality Score = % of good actions minus % of bad actions. A score of {quality:.0f} indicates more underperforming actions in the mix."
        })
    else:
        insights.append({
            "title": "Neutral Quality", 
            "subtitle": "balanced action mix",
            "icon_type": "info",
            "tooltip": "Quality Score = % of good actions minus % of bad actions. A neutral score means your action mix is balanced."
        })
    
    # ========================================
    # ========================================
    # RENDER KEY INSIGHTS CONTAINER
    # ========================================
    # Construct HTML for all insights
    cards_html = ""
    
    # Map icon type to class
    cls_map = {"success": "insight-positive", "warning": "insight-warning", "info": "insight-info", "note": "insight-info"}
    
    for i in range(6): # Ensure 6 slots even if empty
        if i < len(insights):
            insight = insights[i]
            cls_ = cls_map.get(insight.get("icon_type", "info"), "insight-info")
            # Icon symbol
            icon_char = "✓" if cls_ == "insight-positive" else "!" if cls_ == "insight-warning" else "i"
            tooltip = insight.get("tooltip", "")
            
            # Construct card HTML on single lines to prevent Markdown code block interpretation from indentation
            cards_html += f'<div class="{cls_} insight-card" title="{tooltip}" style="margin-bottom: 0;">'
            cards_html += f'<div style="display:flex; align-items:center;">'
            cards_html += f'<div class="insight-icon">{icon_char}</div>'
            cards_html += f'<div>'
            cards_html += f'<div style="font-weight:700; font-size:1.05rem; color:#f1f5f9;">{insight["title"]}</div>'
            cards_html += f'<div style="font-size:0.85rem; color:#94a3b8;">{insight["subtitle"]}</div>'
            cards_html += f'</div></div></div>'
        else:
            # Empty slot placeholder
            cards_html += '<div style="height: 1px;"></div>'

    # Render Container with Header and Grid
    st.markdown(f"""
    <div style="
        border: 1px solid rgba(148, 163, 184, 0.15); 
        border-radius: 12px; 
        overflow: hidden; 
        background: rgba(15, 23, 42, 0.4); 
        margin-top: 10px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    ">
        <div style="
            background: linear-gradient(90deg, rgba(30, 41, 59, 0.4) 0%, rgba(30, 41, 59, 0.2) 100%);
            padding: 14px 24px;
            border-bottom: 1px solid rgba(148, 163, 184, 0.15);
            display: flex;
            align-items: center;
        ">
            <span style="color: #F8FAFC; font-weight: 700; font-size: 1.1rem; letter-spacing: 0.02em;">KEY INSIGHTS</span>
        </div>
        <div style="
            padding: 24px; 
            display: grid; 
            grid-template-columns: repeat(3, 1fr); 
            gap: 20px;
        ">
            {cards_html}
        </div>
    </div>
    """, unsafe_allow_html=True)
