"""
Client Report Page - Premium Dark Theme
========================================
Matches the main dashboard aesthetic with pure black background.
Glassmorphic cards, gradient accents, premium typography.
"""

import streamlit as st
from datetime import datetime
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import html
from features.assistant import AssistantModule
from features.executive_dashboard import ExecutiveDashboard
from features.report_card import ReportCardModule
from core.data_hub import DataHub
from utils.formatters import get_account_currency
from ui.theme import ThemeManager


def safe_html(text: str) -> str:
    """Escape HTML special characters in user/AI generated content."""
    if not text:
        return ""
    return html.escape(str(text))


# =============================================================================
# STYLES - Premium Dark Theme (Pure Black Background)
# =============================================================================

def inject_premium_styles():
    """
    Premium Dark Theme matching the main dashboard.
    Pure black background with glassmorphic cards.
    """
    st.markdown("""
    <style>
    /* ============================================
       TYPOGRAPHY & COLORS
       ============================================ */

    :root {
        --bg-pure-black: #000000;
        --bg-card: rgba(17, 24, 39, 0.6);
        --bg-card-hover: rgba(17, 24, 39, 0.8);
        --border-subtle: rgba(255, 255, 255, 0.08);
        --border-accent: rgba(255, 255, 255, 0.12);

        --text-primary: #f8fafc;
        --text-secondary: #94a3b8;
        --text-muted: #64748b;

        --accent-cyan: #06b6d4;
        --accent-blue: #3b82f6;
        --accent-purple: #8b5cf6;
        --accent-pink: #ec4899;
        --accent-amber: #f59e0b;
        --accent-emerald: #10b981;
        --accent-red: #ef4444;

        --gradient-rainbow: linear-gradient(90deg, #3b82f6, #8b5cf6, #ec4899, #f59e0b);
        --gradient-cyan: linear-gradient(135deg, rgba(6, 182, 212, 0.15) 0%, rgba(59, 130, 246, 0.08) 100%);

        /* System font stack - matches Executive Dashboard */
        --font-primary: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;

        --radius-sm: 8px;
        --radius-md: 12px;
        --radius-lg: 16px;
        --radius-xl: 20px;
    }

    /* ============================================
       GLOBAL STYLES
       ============================================ */

    @media screen {
        .stApp {
            background: var(--bg-pure-black) !important;
        }

        .main .block-container {
            max-width: 1400px;
            padding: 2rem 2.5rem 4rem 2.5rem;
        }

        header[data-testid="stHeader"],
        footer,
        #MainMenu {
            display: none !important;
        }

        /* Apply font to main app wrapper instead of global wildcard to protect icons */
        .stApp {
            font-family: var(--font-primary) !important;
        }
    }

    /* ============================================
       REPORT HEADER - Glassmorphic Card
       ============================================ */

    .report-header-card {
        background: var(--bg-card);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-xl);
        padding: 3rem 2.5rem;
        margin-bottom: 2rem;
        text-align: center;
        position: relative;
        overflow: hidden;
    }

    .report-header-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: var(--gradient-rainbow);
    }

    .report-title {
        font-family: var(--font-primary);
        font-size: 3rem;
        font-weight: 700;
        letter-spacing: -0.03em;
        background: linear-gradient(135deg, #F8FAFC 0%, #94A3B8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0 0 1.5rem 0;
        line-height: 1.1;
    }

    .report-meta-row {
        display: flex;
        justify-content: center;
        gap: 1rem;
        flex-wrap: wrap;
    }

    .meta-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.6rem 1.25rem;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid var(--border-subtle);
        border-radius: 50px;
        font-size: 0.9rem;
        color: var(--text-secondary);
    }

    .meta-badge .dot {
        width: 8px;
        height: 8px;
        background: var(--accent-emerald);
        border-radius: 50%;
    }



    /* ============================================
       SECTION HEADERS
       ============================================ */

    .section-header {
        display: flex;
        align-items: center;
        gap: 1rem;
        margin: 3rem 0 1.5rem 0;
    }

    .section-icon-box {
        width: 44px;
        height: 44px;
        background: var(--gradient-cyan);
        border: 1px solid rgba(6, 182, 212, 0.3);
        border-radius: var(--radius-md);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.25rem;
    }

    .section-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: var(--text-primary);
        margin: 0;
        letter-spacing: -0.01em;
    }

    /* ============================================
       AI INSIGHT CARDS - Cyan Gradient
       ============================================ */

    .ai-insight-card {
        background: linear-gradient(135deg, rgba(6, 182, 212, 0.18) 0%, rgba(59, 130, 246, 0.12) 100%);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(6, 182, 212, 0.3);
        border-top: 1px solid rgba(6, 182, 212, 0.5);
        border-left: 4px solid var(--accent-cyan);
        box-shadow: 0 8px 32px rgba(6, 182, 212, 0.15);
        border-radius: var(--radius-lg);
        padding: 1.5rem;
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
    }

    .ai-insight-card::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(120deg, rgba(255,255,255,0) 30%, rgba(255,255,255,0.05) 50%, rgba(255,255,255,0) 70%);
        pointer-events: none;
    }

    .ai-label {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: var(--accent-cyan);
        background: rgba(6, 182, 212, 0.15);
        padding: 0.3rem 0.75rem;
        border-radius: 50px;
        margin-bottom: 0.75rem;
    }

    .ai-content {
        font-size: 1rem;
        line-height: 1.7;
        color: var(--text-primary);
        margin: 0;
    }

    .ai-content strong {
        color: var(--accent-cyan);
    }

    /* ============================================
       EXECUTIVE SUMMARY CARDS
       ============================================ */

    .summary-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1.5rem;
        margin-bottom: 2rem;
    }

    .summary-card {
        background: var(--bg-card);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-lg);
        padding: 1.5rem;
        height: 100%;
        transition: all 0.2s ease;
    }

    .summary-card:hover {
        border-color: var(--border-accent);
        transform: translateY(-2px);
    }

    .summary-card.achievements {
        border-top: 3px solid var(--accent-emerald);
    }

    .summary-card.monitoring {
        border-top: 3px solid var(--accent-amber);
    }

    .summary-card.nextsteps {
        border-top: 3px solid var(--accent-blue);
    }

    .card-header {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 1.25rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }

    .card-icon {
        font-size: 1.25rem;
    }

    .card-title {
        font-size: 0.95rem;
        font-weight: 600;
        color: var(--text-primary);
        margin: 0;
    }

    .summary-item {
        padding: 0.75rem 0;
        padding-left: 1rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.03);
        font-size: 0.95rem;
        line-height: 1.5;
        color: var(--text-secondary);
    }

    .summary-item:last-child {
        border-bottom: none;
        padding-bottom: 0;
    }

    .summary-card.achievements .summary-item {
        border-left: 2px solid var(--accent-emerald);
    }

    .summary-card.monitoring .summary-item {
        border-left: 2px solid var(--accent-amber);
    }

    .summary-card.nextsteps .summary-item {
        border-left: 2px solid var(--accent-blue);
    }

    /* ============================================
       FOOTER
       ============================================ */

    .report-footer {
        text-align: center;
        padding: 2rem;
        margin-top: 3rem;
        border-top: 1px solid var(--border-subtle);
    }

    .footer-text {
        font-size: 0.85rem;
        color: var(--text-muted);
        margin: 0;
    }

    /* ============================================
       PRINT STYLES
       ============================================ */

    @media print {
        header, footer,
        .stApp > header,
        .stButton, .stSelectbox, .stTextInput,
        [data-testid="stSidebar"],
        [data-testid="stDecoration"],
        [data-testid="stStatusWidget"],
        .export-banner {
            display: none !important;
        }

        * {
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
        }

        .stApp, .main, body {
            background: white !important;
        }

        .main .block-container {
            max-width: 100% !important;
            padding: 0.5in !important;
        }

        .report-header-card,
        .ai-insight-card,
        .summary-card {
            background: #f8fafc !important;
            border: 1px solid #e2e8f0 !important;
            color: #1e293b !important;
        }

        .report-title,
        .section-title,
        .card-title {
            color: #1e293b !important;
        }

        .ai-content,
        .summary-item,
        .meta-badge {
            color: #475569 !important;
        }

        .section-header {
            page-break-before: always;
            margin-top: 1.5rem;
        }

        .section-header:first-of-type {
            page-break-before: avoid;
        }

        .ai-insight-card,
        .summary-card,
        .stPlotlyChart {
            page-break-inside: avoid;
        }
    }
    </style>
    """, unsafe_allow_html=True)


# =============================================================================
# COMPONENT RENDERERS
# =============================================================================

def render_header(date_range: str):
    """Render the report header."""
    current_time = datetime.now().strftime('%B %d, %Y at %I:%M %p')
    escaped_date = safe_html(date_range)

    st.markdown(f'''
    <div class="report-header-card">
        <h1 class="report-title">Account Performance Report</h1>
        <div class="report-meta-row">
            <span class="meta-badge">📅 {escaped_date}</span>
            <span class="meta-badge"><span class="dot"></span> Generated {current_time}</span>
        </div>
    </div>
    ''', unsafe_allow_html=True)





def render_section_header(icon: str, title: str):
    """Render a section header with icon."""
    st.markdown(f'''
    <div class="section-header">
        <div class="section-icon-box">{icon}</div>
        <h2 class="section-title">{safe_html(title)}</h2>
    </div>
    ''', unsafe_allow_html=True)


def render_ai_insight(narrative: str):
    """Render an AI insight card."""
    escaped_narrative = safe_html(narrative)
    st.markdown(f'''
    <div class="ai-insight-card">
        <div class="ai-label">🧠 AI Analysis</div>
        <p class="ai-content">{escaped_narrative}</p>
    </div>
    ''', unsafe_allow_html=True)


def render_executive_summary(summary: dict):
    """Render the executive summary cards."""
    achievements = summary.get("achievements", ["Analysis complete"])
    areas_to_watch = summary.get("areas_to_watch", ["Review dashboard for details"])
    next_steps = summary.get("next_steps", ["Continue monitoring"])

    col1, col2, col3 = st.columns(3)

    with col1:
        items_html = ''.join([f'<div class="summary-item">{safe_html(item)}</div>' for item in achievements])
        st.markdown(f'''
        <div class="summary-card achievements">
            <div class="card-header">
                <span class="card-icon">🏆</span>
                <h3 class="card-title">Key Achievements</h3>
            </div>
            {items_html}
        </div>
        ''', unsafe_allow_html=True)

    with col2:
        items_html = ''.join([f'<div class="summary-item">{safe_html(item)}</div>' for item in areas_to_watch])
        st.markdown(f'''
        <div class="summary-card monitoring">
            <div class="card-header">
                <span class="card-icon">👁️</span>
                <h3 class="card-title">Areas to Monitor</h3>
            </div>
            {items_html}
        </div>
        ''', unsafe_allow_html=True)

    with col3:
        items_html = ''.join([f'<div class="summary-item">{safe_html(item)}</div>' for item in next_steps])
        st.markdown(f'''
        <div class="summary-card nextsteps">
            <div class="card-header">
                <span class="card-icon">🎯</span>
                <h3 class="card-title">Recommended Next Steps</h3>
            </div>
            {items_html}
        </div>
        ''', unsafe_allow_html=True)


def render_footer():
    """Render the report footer."""
    st.markdown('''
    <div class="report-footer">
        <p class="footer-text">✨ Powered by SADDL AdPulse Decision Intelligence</p>
    </div>
    ''', unsafe_allow_html=True)


# =============================================================================
# ALIGNED RENDERERS (Custom for Report)
# =============================================================================

def _render_match_type_table_aligned(data: dict):
    """Render Match Type table with fixed height to align with chart."""
    # Header handled by section wrapper
    
    df = data['df_current'].copy()
    if df.empty:
        st.info("No data available.")
        return
    
    # Use Refined Match Type if available
    group_col = 'Refined Match Type' if 'Refined Match Type' in df.columns else 'Match Type'
    
    # Aggregate
    agg_cols = {'Spend': 'sum', 'Sales': 'sum', 'Orders': 'sum', 'Clicks': 'sum', 'Impressions': 'sum'}
    grouped = df.groupby(group_col).agg(agg_cols).reset_index()
    
    # Calculate metrics
    grouped['ACOS'] = np.where(grouped['Sales'] > 0, grouped['Spend'] / grouped['Sales'] * 100, 0)
    grouped['ROAS'] = np.where(grouped['Spend'] > 0, grouped['Sales'] / grouped['Spend'], 0)
    grouped['CTR'] = np.where(grouped['Impressions'] > 0, grouped['Clicks'] / grouped['Impressions'] * 100, 0)
    grouped['CVR'] = np.where(grouped['Clicks'] > 0, grouped['Orders'] / grouped['Clicks'] * 100, 0)
    grouped['CPC'] = np.where(grouped['Clicks'] > 0, grouped['Spend'] / grouped['Clicks'], 0)
    
    # Sort by Spend descending and remove empty rows
    grouped = grouped[grouped['Spend'] > 0]
    grouped = grouped.sort_values('Spend', ascending=False)
    
    # Display DataFrame with formatting AND FIXED HEIGHT
    currency = get_account_currency()
    st.dataframe(
        grouped,
        use_container_width=True,
        column_config={
            group_col: st.column_config.TextColumn("Match Type"),
            'Spend': st.column_config.NumberColumn(f"Spend", format=f"{currency} %.2f"),
            'Sales': st.column_config.NumberColumn(f"Sales", format=f"{currency} %.2f"),
            'Orders': st.column_config.NumberColumn("Orders", format="%d"),
            'Clicks': st.column_config.NumberColumn("Clicks", format="%d"),
            'Impressions': st.column_config.NumberColumn("Impressions", format="%d"),
            'ACOS': st.column_config.NumberColumn("ACOS", format="%.2f%%"),
            'ROAS': st.column_config.NumberColumn("ROAS", format="%.2fx"),
            'CTR': st.column_config.NumberColumn("CTR", format="%.2f%%"),
            'CVR': st.column_config.NumberColumn("CVR", format="%.2f%%"),
            'CPC': st.column_config.NumberColumn("CPC", format=f"{currency} %.2f"),
        },
        hide_index=True,
        height=450  # MATCHING CHART HEIGHT
    )

def _render_spend_breakdown_aligned(data: dict):
    """Render Spend Breakdown chart with fixed height to align with table."""
    # Self-contained logic from ExecutiveDashboard to ensure correct config
    
    df = data['df_current'].copy()
    if df.empty:
        st.info("No data available.")
        return

    # Use pre-calculated 'Refined Match Type' if available, otherwise fallback
    group_col = 'Refined Match Type' if 'Refined Match Type' in df.columns else 'Match Type'
    
    # Aggregate spend and sales
    breakdown = df.groupby(group_col).agg({'Spend': 'sum', 'Sales': 'sum'}).reset_index()
    total_spend = breakdown['Spend'].sum()
    total_sales = breakdown['Sales'].sum()
    
    # Calculate Percentages
    breakdown['Pct_Spend'] = (breakdown['Spend'] / total_spend * 100).fillna(0)
    breakdown['Pct_Sales'] = (breakdown['Sales'] / total_sales * 100).fillna(0)
    
    # Calculate Efficiency Ratio (Revenue % / Spend %)
    breakdown['Efficiency_Ratio'] = breakdown.apply(
        lambda x: x['Pct_Sales'] / x['Pct_Spend'] if x['Pct_Spend'] > 0 else 0, axis=1
    )
    
    # Filter out empty rows (Spend = 0) before sorting
    breakdown = breakdown[breakdown['Spend'] > 0]
    
    # Sort by Efficiency Ratio desc (visually top-down in Plotly requires ascending=True)
    breakdown = breakdown.sort_values('Efficiency_Ratio', ascending=True)
    
    # Colors (Hardcoded from dashboard premium palette to ensure match)
    COLORS = {
        'success': '#10B981', 'teal': '#14B8A6', 'warning': '#F59E0B', 'danger': '#EF4444', 'gray': '#6B7280'
    }

    def get_status(ratio):
        if ratio >= 1.0:
            return "Amplifier", COLORS['success']
        elif 0.75 <= ratio < 1.0:
            return "Balanced", COLORS['teal']
        elif 0.5 <= ratio < 0.75:
            return "Review", COLORS['warning']
        else:
            return "Drag", COLORS['danger']
    
    breakdown['Color'] = breakdown['Efficiency_Ratio'].apply(lambda x: get_status(x)[1])
    
    # Map nice display names for types
    type_names = {
        'AUTO': 'Auto', 'BROAD': 'Broad', 'PHRASE': 'Phrase', 
        'EXACT': 'Exact', 'PT': 'Product', 'CATEGORY': 'Category', 'OTHER': 'Other'
    }
    breakdown['DisplayName'] = breakdown[group_col].apply(lambda x: type_names.get(str(x).upper(), str(x).title()))
    
    # Horizontal Bar Chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=breakdown['DisplayName'],
        x=breakdown['Efficiency_Ratio'],
        orientation='h',
        marker_color=breakdown['Color'],
        text=breakdown['Efficiency_Ratio'].apply(lambda x: f"{x:.2f}x"),
        textposition='inside',
        insidetextanchor='end',
        textfont=dict(color='white', weight='bold'),
        hovertemplate=(
            "<b>%{y}</b><br>" +
            "Efficiency: <b>%{x:.2f}x</b><br>" +
            "Spend Share: %{customdata[0]:.1f}%<br>" +
            "Rev Share: %{customdata[1]:.1f}%<br>" +
            "<extra></extra>"
        ),
        customdata=breakdown[['Pct_Spend', 'Pct_Sales']]
    ))
    
    # Add Reference Line at 1.0 (Parity)
    fig.add_vline(x=1.0, line_width=1, line_dash="dash", line_color=COLORS['gray'], annotation_text="Parity (1.0)", annotation_position="top right")

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=450, # MATCHING TABLE HEIGHT
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis=dict(
            showgrid=True, 
            gridcolor='rgba(255,255,255,0.1)',
            title=dict(text="Efficiency Ratio (Rev % / Spend %)", font=dict(size=10, color='gray')),
            zeroline=False
        ),
        yaxis=dict(showgrid=False, tickfont=dict(color='rgba(255,255,255,0.8)')),
        uniformtext=dict(mode='hide', minsize=10)
    )
    
    st.plotly_chart(fig, use_container_width=True)


# =============================================================================
# MAIN RUN FUNCTION
# =============================================================================

def run():
    """
    Client Report Page - Premium Dark Theme
    """
    # Inject styles
    inject_premium_styles()

    # Initialize modules
    assistant = AssistantModule()
    exec_dash = ExecutiveDashboard()
    report_card = ReportCardModule()

    # Generate narratives - Cache in session state
    cache_key = f"client_report_narratives_{st.session_state.get('active_account_id', 'default')}"

    if cache_key not in st.session_state:
        panels_to_generate = [
            "performance",
            "health",
            "portfolio",
            "impact",
            "actions",
            "match_type",
            "executive_summary"
        ]

        with st.spinner("Generating AI insights..."):
            narratives = assistant.generate_report_narratives(panels_to_generate)
            st.session_state[cache_key] = narratives
    else:
        narratives = st.session_state[cache_key]

    # Fetch visual data
    with st.spinner("Loading visual data..."):
        exec_data = exec_dash._fetch_data()
        
        # --- DATE RANGE FIX ---
        # Calculate date range from data if available, falling back to session/default
        date_str = "Period Unknown"
        if exec_data and 'date_range' in exec_data:
            dr = exec_data['date_range']
            if dr.get('start') and dr.get('end'):
                s = pd.to_datetime(dr['start']).strftime('%b %d')
                e = pd.to_datetime(dr['end']).strftime('%b %d, %Y')
                date_str = f"{s} – {e}"
        # ----------------------

        hub = DataHub()
        rc_df = hub.get_enriched_data()
        if rc_df is None:
            rc_df = hub.get_data("search_term_report")

        rc_metrics = None
        if rc_df is not None:
            rc_metrics = report_card.analyze(rc_df)

    if not exec_data:
        st.warning("Data analysis pending. Please ensure data is loaded.")
        return

    # Render header with DYNAMIC DATE
    render_header(date_str)

    # =========================================================================
    # EXECUTIVE SUMMARY
    # =========================================================================
    render_section_header('⭐', 'Executive Summary')
    render_executive_summary(narratives.get("executive_summary", {}))

    # =========================================================================
    # PERFORMANCE OVERVIEW
    # =========================================================================
    render_section_header('📈', 'Performance Overview')
    render_ai_insight(narratives.get("performance", "Analysis in progress..."))
    exec_dash._render_kpi_cards(exec_data)

    # =========================================================================
    # ACCOUNT HEALTH
    # =========================================================================
    render_section_header('💚', 'Account Health')
    render_ai_insight(narratives.get("health", "Analysis in progress..."))
    exec_dash._render_gauges(exec_data)

    # =========================================================================
    # PORTFOLIO ANALYSIS
    # =========================================================================
    render_section_header('📊', 'Portfolio Analysis')
    render_ai_insight(narratives.get("portfolio", "Analysis in progress..."))

    c1, c2 = st.columns([7, 3])
    with c1:
        exec_dash._render_performance_scatter(exec_data)
    with c2:
        exec_dash._render_quadrant_donut(exec_data)

    # =========================================================================
    # DECISION IMPACT
    # =========================================================================
    render_section_header('⚡', 'Decision Impact')
    render_ai_insight(narratives.get("impact", "Analysis in progress..."))

    c1, c2 = st.columns([3, 7])
    with c1:
        exec_dash._render_decision_impact_card(exec_data)
    with c2:
        exec_dash._render_decision_timeline(exec_data)

    # =========================================================================
    # MATCH TYPE PERFORMANCE (ALIGNED)
    # =========================================================================
    render_section_header('🎯', 'Match Type Performance')
    render_ai_insight(narratives.get("match_type", "Analysis in progress..."))

    c1, c2 = st.columns([7, 3])
    with c1:
        # Use local ALIGNED renderer
        _render_match_type_table_aligned(exec_data)
    with c2:
        # Use local ALIGNED renderer
        _render_spend_breakdown_aligned(exec_data)

    # =========================================================================
    # ACTIONS & RESULTS
    # =========================================================================
    render_section_header('🏆', 'Actions & Results')
    render_ai_insight(narratives.get("actions", "Analysis in progress..."))

    if rc_metrics:
        report_card._render_section_2_actions(rc_metrics)
    else:
        st.info("No detailed action data available.")

    # =========================================================================
    # FOOTER
    # =========================================================================
    render_footer()


if __name__ == "__main__":
    run()
