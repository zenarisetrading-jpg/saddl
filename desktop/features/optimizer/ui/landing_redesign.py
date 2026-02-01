import streamlit as st
import datetime
import pandas as pd
from typing import Optional

@st.cache_data(ttl=300, show_spinner=False)
def _fetch_target_stats_cached(client_id: str, test_mode: bool):
    """Cache database query for target stats - prevents repeated DB calls on every rerun."""
    from core.db_manager import get_db_manager
    db_manager = get_db_manager(test_mode)
    if db_manager and client_id:
        return db_manager.get_target_stats_df(client_id)
    return None

def render_landing_page_redesign(config: dict):
    """
    Redesigned optimizer landing page matching Report Studio quality.
    Clean, professional, minimal UI with clear action flow.
    """

    # === INJECT PREMIUM STYLES ===
    st.markdown("""
    <style>
    /* Premium Landing Page Styles */
    .optimizer-studio-hero {
        text-align: center;
        padding: 60px 20px 40px 20px;
        margin-bottom: 40px;
    }

    .optimizer-studio-hero h1 {
        font-size: 3rem;
        font-weight: 700;
        margin-bottom: 16px;
        background: linear-gradient(135deg, #F5F5F7 0%, #22D3EE 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.02em;
    }

    .optimizer-studio-hero p {
        font-size: 1.1rem;
        color: #94a3b8;
        max-width: 600px;
        margin: 0 auto;
        line-height: 1.6;
    }

    /* Premium Cards */
    .studio-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%);
        border: 1px solid rgba(148, 163, 184, 0.15);
        border-radius: 16px;
        padding: 32px;
        margin-bottom: 24px;
        backdrop-filter: blur(10px);
    }

    .studio-card h3 {
        font-size: 1rem;
        font-weight: 600;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 24px;
        display: flex;
        align-items: center;
        gap: 12px;
    }

    /* Strategy Selector */
    .strategy-grid {
        display: grid;
        gap: 16px;
        margin-bottom: 24px;
    }

    .strategy-option {
        background: rgba(30, 41, 59, 0.5);
        border: 2px solid rgba(148, 163, 184, 0.15);
        border-radius: 12px;
        padding: 20px;
        cursor: pointer;
        transition: all 0.3s ease;
    }

    .strategy-option:hover {
        border-color: rgba(34, 211, 238, 0.5);
        background: rgba(30, 41, 59, 0.8);
    }

    .strategy-option.selected {
        border-color: #22D3EE;
        background: rgba(34, 211, 238, 0.1);
    }

    .strategy-label {
        font-size: 1.1rem;
        font-weight: 600;
        color: #F5F5F7;
        margin-bottom: 8px;
    }

    .strategy-desc {
        font-size: 0.9rem;
        color: #94a3b8;
        line-height: 1.5;
    }

    /* Feature Grid */
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 20px;
        margin: 40px 0;
    }

    .feature-card {
        background: rgba(30, 41, 59, 0.4);
        border: 1px solid rgba(148, 163, 184, 0.1);
        border-radius: 12px;
        padding: 24px;
        text-align: center;
    }

    .feature-icon {
        font-size: 2rem;
        margin-bottom: 12px;
    }

    .feature-title {
        font-size: 1rem;
        font-weight: 600;
        color: #F5F5F7;
        margin-bottom: 8px;
    }

    .feature-desc {
        font-size: 0.85rem;
        color: #94a3b8;
        line-height: 1.4;
    }
    </style>
    """, unsafe_allow_html=True)

    # === HERO SECTION ===
    st.markdown("""
    <div class="optimizer-studio-hero">
        <h1>PPC Optimizer Studio</h1>
        <p>AI-driven bid management & harvest intelligence to maximize ROAS and reduce wasted spend.</p>
    </div>
    """, unsafe_allow_html=True)

    # === FETCH DATA ===
    from core.data_hub import DataHub
    hub = DataHub()

    client_id = st.session_state.get('active_account_id')
    test_mode = st.session_state.get('test_mode', False)

    # Data Constraints
    max_date = datetime.date.today()
    min_date = max_date - datetime.timedelta(days=60)
    df = None

    # Fetch from database
    if client_id:
        db_df = _fetch_target_stats_cached(client_id, test_mode)
        if db_df is not None and not db_df.empty:
            df = db_df.copy()
            if 'Date' in df.columns:
                try:
                    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                    min_date = df['Date'].min().date()
                    max_date = df['Date'].max().date() + datetime.timedelta(days=6)
                except:
                    pass

    # Initialize session state for dates
    if "opt_start_date" not in st.session_state:
        st.session_state["opt_start_date"] = max(min_date, max_date - datetime.timedelta(days=30))
    if "opt_end_date" not in st.session_state:
        st.session_state["opt_end_date"] = max_date

    # Clamp to valid range
    s_min, s_max = min_date, max_date
    if st.session_state["opt_start_date"] < s_min:
        st.session_state["opt_start_date"] = s_min
    if st.session_state["opt_start_date"] > s_max:
        st.session_state["opt_start_date"] = s_max
    if st.session_state["opt_end_date"] < s_min:
        st.session_state["opt_end_date"] = s_min
    if st.session_state["opt_end_date"] > s_max:
        st.session_state["opt_end_date"] = s_max

    # === MAIN CONFIGURATION ===
    col1, col2 = st.columns([1.5, 1])

    with col1:
        # Analysis Period Card
        st.markdown('<div class="studio-card">', unsafe_allow_html=True)
        st.markdown('<h3>📅 Analysis Period</h3>', unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            st.date_input(
                "Start Date",
                value=st.session_state["opt_start_date"],
                min_value=s_min,
                max_value=s_max,
                key="opt_start_date",
                label_visibility="visible"
            )
        with c2:
            st.date_input(
                "End Date",
                value=st.session_state["opt_end_date"],
                min_value=s_min,
                max_value=s_max,
                key="opt_end_date",
                label_visibility="visible"
            )

        # Show data range
        if df is not None and not df.empty:
            days_span = (st.session_state["opt_end_date"] - st.session_state["opt_start_date"]).days + 1
            st.caption(f"Analyze data relative to today (Feb 01). Data available: {min_date} to {max_date} ({days_span} days selected)")

        st.markdown('</div>', unsafe_allow_html=True)

        # Optimization Strategy Card
        st.markdown('<div class="studio-card">', unsafe_allow_html=True)
        st.markdown('<h3>⚙️ Optimization Strategy</h3>', unsafe_allow_html=True)

        # Strategy selector using columns
        col_cons, col_bal, col_agg = st.columns(3)

        current_profile = st.session_state.get("opt_profile", "balanced")

        with col_cons:
            if st.button(
                "🛡️ Conservative",
                use_container_width=True,
                type="primary" if current_profile == "conservative" else "secondary",
                key="btn_conservative"
            ):
                st.session_state["opt_profile"] = "conservative"
                st.rerun()

        with col_bal:
            if st.button(
                "⚖️ Balanced",
                use_container_width=True,
                type="primary" if current_profile == "balanced" else "secondary",
                key="btn_balanced"
            ):
                st.session_state["opt_profile"] = "balanced"
                st.rerun()

        with col_agg:
            if st.button(
                "🚀 Aggressive",
                use_container_width=True,
                type="primary" if current_profile == "aggressive" else "secondary",
                key="btn_aggressive"
            ):
                st.session_state["opt_profile"] = "aggressive"
                st.rerun()

        # Strategy description
        strategy_descs = {
            "conservative": "Minimal reactivity. Gentle PRD V2 continuous logic. Low risk tolerance.",
            "balanced": "Moderate reactivity. Standard PRD V2 continuous logic. Optimal risk-reward.",
            "aggressive": "High reactivity. Faster adaptation. Higher risk tolerance for growth."
        }

        st.markdown(
            f"<p style='color: #94a3b8; font-size: 0.9rem; margin-top: 12px;'>"
            f"<strong style='color: #22D3EE;'>{current_profile.title()} (Standard):</strong> "
            f"{strategy_descs.get(current_profile, '')}</p>",
            unsafe_allow_html=True
        )

        st.markdown('</div>', unsafe_allow_html=True)

        # Simulation Toggle
        st.markdown('<div class="studio-card">', unsafe_allow_html=True)
        st.markdown('<h3>🔮 Simulation</h3>', unsafe_allow_html=True)

        st.toggle(
            "Run Forecasting Simulation",
            value=st.session_state.get("opt_test_mode", False),
            key="opt_test_mode",
            help="Generate what-if scenarios to preview optimization impact"
        )

        if df is not None and not df.empty:
            # Show current metrics
            filtered_df = df[
                (df['Date'].dt.date >= st.session_state["opt_start_date"]) &
                (df['Date'].dt.date <= st.session_state["opt_end_date"])
            ]

            if not filtered_df.empty and 'Spend' in filtered_df.columns:
                from utils.formatters import get_account_currency, format_currency
                currency = get_account_currency()

                total_spend = filtered_df['Spend'].sum()
                total_sales = filtered_df['Sales'].sum() if 'Sales' in filtered_df.columns else 0
                current_roas = total_sales / total_spend if total_spend > 0 else 0
                current_acos = (total_spend / total_sales * 100) if total_sales > 0 else 0
                num_terms = len(filtered_df)

                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Total Spend", format_currency(total_spend, currency))
                c2.metric("Current ROAS", f"{current_roas:.2f}x")
                c3.metric("Current ACOS", f"{current_acos:.1f}%")
                c4.metric("Search Terms", f"{num_terms:,}")

        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        # Action Card
        st.markdown('<div class="studio-card">', unsafe_allow_html=True)
        st.markdown('<h3>🎯 Ready to Optimize</h3>', unsafe_allow_html=True)

        st.markdown("""
        <p style="color: #94a3b8; margin-bottom: 24px;">
        Start the AI analysis to identify bid adjustments, harvest opportunities, and negative keywords.
        </p>
        """, unsafe_allow_html=True)

        if st.button(
            "⚡ Start Optimization",
            type="primary",
            use_container_width=True,
            key="btn_run_optimizer_studio"
        ):
            st.session_state["run_optimizer_refactored"] = True
            st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

        # Advanced Configuration (Collapsed)
        with st.expander("▸ Advanced Configuration"):
            st.number_input(
                "Target ROAS",
                min_value=1.0,
                max_value=10.0,
                value=float(st.session_state.get("opt_target_roas", 2.5)),
                step=0.1,
                key="opt_target_roas",
                help="Target return on ad spend"
            )

            st.number_input(
                "Negative Clicks Threshold",
                min_value=1,
                max_value=50,
                value=int(st.session_state.get("opt_neg_clicks_threshold", 10)),
                step=1,
                key="opt_neg_clicks_threshold",
                help="Minimum clicks before considering negative keyword"
            )

    # === FEATURE HIGHLIGHTS ===
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
    <div class="feature-grid">
        <div class="feature-card">
            <div class="feature-icon">🤖</div>
            <div class="feature-title">AI Powered</div>
            <div class="feature-desc">Machine learning algorithms analyze patterns and predict optimal bid adjustments</div>
        </div>
        <div class="feature-card">
            <div class="feature-icon">📊</div>
            <div class="feature-title">Impact Tracking</div>
            <div class="feature-desc">Visualize the ROI of your optimizer decisions with before/after validation</div>
        </div>
        <div class="feature-card">
            <div class="feature-icon">⚡</div>
            <div class="feature-title">Real-time Analysis</div>
            <div class="feature-desc">Process thousands of keywords in seconds with intelligent prioritization</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
