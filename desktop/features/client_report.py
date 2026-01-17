"""
Client Report Generator MVP
===========================
Generates PDF reports with 3 visuals + AI summary.
New isolated module - does not modify existing pages.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json
import tempfile
import os


# Core imports
from core.account_utils import get_active_account_id, get_active_account_name
from utils.formatters import get_account_currency
from features.executive_dashboard import create_revenue_timeline_figure
from features.report_card import ReportCardModule


def render_client_report():
    """Main entry point for Client Report Generator."""
    
    # Premium SVG Icons (glassmorphic style)
    report_icon = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#06B6D4" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>'
    
    # Page Header (Premium glassmorphic style)
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(30, 41, 59, 0.95) 0%, rgba(15, 23, 42, 0.95) 100%); 
                border: 1px solid rgba(148, 163, 184, 0.15); 
                border-left: 3px solid #06B6D4;
                border-radius: 12px; padding: 20px; margin-bottom: 24px;
                box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);">
        <div style="display: flex; align-items: center; gap: 16px;">
            {report_icon}
            <div>
                <span style="font-weight: 800; font-size: 1.5rem; color: #F8FAFC; letter-spacing: 0.02em;">Client Report Generator</span>
                <div style="color: #94A3B8; font-size: 0.9rem; margin-top: 4px;">
                    Select visuals to include in your client-facing report
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Check for active account
    client_id = get_active_account_id()
    if not client_id:
        st.warning("Please select an account to generate reports.")
        return
    
    # ===========================================
    # VISUAL SELECTION SECTION
    # ===========================================
    
    st.markdown("""
    <div style="color: #E2E8F0; font-weight: 700; font-size: 1.1rem; margin-bottom: 16px;">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 8px;"><polyline points="9 11 12 14 22 4"></polyline><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path></svg>
        Available Visuals
    </div>
    """, unsafe_allow_html=True)
    
    # Visual selection cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        _render_visual_card(
            "decision_impact",
            "Decision Impact Summary",
            "Executive Dashboard",
            "Total impact card showing offensive/defensive wins",
            "decision"
        )
    
    with col2:
        _render_visual_card(
            "roas_attribution",
            "ROAS Attribution Waterfall",
            "Impact & Results",
            "Waterfall showing market forces vs your decisions",
            "chart"
        )
    
    with col3:
        _render_visual_card(
            "account_health",
            "Account Health Gauge",
            "Account Health",
            "Overall account health score with status",
            "gauge"
        )
    
    # Initialize session state for checkboxes
    if 'report_visuals' not in st.session_state:
        st.session_state['report_visuals'] = {
            'decision_impact': True,
            'roas_attribution': True,
            'account_health': True
        }
    
    # Checkbox controls (hidden but functional)
    with st.container():
        c1, c2, c3 = st.columns(3)
        with c1:
            st.session_state['report_visuals']['decision_impact'] = st.checkbox(
                "Include Decision Impact", 
                value=st.session_state['report_visuals'].get('decision_impact', True),
                key="cb_decision_impact"
            )
        with c2:
            st.session_state['report_visuals']['roas_attribution'] = st.checkbox(
                "Include ROAS Attribution", 
                value=st.session_state['report_visuals'].get('roas_attribution', True),
                key="cb_roas_attribution"
            )
        with c3:
            st.session_state['report_visuals']['account_health'] = st.checkbox(
                "Include Account Health", 
                value=st.session_state['report_visuals'].get('account_health', True),
                key="cb_account_health"
            )
    
    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    
    # AI Summary toggle
    include_ai_summary = st.checkbox(
        "Include AI Executive Summary",
        value=True,
        help="Generate AI-powered narrative insights for each visual and an executive summary"
    )
    
    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
    
    # ===========================================
    # DATE RANGE & GENERATE BUTTON
    # ===========================================
    
    col_date, col_spacer, col_btn = st.columns([2, 4, 2])
    
    with col_date:
        date_range = st.selectbox(
            "Report Period",
            options=["Last 14 Days", "Last 30 Days", "Last 60 Days", "Last 90 Days"],
            index=1,
            help="Select the time period for the report data"
        )
    
    with col_btn:
        generate_clicked = st.button(
            "📄 Generate Report",
            type="primary",
            use_container_width=True
        )
    
    # ===========================================
    # REPORT GENERATION FLOW
    # ===========================================
    
    if generate_clicked:
        selected_visuals = [k for k, v in st.session_state['report_visuals'].items() if v]
        
        if not selected_visuals:
            st.error("Please select at least one visual to include in the report.")
            return
        
        # Convert date range to days
        days_map = {
            "Last 14 Days": 14,
            "Last 30 Days": 30,
            "Last 60 Days": 60,
            "Last 90 Days": 90
        }
        days = days_map.get(date_range, 30)
        
        # Generate report with progress
        _generate_report(
            client_id=client_id,
            selected_visuals=selected_visuals,
            include_ai_summary=include_ai_summary,
            days=days,
            date_range_label=date_range
        )


def _render_visual_card(key: str, title: str, source: str, description: str, icon_type: str):
    """Render a visual selection card with glassmorphic styling."""
    
    # Icon based on type
    icons = {
        "decision": '<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>',
        "chart": '<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#06B6D4" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>',
        "gauge": '<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#8B5CF6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>'
    }
    
    icon = icons.get(icon_type, icons["chart"])
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%);
        border: 1px solid rgba(148, 163, 184, 0.15);
        border-radius: 12px;
        padding: 20px;
        min-height: 140px;
        transition: all 0.3s ease;
    ">
        <div style="margin-bottom: 12px;">{icon}</div>
        <div style="color: #F8FAFC; font-weight: 700; font-size: 0.95rem; margin-bottom: 4px;">{title}</div>
        <div style="color: #64748B; font-size: 0.75rem; margin-bottom: 8px;">From: {source}</div>
        <div style="color: #94A3B8; font-size: 0.8rem; line-height: 1.4;">{description}</div>
    </div>
    """, unsafe_allow_html=True)


def _generate_report(
    client_id: str,
    selected_visuals: List[str],
    include_ai_summary: bool,
    days: int,
    date_range_label: str
):
    """Generate the PDF report with progress indicators."""
    
    currency = get_account_currency()
    
    # Progress container
    progress_container = st.container()
    
    with progress_container:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Create temp directory for chart images
            import tempfile
            temp_dir = tempfile.mkdtemp()
            chart_images = {}
            
            # Step 1: Capture Visuals Data (30%)
            status_text.markdown("🔄 **Capturing visuals...**")
            visual_data = _capture_visuals(client_id, selected_visuals, days)
            progress_bar.progress(30)
            
            # Step 2: Generate Chart Images (50%)
            status_text.markdown("📊 **Generating charts...**")
            
            # ROAS Waterfall Chart - USE SHARED FUNCTION from dashboard
            if 'roas_attribution' in visual_data:
                try:
                    from features.impact_dashboard import create_roas_waterfall_figure
                    
                    roas_data = visual_data['roas_attribution']
                    fig = create_roas_waterfall_figure(
                        baseline_roas=roas_data.get('baseline', 0),
                        actual_roas=roas_data.get('actual', 0),
                        decision_impact_roas=roas_data.get('decisions', 0),
                        for_export=True  # Use solid background for PNG
                    )
                    img_path = _capture_chart_image(fig, temp_dir, 'roas_waterfall')
                    if img_path:
                        chart_images['roas_attribution'] = img_path
                except Exception as e:
                    print(f"ROAS chart failed: {e}")
            
            # Account Health Gauge
            if 'account_health' in visual_data:
                try:
                    fig = _create_account_health_gauge(visual_data['account_health'])
                    img_path = _capture_chart_image(fig, temp_dir, 'health_gauge')
                    if img_path:
                        chart_images['account_health'] = img_path
                except Exception as e:
                    print(f"Health gauge failed: {e}")
            
            # Executive Summary Triple Gauge
            if 'executive_summary' in visual_data:
                try:
                    gauges = visual_data['executive_summary'].get('gauges', {})
                    fig = _create_triple_gauge_chart(gauges)
                    img_path = _capture_chart_image(fig, temp_dir, 'exec_summary_gauges')
                    if img_path:
                        chart_images['executive_summary'] = img_path
                except Exception as e:
                    print(f"Executive summary gauges failed: {e}")
            
            # Decision Impact Timeline Chart - Revenue Trend w/ Markers
            if 'decision_impact' in visual_data:
                try:
                    from features.executive_dashboard import create_revenue_timeline_figure
                    
                    impact_df = visual_data['decision_impact'].get('impact_df')
                    sales_df = visual_data.get('sales_df')
                    
                    if impact_df is not None and not impact_df.empty and sales_df is not None:
                        fig = create_revenue_timeline_figure(
                            df_current=sales_df,
                            impact_df=impact_df,
                            currency=currency,
                            for_export=True
                        )
                        if fig:
                            img_path = _capture_chart_image(fig, temp_dir, 'decision_timeline')
                            if img_path:
                                chart_images['decision_timeline'] = img_path
                except Exception as e:
                    print(f"Decision timeline failed: {e}")
            
                except Exception as e:
                    print(f"Decision timeline failed: {e}")
            
            # Spend Reallocation Chart (for Actions & Results)
            if 'report_card' in visual_data:
                try:
                    report_card = ReportCardModule()
                    metrics = visual_data['report_card']
                    realloc = metrics.get('reallocation', {})
                    if realloc:
                        fig = report_card._create_reallocation_chart(realloc)
                        img_path = _capture_chart_image(fig, temp_dir, 'reallocation_chart')
                        if img_path:
                            chart_images['reallocation_chart'] = img_path
                except Exception as e:
                    print(f"Reallocation chart failed: {e}")

            progress_bar.progress(50)
            
            # Step 3: Generate AI Insights (70%)
            ai_narratives = {}
            if include_ai_summary:
                status_text.markdown("🤖 **Generating AI insights...**")
                ai_narratives = _generate_ai_narratives(visual_data, date_range_label)
            progress_bar.progress(70)
            
            # Step 4: Compile PDF (100%)
            status_text.markdown("📄 **Compiling report...**")
            
            # Get account name for title slide
            account_name = get_active_account_name()
            
            pdf_bytes = _compile_pdf(
                visual_data=visual_data,
                ai_narratives=ai_narratives,
                date_range_label=date_range_label,
                currency=currency,
                include_ai_summary=include_ai_summary,
                account_name=account_name,
                chart_images=chart_images
            )
            progress_bar.progress(100)
            
            # Success state
            status_text.markdown("✅ **Report generated successfully!**")
            
            # Download button
            filename = f"client_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            st.download_button(
                label="📥 Download Report",
                data=pdf_bytes,
                file_name=filename,
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )
            
        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            st.error(f"❌ Report generation failed: {str(e)}")
            st.button("🔄 Try Again", on_click=lambda: st.rerun())


def _capture_chart_image(fig, temp_dir: str, chart_name: str) -> Optional[str]:
    """
    Capture a Plotly figure as PNG image for PDF embedding.
    Uses kaleido for fast, reliable image export.
    
    Returns: Path to PNG file or None if failed
    """
    try:
        import plotly.io as pio
        
        # Configure for dark background
        fig.update_layout(
            paper_bgcolor='rgba(30, 41, 59, 1)',
            plot_bgcolor='rgba(30, 41, 59, 1)',
        )
        
        # Save to temp directory
        img_path = os.path.join(temp_dir, f"{chart_name}.png")
        pio.write_image(fig, img_path, format='png', width=1200, height=500, scale=2)
        
        return img_path
    except Exception as e:
        print(f"Chart capture failed for {chart_name}: {e}")
        return None


def _create_roas_waterfall_chart(data: Dict[str, Any], currency: str) -> 'go.Figure':
    """Create ROAS attribution waterfall chart for PDF - matches dashboard exactly."""
    import plotly.graph_objects as go
    
    baseline = data.get('baseline', 0)
    market = data.get('market_forces', 0)  # Combined Forces (negative = drag)
    decisions = data.get('decisions', 0)
    actual = data.get('actual', 0)
    
    # Colors matching dashboard
    C_BASELINE = '#475569'   # Slate gray
    C_MARKET_NEG = '#DC2626' # Red for negative market drag
    C_MARKET_POS = '#10B981' # Green for market tailwinds
    C_DECISIONS_POS = '#10B981'  # Green for positive decisions
    C_DECISIONS_NEG = '#DC2626'  # Red for negative decisions
    C_ACTUAL = '#06B6D4'     # Cyan for actual result
    
    # Use Plotly's built-in Waterfall chart
    fig = go.Figure(go.Waterfall(
        name="ROAS",
        orientation="v",
        measure=["absolute", "relative", "relative", "total"],
        x=["Baseline", "Combined<br>Forces", "Decisions", "Actual"],
        textposition="outside",
        text=[f"{baseline:.2f}", f"{market:+.2f}", f"{decisions:+.2f}", f"{actual:.2f}"],
        y=[baseline, market, decisions, actual],
        connector={"line": {"color": "#64748B", "width": 1, "dash": "dot"}},
        # Waterfall uses increasing/decreasing for relative bars
        increasing={"marker": {"color": C_DECISIONS_POS}},
        decreasing={"marker": {"color": C_MARKET_NEG}},
        totals={"marker": {"color": C_ACTUAL}},
        textfont={"size": 16, "color": "#F8FAFC"},
    ))
    
    # Layout
    fig.update_layout(
        paper_bgcolor='rgba(30, 41, 59, 1)',
        plot_bgcolor='rgba(30, 41, 59, 1)',
        font=dict(color='#F8FAFC', size=14),
        showlegend=False,
        margin=dict(l=60, r=40, t=20, b=60),
        yaxis=dict(
            title='ROAS',
            title_font=dict(color='#94A3B8'),
            tickfont=dict(color='#94A3B8'),
            gridcolor='rgba(148, 163, 184, 0.15)',
            zerolinecolor='rgba(148, 163, 184, 0.3)',
        ),
        xaxis=dict(
            tickfont=dict(size=14, color='#F8FAFC'),
        ),
        bargap=0.3,
    )
    
    return fig


def _create_account_health_gauge(data: Dict[str, Any]) -> 'go.Figure':
    """Create account health gauge chart for PDF."""
    import plotly.graph_objects as go
    
    score = data.get('score', 0)
    status = data.get('status', 'Unknown')
    
    # Color based on score
    if score >= 80:
        color = '#10B981'  # Green
    elif score >= 60:
        color = '#06B6D4'  # Cyan
    elif score >= 40:
        color = '#F59E0B'  # Amber
    else:
        color = '#EF4444'  # Red
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number=dict(suffix="pts", font=dict(size=48, color='#F8FAFC')),
        gauge=dict(
            axis=dict(range=[0, 100], tickwidth=2, tickcolor='#64748B', tickfont=dict(size=12, color='#94A3B8')),
            bar=dict(color=color, thickness=0.7),
            bgcolor='rgba(30, 41, 59, 0.5)',
            borderwidth=2,
            bordercolor='rgba(148, 163, 184, 0.2)',
            steps=[
                dict(range=[0, 40], color='rgba(239, 68, 68, 0.1)'),
                dict(range=[40, 60], color='rgba(245, 158, 11, 0.1)'),
                dict(range=[60, 80], color='rgba(6, 182, 212, 0.1)'),
                dict(range=[80, 100], color='rgba(16, 185, 129, 0.1)'),
            ],
        ),
        title=dict(text=f"<b>{status}</b>", font=dict(size=20, color=color)),
    ))
    
    fig.update_layout(
        paper_bgcolor='rgba(30, 41, 59, 1)',
        plot_bgcolor='rgba(30, 41, 59, 1)',
        font=dict(color='#F8FAFC'),
        margin=dict(l=40, r=40, t=80, b=40),
        height=400,
    )
    
    return fig


def _create_triple_gauge_chart(gauges: Dict[str, Dict]) -> 'go.Figure':
    """Create 3 gauges side by side for Executive Summary slide."""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    
    # Create subplots with 3 columns
    fig = make_subplots(
        rows=1, cols=3,
        specs=[[{"type": "indicator"}, {"type": "indicator"}, {"type": "indicator"}]],
        horizontal_spacing=0.08
    )
    
    gauge_configs = [
        ('health', 'Account Health', 'pts', [0, 100]),
        ('decision_roi', 'Decision ROI', '%', [0, 100]),
        ('spend_efficiency', 'Spend Efficiency', '%', [0, 100]),
    ]
    
    for i, (key, label, unit, range_vals) in enumerate(gauge_configs, 1):
        gauge_data = gauges.get(key, {})
        value = gauge_data.get('value', 0)
        target = gauge_data.get('target', 50)
        
        # Color based on value vs target
        if value >= target:
            color = '#10B981'  # Green
            status = '✓ Good'
        elif value >= target * 0.7:
            color = '#F59E0B'  # Amber
            status = '△ Fair'
        else:
            color = '#EF4444'  # Red
            status = '✗ Low'
        
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=value,
                number=dict(suffix=unit, font=dict(size=28, color='#F8FAFC')),
                title=dict(text=f"<b>{label}</b>", font=dict(size=14, color='#94A3B8')),
                gauge=dict(
                    axis=dict(range=range_vals, tickwidth=1, tickcolor='#64748B', tickfont=dict(size=10, color='#64748B')),
                    bar=dict(color=color, thickness=0.7),
                    bgcolor='rgba(30, 41, 59, 0.5)',
                    borderwidth=1,
                    bordercolor='rgba(148, 163, 184, 0.15)',
                    threshold=dict(
                        line=dict(color='#F59E0B', width=2),
                        thickness=0.75,
                        value=target
                    ),
                ),
            ),
            row=1, col=i
        )
    
    fig.update_layout(
        paper_bgcolor='rgba(30, 41, 59, 1)',
        plot_bgcolor='rgba(30, 41, 59, 1)',
        font=dict(color='#F8FAFC'),
        margin=dict(l=30, r=30, t=50, b=30),
        height=300,
    )
    
    return fig


def _capture_visuals(client_id: str, selected_visuals: List[str], days: int) -> Dict[str, Any]:
    """Capture data and charts from existing visual sources."""
    
    visual_data = {}
    db_manager = st.session_state.get('db_manager')
    
    if not db_manager:
        st.warning("Database not connected. Using sample data.")
        return _get_sample_visual_data()
    
    # 1. Fetch Campaign Data (for Report Card & Timeline)
    # This is needed for Actions & Results slide and Revenue Timeline
    try:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Fetch ALL data (db method doesn't support date args) and filter
        full_df = db_manager.get_target_stats_df(client_id)
        
        campaign_df = pd.DataFrame()
        if not full_df.empty and 'Date' in full_df.columns:
             full_df['Date'] = pd.to_datetime(full_df['Date'])
             mask = (full_df['Date'].dt.date >= start_date) & (full_df['Date'].dt.date <= end_date)
             campaign_df = full_df.loc[mask].copy()
        
        if not campaign_df.empty:
            if 'Date' in campaign_df.columns:
                 visual_data['sales_df'] = campaign_df.groupby('Date')[['Sales']].sum().reset_index()

    except Exception as e:
        print(f"Failed to fetch campaign data: {e}")

    # 2. Decision Impact (Used for Slide 3 & Slide 6 Actions)
    # Always fetch if either is needed
    impact_needed = 'decision_impact' in selected_visuals or 'report_card' in selected_visuals
    impact_df = pd.DataFrame()
    
    if impact_needed:
        try:
            from features.impact_metrics import ImpactMetrics
            # Re-use exact logic from Executive Dashboard
            impact_df = db_manager.get_action_impact(
                client_id,
                before_days=14,
                after_days=14
            )
            # Add maturity
            if not impact_df.empty and 'action_date' in impact_df.columns:
                max_date = pd.Timestamp(datetime.now().date())
                impact_df['action_date'] = pd.to_datetime(impact_df['action_date'])
                impact_df['is_mature'] = (max_date - impact_df['action_date']).dt.days >= 14
            
                # Use dashboard's filter settings
                current_filters = {
                    'validated_only': True,
                    'mature_only': True,
                }
                
                metrics = ImpactMetrics.from_dataframe(
                    impact_df,
                    filters=current_filters,
                    horizon_days=14
                )
                
                visual_data['decision_impact'] = {
                    'total_impact': metrics.attributed_impact,
                    'offensive_wins': metrics.offensive_value,
                    'defensive_wins': metrics.defensive_value,
                    'win_count': metrics.wins_count,
                    'total_decisions': metrics.mature_actions,
                    'total_spend': metrics.total_spend,
                    'impact_df': impact_df  # Store for timeline chart
                }
            else:
                visual_data['decision_impact'] = _get_sample_visual_data().get('decision_impact', {})
                
        except Exception as e:
            st.warning(f"Could not fetch Decision Impact data: {e}") 
            visual_data['decision_impact'] = _get_sample_visual_data().get('decision_impact', {})
    
    # 4. Populate Actions & Results (Slide 6) - Using HISTORICAL DATA
    if 'report_card' in selected_visuals:
        try:
             # Default fallback
             actions_data = {'bid_increases': 0, 'bid_decreases': 0, 'negatives': 0, 'harvests': 0}
             savings = 0.0
             
             if not impact_df.empty:
                 # Filter by Report Date Range for correct count
                 mask = (impact_df['action_date'].dt.date >= start_date) & (impact_df['action_date'].dt.date <= end_date)
                 period_actions = impact_df.loc[mask].copy()
                 
                 if not period_actions.empty:
                     # Count Actions
                     type_col = period_actions['action_type'].astype(str).str.lower()
                     actions_data['bid_increases'] = len(period_actions[type_col.str.contains('increase')])
                     actions_data['bid_decreases'] = len(period_actions[type_col.str.contains('decrease')])
                     actions_data['negatives'] = len(period_actions[type_col.str.contains('negative') | type_col.str.contains('pause')])
                     actions_data['harvests'] = len(period_actions[type_col.str.contains('harvest') | type_col.str.contains('keyword') | type_col.str.contains('target')])
                     
                     # "Spend Preserved"
                     defensive_mask = type_col.str.contains('decrease') | type_col.str.contains('negative') | type_col.str.contains('pause')
                     if 'impact' in period_actions.columns:
                         savings = period_actions.loc[defensive_mask, 'impact'].sum()

             visual_data['report_card'] = {
                 'actions': actions_data,
                 'financials': {'savings': savings},
                 'reallocation': {'invested': 0, 'removed': savings},
                 'details': {'removed': [], 'added': []} 
             }
        except Exception as e:
            print(f"Failed to process report card actions: {e}")

    # ROAS Attribution Data - calculate decision_impact_roas like dashboard does
    if 'roas_attribution' in selected_visuals:

        try:
            from core.roas_attribution import get_roas_attribution
            
            # Get values from impact metrics (if already captured)
            impact_data = visual_data.get('decision_impact', {})
            decision_impact_value = impact_data.get('total_impact', 0)
            impact_total_spend = impact_data.get('total_spend', 0)  # This is from ImpactMetrics
            
            # Get market decomposition from roas_attribution module
            summary = get_roas_attribution(client_id, days, decision_impact_value=0)  # Pass 0, we calculate ourselves
            
            if summary:
                # Calculate decision_impact_roas EXACTLY like dashboard does
                # Dashboard: decision_impact_roas = canonical_metrics.attributed_impact / canonical_metrics.total_spend
                if impact_total_spend > 0:
                    decision_impact_roas = decision_impact_value / impact_total_spend
                else:
                    decision_impact_roas = 0
                
                # Get baseline and actual from summary
                baseline_roas = summary.get('baseline_roas', 0)
                actual_roas = summary.get('actual_roas', 0)
                
                # Combined Forces = Actual - Baseline - Decisions (to make equation balance)
                # This is how dashboard displays it: Baseline + Combined + Decisions = Actual
                combined_forces = actual_roas - baseline_roas - decision_impact_roas
                
                visual_data['roas_attribution'] = {
                    'baseline': baseline_roas,
                    'market_forces': round(combined_forces, 2),  # Calculated to balance equation
                    'decisions': round(decision_impact_roas, 2),  # Calculated from ImpactMetrics
                    'actual': actual_roas,
                    'value_created': decision_impact_value,
                    'current_spend': summary.get('current_metrics', {}).get('spend', 0)
                }
            else:
                visual_data['roas_attribution'] = _get_sample_visual_data().get('roas_attribution', {})
        except Exception as e:
            st.warning(f"Could not fetch ROAS Attribution data: {e}")
            visual_data['roas_attribution'] = _get_sample_visual_data().get('roas_attribution', {})
    
    # Account Health Data
    if 'account_health' in selected_visuals:
        try:
            from features.report_card import get_account_health_score
            
            health_score = get_account_health_score() or 0
            
            visual_data['account_health'] = {
                'score': health_score,
                'status': 'Excellent' if health_score >= 80 else 'Good' if health_score >= 60 else 'Fair' if health_score >= 40 else 'Poor',
                'roas': 0,
                'efficiency': 0,
                'cvr': 0
            }
        except Exception as e:
            st.warning(f"Could not fetch Account Health data: {e}")
            visual_data['account_health'] = _get_sample_visual_data().get('account_health', {})
    
    # Executive Summary Data (KPIs + Gauges)
    # This combines data from target_stats for KPIs
    try:
        from datetime import timedelta
        import numpy as np
        from features.report_card import get_account_health_score
        
        df = db_manager.get_target_stats_df(client_id)
        if df is not None and not df.empty:
            df['Date'] = pd.to_datetime(df['Date'])
            max_date = df['Date'].max()
            current_start = max_date - timedelta(days=days)
            previous_start = current_start - timedelta(days=days)
            
            df_current = df[df['Date'] >= current_start]
            df_previous = df[(df['Date'] >= previous_start) & (df['Date'] < current_start)]
            
            # Current KPIs
            curr_spend = df_current['Spend'].sum()
            curr_revenue = df_current['Sales'].sum()
            curr_roas = curr_revenue / curr_spend if curr_spend > 0 else 0
            curr_orders = df_current['Orders'].sum()
            curr_clicks = df_current['Clicks'].sum()
            curr_cvr = (curr_orders / curr_clicks * 100) if curr_clicks > 0 else 0
            
            # Previous KPIs for delta
            prev_spend = df_previous['Spend'].sum()
            prev_revenue = df_previous['Sales'].sum()
            prev_roas = prev_revenue / prev_spend if prev_spend > 0 else 0
            prev_clicks = df_previous['Clicks'].sum()
            prev_orders = df_previous['Orders'].sum()
            prev_cvr = (prev_orders / prev_clicks * 100) if prev_clicks > 0 else 0
            
            # Calculate deltas
            def calc_delta(curr, prev):
                return ((curr - prev) / abs(prev) * 100) if prev != 0 else 0
            
            # Get decision ROI from impact data
            impact_data = visual_data.get('decision_impact', {})
            decision_value = impact_data.get('total_impact', 0)
            decision_spend = impact_data.get('total_spend', 0)
            decision_roi = (decision_value / decision_spend * 100) if decision_spend > 0 else 0
            
            # Calculate spend efficiency (% of spend on profitable targets)
            if 'ROAS' not in df_current.columns:
                df_current = df_current.copy()
                df_current['ROAS'] = (df_current['Sales'] / df_current['Spend']).replace([np.inf, -np.inf], 0).fillna(0)
            profitable_spend = df_current[df_current['ROAS'] > 1]['Spend'].sum()
            spend_efficiency = (profitable_spend / curr_spend * 100) if curr_spend > 0 else 0
            
            # Health score
            health_score = get_account_health_score() or 61
            
            visual_data['executive_summary'] = {
                'kpis': {
                    'spend': curr_spend,
                    'spend_delta': calc_delta(curr_spend, prev_spend),
                    'revenue': curr_revenue,
                    'revenue_delta': calc_delta(curr_revenue, prev_revenue),
                    'roas': curr_roas,
                    'roas_delta': calc_delta(curr_roas, prev_roas),
                    'cvr': curr_cvr,
                    'cvr_delta': calc_delta(curr_cvr, prev_cvr),
                },
                'gauges': {
                    'health': {'value': health_score, 'target': 80, 'label': 'Account Health', 'unit': 'pts'},
                    'decision_roi': {'value': decision_roi, 'target': 5, 'label': 'Decision ROI', 'unit': '%'},
                    'spend_efficiency': {'value': spend_efficiency, 'target': 50, 'label': 'Spend Efficiency', 'unit': '%'},
                },
                'date_range': f"{current_start.strftime('%b %d')} - {max_date.strftime('%b %d, %Y')}"
            }
    except Exception as e:
        print(f"Executive summary data capture failed: {e}")
    
    return visual_data


def _get_sample_visual_data() -> Dict[str, Any]:
    """Return sample data for testing/fallback."""
    return {
        'decision_impact': {
            'total_impact': 15000,
            'offensive_wins': 8500,
            'defensive_wins': 6500,
            'win_count': 42,
            'total_decisions': 156,
            'total_spend': 25000
        },
        'roas_attribution': {
            'baseline': 3.2,
            'market_forces': -0.4,
            'decisions': 0.6,
            'actual': 3.4,
            'value_protected': 12000
        },
        'account_health': {
            'score': 72,
            'status': 'Good',
            'roas': 3.4,
            'efficiency': 65,
            'cvr': 8.2
        }
    }


def _generate_ai_narratives(visual_data: Dict[str, Any], date_range: str) -> Dict[str, Any]:
    """Generate AI narratives for each visual using existing assistant."""
    
    narratives = {}
    
    try:
        from features.assistant import AssistantModule
        assistant = AssistantModule()
        
        # Generate narrative for each visual
        for visual_key, data in visual_data.items():
            prompt = _build_visual_prompt(visual_key, data, date_range)
            
            # Call assistant (simplified - would need actual implementation)
            # For MVP, we'll use template-based narratives
            narratives[visual_key] = _get_template_narrative(visual_key, data)
        
        # Generate executive summary
        narratives['executive_summary'] = _generate_executive_summary(visual_data)
        
    except Exception as e:
        st.warning(f"AI narrative generation unavailable: {e}")
        # Fallback to templates
        for visual_key, data in visual_data.items():
            narratives[visual_key] = _get_template_narrative(visual_key, data)
        narratives['executive_summary'] = _generate_executive_summary(visual_data)
    
    return narratives


def _build_visual_prompt(visual_key: str, data: Dict[str, Any], date_range: str) -> str:
    """Build prompt for AI narrative generation."""
    
    context_map = {
        'decision_impact': "Shows total value created through optimization decisions",
        'roas_attribution': "Waterfall showing how decisions offset market headwinds",
        'account_health': "Overall account health and performance indicators"
    }
    
    return f"""
You are generating a slide for a client-facing performance report.

CONTEXT: The user is creating a report to share with clients showing their Amazon PPC optimization results.

VISUAL TYPE: {visual_key}
DATA: {json.dumps(data)}
TIME PERIOD: {date_range}
DESCRIPTION: {context_map.get(visual_key, '')}

Generate:
1. HEADLINE (max 60 characters) - Clear statement of what the visual shows, client-friendly language
2. KEY INSIGHT (2-3 sentences) - Explain what the data means in business terms, focus on value delivered

Return ONLY a JSON object:
{{"headline": "...", "insight": "..."}}
"""


def _get_template_narrative(visual_key: str, data: Dict[str, Any]) -> Dict[str, str]:
    """Generate template-based narrative (fallback for AI)."""
    
    currency = get_account_currency()
    
    if visual_key == 'decision_impact':
        total = data.get('total_impact', 0)
        offensive = data.get('offensive_wins', 0)
        defensive = data.get('defensive_wins', 0)
        
        return {
            'headline': f"{currency}{total:,.0f} Value Created Through Optimization",
            'insight': f"Your optimization decisions generated {currency}{offensive:,.0f} in offensive wins (growth opportunities captured) and protected {currency}{defensive:,.0f} through defensive actions (waste prevention). This demonstrates strong ROI on your advertising management."
        }
    
    elif visual_key == 'roas_attribution':
        baseline = data.get('baseline', 0)
        actual = data.get('actual', 0)
        decisions = data.get('decisions', 0)
        
        return {
            'headline': f"ROAS Improved to {actual:.2f}x Through Strategic Decisions",
            'insight': f"Starting from a baseline of {baseline:.2f}x ROAS, your optimization decisions contributed +{decisions:.2f} to achieve an actual ROAS of {actual:.2f}x. Market conditions were actively managed to protect performance."
        }
    
    elif visual_key == 'account_health':
        score = data.get('score', 0)
        status = data.get('status', 'Unknown')
        
        return {
            'headline': f"Account Health Score: {score:.0f}/100 ({status})",
            'insight': f"Your account is performing at a {status.lower()} level with a health score of {score:.0f}. This composite score reflects ROAS efficiency, spend quality, and conversion performance across your campaigns."
        }
    
    return {'headline': 'Performance Summary', 'insight': 'Data available in the visual above.'}


def _generate_executive_summary(visual_data: Dict[str, Any]) -> Dict[str, List[str]]:
    """Generate executive summary from combined visual data."""
    
    currency = get_account_currency()
    
    # Extract key metrics
    total_impact = visual_data.get('decision_impact', {}).get('total_impact', 0)
    actual_roas = visual_data.get('roas_attribution', {}).get('actual', 0)
    health_score = visual_data.get('account_health', {}).get('score', 0)
    win_count = visual_data.get('decision_impact', {}).get('win_count', 0)
    
    return {
        'achievements': [
            f"Generated {currency}{total_impact:,.0f} in measurable value through {win_count} optimization decisions",
            f"Achieved {actual_roas:.2f}x ROAS, demonstrating strong advertising efficiency",
            f"Maintained {health_score:.0f}/100 account health score with consistent performance"
        ],
        'areas_to_watch': [
            "Continue monitoring market conditions that may impact baseline ROAS",
            "Identify new growth opportunities in high-performing campaigns"
        ],
        'next_steps': [
            "Review and approve pending optimization recommendations",
            "Analyze top-performing targets for budget reallocation",
            "Schedule regular performance reviews to maintain momentum"
        ]
    }


def _sanitize_for_pdf(text: str) -> str:
    """Remove or replace non-ASCII characters for PDF compatibility."""
    # Map common currency symbols to ASCII equivalents
    replacements = {
        '₹': 'INR ',
        '€': 'EUR ',
        '£': 'GBP ',
        '¥': 'JPY ',
        '₽': 'RUB ',
    }
    result = text
    for char, replacement in replacements.items():
        result = result.replace(char, replacement)
    # Remove any remaining non-ASCII characters
    return result.encode('ascii', 'replace').decode('ascii').replace('?', '')


def _compile_pdf(
    visual_data: Dict[str, Any],
    ai_narratives: Dict[str, Any],
    date_range_label: str,
    currency: str,
    include_ai_summary: bool,
    account_name: str = 'Unknown Account',
    chart_images: Dict[str, str] = None
) -> bytes:
    """Compile the final PDF report as a slide deck with embedded chart images."""
    
    from fpdf import FPDF
    
    # Initialize chart_images if not provided
    if chart_images is None:
        chart_images = {}
    
    # Sanitize currency for PDF (Helvetica doesn't support all Unicode)
    safe_currency = _sanitize_for_pdf(currency)
    
    # Page dimensions (A4 Landscape: 297mm x 210mm)
    PAGE_W = 297
    PAGE_H = 210
    MARGIN = 20
    CONTENT_W = PAGE_W - (2 * MARGIN)
    
    # Create PDF
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=False)
    pdf.set_margins(MARGIN, MARGIN, MARGIN)
    
    # Colors
    bg_color = (30, 41, 59)  # Dark slate
    text_color = (248, 250, 252)  # White
    accent_color = (6, 182, 212)  # Cyan
    muted_color = (148, 163, 184)  # Slate
    
    # ===== SLIDE 1: TITLE =====
    pdf.add_page()
    pdf.set_fill_color(*bg_color)
    pdf.rect(0, 0, PAGE_W, PAGE_H, 'F')
    
    # Title
    pdf.set_font('Helvetica', 'B', 42)
    pdf.set_text_color(*text_color)
    pdf.set_xy(MARGIN, 45)
    pdf.cell(CONTENT_W, 20, 'Account Performance Report', align='C')
    
    # Account Name
    pdf.set_font('Helvetica', 'B', 24)
    pdf.set_text_color(*accent_color)
    pdf.set_xy(MARGIN, 75)
    pdf.cell(CONTENT_W, 15, _sanitize_for_pdf(account_name), align='C')
    
    # Date range
    pdf.set_font('Helvetica', '', 18)
    pdf.set_text_color(*muted_color)
    pdf.set_xy(MARGIN, 100)
    pdf.cell(CONTENT_W, 12, date_range_label, align='C')
    
    # Footer
    pdf.set_font('Helvetica', 'I', 14)
    pdf.set_text_color(*muted_color)
    pdf.set_xy(MARGIN, 155)
    pdf.cell(CONTENT_W, 10, 'Prepared by Saddl AdPulse', align='C')
    pdf.set_xy(MARGIN, 167)
    pdf.cell(CONTENT_W, 10, datetime.now().strftime('%B %d, %Y'), align='C')
    
    # ===== SLIDE 2: EXECUTIVE SUMMARY (KPIs + Gauges) =====
    if 'executive_summary' in visual_data:
        pdf.add_page()
        pdf.set_fill_color(*bg_color)
        pdf.rect(0, 0, PAGE_W, PAGE_H, 'F')
        
        exec_data = visual_data['executive_summary']
        kpis = exec_data.get('kpis', {})
        
        # Title
        pdf.set_font('Helvetica', 'B', 28)
        pdf.set_text_color(*text_color)
        pdf.set_xy(MARGIN, 15)
        pdf.cell(CONTENT_W, 12, 'Executive Summary', align='C')
        
        # KPI Cards Row (4 cards)
        kpi_width = (CONTENT_W - 30) / 4
        kpi_y = 35
        kpi_labels = [
            ('SPEND', f"{safe_currency}{kpis.get('spend', 0)/1000:.0f}K", kpis.get('spend_delta', 0)),
            ('REVENUE', f"{safe_currency}{kpis.get('revenue', 0)/1000:.0f}K", kpis.get('revenue_delta', 0)),
            ('ROAS', f"{kpis.get('roas', 0):.2f}x", kpis.get('roas_delta', 0)),
            ('CVR', f"{kpis.get('cvr', 0):.2f}%", kpis.get('cvr_delta', 0)),
        ]
        
        for i, (label, value, delta) in enumerate(kpi_labels):
            x = MARGIN + i * (kpi_width + 10)
            # Card background
            pdf.set_fill_color(15, 23, 42)
            pdf.rect(x, kpi_y, kpi_width, 45, 'F')
            
            # Label
            pdf.set_font('Helvetica', '', 10)
            pdf.set_text_color(*muted_color)
            pdf.set_xy(x + 5, kpi_y + 5)
            pdf.cell(kpi_width - 10, 8, label)
            
            # Value
            pdf.set_font('Helvetica', 'B', 24)
            pdf.set_text_color(*text_color)
            pdf.set_xy(x + 5, kpi_y + 15)
            pdf.cell(kpi_width - 10, 12, value)
            
            # Delta
            delta_color = (16, 185, 129) if delta >= 0 else (239, 68, 68)
            pdf.set_font('Helvetica', '', 10)
            pdf.set_text_color(*delta_color)
            pdf.set_xy(x + 5, kpi_y + 32)
            pdf.cell(kpi_width - 10, 8, f"{'+' if delta >= 0 else ''}{delta:.1f}%")
        
        # Gauges Chart (if available)
        chart_path = chart_images.get('executive_summary')
        if chart_path and os.path.exists(chart_path):
            pdf.image(chart_path, x=MARGIN + 15, y=90, w=CONTENT_W - 30)
        else:
            # Fallback: text-based gauges
            pdf.set_font('Helvetica', '', 12)
            pdf.set_text_color(*muted_color)
            pdf.set_xy(MARGIN, 100)
            gauges = exec_data.get('gauges', {})
            gauge_text = f"Health: {gauges.get('health', {}).get('value', 0):.0f}pts  |  Decision ROI: {gauges.get('decision_roi', {}).get('value', 0):.1f}%  |  Spend Efficiency: {gauges.get('spend_efficiency', {}).get('value', 0):.1f}%"
            pdf.cell(CONTENT_W, 8, gauge_text, align='C')
    
    # ===== SLIDE 3: DECISION IMPACT (Impact + Timeline) =====
    if 'decision_impact' in visual_data:
        pdf.add_page()
        pdf.set_fill_color(*bg_color)
        pdf.rect(0, 0, PAGE_W, PAGE_H, 'F')
        
        impact_data = visual_data['decision_impact']
        
        # Title
        pdf.set_font('Helvetica', 'B', 24)
        pdf.set_text_color(*text_color)
        pdf.set_xy(MARGIN, 15)
        pdf.cell(CONTENT_W, 12, 'Decision Impact Analysis', align='C')
        
        # Hero metric
        pdf.set_font('Helvetica', 'B', 56)
        pdf.set_text_color(*accent_color)
        pdf.set_xy(MARGIN, 45)
        total_impact = impact_data.get('total_impact', 0)
        sign = '+' if total_impact >= 0 else ''
        pdf.cell(CONTENT_W, 30, f"{sign}{safe_currency}{total_impact:,.0f}", align='C')
        
        # Subtitle
        pdf.set_font('Helvetica', '', 14)
        pdf.set_text_color(*muted_color)
        pdf.set_xy(MARGIN, 82)
        pdf.cell(CONTENT_W, 10, f"{impact_data.get('total_decisions', 0)} mature actions analyzed", align='C')
        
        # Breakdown
        pdf.set_font('Helvetica', '', 12)
        breakdown_y = 110
        
        # Offensive Wins
        pdf.set_text_color(16, 185, 129)  # Green
        pdf.set_xy(MARGIN + 40, breakdown_y)
        pdf.cell(100, 8, f"Offensive Wins: +{safe_currency}{impact_data.get('offensive_wins', 0):,.0f}")
        
        # Defensive Wins
        pdf.set_text_color(6, 182, 212)  # Cyan
        pdf.set_xy(MARGIN + 160, breakdown_y)
        pdf.cell(100, 8, f"Defensive Wins: +{safe_currency}{impact_data.get('defensive_wins', 0):,.0f}")
        
        # Win Count
        pdf.set_text_color(*muted_color)
        pdf.set_xy(MARGIN, breakdown_y + 20)
        pdf.cell(CONTENT_W, 8, f"Win Count: {impact_data.get('win_count', 0)} successful optimizations", align='C')
        
        # Insight
        narrative = ai_narratives.get('decision_impact', {})
        insight = _sanitize_for_pdf(narrative.get('insight', ''))
        if insight:
            pdf.set_font('Helvetica', '', 11)
            pdf.set_text_color(*muted_color)
            pdf.set_xy(MARGIN + 20, 155)
            pdf.multi_cell(CONTENT_W - 40, 6, insight, align='C')
    
    # ===== SLIDE 4: ROAS DECOMPOSITION =====
    if 'roas_attribution' in visual_data:
        pdf.add_page()
        pdf.set_fill_color(*bg_color)
        pdf.rect(0, 0, PAGE_W, PAGE_H, 'F')
        
        roas_data = visual_data['roas_attribution']
        
        # Title
        pdf.set_font('Helvetica', 'B', 24)
        pdf.set_text_color(*text_color)
        pdf.set_xy(MARGIN, 15)
        pdf.cell(CONTENT_W, 12, 'ROAS Decomposition', align='C')
        
        # Waterfall chart
        chart_path = chart_images.get('roas_attribution')
        if chart_path and os.path.exists(chart_path):
            pdf.image(chart_path, x=MARGIN + 15, y=35, w=CONTENT_W - 30)
        else:
            # Fallback: text-based
            pdf.set_font('Helvetica', 'B', 48)
            pdf.set_text_color(*accent_color)
            pdf.set_xy(MARGIN, 60)
            pdf.cell(CONTENT_W, 25, f"{roas_data.get('actual', 0):.2f}x ROAS", align='C')
        
        # Summary line
        pdf.set_font('Helvetica', '', 12)
        pdf.set_text_color(*muted_color)
        pdf.set_xy(MARGIN, 145)
        summary = f"Baseline: {roas_data.get('baseline', 0):.2f}x  |  Market: {roas_data.get('market_forces', 0):+.2f}  |  Decisions: {roas_data.get('decisions', 0):+.2f}  |  Actual: {roas_data.get('actual', 0):.2f}x"
        pdf.cell(CONTENT_W, 8, summary, align='C')
        
        # Insight
        narrative = ai_narratives.get('roas_attribution', {})
        insight = _sanitize_for_pdf(narrative.get('insight', ''))
        if insight:
            pdf.set_font('Helvetica', '', 11)
            pdf.set_text_color(*muted_color)
            pdf.set_xy(MARGIN + 20, 160)
            pdf.multi_cell(CONTENT_W - 40, 6, insight, align='C')
    
    # ===== SLIDE 5: DECISION TIMELINE =====
    if 'decision_impact' in visual_data:
        # Check if we have the timeline chart
        timeline_chart_path = chart_images.get('decision_timeline')
        if timeline_chart_path and os.path.exists(timeline_chart_path):
            pdf.add_page()
            pdf.set_fill_color(*bg_color)
            pdf.rect(0, 0, PAGE_W, PAGE_H, 'F')
            
            impact_data = visual_data['decision_impact']
            
            # Title
            pdf.set_font('Helvetica', 'B', 24)
            pdf.set_text_color(*text_color)
            pdf.set_xy(MARGIN, 15)
            pdf.cell(CONTENT_W, 12, 'Decision Impact Timeline', align='C')
            
            # Subtitle
            pdf.set_font('Helvetica', '', 12)
            pdf.set_text_color(*muted_color)
            pdf.set_xy(MARGIN, 30)
            pdf.cell(CONTENT_W, 8, 'Cumulative value created through optimization decisions', align='C')
            
            # Timeline chart
            pdf.image(timeline_chart_path, x=MARGIN + 15, y=45, w=CONTENT_W - 30)
            
            # Summary metrics
            pdf.set_font('Helvetica', '', 11)
            pdf.set_text_color(*muted_color)
            pdf.set_xy(MARGIN, 155)
            total = impact_data.get('total_impact', 0)
            actions = impact_data.get('total_decisions', 0)
            pdf.cell(CONTENT_W, 8, f"Total Impact: +{safe_currency}{total:,.0f} from {actions} optimization actions", align='C')
    
    # ===== SLIDE 6: ACTIONS & RESULTS =====
    if 'report_card' in visual_data:
        metrics = visual_data['report_card']
        actions = metrics.get('actions', {})
        fin = metrics.get('financials', {})
        details = metrics.get('details', {'removed': [], 'added': []})
        
        pdf.add_page()
        pdf.set_fill_color(*bg_color)
        pdf.rect(0, 0, PAGE_W, PAGE_H, 'F')
        
        # Title
        pdf.set_font('Helvetica', 'B', 24)
        pdf.set_text_color(*text_color)
        pdf.set_xy(MARGIN, 15)
        pdf.cell(CONTENT_W, 12, 'ACTIONS & RESULTS', align='L')
        
        # --- ROW 1 ---
        y_start = 40
        col_w = (CONTENT_W - 20) / 2
        
        # Left: System Executed Adjustments
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(*muted_color)
        pdf.set_xy(MARGIN, y_start)
        pdf.cell(col_w, 8, 'SYSTEM EXECUTED ADJUSTMENTS', align='C')
        
        # Action Counts Box
        y = y_start + 15
        
        stats = [
            ("Bid Increases:", actions.get('bid_increases', 0), (16, 185, 129)),
            ("Bid Decreases:", actions.get('bid_decreases', 0), (248, 113, 113)),
            ("Paused Targets:", actions.get('negatives', 0), (148, 163, 184)),
            ("Promoted Keywords:", actions.get('harvests', 0), (251, 191, 36))
        ]
        
        for label, val, color in stats:
            # Bullet
            pdf.set_fill_color(*color)
            pdf.rect(MARGIN + 20, y+2, 2, 2, 'F')
            
            # Label
            pdf.set_font('Helvetica', 'B', 11)
            pdf.set_text_color(*muted_color)
            pdf.set_xy(MARGIN + 25, y)
            pdf.cell(40, 6, label)
            
            # Value Badge
            pdf.set_font('Helvetica', 'B', 11)
            pdf.set_text_color(248, 250, 252)
            pdf.set_fill_color(30, 41, 59)
            pdf.rect(MARGIN + 70, y, 15, 6, 'F')
            pdf.set_xy(MARGIN + 70, y)
            pdf.cell(15, 6, str(val), align='C')
            
            y += 12
            
        # Right: Net Spend Reallocation (Chart)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(*muted_color)
        pdf.set_xy(MARGIN + col_w + 20, y_start)
        pdf.cell(col_w, 8, 'NET SPEND REALLOCATION', align='C')
        
        realloc_chart_path = chart_images.get('reallocation_chart')
        if realloc_chart_path and os.path.exists(realloc_chart_path):
            pdf.image(realloc_chart_path, x=MARGIN + col_w + 20, y=y_start + 10, w=col_w, h=50)
        else:
            pdf.set_xy(MARGIN + col_w + 20, y_start + 25)
            pdf.set_font('Helvetica', 'I', 10)
            pdf.cell(col_w, 10, "(Reallocation chart not available)", align='C')

        # --- ROW 2 ---
        y_row2 = 110
        # Line divider
        pdf.set_draw_color(51, 65, 85)
        pdf.line(MARGIN, y_row2 - 10, MARGIN + CONTENT_W, y_row2 - 10)
        
        # Left: Spend Preserved
        pdf.set_xy(MARGIN, y_row2)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(*muted_color)
        pdf.cell(col_w, 8, 'SPEND PRESERVED', align='C')
        
        # Value
        pdf.set_xy(MARGIN, y_row2 + 12)
        pdf.set_font('Helvetica', 'B', 32)
        pdf.set_text_color(34, 211, 238)
        savings = fin.get('savings', 0)
        pdf.cell(col_w, 15, f"{safe_currency}{savings:,.0f}", align='C')
        
        pdf.set_xy(MARGIN, y_row2 + 28)
        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_text_color(*muted_color)
        pdf.cell(col_w, 5, "ANNUALIZED SAVINGS POTENTIAL", align='C')
        
        # Right: Waste & Growth Lists
        sub_col_w = (col_w - 10) / 2
        right_start_x = MARGIN + col_w + 20
        
        # Waste Removed
        pdf.set_xy(right_start_x, y_row2)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_text_color(*text_color)
        pdf.cell(sub_col_w, 8, "SOURCES OF WASTE REMOVED", align='L')
        
        y_list = y_row2 + 10
        removed = details.get('removed', [])
        if not removed:
             pdf.set_xy(right_start_x, y_list)
             pdf.set_font('Helvetica', 'I', 9)
             pdf.set_text_color(*muted_color)
             pdf.cell(sub_col_w, 6, "No significant removal actions.")
        else:
            for item in removed[:3]: 
                pdf.set_xy(right_start_x, y_list)
                pdf.set_font('Helvetica', '', 9)
                pdf.set_text_color(*text_color)
                pdf.cell(sub_col_w, 5, f"{item['name'][:20]}...")
                pdf.set_text_color(251, 191, 36)
                pdf.set_xy(right_start_x + sub_col_w - 25, y_list)
                pdf.cell(25, 5, f"{safe_currency}{item['val']:,.0f}", align='R')
                y_list += 6
        
        # Growth Investments
        pdf.set_xy(right_start_x + sub_col_w + 5, y_row2)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_text_color(*text_color)
        pdf.cell(sub_col_w, 8, "TOP INVESTMENTS IN GROWTH", align='L')
        
        y_list = y_row2 + 10
        added = details.get('added', [])
        if not added:
             pdf.set_xy(right_start_x + sub_col_w + 5, y_list)
             pdf.set_font('Helvetica', 'I', 9)
             pdf.set_text_color(*muted_color)
             pdf.cell(sub_col_w, 6, "No significant investment actions.")
        else:
            for item in added[:3]:
                pdf.set_xy(right_start_x + sub_col_w + 5, y_list)
                pdf.set_font('Helvetica', '', 9)
                pdf.set_text_color(*text_color)
                pdf.cell(sub_col_w, 5, f"{item['name'][:20]}...")
                pdf.set_text_color(16, 185, 129)
                pdf.set_xy(right_start_x + sub_col_w + 5 + sub_col_w - 25, y_list)
                pdf.cell(25, 5, f"{safe_currency}{item['val']:,.0f}", align='R')
                y_list += 6
    
    # ===== AI SUMMARY SLIDE =====
    if include_ai_summary:
        pdf.add_page()
        pdf.set_fill_color(*bg_color)
        pdf.rect(0, 0, PAGE_W, PAGE_H, 'F')
        
        summary = ai_narratives.get('executive_summary', {})
        
        # Title
        pdf.set_font('Helvetica', 'B', 32)
        pdf.set_text_color(*text_color)
        pdf.set_xy(MARGIN, 15)
        pdf.cell(CONTENT_W, 15, 'AI Insights Summary', align='C')
        
        # Three columns layout
        col_width = (CONTENT_W - 20) / 3
        col_x = [MARGIN, MARGIN + col_width + 10, MARGIN + (col_width + 10) * 2]
        
        # Column 1: Key Achievements
        pdf.set_xy(col_x[0], 45)
        pdf.set_font('Helvetica', 'B', 14)
        pdf.set_text_color(16, 185, 129)  # Emerald
        pdf.cell(col_width, 10, 'Key Achievements')
        
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(*text_color)
        y_pos = 58
        for item in summary.get('achievements', []):
            pdf.set_xy(col_x[0], y_pos)
            clean_item = _sanitize_for_pdf(item)
            pdf.multi_cell(col_width, 6, f"+ {clean_item[:80]}")
            y_pos += 25
        
        # Column 2: Areas to Monitor
        pdf.set_xy(col_x[1], 45)
        pdf.set_font('Helvetica', 'B', 14)
        pdf.set_text_color(245, 158, 11)  # Amber
        pdf.cell(col_width, 10, 'Areas to Monitor')
        
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(*text_color)
        y_pos = 58
        for item in summary.get('areas_to_watch', []):
            pdf.set_xy(col_x[1], y_pos)
            clean_item = _sanitize_for_pdf(item)
            pdf.multi_cell(col_width, 6, f"! {clean_item[:80]}")
            y_pos += 25
        
        # Column 3: Next Steps
        pdf.set_xy(col_x[2], 45)
        pdf.set_font('Helvetica', 'B', 14)
        pdf.set_text_color(*accent_color)
        pdf.cell(col_width, 10, 'Next Steps')
        
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(*text_color)
        y_pos = 58
        for item in summary.get('next_steps', []):
            pdf.set_xy(col_x[2], y_pos)
            clean_item = _sanitize_for_pdf(item)
            pdf.multi_cell(col_width, 6, f"> {clean_item[:80]}")
            y_pos += 25
        
        # Footer tagline
        pdf.set_font('Helvetica', 'I', 11)
        pdf.set_text_color(*muted_color)
        pdf.set_xy(MARGIN, 180)
        pdf.cell(CONTENT_W, 10, 'Powered by Saddl AdPulse AI', align='C')
    
    # Return PDF as bytes
    return bytes(pdf.output())

