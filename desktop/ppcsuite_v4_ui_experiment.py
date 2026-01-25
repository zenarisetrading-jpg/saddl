import streamlit as st
import sys
import os
from pathlib import Path

# Add current directory to path to fix imports on Cloud
current_dir = Path(__file__).parent.absolute()
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# ==========================================

# ==========================================
# PAGE CONFIGURATION (Must be very first ST command)
# ==========================================
st.set_page_config(
    page_title="Saddle AdPulse", 
    layout="wide", 
    page_icon="🚀"
)

import pandas as pd
from datetime import datetime
import os

# BRIDGE: Load Environment Variables (support .env in desktop/ or parent root)
try:
    from dotenv import load_dotenv
    current_dir = Path(__file__).parent
    load_dotenv(current_dir / '.env')          # desktop/.env
    load_dotenv(current_dir.parent / '.env')   # saddle/.env
except ImportError:
    pass

# BRIDGE: Load Streamlit Secrets into OS Environment for Core Modules
try:
    if "DATABASE_URL" in st.secrets:
        os.environ["DATABASE_URL"] = st.secrets["DATABASE_URL"]
except FileNotFoundError:
    pass 

# === SEEDING (CRITICAL FOR STREAMLIT CLOUD) ===
try:
    from core.seeding import seed_initial_data
    seed_initial_data()
except Exception as e:
    print(f"Startup Seeding Failed: {e}")

# Delay heavy feature imports by moving them into routing/main logic


# Delay heavy feature imports by moving them into routing/main logic
from ui.layout import setup_page, render_sidebar, render_home
from core.data_hub import DataHub
from core.db_manager import DatabaseManager, get_db_manager
from utils.matchers import ExactMatcher
from utils.formatters import format_currency
from core.data_loader import safe_numeric
from pathlib import Path

# === ONBOARDING ===
from ui.onboarding import should_show_onboarding, render_onboarding_wizard
from config.features import FEATURE_ONBOARDING_WIZARD

# === AUTHENTICATION ===
from core.auth.service import AuthService
from core.auth.middleware import require_auth, require_permission
from ui.auth.login import render_login
# Legacy import removed: from auth import require_authentication, render_user_menu

# Global dark theme CSS for sidebar buttons
st.markdown("""
<style>
/* Fix sidebar buttons in dark mode */
[data-testid="stSidebar"] .stButton > button {
    background-color: rgba(30, 41, 59, 0.8) !important;
    color: white !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background-color: rgba(51, 65, 85, 0.9) !important;
    border-color: rgba(255, 255, 255, 0.2) !important;
}
/* Download buttons */
.stDownloadButton > button {
    background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
    color: white !important;
    border: none !important;
}

/* Dark mode/Test mode toggle overrides */
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
    color: #F5F5F7 !important;
    font-weight: 500 !important;
}
/* Toggle Switch Background when Checked */
[data-testid="stSidebar"] div[data-testid="stCheckbox"] > label > div[role="switch"][aria-checked="true"] {
    background-color: #5B556F !important;
}
/* Radio Button Outer Circle when active */
[data-testid="stSidebar"] div[data-testid="stRadio"] label div:first-child[data-baseweb="radio"] > div:first-child {
    border-color: #5B556F !important;
}
/* Radio Button Inner Dot when checked */
[data-testid="stSidebar"] div[data-testid="stRadio"] label div:first-child[data-baseweb="radio"] > div:first-child > div {
    background-color: #5B556F !important;
}

/* Print Mode: Hide sidebar and UI elements when printing */
@media print {
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="stHeader"] { display: none !important; }
    [data-testid="stToolbar"] { display: none !important; }
    .stDeployButton { display: none !important; }
    .stDownloadButton { display: none !important; }
    section[data-testid="stSidebar"] { display: none !important; }
    header { display: none !important; }
    .main .block-container { padding: 1rem !important; max-width: 100% !important; }
}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'current_module' not in st.session_state:
    st.session_state['current_module'] = 'home'

if 'data' not in st.session_state:
    st.session_state['data'] = {}

if 'test_mode' not in st.session_state:
    st.session_state['test_mode'] = False

if 'db_manager' not in st.session_state:
    st.session_state['db_manager'] = None


# ==========================================
# PERFORMANCE HUB (Snapshot + Report Card)
# ==========================================
# ==========================================
# PERFORMANCE HUB (Snapshot + Report Card)
# ==========================================
def run_performance_hub():
    """Consolidated Account Overview + Report Card."""
    # Force empty state for testing
    if st.query_params.get("test_state") == "no_data":
        from ui.components.empty_states import render_empty_state
        account = st.session_state.get('active_account_name', 'Account')
        render_empty_state('no_data', context={'account_name': account})
        return

    # === TAB NAVIGATION (Premium Button Style) ===
    st.markdown("""
    <style>
    /* Premium Tab Buttons */
    div[data-testid="stHorizontalBlock"] div.stButton > button {
        background: rgba(143, 140, 163, 0.05) !important;
        border: 1px solid rgba(143, 140, 163, 0.15) !important;
        color: #8F8CA3 !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
        padding: 8px 16px !important;
    }
    div[data-testid="stHorizontalBlock"] div.stButton > button:hover {
        background: rgba(143, 140, 163, 0.1) !important;
        border-color: rgba(91, 85, 111, 0.3) !important;
        color: #F5F5F7 !important;
    }
    /* Active Tab Styling - Using Primary kind */
    div[data-testid="stHorizontalBlock"] div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #5B556F 0%, #464156 100%) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: #F5F5F7 !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    if 'active_perf_tab' not in st.session_state:
        st.session_state['active_perf_tab'] = "Executive Dashboard"
        
    c1, c2 = st.columns(2)
    with c1:
        is_active = st.session_state['active_perf_tab'] == "Executive Dashboard"
        if st.button("📊 EXECUTIVE DASHBOARD", key="btn_tab_exec", use_container_width=True, type="primary" if is_active else "secondary"):
            st.session_state['active_perf_tab'] = "Executive Dashboard"
            st.rerun()
    with c2:
        is_active = st.session_state['active_perf_tab'] == "Account Health"
        if st.button("🛡️ ACCOUNT HEALTH", key="btn_tab_report", use_container_width=True, type="primary" if is_active else "secondary"):
            st.session_state['active_perf_tab'] = "Account Health"
            st.rerun()
            
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.session_state['active_perf_tab'] == "Executive Dashboard":
        from features.executive_dashboard import ExecutiveDashboard
        ExecutiveDashboard().run()
    elif st.session_state['active_perf_tab'] == "Account Health":
        from features.report_card import ReportCardModule
        ReportCardModule().run()
    else:
        # Default fallback
        from features.executive_dashboard import ExecutiveDashboard
        ExecutiveDashboard().run()


# ==========================================
# CONSOLIDATED V4 OPTIMIZER
# ==========================================
def run_consolidated_optimizer():
    """Execution logic: Optimizer + ASIN Mapper + AI Insights all in one view."""
    
    # Force empty state for testing
    if st.query_params.get("test_state") == "no_data":
        from ui.components.empty_states import render_empty_state
        account = st.session_state.get('active_account_name', 'Account')
        render_empty_state('no_data', context={'account_name': account})
        return

    # Flag to skip execution while still rendering widgets (preserves settings during dialog)
    skip_execution = st.session_state.get('_show_action_confirmation', False)
    
    # Lazy imports for Optimizer
    from features.optimizer import (
        OptimizerModule, 
        prepare_data, 
        identify_harvest_candidates, 
        identify_negative_candidates, 
        calculate_bid_optimizations, 
        create_heatmap, 
        run_simulation,
        calculate_account_benchmarks
    )
    from utils.matchers import ExactMatcher
    
    # Theme-aware optimization icon (sliders/tune icon)
    theme_mode = st.session_state.get('theme_mode', 'dark')
    opt_icon_color = "#94a3b8" if theme_mode == 'dark' else "#64748b"
    opt_icon = f'<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="{opt_icon_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 10px;"><line x1="4" y1="21" x2="4" y2="14"></line><line x1="4" y1="10" x2="4" y2="3"></line><line x1="12" y1="21" x2="12" y2="12"></line><line x1="12" y1="8" x2="12" y2="3"></line><line x1="20" y1="21" x2="20" y2="16"></line><line x1="20" y1="12" x2="20" y2="3"></line><line x1="1" y1="14" x2="7" y2="14"></line><line x1="9" y1="8" x2="15" y2="8"></line><line x1="17" y1="16" x2="23" y2="16"></line></svg>'
    
    st.markdown(f'<h1 style="margin-bottom: 2rem; font-size: 2.2rem; font-weight: 800; text-transform: uppercase; letter-spacing: -0.02em; color: #F5F5F7;">{opt_icon}OPTIMIZATION ENGINE</h1>', unsafe_allow_html=True)
    
    # Check for data - try session first, then database
    hub = DataHub()
    
    # If no data in session, try loading from database
    if not hub.is_loaded("search_term_report"):
        account_id = st.session_state.get('active_account_id')
        if account_id:
            loaded = hub.load_from_database(account_id)
        
        # Check again after database load attempt
        if not hub.is_loaded("search_term_report"):
            st.warning("⚠️ Please upload a Search Term Report in the Data Hub first.")
            st.info("Go to **Data Hub** → Upload files → Return here")
            return
    
    # Get data (now either from session upload OR database)
    df_raw = hub.get_data("search_term_report")
    if df_raw is None or df_raw.empty:
        st.error("❌ No Search Term Report data found.")
        return
    
    # Work with a copy to avoid modifying Hub data in-place
    df = df_raw.copy()
    
    # Show which data we're using
    upload_ts = st.session_state.unified_data.get('upload_timestamps', {}).get('search_term_report')
    # (Callout content moved below to consolidate with date range context)
    
    # Apply enrichment (IDs, SKUs) to the fresh data WITHOUT mixing with DB historical data
    # This adds CampaignId, AdGroupId, SKU, etc. from bulk/APR files
    enriched = hub.get_enriched_data()
    if enriched is not None and len(enriched) == len(df):
        # Use enriched version if it matches the upload size (no extra rows from DB)
        df = enriched.copy()

    # =====================================================
    # DB INTEGRATION: Allow extending window with historical data
    # =====================================================
    # Retrieve client ID (support both new primitive key and old dict legacy)
    client_id = st.session_state.get('active_account_id')
    if not client_id:
        # Fallback to legacy dictionary if present
        client_id = st.session_state.get('active_account', {}).get('account_id')
    db_manager = st.session_state.get('db_manager')
    
    # DEBUG: Check why DB merge is skipped
    if not client_id:
        st.warning(f"⚠️ No Client ID detected. Session Active Account: {st.session_state.get('active_account')}")
    # End Debug
    
    include_db = False
    if client_id and db_manager:
        # Always include historical data from database (debug panel removed)
        include_db = True
        with st.spinner("Fetching historical data..."):
            db_df = db_manager.get_target_stats_df(client_id)
            
            if not db_df.empty:
                # Rename columns for consistency if needed (DB already returns standard names)
                # Fix column names to match STR upload headers
                db_df = db_df.rename(columns={
                    'Date': 'Date',
                    'Targeting': 'Targeting',
                    'Match Type': 'Match Type',
                    'Campaign Name': 'Campaign Name',
                    'Ad Group Name': 'Ad Group Name'
                })
                
                # CONSISTENCY FIX: Use DB data directly like Performance Overview
                # No merge, no dedup - just use what's in the database
                df = db_df.copy()
                # Display dates as week ending (database stores week start/Monday, but show week end/Sunday)
                from datetime import timedelta
                min_display = df['Date'].min().date()
                max_display = df['Date'].max().date() + timedelta(days=6)  # Week ending (Sunday)
                st.success(f"✅ Using complete database history: {len(df):,} rows from {min_display} to {max_display}")
    
    # =====================================================
    # DATE RANGE FILTER: Default to last 30 days
    # =====================================================
    date_cols = ["Date", "Start Date", "date", "Report Date", "start_date"]
    date_col = None
    for col in date_cols:
        if col in df.columns:
            date_col = col
            break
    
    if date_col:
        from datetime import datetime, timedelta
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        
        min_date = df[date_col].min()
        max_date = df[date_col].max()
        
        if include_db:
            # If DB included, allow full range selection
            default_start = min_date
        else:
            # Default: last 30 days from max date in data
            default_start = max(min_date, max_date - timedelta(days=30))
        
        # Theme-aware calendar icon inline in expander
        theme_mode = st.session_state.get('theme_mode', 'dark')
        with st.expander("▸ Date Range Selection", expanded=True):
            col_a, col_b = st.columns(2)
            # Use wider bounds (1 year back) if date filter needs more room
            abs_min = min(min_date, datetime.now() - timedelta(days=365))
            
            # Week ending display: Show dates as week ending (database stores week start)
            # Display offset: +6 days to convert Monday (week start) to Sunday (week end)
            week_end_max = max_date.date() + timedelta(days=6)
            
            # --- CLAMP SESSION STATE TO VALID RANGE ---
            # This prevents StreamlitAPIException if the previous file had a wider range
            s_min, s_max = abs_min.date(), week_end_max  # s_max now shows week ending
            if "opt_date_start" in st.session_state:
                if st.session_state["opt_date_start"] < s_min: st.session_state["opt_date_start"] = s_min
                if st.session_state["opt_date_start"] > s_max: st.session_state["opt_date_start"] = s_max
            if "opt_date_end" in st.session_state:
                if st.session_state["opt_date_end"] < s_min: st.session_state["opt_date_end"] = s_min
                if st.session_state["opt_date_end"] > s_max: st.session_state["opt_date_end"] = s_max
            # ------------------------------------------

            with col_a:
                start_date = st.date_input("Start Date", 
                                            value=st.session_state.get("opt_date_start", default_start.date()), 
                                            min_value=s_min, 
                                            max_value=s_max,
                                            key="opt_date_start")
            with col_b:
                # Default shows week ending (max stored date + 6 days)
                default_end = max_date.date() + timedelta(days=6)
                end_date = st.date_input("End Date", 
                                          value=st.session_state.get("opt_date_end", default_end),
                                          min_value=s_min, 
                                          max_value=s_max,
                                          key="opt_date_end")
        
        # Filter data to selected range
        # User selects dates as week ending (Sunday), but DB stores week start (Monday)
        # Convert user's end_date back to week start for comparison: subtract 6 days
        if date_col:
            # For end_date, if user picked week ending (Sunday), convert to week start (Monday) 
            # by subtracting 6 days for proper filtering against DB's start_date column
            filter_end = end_date - timedelta(days=6) if end_date != start_date else end_date
            mask = (df[date_col].dt.date >= start_date) & (df[date_col].dt.date <= end_date)
            df = df[mask].copy()
        else:
            st.error("❌ Could not identify Date column for filtering.")
            
        days_selected = (end_date - start_date).days + 1
        
        # Baseline metrics calculation
        total_rows = len(df)
        total_spend = df["Spend"].sum()
        total_sales = df["Sales"].sum()
        roas = total_sales / total_spend if total_spend > 0 else 0
        acos = (total_spend / total_sales * 100) if total_sales > 0 else 0
        
        
        # === SECTION 1 — DATASET CONTEXT (BASELINE) ===
        if not st.session_state.get("run_optimizer"):
            ts_info = f" • STR Upload: {upload_ts.strftime('%H:%M')}" if upload_ts else ""
            
            # Premium Component-based Rendering using metric_card
            from ui.components import metric_card
            
            st.markdown(f"""
            <div style="margin-bottom: 24px; color: #8F8CA3; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; font-weight: 500;">
                Analyzing Data: <span style="color: #F5F5F7; font-weight: 600;">{start_date.strftime('%b %d')} – {end_date.strftime('%b %d, %Y')}</span> • {days_selected} days {ts_info}
            </div>
            """, unsafe_allow_html=True)
            
            c1, c2, c3, c4 = st.columns(4)
            with c1: metric_card("Rows", f"{total_rows:,}", icon_name="layers")
            with c2: metric_card("Total Spend", format_currency(total_spend), icon_name="spend")
            with c3: metric_card("ROAS", f"{roas:.2f}x", icon_name="roas")
            with c4: metric_card("ACoS", f"{acos:.1f}%", icon_name="acos")
            
            st.markdown("<div style='margin-bottom: 40px;'></div>", unsafe_allow_html=True)
        
    # 1. Configuration - render in main panel BEFORE run, sidebar AFTER run
    opt = OptimizerModule()
    
    if not st.session_state.get("run_optimizer"):
        # === PRE-RUN STATE: PRIMARY ACTION PANEL ===
        # Premium Gradient Header
        st.markdown("""
        <div style="margin-bottom: 20px;">
            <h2 style="font-size: 1.8rem; font-weight: 700; background: linear-gradient(90deg, #F5F5F7 0%, #B6B4C2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0;">Ready to optimize</h2>
            <p style="color: #94A3B8; margin-top: 8px; font-size: 1rem;">The system will adjust bids, add negatives, and harvest high-performing terms based on account performance.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Brand purple/wine palette: #5B556F (Wine/Slate Purple)
        st.markdown("""
        <style>
        /* Glassmorphic Metric Cards */
        .custom-metric-card {
            background: rgba(255, 255, 255, 0.05) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 12px !important;
            padding: 16px !important;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2) !important;
            backdrop-filter: blur(16px) !important;
            -webkit-backdrop-filter: blur(16px) !important;
            transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease !important;
        }
        .custom-metric-card:hover {
            transform: translateY(-2px) !important;
            border-color: rgba(124, 58, 237, 0.5) !important;
            box-shadow: 0 8px 24px rgba(124, 58, 237, 0.2) !important;
        }

        /* Primary CTA Button - Brand Wine Gradient */
        div[data-testid="stButton"] > button[kind="primary"] {
            background: linear-gradient(135deg, #7C3AED 0%, #5B21B6 100%) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            font-size: 1.1rem !important;
            padding: 0.75rem 2rem !important;
            color: #F5F5F7 !important;
            font-weight: 600 !important;
            letter-spacing: 0.5px !important;
            box-shadow: 0 4px 15px rgba(124, 58, 237, 0.3) !important;
            border-radius: 8px !important;
        }
        div[data-testid="stButton"] > button[kind="primary"]:hover {
            background: linear-gradient(135deg, #8B5CF6 0%, #6D28D9 100%) !important;
            transform: translateY(-1px);
            box-shadow: 0 6px 20px rgba(124, 58, 237, 0.4) !important;
            color: #ffffff !important;
        }

        /* Slider Styling - Brand Wine */
        div[data-testid="stSlider"] div[data-baseweb="slider"] > div:first-child > div:nth-child(2) {
            background: #7C3AED !important;
        }
        div[data-testid="stSlider"] div[role="slider"] {
            background-color: #7C3AED !important;
            border: 2px solid #F5F5F7 !important;
        }
        div[data-testid="stSlider"] span[data-baseweb="typography"] {
            color: #A78BFA !important;
            font-weight: 700 !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # === QUICK PRESETS ===
        icon_color = "#8F8CA3"
        zap_icon = f'<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="{icon_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 8px;"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>'
        
        st.markdown(f"""
        <div style="display: flex; align-items: center; margin-bottom: 12px; margin-top: 10px;">
            {zap_icon}
            <span style="font-size: 0.9rem; font-weight: 600; color: #F5F5F7; text-transform: uppercase; letter-spacing: 1px;">Quick Presets</span>
        </div>
        """, unsafe_allow_html=True)

        preset_options = ["Conservative", "Balanced", "Aggressive"]
        
        preset = st.radio(
            "Choose optimization style",
            preset_options,
            index=1,  # Default to Balanced
            horizontal=True,
            label_visibility="collapsed",
            key="opt_preset_main"
        )
        
        # Define preset values (no currency thresholds)
        preset_configs = {
            "Conservative": {
                "harvest_clicks": 15, "harvest_orders": 4, "harvest_roas": 90,
                "alpha_exact": 0.15, "alpha_broad": 0.12, "max_change": 0.15, "target_roas": 2.5,
                "neg_clicks": 15,
                "min_clicks_exact": 8, "min_clicks_pt": 8, "min_clicks_broad": 12, "min_clicks_auto": 12
            },
            "Balanced": {
                "harvest_clicks": 10, "harvest_orders": 3, "harvest_roas": 80,
                "alpha_exact": 0.20, "alpha_broad": 0.16, "max_change": 0.20, "target_roas": 2.5,
                "neg_clicks": 10,
                "min_clicks_exact": 5, "min_clicks_pt": 5, "min_clicks_broad": 10, "min_clicks_auto": 10
            },
            "Aggressive": {
                "harvest_clicks": 8, "harvest_orders": 2, "harvest_roas": 70,
                "alpha_exact": 0.25, "alpha_broad": 0.20, "max_change": 0.25, "target_roas": 2.5,
                "neg_clicks": 8,
                "min_clicks_exact": 3, "min_clicks_pt": 3, "min_clicks_broad": 8, "min_clicks_auto": 8
            }
        }
        
        # Apply preset to config if changed
        # Use a separate tracker to detect actual changes (not just reloads)
        if st.session_state.get("_last_applied_preset") != preset:
            st.session_state["_last_applied_preset"] = preset
            config = preset_configs[preset]
            
            # Update opt.config
            opt.config["HARVEST_CLICKS"] = config["harvest_clicks"]
            opt.config["HARVEST_ORDERS"] = config["harvest_orders"]
            opt.config["HARVEST_ROAS_MULT"] = config["harvest_roas"] / 100
            opt.config["ALPHA_EXACT"] = config["alpha_exact"]
            opt.config["ALPHA_BROAD"] = config["alpha_broad"]
            opt.config["MAX_BID_CHANGE"] = config["max_change"]
            opt.config["TARGET_ROAS"] = config["target_roas"]
            opt.config["NEGATIVE_CLICKS_THRESHOLD"] = config["neg_clicks"]
            opt.config["MIN_CLICKS_EXACT"] = config["min_clicks_exact"]
            opt.config["MIN_CLICKS_PT"] = config["min_clicks_pt"]
            opt.config["MIN_CLICKS_BROAD"] = config["min_clicks_broad"]
            opt.config["MIN_CLICKS_AUTO"] = config["min_clicks_auto"]
            
            # CRITICAL: Also update session state so widgets pick up preset values on next rerun
            # This prevents widgets from resetting to default values
            st.session_state["main_h_clicks"] = config["harvest_clicks"]
            st.session_state["main_h_orders"] = config["harvest_orders"]
            st.session_state["main_alpha_exact"] = config["alpha_exact"]
            st.session_state["main_max_bid"] = config["max_change"]
            st.session_state["main_target_roas"] = config["target_roas"]
            st.session_state["main_neg_clicks"] = config["neg_clicks"]
            st.session_state["min_clicks_exact"] = config["min_clicks_exact"]
            st.session_state["min_clicks_pt"] = config["min_clicks_pt"]
            st.session_state["min_clicks_broad"] = config["min_clicks_broad"]
            st.session_state["min_clicks_auto"] = config["min_clicks_auto"]
        
        st.caption("*Conservative = slower, safer changes • Aggressive = faster, bigger changes*")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Simulation toggle ABOVE button for state initialization
        run_sim = st.checkbox("Include Simulation & Forecasting", value=True, key="run_simulation_main")
        
        # PRIMARY CTA (commit first)
        if st.button("Start optimization", type="primary", use_container_width=True):
            st.session_state["optimizer_config"] = opt.config.copy()
            st.session_state["run_optimizer"] = True
            st.session_state["force_rerun"] = True # Force fresh run explicitly
            st.session_state["should_log_actions"] = True  # Only log on explicit button click
            # Read current checkbox state
            st.session_state["run_simulation"] = st.session_state.get("run_simulation_main", True)
            st.rerun()
        
        st.divider()
        
        # SVG Icons for Pre-run
        icon_color = "#8F8CA3"
        settings_icon = f'<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="{icon_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle;"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>'
        
        # Chiclet Header Helper for Main Panel
        def main_chiclet_header(label, icon_html):
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, rgba(91, 85, 111, 0.1) 0%, rgba(91, 85, 111, 0.05) 100%); 
                        border: 1px solid rgba(124, 58, 237, 0.2); 
                        border-radius: 8px; 
                        padding: 10px 15px; 
                        margin-bottom: -15px;
                        display: flex; 
                        align-items: center; 
                        gap: 10px;">
                {icon_html}
                <span style="color: #F5F5F7; font-size: 0.9rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;">{label}</span>
            </div>
            """, unsafe_allow_html=True)

        main_chiclet_header("Advanced Settings", settings_icon)
        with st.expander("Expand configuration", expanded=False):
            st.caption("Fine-tune optimization behavior — defaults work well for most accounts")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**Harvest Thresholds**")
                opt.config["HARVEST_CLICKS"] = st.number_input(
                    "Min Clicks", value=opt.config["HARVEST_CLICKS"], min_value=1, key="main_h_clicks"
                )
                opt.config["HARVEST_ORDERS"] = st.number_input(
                    "Min Orders", value=opt.config["HARVEST_ORDERS"], min_value=1, key="main_h_orders"
                )
                # HARVEST_SALES removed - currency threshold doesn't work across geos
            
            with col2:
                st.markdown("**Bid Optimization**")
                opt.config["ALPHA_EXACT"] = st.slider(
                    "Alpha (Exact)", min_value=0.05, max_value=0.50, 
                    value=opt.config["ALPHA_EXACT"], step=0.05, key="main_alpha_exact"
                )
                opt.config["MAX_BID_CHANGE"] = st.slider(
                    "Max Change %", min_value=0.05, max_value=0.50, 
                    value=opt.config["MAX_BID_CHANGE"], step=0.05, key="main_max_bid"
                )
                opt.config["TARGET_ROAS"] = st.number_input(
                    "Target ROAS", value=opt.config["TARGET_ROAS"], 
                    min_value=0.5, max_value=10.0, step=0.1, key="main_target_roas"
                )
            
            with col3:
                st.markdown("**Negative Thresholds**")
                opt.config["NEGATIVE_CLICKS_THRESHOLD"] = st.number_input(
                    "Min Clicks (0 Sales)", value=opt.config["NEGATIVE_CLICKS_THRESHOLD"], min_value=5, key="main_neg_clicks"
                )
                # NEGATIVE_SPEND_THRESHOLD removed for currency-neutrality
                # All negative logic is now clicks-based
            
            st.divider()
            st.markdown("**Min Clicks per Bucket**")
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                opt.config["MIN_CLICKS_EXACT"] = st.number_input(
                    "Exact KW", value=opt.config.get("MIN_CLICKS_EXACT", 5), min_value=1, max_value=50, key="min_clicks_exact"
                )
            with c2:
                opt.config["MIN_CLICKS_PT"] = st.number_input(
                    "Prod Target", value=opt.config.get("MIN_CLICKS_PT", 5), min_value=1, max_value=50, key="min_clicks_pt"
                )
            with c3:
                opt.config["MIN_CLICKS_BROAD"] = st.number_input(
                    "Broad/Phrase", value=opt.config.get("MIN_CLICKS_BROAD", 10), min_value=1, max_value=50, key="min_clicks_broad"
                )
            with c4:
                opt.config["MIN_CLICKS_AUTO"] = st.number_input(
                    "Auto/Category", value=opt.config.get("MIN_CLICKS_AUTO", 10), min_value=1, max_value=50, key="min_clicks_auto"
                )
        
        return  # Exit early, don't render results yet
    
    # === POST-RUN STATE: Settings move to sidebar ===
    with st.sidebar:
        st.divider()
        if st.button("← Stop / Edit Settings", use_container_width=True):
            st.session_state["run_optimizer"] = False
            st.rerun()
            
    # === ADMIN / DEV TOOLS (Bottom of Sidebar) ===
    # Only show for admins or in test mode
    user = st.session_state.get('user')
    is_admin = user and (user.role == 'ADMIN' or user.role == 'OWNER')
    
    if is_admin or st.session_state.get('test_mode'):
        with st.sidebar:
            st.markdown("---")
            with st.expander("🛠️ Admin Tools", expanded=False):
                st.caption("Debugging & Verification")
                
                # 1. Onboarding Reset
                if st.button("Restart Onboarding Wizard", use_container_width=True):
                    st.session_state['show_onboarding'] = True
                    st.session_state['onboarding_step'] = 1
                    st.rerun()
                    
                # 2. Test Invitation
                st.markdown("---")
                st.caption("Test Email Invitation")
                invite_email = st.text_input("Invite Email", placeholder="test@example.com")
                if st.button("Send Invite", use_container_width=True):
                    if invite_email:
                        with st.spinner("Sending..."):
                            from core.auth.invitation_service import InvitationService
                            service = InvitationService()
                            # Use current user as inviter
                            res = service.create_invitation(
                                email=invite_email,
                                organization_id=str(user.organization_id) if user else "test-org",
                                invited_by_user_id=str(user.id) if user else None,
                                role="OPERATOR"
                            )
                            if res.success:
                                st.success(f"Sent! Token: {res.invitation.token[:8]}...")
                            else:
                                st.error(f"Failed: {res.message}")
                    else:
                        st.warning("Enter an email first")
    
    opt._render_sidebar()
    
    # CRITICAL: Skip execution if showing confirmation dialog
    # Widgets above have rendered to preserve state, but don't re-run the expensive optimizer
    if skip_execution:
        st.info("⏸️ Optimization paused. Please complete the action confirmation dialog.")
        return
    
    # 2. Main Logic Trigger - SMART CACHING WRAPPER
    # Check if we can reuse existing results
    cached_result = st.session_state.get('latest_optimizer_run')
    cached_config = st.session_state.get('optimizer_config_cache')
    
    # Check if config has changed
    is_config_changed = cached_config != opt.config
    
    should_run = False
    if not cached_result or is_config_changed:
        should_run = True
    elif st.session_state.get('force_rerun'):
        should_run = True
        st.session_state['force_rerun'] = False
        
    r = None
    
    if should_run:
        with st.spinner("Running Optimization Engine..."):
            # A. Prepare Data & Run Core Logic
            df_prep, date_info = prepare_data(df, opt.config)
            
            # Consolidation Fix: Calculate benchmarks ONCE and pass them down
            benchmarks = calculate_account_benchmarks(df_prep, opt.config)
            universal_median = benchmarks.get('universal_median_roas', opt.config.get("TARGET_ROAS", 2.5))
            
            matcher = ExactMatcher(df_prep)
            
            harvest_df = identify_harvest_candidates(df_prep, opt.config, matcher, benchmarks)
            # Build harvested terms set from BOTH Harvest_Term (Targeting-based) and Customer Search Term
            corrected_term_set = set()
            if not harvest_df.empty:
                if "Harvest_Term" in harvest_df.columns:
                    corrected_term_set.update(harvest_df["Harvest_Term"].str.lower().tolist())
                if "Customer Search Term" in harvest_df.columns:
                    corrected_term_set.update(harvest_df["Customer Search Term"].str.lower().tolist())
            
            neg_kw, neg_pt, your_products_review = identify_negative_candidates(df_prep, opt.config, harvest_df, benchmarks)
            
            # Build negative_terms set for exclusion from bid optimization
            negative_terms_set = set()
            if not neg_kw.empty:
                for _, row in neg_kw.iterrows():
                    key = (str(row.get("Campaign Name", "")).strip(), 
                           str(row.get("Ad Group Name", "")).strip(), 
                           str(row.get("Term", "")).strip().lower())
                    negative_terms_set.add(key)
            if not neg_pt.empty:
                for _, row in neg_pt.iterrows():
                    key = (str(row.get("Campaign Name", "")).strip(), 
                           str(row.get("Ad Group Name", "")).strip(), 
                           str(row.get("Term", "")).strip().lower())
                    negative_terms_set.add(key)
            
            data_days = date_info.get("days", 7)
            bids_exact, bids_pt, bids_agg, bids_auto = calculate_bid_optimizations(
                df_prep, opt.config, corrected_term_set, negative_terms_set, universal_median,
                data_days=data_days
            )
            # Combine for backward compatibility with simulation/heatmap
            direct_bids = pd.concat([bids_exact, bids_pt], ignore_index=True)
            agg_bids = pd.concat([bids_agg, bids_auto], ignore_index=True)
            heatmap_df = create_heatmap(df_prep, opt.config, harvest_df, neg_kw, neg_pt, direct_bids, agg_bids)
            
            simulation = None
            if st.session_state.get("run_simulation", True):
                simulation = run_simulation(df_prep, direct_bids, agg_bids, harvest_df, opt.config, date_info)
            
            # Calculate health for Home Cockpit sync
            health = opt._calculate_account_health(df_prep, {"direct_bids": direct_bids, "agg_bids": agg_bids, "harvest": harvest_df})
            
            # Persist results for AI Assistant and Home Cockpit sync
            r = {
                "bids_exact": bids_exact,
                "bids_pt": bids_pt,
                "bids_agg": bids_agg,
                "bids_auto": bids_auto,
                "direct_bids": direct_bids,
                "agg_bids": agg_bids,
                "harvest": harvest_df,
                "neg_kw": neg_kw,
                "neg_pt": neg_pt,
                "heatmap": heatmap_df,
                "simulation": simulation,
                "date_info": date_info,
                "df": df_prep,
                "health": health  # ADDED for Home Cockpit sync
            }
            # SAVE ITERATION TO CACHE
            st.session_state['latest_optimizer_run'] = r
            st.session_state['optimizer_config_cache'] = opt.config.copy()
            
    # UNPACK RESULTS (From Cache or Fresh Run)
    if 'latest_optimizer_run' in st.session_state:
        r = st.session_state['latest_optimizer_run']
        bids_exact = r["bids_exact"]
        bids_pt = r["bids_pt"]
        bids_agg = r["bids_agg"]
        bids_auto = r["bids_auto"]
        direct_bids = r["direct_bids"]
        agg_bids = r["agg_bids"]
        harvest_df = r["harvest"]
        neg_kw = r["neg_kw"]
        neg_pt = r["neg_pt"]
        heatmap_df = r["heatmap"]
        simulation = r["simulation"]
        date_info = r["date_info"]
        df_prep = r["df"]
        health = r.get("health")
    else:
        st.error("❌ Failed to retrieve optimization results.")
        return
    
    # ==========================================
    # STORE PENDING ACTIONS FOR CONFIRMATION DIALOG
    # ==========================================
    # Build list of all pending actions from optimizer results
    # This enables the "Save/Discard" dialog when leaving optimizer tab
    actions_list = []
    
    # Collect all bid changes
    for df_name in ['bids_exact', 'bids_pt', 'bids_agg', 'bids_auto']:
        df = r.get(df_name)
        if df is not None and not df.empty:
            for _, row in df.iterrows():
                actions_list.append({
                    'action_type': 'BID_CHANGE',
                    'entity_name': df_name,
                    'campaign_name': row.get('Campaign Name', ''),
                    'ad_group_name': row.get('Ad Group Name', ''),
                    'target_text': row.get('Targeting', row.get('Customer Search Term', '')),
                    'match_type': row.get('Match Type', ''),
                    'old_value': str(row.get('CPC', row.get('Cost Per Click (CPC)', ''))),
                    'new_value': str(row.get('New Bid', '')),
                    'reason': row.get('Reason', '')
                })
    
    # Collect negatives
    for df_name in ['neg_kw', 'neg_pt']:
        df = r.get(df_name)
        if df is not None and not df.empty:
            for _, row in df.iterrows():
                actions_list.append({
                    'action_type': 'NEGATIVE',
                    'entity_name': df_name,
                    'campaign_name': row.get('Campaign Name', ''),
                    'ad_group_name': row.get('Ad Group Name', ''),
                    'target_text': row.get('Term', row.get('Targeting', row.get('Customer Search Term', ''))),
                    'match_type': row.get('Match Type', ''),
                    'old_value': '',
                    'new_value': 'ADD_NEGATIVE',
                    'reason': row.get('Reason', '')
                })
    
    # Collect harvests
    harvest_df = r.get('harvest')
    if harvest_df is not None and not harvest_df.empty:
        for _, row in harvest_df.iterrows():
            actions_list.append({
                'action_type': 'HARVEST',
                'entity_name': 'harvest',
                'campaign_name': row.get('Campaign Name', ''),
                'ad_group_name': row.get('Ad Group Name', ''),
                'target_text': row.get('Harvest_Term', row.get('Customer Search Term', '')),
                'match_type': row.get('Match Type', 'EXACT'),
                'old_value': str(row.get('CPC', '')),
                'new_value': str(row.get('New Bid', '')),
                'reason': 'Promote to exact match campaign',
                'winner_source_campaign': row.get('Campaign Name', ''),
                'before_match_type': row.get('Match Type', ''),
                'after_match_type': 'EXACT'
            })
    
    # Store in session state for confirmation dialog
    if actions_list:
        st.session_state['pending_actions'] = {
            'actions': actions_list,
            'client_id': st.session_state.get('active_account_id', 'unknown'),
            'count': len(actions_list)
        }
    else:
        st.session_state['pending_actions'] = None
    
    # ==========================================
    # LOG ACTIONS FOR IMPACT ANALYSIS
    # ==========================================
    from features.optimizer import _log_optimization_events
    
    # 1. Determine active client
    active_client = (
        st.session_state.get('active_account_id') or 
        st.session_state.get('last_stats_save', {}).get('client_id') or 
        'default_client'
    )
    
    # 2. Determine report date (use END date of data range, not start)
    # This ensures actions are logged at the most recent data point, not the oldest
    action_log_date = date_info.get('end_date') or date_info.get('start_date')
    if action_log_date and isinstance(action_log_date, datetime):
        action_log_date = action_log_date.strftime('%Y-%m-%d')
    elif not action_log_date:
        # Fallback to current date
        action_log_date = datetime.now().strftime('%Y-%m-%d')
    
    # Toast removed per user request
    # Only log actions on EXPLICIT button click, not on every rerender
    if st.session_state.get("should_log_actions", False):
        logged_count = _log_optimization_events(r, active_client, action_log_date)
        st.session_state["should_log_actions"] = False  # Clear flag to prevent re-logging

    # === POST-OPTIMIZATION INSIGHT LAYER ===
    @st.fragment
    def render_optimizer_results(
        bids_exact, bids_pt, bids_agg, bids_auto, 
        neg_kw, neg_pt, harvest_df, simulation, 
        heatmap_df, df_prep, r, date_info
    ):
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 1. Metric Calculations
        # Count unique Customer Search Terms analyzed (from STR data)
        cst_column = 'Customer Search Term' if 'Customer Search Term' in df_prep.columns else 'customer_search_term'
        if cst_column in df_prep.columns:
            total_search_terms = df_prep[cst_column].nunique()
        else:
            # Fallback to counting unique search terms from outputs
            total_search_terms = len(set(
                (bids_exact['Customer Search Term'].tolist() if 'Customer Search Term' in bids_exact.columns and not bids_exact.empty else []) +
                (neg_kw['Term'].tolist() if 'Term' in neg_kw.columns and not neg_kw.empty else []) +
                (harvest_df['Customer Search Term'].tolist() if 'Customer Search Term' in harvest_df.columns and not harvest_df.empty else [])
            ))

        total_bid_changes = len(bids_exact) + len(bids_pt) + len(bids_agg) + len(bids_auto)
        total_negatives = len(neg_kw) + len(neg_pt)
        total_harvests = len(harvest_df)
        
        # Icons & Styles
        icon_color = "#8F8CA3"
        layers_icon = f'<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="{icon_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 8px;"><polygon points="12 2 2 7 12 12 22 7 12 2"></polygon><polyline points="2 17 12 22 22 17"></polyline><polyline points="2 12 12 17 22 12"></polyline></svg>'
        sliders_icon = f'<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="{icon_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 8px;"><line x1="4" y1="21" x2="4" y2="14"></line><line x1="4" y1="10" x2="4" y2="3"></line><line x1="12" y1="21" x2="12" y2="12"></line><line x1="12" y1="8" x2="12" y2="3"></line><line x1="20" y1="21" x2="20" y2="16"></line><line x1="20" y1="12" x2="20" y2="3"></line><line x1="1" y1="14" x2="7" y2="14"></line><line x1="9" y1="8" x2="15" y2="8"></line><line x1="17" y1="16" x2="23" y2="16"></line></svg>'
        shield_icon = f'<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="{icon_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 8px;"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>'
        leaf_icon = f'<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="{icon_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 8px;"><path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8a8 8 0 0 1-8 8Z"></path><path d="M11 20c0-2.5 2-5.5 2-5.5"></path></svg>'
        search_icon = f'<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="{icon_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 6px;"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>'

        sim_badge = ""
        if simulation:
            sim_badge = '<span style="background: rgba(154, 219, 232, 0.08); color: #9ADBE8; padding: 4px 12px; border-radius: 12px; font-size: 0.7rem; font-weight: 600; border: 1px solid rgba(154, 219, 232, 0.2); letter-spacing: 0.5px; text-transform: uppercase; float: right;">Simulation included</span>'

        st.markdown(f"""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <h3 style="margin: 0; font-weight: 700;">Optimization Summary</h3>
            {sim_badge}
        </div>
        """, unsafe_allow_html=True)

        # Inject Premium CSS for metric cards
        st.markdown("""
        <style>
            .custom-metric-card {
                background: rgba(255, 255, 255, 0.05) !important;
                border: 1px solid rgba(255, 255, 255, 0.1) !important;
                border-radius: 12px !important;
                padding: 16px !important;
                box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2) !important;
                backdrop-filter: blur(16px) !important;
                -webkit-backdrop-filter: blur(16px) !important;
                transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease !important;
            }
            .custom-metric-card:hover {
                transform: translateY(-2px) !important;
                border-color: rgba(124, 58, 237, 0.5) !important;
                box-shadow: 0 8px 24px rgba(124, 58, 237, 0.2) !important;
            }
        </style>
        """, unsafe_allow_html=True)

        from ui.components import metric_card

        # Summary Tiles
        c1, c2, c3, c4 = st.columns(4)
        
        with c1: metric_card("Search Terms", f"{total_search_terms:,}", icon_name="search")
        with c2: metric_card("Bids", f"{total_bid_changes}", icon_name="sliders")
        with c3: metric_card("Negatives", f"{total_negatives}", icon_name="shield")
        with c4: metric_card("Harvest", f"{total_harvests}", icon_name="leaf")

        # === SAVE RUN CTA ===
        # Brand guidelines: Primary CTA uses Signal Blue (#2A8EC9)
        st.markdown("<div style='margin-top: 20px; margin-bottom: 10px;'></div>", unsafe_allow_html=True)
        
        total_actions = total_bid_changes + total_negatives + total_harvests
        
        # Style for primary CTA per brand guidelines
        st.markdown("""
        <style>
        div[data-testid="stButton"] > button.save-run-cta {
            background: #2A8EC9 !important;
            color: #FFFFFF !important;
            border: none !important;
            font-weight: 600 !important;
            padding: 12px 24px !important;
            border-radius: 8px !important;
            transition: all 0.2s ease !important;
        }
        div[data-testid="stButton"] > button.save-run-cta:hover {
            background: #238BB8 !important;
            box-shadow: 0 4px 12px rgba(42, 142, 201, 0.3) !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        col_spacer_l, col_cta, col_spacer_r = st.columns([2, 3, 2])
        with col_cta:
            if st.button(
                f"💾 Save Run to History ({total_actions} actions)", 
                key="save_optimizer_run_cta",
                type="primary",
                use_container_width=True
            ):
                # Get pending actions from session state
                pending = st.session_state.get('pending_actions')
                if pending and pending.get('actions'):
                    from core.db_manager import get_db_manager
                    db = get_db_manager(st.session_state.get('test_mode', False))
                    
                    try:
                        actions = pending['actions']
                        client_id = pending.get('client_id', st.session_state.get('active_account_id', 'unknown'))
                        
                        # Generate batch ID and get report date
                        import uuid
                        batch_id = str(uuid.uuid4())[:8]
                        report_date = date_info.get('end_date')
                        if hasattr(report_date, 'strftime'):
                            report_date = report_date.strftime('%Y-%m-%d')
                        
                        # Save to database
                        saved_count = db.log_action_batch(actions, client_id, batch_id, report_date)
                        
                        st.success(f"✅ Saved {saved_count} actions to history!")
                        st.session_state['pending_actions'] = None  # Clear pending
                        st.session_state['optimizer_actions_accepted'] = True
                        
                    except Exception as e:
                        st.error(f"Failed to save: {str(e)}")
                else:
                    st.warning("No actions to save. Run the optimizer first.")

        st.markdown("<div style='margin-bottom: 40px;'></div>", unsafe_allow_html=True)

        # Tab Navigation
        tabs_list = [
            {"name": "Overview", "icon": layers_icon},
            {"name": "Defence", "icon": shield_icon},
            {"name": "Bids", "icon": sliders_icon},
            {"name": "Harvest", "icon": leaf_icon},
            {"name": "Audit", "icon": search_icon},
            {"name": "Bulk Export", "icon": search_icon}
        ]
        active_tab = st.session_state.get('active_opt_tab', 'Overview')
        tab_cols = st.columns(len(tabs_list))
        
        for i, tab in enumerate(tabs_list):
            if tab_cols[i].button(tab["name"], key=f"tab_{tab['name']}", use_container_width=True, type="primary" if active_tab == tab["name"] else "secondary"):
                st.session_state['active_opt_tab'] = tab["name"]
                st.rerun()

        st.markdown("<div style='margin-bottom: 32px;'></div>", unsafe_allow_html=True)
        active_tab = st.session_state.get('active_opt_tab', 'Overview')
        
        if active_tab == "Overview":
            opt._display_dashboard_v2({"direct_bids": direct_bids, "agg_bids": agg_bids, "harvest": harvest_df, "simulation": simulation, "df": df_prep, "neg_kw": neg_kw})
        elif active_tab == "Defence":
            opt._display_negatives(neg_kw, neg_pt)
        elif active_tab == "Bids":
            opt._display_bids(bids_exact=bids_exact, bids_pt=bids_pt, bids_agg=bids_agg, bids_auto=bids_auto)
        elif active_tab == "Harvest":
            opt._display_harvest(harvest_df)
        elif active_tab == "Audit":
            opt._display_heatmap(heatmap_df)
        elif active_tab == "Bulk Export":
            opt._display_downloads(r)

    # Invoke Fragment
    render_optimizer_results(
        bids_exact, bids_pt, bids_agg, bids_auto, 
        neg_kw, neg_pt, harvest_df, simulation, 
        heatmap_df, df_prep, r, date_info
    )

    # Original logic followed here - we can delete the redundant parts below
    



    # Bid Adjustments
    total_bid_changes = len(bids_exact) + len(bids_pt) + len(bids_agg) + len(bids_auto)
    
    # Negatives Identified
    total_negatives = len(neg_kw) + len(neg_pt)
    
    # Harvest Opportunities
    total_harvests = len(harvest_df)
    
    # Icons
    icon_color = "#8F8CA3"
    layers_icon = f'<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="{icon_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 6px;"><polygon points="12 2 2 7 12 12 22 7 12 2"></polygon><polyline points="2 17 12 22 22 17"></polyline><polyline points="2 12 12 17 22 12"></polyline></svg>'
    search_icon = f'<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="{icon_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 6px;"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>'
    sliders_icon = f'<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="{icon_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 6px;"><line x1="4" y1="21" x2="4" y2="14"></line><line x1="4" y1="10" x2="4" y2="3"></line><line x1="12" y1="21" x2="12" y2="12"></line><line x1="12" y1="8" x2="12" y2="3"></line><line x1="20" y1="21" x2="20" y2="16"></line><line x1="20" y1="12" x2="20" y2="3"></line><line x1="1" y1="14" x2="7" y2="14"></line><line x1="9" y1="8" x2="15" y2="8"></line><line x1="17" y1="16" x2="23" y2="16"></line></svg>'
    shield_icon = f'<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="{icon_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 6px;"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>'
    leaf_icon = f'<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="{icon_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 6px;"><path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 3.5 2 7a7 7 0 0 1-10 11z"></path></svg>'

    sim_badge = ""
    if simulation:
        sim_badge = '<span style="background: rgba(154, 219, 232, 0.08); color: #9ADBE8; padding: 4px 12px; border-radius: 12px; font-size: 0.7rem; font-weight: 600; border: 1px solid rgba(154, 219, 232, 0.2); letter-spacing: 0.5px; text-transform: uppercase; float: right;">Simulation included</span>'










# ==========================================
# MAIN ROUTER
# ==========================================
def main():
    setup_page()
    
    # === AUTHENTICATION GATE ===
    # Shows login page if not authenticated, blocks access to main app
    # === AUTHENTICATION GATE (V2) ===
    # Using strict V2 Auth Service with Type Assertion
    from core.auth.models import User
    from core.auth.service import AuthService  # Explicit local import to guarantee scope
    from core.auth.permissions import has_permission, has_permission_for_account
    
    auth_service = AuthService()
    user = auth_service.get_current_user() # Gets from session
    
    if user is None:
        # Not logged in? Show V2 login screen and stop
        render_login()
        st.stop()
    
    # STRICT TYPE ASSERTION (Guardrail)
    if not isinstance(user, User):
        # This catches session corruption or mixing legacy/v2 usage
        auth_service.sign_out()
        st.error("Session type mismatch. Please refresh and login again.")
        st.stop()

    # === PHASE 3: ONBOARDING WIZARD ===
    # Show wizard for new users who haven't completed onboarding
    # Must come AFTER authentication but BEFORE any main content
    if FEATURE_ONBOARDING_WIZARD and should_show_onboarding():
        render_onboarding_wizard()
        st.stop()  # Don't render main app while wizard is active

    # PHASE 3: FORCED PASSWORD RESET MIDDLEWARE
    if user.must_reset_password:
        # If user must reset, lock them to 'profile' module
        if st.session_state.get('current_module') != 'profile':
            st.session_state['current_module'] = 'profile'
            st.warning("⚠️ You must change your password to proceed.")
            st.rerun()

    # PHASE 3 SECURITY: UPDATE LAST LOGIN
    # We do this here (middleware) to ensure it runs on every fresh session
    # but to avoid DB spam, we only do it if the session is "fresh" (e.g. not updated in last 5 min)
    # simplified: just do it on first load of session
    if 'login_tracked' not in st.session_state:
        try:
             # Quick direct update using manual cursor management for SQLite compatibility
             ph = auth_service.db_manager.placeholder
             with auth_service._get_connection() as conn:
                 cur = conn.cursor()
                 try:
                     # CURRENT_TIMESTAMP is standard SQL (works in PG and SQLite)
                     query = f"UPDATE users SET last_login_at = CURRENT_TIMESTAMP WHERE id = {ph}"
                     cur.execute(query, (str(user.id),))
                 finally:
                     cur.close()
             st.session_state['login_tracked'] = True
        except Exception as e:
            print(f"Login Track Error: {e}")

    # User is valid V2 user - proceed
    
    # === DATABASE INITIALIZATION ===
    
    # Phase 3.5: Set Account Context for Permissions
    # Must be done after DB init/loading where active_account_id is derived
    acc_ctx = None
    if 'active_account_id' in st.session_state:
        from uuid import UUID
        try:
            acc_ctx = UUID(str(st.session_state['active_account_id']))
        except:
            pass
    st.session_state['permission_account_context'] = acc_ctx

    # Initialize db_manager right after auth, before any UI that needs it
    if st.session_state.get('db_manager') is None:
        st.session_state['db_manager'] = get_db_manager(st.session_state.get('test_mode', False))

    # Phase 3.5: Set Account Context for Permissions
    # Must be done after DB init/loading where active_account_id is derived
    acc_ctx = None
    if 'active_account_id' in st.session_state:
        from uuid import UUID
        try:
            acc_ctx = UUID(str(st.session_state['active_account_id']))
        except:
            pass
    st.session_state['permission_account_context'] = acc_ctx
    
    # === TOP-RIGHT HEADER (Profile, Account, Logout) ===
    # This renders a fixed-position header component
    # Legacy: render_user_menu() -> Removed in V2 (Logout in sidebar)
    
    # Helper: Safe navigation (checks for pending actions when leaving optimizer)
    # Helper: Navigation
    def safe_navigate(target_module):
        st.session_state['current_module'] = target_module
        st.rerun()
    
    # Simplified V4 Sidebar
    with st.sidebar:
        # Sidebar Logo at TOP (theme-aware, prominent)
        import base64
        from pathlib import Path
        theme_mode = st.session_state.get('theme_mode', 'dark')
        logo_filename = "saddle_logo.png" if theme_mode == 'dark' else "saddle_logo_light.png"
        logo_path = Path(__file__).parent / "static" / logo_filename
        
        if logo_path.exists():
            with open(logo_path, "rb") as f:
                logo_data = base64.b64encode(f.read()).decode()
            st.markdown(
                f'<div style="text-align: center; padding: 15px 0 20px 0;"><img src="data:image/png;base64,{logo_data}" style="width: 200px;" /></div>',
                unsafe_allow_html=True
            )
        
        # Account selector (right after logo)
        from ui.account_manager import render_account_selector
        render_account_selector()
        
        # Logout button (compact)
        from core.auth.service import AuthService
        auth = AuthService()
        if st.button("⏻ Logout", key="sidebar_logout", use_container_width=True, help="Sign out"):
            auth.sign_out()
            st.rerun()
        
        st.divider()
        
        # =========================
        # PRIMARY NAVIGATION
        # =========================
        # Side Navigation Icons
        nav_icon_color = "#8F8CA3"
        home_icon = f'<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="{nav_icon_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle;"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg>'
        performance_icon = f'<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="{nav_icon_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle;"><rect width="18" height="18" x="3" y="3" rx="2"/><path d="M7 12v5"/><path d="M12 9v8"/><path d="M17 11v6"/></svg>'
        report_card_icon = f'<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="{nav_icon_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle;"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><line x1="10" y1="9" x2="8" y2="9"/></svg>'
        impact_icon = f'<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="{nav_icon_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle;"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>'
        check_icon = f'<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="{nav_icon_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle;"><path d="m9 11 3 3L22 4"></path><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path></svg>'
        sim_icon = f'<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="{nav_icon_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle;"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline><polyline points="17 6 23 6 23 12"></polyline></svg>'
        rocket_icon = f'<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="{nav_icon_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle;"><path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"></path><path d="m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"></path><path d="m9 12 2.5 2.5"></path></svg>'
        storage_icon = f'<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="{nav_icon_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle;"><path d="M21 20V4a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v16"></path><rect x="3" y="4" width="18" height="4" rx="2"></rect><rect x="3" y="12" width="18" height="4" rx="2"></rect></svg>'
        help_icon = f'<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="{nav_icon_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle;"><circle cx="12" cy="12" r="10"></circle><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>'
        settings_icon = f'<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="{nav_icon_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle;"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>'

        # Stylized nav button with CSS injection for hover effects and integrated SVG
        st.markdown(f"""
        <style>
        .nav-chiclet {{
            background: rgba(143, 140, 163, 0.05);
            border: 1px solid rgba(143, 140, 163, 0.1);
            border-radius: 10px;
            padding: 10px 15px;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 12px;
            cursor: pointer;
            transition: all 0.2s ease;
            color: #B6B4C2;
            text-decoration: none;
        }}
        .nav-chiclet:hover {{
            background: rgba(143, 140, 163, 0.1);
            border-color: rgba(124, 58, 237, 0.4);
            color: #F5F5F7;
            transform: translateX(4px);
        }}
        .nav-chiclet.active {{
            background: linear-gradient(135deg, rgba(124, 58, 237, 0.15) 0%, rgba(124, 58, 237, 0.08) 100%);
            border-color: rgba(124, 58, 237, 0.5);
            color: #F5F5F7;
        }}
        </style>
        """, unsafe_allow_html=True)

        def nav_chiclet_link(label, icon_html, module_key):
            is_active = st.session_state.get('current_module') == module_key
            active_class = "active" if is_active else ""
            
            # Use a transparent button over the chiclet for interactivity
            if st.button(label, key=f"nav_{module_key}", use_container_width=True):
                # Check if leaving optimizer with pending actions
                if st.session_state.get('current_module') == 'optimizer' and st.session_state.get('pending_actions'):
                    # Trigger confirmation dialog instead of navigating
                    st.session_state['_show_action_confirmation'] = True
                    st.session_state['_pending_navigation_target'] = module_key
                    st.rerun()
                else:
                    # Navigate directly
                    st.session_state['current_module'] = module_key
                    st.rerun()

        # Re-using the nav_button logic but with the chiclet feel properly integrated
        # We'll use Streamlit's native buttons but style them to look like the chiclets
        st.markdown("""
        <style>
        /* Base Sidebar Button Styling - Targets all buttons in our custom wrappers */
        [data-testid="stSidebar"] .nav-item-wrapper div.stButton > button,
        [data-testid="stSidebar"] .sub-nav-wrapper div.stButton > button {
            background: rgba(143, 140, 163, 0.05) !important;
            border: 1px solid rgba(143, 140, 163, 0.1) !important;
            border-radius: 10px !important;
            color: #B6B4C2 !important;
            text-align: left !important;
            padding: 8px 12px !important;
            margin-bottom: 0px !important;
            font-weight: 500 !important;
            transition: all 0.2s ease !important;
        }
        
        /* Balanced vertical spacing between sidebar elements */
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
            gap: 0.5rem !important;
        }
        
        /* Fix the alignment and gap of the icon column */
        [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] {
            gap: 0.5rem !important;
        }

        /* Balanced Dividers */
        [data-testid="stSidebar"] hr {
            margin: 1rem 0 !important;
            opacity: 0.15 !important;
        }
        
        [data-testid="stSidebar"] .nav-item-wrapper div.stButton > button:hover {
            background: rgba(143, 140, 163, 0.1) !important;
            border-color: rgba(91, 85, 111, 0.4) !important;
            color: #F5F5F7 !important;
            transform: translateX(4px) !important;
        }
        </style>
        """, unsafe_allow_html=True)

        # Helper for stylized nav buttons with inline SVGs
        def nav_button_chiclet(label, icon_html, key):
            is_active = st.session_state.get('current_module') == key
            active_bg = "linear-gradient(135deg, rgba(91, 85, 111, 0.2) 0%, rgba(91, 85, 111, 0.1) 100%)" if is_active else "rgba(143, 140, 163, 0.05)"
            active_border = "rgba(91, 85, 111, 0.5)" if is_active else "rgba(143, 140, 163, 0.1)"
            
            # Use specific CSS for active button targeting the wrapper
            st.markdown(f"""
            <style>
            .nav-wrapper-{key} div.stButton > button {{
                background: {active_bg} !important;
                border-color: {active_border} !important;
                color: {"#F5F5F7" if is_active else "#B6B4C2"} !important;
            }}
            </style>
            """, unsafe_allow_html=True)

            st.markdown(f'<div class="nav-item-wrapper nav-wrapper-{key}">', unsafe_allow_html=True)
            col1, col2 = st.columns([1, 6])
            with col1:
                st.markdown(f'<div style="margin-top: 5px; margin-left: 5px; opacity: {"1.0" if is_active else "0.6"};">{icon_html}</div>', unsafe_allow_html=True)
            with col2:
                if st.button(label, use_container_width=True, key=f"nav_btn_v6_{key}"):
                    safe_navigate(key)
            st.markdown('</div>', unsafe_allow_html=True)

        nav_button_chiclet("Home", home_icon, "home")
        nav_button_chiclet("Account Overview", performance_icon, "performance")
        
        st.divider()
        st.markdown("##### ANALYZE")
        
        # PERMISSION GATING (V2)
        from core.auth.permissions import has_permission
        
        # Optimizer - Requires 'run_optimizer'
        # Phase 3.5: Operator cannot run optimizer if overridden to VIEWER on this account
        if has_permission_for_account(user, 'run_optimizer', st.session_state.get('permission_account_context')):
            nav_button_chiclet("Actions Review", check_icon, "optimizer")
            
        nav_button_chiclet("What If (Forecast)", sim_icon, "simulator")
        nav_button_chiclet("Impact & Results", impact_icon, "impact")
        
        
        # Client Report feature removed
        
        # Launch - Requires 'run_optimizer' (Creating campaigns)
        if has_permission_for_account(user, 'run_optimizer', st.session_state.get('permission_account_context')):
            nav_button_chiclet("Launch", rocket_icon, "creator")

        st.divider()
        
        # ADMIN SECTION
        if has_permission(user.role, 'manage_users'):
             st.markdown("##### ORGANIZATION")
             # Icons for new sections
             team_icon = f'<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="{nav_icon_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle;"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>'
             billing_icon = f'<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="{nav_icon_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle;"><rect x="2" y="5" width="20" height="14" rx="2"></rect><line x1="2" y1="10" x2="22" y2="10"></line></svg>'
             
             nav_button_chiclet("Team", team_icon, "team_settings")
             # Billing is placeholder for now (Phase 3)
             # nav_button_chiclet("Billing", billing_icon, "billing")

        st.divider()

        # PROFILE SECTION (Everyone)
        nav_button_chiclet("Profile", settings_icon, "profile")

        st.divider()

        # =========================
        # SECONDARY / SYSTEM
        # =========================
        nav_button_chiclet("Data Setup", storage_icon, "data_hub")
        
        # SUPER ADMIN SECTION
        # Check against DEFAULT_ADMIN_EMAIL or a config list
        # We hardcode admin@saddl.io here as per plan for simplicity/security
        

        if user.email and user.email.lower().strip() == "admin@saddl.io":
            platform_icon = f'<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="{nav_icon_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle;"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line></svg>'
            nav_button_chiclet("Platform Admin", platform_icon, "platform_admin")
            
        # Account Settings (Merged into Profile)
        nav_button_chiclet("Help", help_icon, "readme")
        
        # Show undo toast if available
        from ui.action_confirmation import show_undo_toast
        show_undo_toast()
        
        # Theme Toggle (logout moved to top header)
        st.divider()
        from ui.theme import ThemeManager
        ThemeManager.render_toggle()
        
        # Database Mode Toggle (below Help)
        st.divider()
        test_mode = st.toggle("Test Mode", value=st.session_state.get('test_mode', False))
        if test_mode != st.session_state.get('test_mode', False):
            st.session_state['test_mode'] = test_mode
            st.session_state['db_manager'] = get_db_manager(test_mode)
            st.rerun()
        if st.session_state['db_manager'] is None:
            st.session_state['db_manager'] = get_db_manager(st.session_state['test_mode'])
        if st.session_state['test_mode']:
            st.caption("Using: `ppc_test.db`")
        else:
            # Show actual database type
            db = st.session_state.get('db_manager')
            if db and type(db).__name__ == 'PostgresManager':
                st.caption("Using: `Supabase (Postgres)`")
            else:
                st.caption("Using: `ppc_live.db`")
            
    # Routing
    current = st.session_state.get('current_module', 'home')
    
    # Check for pending actions confirmation dialog - REMOVED per user request
    # Actions are now saved explicitly via "Save Run" button in optimizer
    # from ui.action_confirmation import render_action_confirmation_modal
    # render_action_confirmation_modal()
    
    # Show test mode warning banner
    if st.session_state.get('test_mode', False):
        st.warning("⚠️ **TEST MODE ACTIVE** — All data is being saved to `ppc_test.db`. Switch off to use production database.")
    
    if current == 'home':
        render_home()
    
    elif current == 'data_hub':
        from ui.data_hub import render_data_hub
        render_data_hub()
        
    elif current == 'platform_admin':
        # Strictly verify access even if session state thinks we are here
        if user.email and user.email.lower().strip() == "admin@saddl.io":
            from features.platform_admin import render_platform_admin
            render_platform_admin()
        else:
            # Unauthorized access attempt or sticky session state - reset to home
            st.session_state['current_module'] = 'home'
            st.rerun()
    
    elif current == 'account_settings':
        # Route legacy calls to consolidated module
        from features.account_settings import run_account_settings
        run_account_settings()

    elif current == 'team_settings':
        from ui.auth.user_management import render_user_management
        render_user_management()

    elif current == 'profile':
        from features.account_settings import run_account_settings
        run_account_settings()
        
    elif current == 'billing':
        st.info("Billing module coming in Phase 3.")
        
    elif current == 'readme':
        from ui.readme import render_readme
        render_readme()
    
    elif current == 'optimizer':
        run_consolidated_optimizer()
        
    elif current == 'simulator':
        from features.simulator import SimulatorModule
        SimulatorModule().run()
        
    elif current == 'performance':
        run_performance_hub()
    
    elif current == 'creator':
        from features.creator import CreatorModule
        creator = CreatorModule()
        creator.run()
    
    elif current == 'assistant':
        from features.assistant import AssistantModule
        AssistantModule().render_interface()
        
    # ASIN/AI modules are now inside Optimizer, but we keep routing valid just in case
    elif current == 'asin_mapper':
        from features.asin_mapper import ASINMapperModule
        ASINMapperModule().run()
    elif current == 'ai_insights':
        from features.kw_cluster import AIInsightsModule
        AIInsightsModule().run()
    elif current == 'impact':
        from features.impact_dashboard import render_impact_dashboard
        render_impact_dashboard()
    # Client Report feature removed

    # Render Floating Chat Bubble (unless already on assistant page)
    if current != 'assistant':
        from features.assistant import AssistantModule
        assistant = AssistantModule()
        assistant.render_floating_interface()
        assistant.render_interface()

if __name__ == "__main__":
    main()

