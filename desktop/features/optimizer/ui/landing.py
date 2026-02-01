import streamlit as st
import datetime
from .components import render_status_badge

@st.cache_data(ttl=300, show_spinner=False)
def _fetch_target_stats_cached(client_id: str, test_mode: bool):
    """Cache database query for target stats - prevents repeated DB calls on every rerun."""
    from core.db_manager import get_db_manager
    db_manager = get_db_manager(test_mode)
    if db_manager and client_id:
        return db_manager.get_target_stats_df(client_id)
    return None

def render_landing_page(config: dict):
    """
    Renders the pre-optimization landing page with Hero, Snapshot, and Presets.
    """
    # 1. Hero Section
    st.markdown('<div class="optimizer-hero">', unsafe_allow_html=True)
    render_status_badge("Ready to Optimize", active=True)

    st.markdown("""
    <h1 style="font-size: 56px; font-weight: 700; line-height: 1.1; margin-bottom: 16px; letter-spacing: -2px;">
        PPC<br>
        <span style="background: linear-gradient(135deg, #2dd4bf 0%, #06b6d4 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Optimizer</span>
    </h1>
    <p style="font-size: 18px; color: #94a3b8; max-width: 600px; margin: 0 auto;">
        AI-driven bid management & harvest intelligence to maximize ROAS and reduce wasted spend.
    </p>
    </div>
    """, unsafe_allow_html=True)

    # 2. Account Snapshot (Dynamic Data from DataHub)
    from core.data_hub import DataHub
    from utils.formatters import get_account_currency
    import pandas as pd

    hub = DataHub()

    # Initialize Logic Defaults
    snap_spend = "—"
    snap_roas = "—"
    snap_acos = "—"
    snap_terms = "—"
    df = None

    # Fetch data from database (like legacy optimizer) - NOW CACHED!
    client_id = st.session_state.get('active_account_id')
    test_mode = st.session_state.get('test_mode', False)

    # Data Constraints - Start with defaults
    max_date = datetime.date.today()
    min_date = max_date - datetime.timedelta(days=60)

    # Fetch Data & Determine Constraints from actual database
    if client_id:
        db_df = _fetch_target_stats_cached(client_id, test_mode)

        if not db_df.empty:
            df = db_df.copy()
            # Determine Min/Max Date from Database Data
            if 'Date' in df.columns:
                try:
                    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                    min_date = df['Date'].min().date()
                    # Add 6 days to max for week-ending display (database stores week start)
                    max_date = df['Date'].max().date() + datetime.timedelta(days=6)
                except:
                    pass
    elif hub.is_loaded("search_term_report"):
        # Fallback to uploaded data if no database
        df_raw = hub.get_data("search_term_report")
        if df_raw is not None and not df_raw.empty:
             df = df_raw.copy()
             # Determine Min/Max Date from Data
             date_col = "Date" if "Date" in df.columns else None
             if date_col:
                 try:
                     df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
                     max_date = df[date_col].max().date()
                     min_date = df[date_col].min().date()
                 except:
                     pass

    # Initialize Session State for Dates if needed
    if "opt_start_date" not in st.session_state:
        # Default to Last 30 Days from Max Data Date
        st.session_state["opt_start_date"] = max(min_date, max_date - datetime.timedelta(days=30))
    if "opt_end_date" not in st.session_state:
        st.session_state["opt_end_date"] = max_date

    # --- CLAMP SESSION STATE TO VALID RANGE ---
    # This prevents StreamlitAPIException if the previous file had a wider range
    # or when switching accounts with different date ranges
    s_min, s_max = min_date, max_date
    if "opt_start_date" in st.session_state:
        if st.session_state["opt_start_date"] < s_min: st.session_state["opt_start_date"] = s_min
        if st.session_state["opt_start_date"] > s_max: st.session_state["opt_start_date"] = s_max
    if "opt_end_date" in st.session_state:
        if st.session_state["opt_end_date"] < s_min: st.session_state["opt_end_date"] = s_min
        if st.session_state["opt_end_date"] > s_max: st.session_state["opt_end_date"] = s_max
    # ------------------------------------------

    sel_start = st.session_state["opt_start_date"]
    sel_end = st.session_state["opt_end_date"]

    # 3. Configuration Section (Restored Date Pickers)
    c1, c2 = st.columns([1, 2])

    with c1:
        st.markdown("### Analysis Period")
        
        # Robust Date Pickers (Legacy Style)
        d_col1, d_col2 = st.columns(2)
        with d_col1:
            new_start = st.date_input(
                "Start Date",
                value=sel_start,
                min_value=s_min,
                max_value=s_max,
                key="picker_start"
            )
        with d_col2:
            new_end = st.date_input(
                "End Date",
                value=sel_end,
                min_value=s_min,
                max_value=s_max,
                key="picker_end"
            )
            
        # Update State
        st.session_state["opt_start_date"] = new_start
        st.session_state["opt_end_date"] = new_end
        
        # Update Locals for Filtering immediately
        sel_start = new_start
        sel_end = new_end
        
        data_days = (max_date - min_date).days
        st.caption(f"Data available: {min_date} to {max_date} ({data_days} days)")
        
    # Apply Filtering to Snapshot (using the calculated dates)
    if df is not None:
        calc_df = df
        if "Date" in df.columns:
            # Ensure Date column is datetime for proper filtering
            if not pd.api.types.is_datetime64_any_dtype(df["Date"]):
                df["Date"] = pd.to_datetime(df["Date"], errors='coerce')
            # Filter using date comparison
            calc_df = df[(df["Date"].dt.date >= sel_start) & (df["Date"].dt.date <= sel_end)]
        
        # Calculate Metrics
        currency = get_account_currency()
        spend_col = "Spend" if "Spend" in calc_df.columns else None
        sales_col = "7 Day Total Sales" if "7 Day Total Sales" in calc_df.columns else ("Sales" if "Sales" in calc_df.columns else None)

        if spend_col:
            total_spend = calc_df[spend_col].sum()
            if total_spend >= 100000:
                snap_spend = f"{currency}{total_spend/100000:.2f}L"
            elif total_spend >= 1000:
                snap_spend = f"{currency}{total_spend/1000:.1f}K"
            else:
                snap_spend = f"{currency}{total_spend:,.0f}"

        if spend_col and sales_col:
            total_sales = calc_df[sales_col].sum()
            if total_spend > 0:
                roas = total_sales / total_spend
                snap_roas = f"{roas:.2f}x"
            if total_sales > 0:
                acos = (total_spend / total_sales) * 100
                snap_acos = f"{acos:.1f}%"
        
        snap_terms = f"{len(calc_df):,}"

    # Render Snapshot Cards
    st.markdown(f"""
    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 48px;">
        <div class="snapshot-card">
            <div class="snapshot-label">Total Spend (Selected Period)</div>
            <div class="snapshot-value">{snap_spend}</div>
        </div>
        <div class="snapshot-card">
            <div class="snapshot-label">Current ROAS</div>
            <div class="snapshot-value" style="color: #2dd4bf;">{snap_roas}</div>
        </div>
        <div class="snapshot-card">
            <div class="snapshot-label">Current ACOS</div>
            <div class="snapshot-value">{snap_acos}</div>
        </div>
        <div class="snapshot-card">
            <div class="snapshot-label">Search Terms</div>
            <div class="snapshot-value">{snap_terms}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with c1:
         # Restore elements below date pickers
         st.markdown("### Simulation")
         st.toggle("Run Forecasting Simulation", value=True, key="opt_run_simulation",
                 help="Project impact of optimizations before applying")

    with c2:
        st.markdown("### Optimization Strategy")

        # Custom Preset Selector using Columns and Buttons/Clickable Divs
        # Since we can't easily make divs clickable in Streamlit without callbacks,
        # we'll use a hidden radio and visual cards, or Streamlit's new `pills` if available,
        # but for robustness we'll stick to a styled radio that LOOKS like cards,
        # or just standard radio for now but styled.
        # ALLOWED: "What you can change: Component layout... Visual hierarchy"

        preset_key = st.session_state.get("opt_profile", "balanced").capitalize()
        if preset_key not in ["Conservative", "Balanced", "Aggressive"]:
             preset_key = "Balanced"
             
        preset_choice = st.radio(
            "Strategy Preset",
            ["Conservative", "Balanced", "Aggressive"],
            index=["Conservative", "Balanced", "Aggressive"].index(preset_key),
            horizontal=True,
            label_visibility="collapsed",
            key="opt_profile_ui"
        )
        
        # Sync UI selection to Backend State (Lowercase)
        st.session_state["opt_profile"] = preset_choice.lower()

        # Update Descriptions based on new Reactivity Model
        if preset_choice == "Conservative":
            desc = "🛡️ **Conservative (Stable)**: Low reactivity. Slow bid changes, high harvest barriers. Protects profit."
        elif preset_choice == "Balanced":
            desc = "⚖️ **Balanced (Standard)**: Moderate reactivity. Standard PRD V2 continuous logic. Optimal risk-reward."
        elif preset_choice == "Aggressive":
            desc = "🚀 **Aggressive (Ruthless)**: High reactivity. Fast scaling up, fast cutting down. Maximizes velocity."
            
        st.info(desc)

    # 4. Advanced Settings (Collapsible)
    with st.expander("Advanced Configuration", expanded=False):
        st.markdown("Fine-tune specific thresholds and multipliers.")
        ac1, ac2, ac3 = st.columns(3)
        with ac1:
            st.number_input("Target ROAS", value=2.5, step=0.1, key="opt_target_roas_adv")
        with ac2:
            st.number_input("Max Bid Increase %", value=20, key="opt_max_bid_increase")
        with ac3:
            st.number_input("Harvest Click Threshold", value=10, key="opt_harvest_threshold")

    # 5. Primary CTA
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("⚡ Start Optimization", type="primary", use_container_width=True):
        st.session_state["run_optimizer_refactored"] = True
        st.rerun()
