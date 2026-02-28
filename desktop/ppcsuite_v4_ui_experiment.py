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
    initial_sidebar_state="expanded",
    page_icon="🚀",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
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
# Run seeding with @st.cache_resource to execute only once per app instance
# This prevents connection pool exhaustion from concurrent seeding attempts
# MOVED TO LAZY EXECUTION: Now runs in main() BEFORE login check, not at module load time
@st.cache_resource(show_spinner=False)  # Cache forever - seeding only needs to run once per deployment
def run_seeding():
    # Skip seeding if explicitly disabled via environment variable
    # NOTE: Seeding disabled by default on Streamlit Cloud to prevent hanging
    if os.getenv("SKIP_SEEDING") == "true":
        print("SEED: Skipping (SKIP_SEEDING=true)")
        return "Seeding skipped"

    try:
        from app_core.seeding import seed_initial_data
        # Simple execution - no timeout handling to avoid signal/threading issues
        result = seed_initial_data()
        return result or "Seeding completed"

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Startup Seeding Failed: {e}")
        return f"Seeding failed: {e}"

# Seeding will be called lazily in main() to avoid blocking module import

# Delay heavy feature imports by moving them into routing/main logic


# Delay heavy feature imports by moving them into routing/main logic
from ui.layout import setup_page, render_sidebar, render_home
from app_core.data_hub import DataHub
from app_core.db_manager import get_db_manager
from utils.matchers import ExactMatcher
from utils.formatters import format_currency
from app_core.data_loader import safe_numeric
from pathlib import Path

# === ONBOARDING ===
from ui.onboarding import should_show_onboarding, render_onboarding_wizard
from config.features import FEATURE_ONBOARDING_WIZARD
from config.features import FeatureFlags

# === AUTHENTICATION ===
from app_core.auth.service import AuthService
from app_core.auth.middleware import require_auth, require_permission
from ui.auth.login import render_login
# Legacy import removed: from auth import require_authentication, render_user_menu

# ── PostgreSQL enforcement ──────────────────────────────────────────────────
import sys as _sys
_db_url = os.environ.get("DATABASE_URL", "")
if not _db_url.startswith("postgresql"):
    print("ERROR: SADDL requires a PostgreSQL connection. SQLite is not supported.")
    _sys.exit(1)
# ────────────────────────────────────────────────────────────────────────────

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

if "active_perf_tab" not in st.session_state:
    st.session_state["active_perf_tab"] = "overview"


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
    
    if FeatureFlags.is_enabled("ENABLE_PERFORMANCE_DASHBOARD_BUSINESS_OVERVIEW"):
        _show_ppc_tab = FeatureFlags.is_enabled("ENABLE_PERFORMANCE_DASHBOARD_PPC_OVERVIEW")
        _show_legacy_tab = FeatureFlags.is_enabled("ENABLE_ACCOUNT_OVERVIEW_LEGACY")

        if "active_perf_tab" not in st.session_state:
            st.session_state["active_perf_tab"] = "Business Overview"

        # If legacy tab is disabled and it was previously selected, reset to Business Overview
        if not _show_legacy_tab and st.session_state.get("active_perf_tab") == "Client Report":
            st.session_state["active_perf_tab"] = "Business Overview"

        _num_tabs = 1 + int(_show_ppc_tab) + int(_show_legacy_tab)
        _tab_cols = st.columns(_num_tabs)
        _col_idx = 0
        with _tab_cols[_col_idx]:
            if st.button(
                "BUSINESS OVERVIEW",
                key="btn_business_overview",
                use_container_width=True,
                type="primary" if st.session_state["active_perf_tab"] == "Business Overview" else "secondary",
            ):
                st.session_state["active_perf_tab"] = "Business Overview"
                st.rerun()
        _col_idx += 1
        if _show_legacy_tab:
            with _tab_cols[_col_idx]:
                if st.button(
                    "ACCOUNT OVERVIEW (LEGACY)",
                    key="btn_account_overview_legacy",
                    use_container_width=True,
                    type="primary" if st.session_state["active_perf_tab"] == "Client Report" else "secondary",
                ):
                    st.session_state["active_perf_tab"] = "Client Report"
                    st.rerun()
            _col_idx += 1
        if _show_ppc_tab:
            with _tab_cols[_col_idx]:
                if st.button(
                    "PPC OVERVIEW",
                    key="btn_ppc_overview",
                    use_container_width=True,
                    type="primary" if st.session_state["active_perf_tab"] == "PPC Overview" else "secondary",
                ):
                    st.session_state["active_perf_tab"] = "PPC Overview"
                    st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        if st.session_state["active_perf_tab"] == "Business Overview":
            from features.dashboard.business_overview import render_business_overview
            render_business_overview()
        elif _show_ppc_tab and st.session_state["active_perf_tab"] == "PPC Overview":
            from ui.performance_dashboard.ppc_overview import render_ppc_overview
            render_ppc_overview()
        elif _show_legacy_tab and st.session_state["active_perf_tab"] == "Client Report":
            import ui.client_report_page as client_report
            import importlib
            importlib.reload(client_report)
            client_report.run()
        else:
            # Fallback: always show Business Overview when legacy is disabled
            from features.dashboard.business_overview import render_business_overview
            render_business_overview()
        return

    if 'active_perf_tab' not in st.session_state:
        st.session_state['active_perf_tab'] = "Executive Dashboard"
        
    # Custom Tab Styling with Glassmorphic Icons
    st.markdown("""
    <style>
    /* Wrapper for Tab Buttons */
    div.tab-btn-wrapper button {
        height: 54px;
        border-radius: 12px !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px !important;
        transition: all 0.2s ease !important;
        padding-left: 52px !important; /* Space for icon */
        position: relative;
        overflow: hidden; 
        text-transform: uppercase;
    }
    
    /* Icon: Executive Dashboard (Cyan Chart) */
    div.tab-exec button::before {
        content: "";
        position: absolute;
        left: 20px;
        top: 50%;
        transform: translateY(-50%);
        width: 24px;
        height: 24px;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2322d3ee' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='3' y='3' width='7' height='7' rx='1'%3E%3C/rect%3E%3Crect x='14' y='3' width='7' height='7' rx='1'%3E%3C/rect%3E%3Crect x='14' y='14' width='7' height='7' rx='1'%3E%3C/rect%3E%3Crect x='3' y='14' width='7' height='7' rx='1'%3E%3C/rect%3E%3C/svg%3E");
        background-repeat: no-repeat;
        background-position: center;
        opacity: 0.95;
        filter: drop-shadow(0 0 6px rgba(34, 211, 238, 0.5));
    }
    
    /* Icon: Account Health (Pink Shield) */
    div.tab-health button::before {
        content: "";
        position: absolute;
        left: 20px;
        top: 50%;
        transform: translateY(-50%);
        width: 24px;
        height: 24px;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23F43F5E' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z'%3E%3C/path%3E%3Cpath d='M12 8v4'%3E%3C/path%3E%3Cpath d='M12 16h.01'%3E%3C/path%3E%3C/svg%3E");
        background-repeat: no-repeat;
        background-position: center;
        opacity: 0.95;
        filter: drop-shadow(0 0 6px rgba(244, 63, 94, 0.5));
    }
    
    /* Icon: Client Report (Cyan Document) */
    div.tab-report button::before {
        content: "";
        position: absolute;
        left: 20px;
        top: 50%;
        transform: translateY(-50%);
        width: 24px;
        height: 24px;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2322d3ee' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z'%3E%3C/path%3E%3Cpolyline points='14 2 14 8 20 8'%3E%3C/polyline%3E%3Cline x1='16' y1='13' x2='8' y2='13'%3E%3C/line%3E%3Cline x1='16' y1='17' x2='8' y2='17'%3E%3C/line%3E%3Cpolyline points='10 9 9 9 8 9'%3E%3C/polyline%3E%3C/svg%3E");
        background-repeat: no-repeat;
        background-position: center;
        opacity: 0.95;
        filter: drop-shadow(0 0 6px rgba(34, 211, 238, 0.5));
    }
    </style>
    """, unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    
    # === HIDE TABS: Option A (Short-term) ===
    # We are hiding the first two tabs and defaulting to Client Report (Renamed to "Account Overview")
    
    # with c1:
    #     is_active = st.session_state['active_perf_tab'] == "Executive Dashboard"
    #     st.markdown('<div class="tab-btn-wrapper tab-exec">', unsafe_allow_html=True)
    #     # Removed emoji 📊
    #     if st.button("EXECUTIVE DASHBOARD", key="btn_tab_exec", use_container_width=True, type="primary" if is_active else "secondary"):
    #         st.session_state['active_perf_tab'] = "Executive Dashboard"
    #         st.rerun()
    #     st.markdown('</div>', unsafe_allow_html=True)
        
    # with c2:
    #     is_active = st.session_state['active_perf_tab'] == "Account Health"
    #     st.markdown('<div class="tab-btn-wrapper tab-health">', unsafe_allow_html=True)
    #     # Removed emoji 🛡️
    #     if st.button("ACCOUNT HEALTH", key="btn_tab_report", use_container_width=True, type="primary" if is_active else "secondary"):
    #         st.session_state['active_perf_tab'] = "Account Health"
    #         st.rerun()
    #     st.markdown('</div>', unsafe_allow_html=True)
        
    # Force single view for now
    st.session_state['active_perf_tab'] = "Client Report"
    
    # Use full width for the single tab
    with c2: 
        pass
            
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.session_state['active_perf_tab'] == "Executive Dashboard":
        from features.executive_dashboard import ExecutiveDashboard
        ExecutiveDashboard().run()
    elif st.session_state['active_perf_tab'] == "Account Health":
        from features.report_card import ReportCardModule
        ReportCardModule().run()
    elif st.session_state['active_perf_tab'] == "Client Report":
        import ui.client_report_page as client_report
        import importlib
        importlib.reload(client_report)
        client_report.run()
    else:
        # Default fallback
        from features.executive_dashboard import ExecutiveDashboard
        ExecutiveDashboard().run()


def run_diagnostics_hub():
    """Diagnostics Control Center v2.0."""
    from features.diagnostics.control_center import render_control_center
    
    # Retrieve client ID (support both new primitive key and old dict legacy)
    client_id = st.session_state.get('active_account_id')
    if not client_id:
        # Fallback to legacy dictionary if present
        client_id = st.session_state.get('active_account', {}).get('account_id', 's2c_uae_test')
        
    render_control_center(client_id)


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
    
    # === OPTIMIZER V2 (REFACTORED) ===
    # User Request: "deprecate the optimizer legacy dashboard... remove all the wiring"
    # We now exclusively run the Refactored V2 Optimizer
    
    from features.optimizer_v2.main import render_optimizer_v2
    render_optimizer_v2()
    return  # Stop execution here - do not run legacy code below

# ==========================================
# MAIN ROUTER
# ==========================================

def render_shared_report():
    """
    Render read-only shared report view.
    Route: ?page=shared_report&id={report_id}
    """
    import streamlit as st
    from app_core.db_manager import get_db_manager
    from ui import client_report_page as client_report
    
    # Get report ID from URL
    query_params = st.query_params
    report_id = query_params.get("id")
    
    if not report_id:
        st.error("⚠️ **Invalid Share Link**")
        st.info("This link appears to be incomplete. Please check the URL and try again.")
        st.stop()
    
    try:
        # Fetch report from database
        db = get_db_manager()
        report_data = db.get_shared_report(report_id)
        
        # Set session state for report context
        st.session_state['active_account_id'] = report_data['client_id']
        st.session_state['date_range'] = report_data['date_range']
        st.session_state['read_only_mode'] = True
        st.session_state['show_client_report'] = True  # Bypass landing page
        
        # Hydrate AI Narratives (if they exist)
        narratives = report_data.get('metadata', {}).get('narratives', {})
        if narratives:
             cache_key = f"client_report_narratives_{report_data['client_id']}"
             st.session_state[cache_key] = narratives
        
        # Show view counter badge
        views = report_data.get('views', 1)
        if views > 1:
            st.caption(f"👁️ This report has been viewed **{views} times**")
        
        # Render report (same page, read-only mode)
        client_report.run()
        
    except ValueError as e:
        # Report not found or expired
        error_msg = str(e)
        
        st.error(f"⚠️ **{error_msg}**")
        
        if "expired" in error_msg.lower():
            st.info("💡 **Shared reports expire after 30 days.** Please contact the report sender for a new link.")
        elif "not found" in error_msg.lower():
            st.info("💡 **This report may have been deleted or the link is incorrect.** Please verify the URL.")
        else:
            st.info("💡 **Unable to load report.** Please contact the report sender for assistance.")
        
        st.stop()
        
    except Exception as e:
        st.error(f"❌ **Error loading report:** {str(e)}")
        st.info("Please try refreshing the page. If the issue persists, contact support.")
        st.stop()


# ==========================================
# MAIN ROUTER
# ==========================================
def main():
    # === SHARED REPORT ROUTE (Public/No Auth) ===
    # Must be first to bypass auth
    query_params = st.query_params
    if query_params.get("page") == "shared_report":
        render_shared_report()
        return

    setup_page()

    # === FORCE SIDEBAR STATE TO EXPANDED ===
    # Reset sidebar state in session to force it expanded
    # Check multiple possible session state keys that Streamlit uses internally
    for key in ['_sidebar_state', 'sidebar_state', '_main_menu_visibility']:
        if key in st.session_state:
            if key == '_main_menu_visibility':
                st.session_state[key] = 'hidden'
            else:
                st.session_state[key] = 'expanded'

    # === LOCK SIDEBAR OPEN & HIDE HEADER ===
    # CSS-only approach that runs before authentication
    # JavaScript will be injected AFTER authentication to avoid interfering with login
    st.markdown("""
    <style>
        /* CRITICAL: Hide ALL sidebar collapse controls */
        [data-testid="stSidebarCollapsedControl"],
        [data-testid="stSidebarCollapseButton"],
        [data-testid="collapsedControl"],
        button[kind="header"][data-testid="baseButton-header"],
        button[kind="headerNoPadding"],
        section[data-testid="stSidebar"] button[kind="header"],
        section[data-testid="stSidebar"] > div > button[kind="header"] {
            display: none !important;
            visibility: hidden !important;
            pointer-events: none !important;
            opacity: 0 !important;
            width: 0 !important;
            height: 0 !important;
        }

        /* Force sidebar to ALWAYS be visible and expanded */
        section[data-testid="stSidebar"] {
            display: block !important;
            visibility: visible !important;
            position: relative !important;
            min-width: 244px !important;
            max-width: 244px !important;
            width: 244px !important;
            transform: translateX(0) !important;
            transition: none !important;
        }

        /* Override ANY collapsed state styling */
        section[data-testid="stSidebar"][aria-expanded="false"],
        section[data-testid="stSidebar"].collapsed,
        section[data-testid="stSidebar"][data-collapsed="true"] {
            display: block !important;
            visibility: visible !important;
            min-width: 244px !important;
            max-width: 244px !important;
            width: 244px !important;
            transform: translateX(0) !important;
        }

        /* Ensure sidebar content is visible */
        section[data-testid="stSidebar"] > div {
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
        }

        /* Hide the main header, toolbar, and decoration */
        header[data-testid="stHeader"],
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        .stApp > header {
            visibility: hidden !important;
            height: 0 !important;
            padding: 0 !important;
            margin: 0 !important;
            display: none !important;
        }

        /* Hide the deploy button specifically */
        .stDeployButton,
        [data-testid="stStatusWidget"] {
            display: none !important;
        }

        /* Hide the footer and "Made with Streamlit" */
        footer,
        footer[data-testid="stFooter"] {
            visibility: hidden !important;
            display: none !important;
        }

        /* Adjust top padding since header is gone */
        .main .block-container {
            padding-top: 1rem !important;
        }
    </style>
    """, unsafe_allow_html=True)



    # === AUTHENTICATION GATE ===
    # Shows login page if not authenticated, blocks access to main app
    # === AUTHENTICATION GATE (V2) ===
    # Using strict V2 Auth Service with Type Assertion
    from app_core.auth.models import User
    from app_core.auth.service import AuthService  # Explicit local import to guarantee scope
    from app_core.auth.permissions import has_permission, has_permission_for_account
    
    auth_service = AuthService()
    user = auth_service.get_current_user() # Gets from session
    
    # === AMAZON OAUTH CALLBACK INTERCEPTION ===
    # Check if we are returning from the Amazon LWA OAuth flow (via Supabase Edge Function)
    query_params = st.query_params
    if query_params.get("amazon_auth") == "success":
        connected_client_id = query_params.get("client_id")
        if connected_client_id:
            st.session_state['amazon_connected'] = True
            st.session_state['amazon_client_id'] = connected_client_id
            st.toast("✅ Successfully connected to Amazon Ads!")
        
        # Clear the params so a refresh doesn't trigger it again
        st.query_params.clear()
        
    elif query_params.get("amazon_auth") == "failed":
        reason = query_params.get("reason", "Unknown error")
        st.error(f"Failed to connect to Amazon Ads: {reason}")
        st.query_params.clear()

    if user is None:
        # === RUN SEEDING BEFORE LOGIN ===
        # Database must be initialized for login to work
        # Only runs once per app instance (cached)
        # Show a friendly message while initializing
        try:
            import time
            from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

            # Run seeding with timeout to prevent infinite hang
            with st.spinner("Initializing database..."):
                start_time = time.time()
                executor = ThreadPoolExecutor(max_workers=1)
                future = executor.submit(run_seeding)

                try:
                    seeding_result = future.result(timeout=10.0)
                    elapsed = time.time() - start_time
                    print(f"SEED: Completed in {elapsed:.2f}s")

                    if seeding_result and "Error" in str(seeding_result):
                        st.warning(f"⚠️ Database initialization had issues: {seeding_result}")
                        st.info("You may still be able to log in if the database was previously initialized.")
                except FuturesTimeoutError:
                    # Do not block startup waiting for a stuck worker thread.
                    future.cancel()
                    st.warning("⚠️ Database initialization is taking too long.")
                    st.info("Continuing to login. If sign-in fails, check DATABASE_URL and database reachability.")
                finally:
                    executor.shutdown(wait=False, cancel_futures=True)
        except Exception as e:
            st.error(f"❌ Database initialization failed: {e}")
            st.info("If the database was already initialized, you can proceed to login.")
            import traceback
            with st.expander("Error Details"):
                st.code(traceback.format_exc())

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
        from app_core.auth.service import AuthService
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
        diagnostics_icon = f'<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="{nav_icon_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle;"><path d="M3 3h7v7H3z"></path><path d="M14 3h7v7h-7z"></path><path d="M14 14h7v7h-7z"></path><path d="M3 14h7v7H3z"></path></svg>'
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
        from app_core.auth.permissions import has_permission
        
        # Optimizer - Requires 'run_optimizer'
        # Phase 3.5: Operator cannot run optimizer if overridden to VIEWER on this account
        if has_permission_for_account(user, 'run_optimizer', st.session_state.get('permission_account_context')):
            nav_button_chiclet("Optimizer", check_icon, "optimizer")
            
        nav_button_chiclet("What If (Forecast)", sim_icon, "simulator")
        if FeatureFlags.is_enabled("ENABLE_DIAGNOSTICS_LEGACY"):
            nav_button_chiclet("Diagnostics", diagnostics_icon, "diagnostics")
        nav_button_chiclet("Impact & Results", impact_icon, "impact_v2")


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

    # Ghost content prevention removed - caused pages not to load
    # Will address in polish phase

    # Check for pending actions confirmation dialog - REMOVED per user request
    # Actions are now saved explicitly via "Save Run" button in optimizer
    # from ui.action_confirmation import render_action_confirmation_modal
    # render_action_confirmation_modal()

    # Show test mode warning banner
    if st.session_state.get('test_mode', False):
        st.warning("⚠️ **TEST MODE ACTIVE** — All data is being saved to `ppc_test.db`. Switch off to use production database.")

    # Create main content container for proper clearing
    main_content = st.container()

    with main_content:
        if current == 'home':
            render_home()

        elif current == 'data_hub':
            import importlib
            import sys
            # Clear module cache to prevent KeyError
            if 'ui.data_hub' in sys.modules:
                importlib.reload(sys.modules['ui.data_hub'])
                from ui.data_hub import render_data_hub
            else:
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
            import importlib
            import sys
            # Clear module cache to prevent KeyError
            if 'ui.auth.user_management' in sys.modules:
                importlib.reload(sys.modules['ui.auth.user_management'])
                from ui.auth.user_management import render_user_management
            else:
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
            from features.optimizer_v2.main import render_optimizer_v2
            render_optimizer_v2()

        elif current == 'simulator':
            from features.simulator import SimulatorModule
            SimulatorModule().run()

        elif current == 'diagnostics':
            run_diagnostics_hub()

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

        elif current == 'debug_impact':
            from features.debug_ui import render_debug_metrics
            render_debug_metrics()

        elif current == 'ai_insights':
            from features.kw_cluster import AIInsightsModule
            AIInsightsModule().run()

        # Legacy impact_dashboard.py wiring removed - v2 is now primary
        elif current == 'impact_v2':
            from features.impact.main import render_impact_dashboard_v2
            render_impact_dashboard_v2()
        # Client Report feature removed

    # Render Floating Chat Bubble (unless already on assistant page)
    if current != 'assistant':
        from features.assistant import AssistantModule
        assistant = AssistantModule()
        assistant.render_floating_interface()
        assistant.render_interface()

if __name__ == "__main__":
    main()
