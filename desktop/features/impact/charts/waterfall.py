"""
Waterfall Charts - ROAS waterfall and attribution charts.
Aligned with legacy impact_dashboard.py visuals.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, Any, Optional

from features.impact.styles.css import BRAND_COLORS, get_chart_styles


def create_roas_waterfall_figure(
    summary: Dict[str, Any],
    currency: str = "$",
    height: int = 380
) -> go.Figure:
    """
    Create a ROAS waterfall chart figure.

    This is a factory function that returns a Plotly figure,
    used by client report generation.

    Args:
        summary: Summary dict with by_action_type breakdown
        currency: Currency symbol
        height: Chart height in pixels

    Returns:
        Plotly Figure object
    """
    by_type = summary.get('by_action_type', {})

    if not by_type:
        # Return empty figure
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig

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
        agg_data[name] = agg_data.get(name, 0) + data.get('net_sales', 0)

    # Sort
    sorted_data = sorted(agg_data.items(), key=lambda x: x[1], reverse=True)
    names = [x[0] for x in sorted_data]
    impacts = [x[1] for x in sorted_data]

    # Create waterfall
    fig = go.Figure(go.Waterfall(
        name="Impact",
        orientation="v",
        measure=["relative"] * len(impacts) + ["total"],
        x=names + ['Total'],
        y=impacts + [sum(impacts)],
        connector={"line": {"color": "rgba(148, 163, 184, 0.2)"}},
        decreasing={"marker": {"color": BRAND_COLORS['slate_light']}},
        increasing={"marker": {"color": BRAND_COLORS['purple']}},
        totals={"marker": {"color": BRAND_COLORS['cyan']}},
        textposition="outside",
        textfont=dict(size=14, color="#e2e8f0"),
        text=[f"{currency}{v:+,.0f}" for v in impacts] + [f"{currency}{sum(impacts):+,.0f}"]
    ))

    fig.update_layout(
        showlegend=False,
        height=height,
        margin=dict(t=60, b=40, l=30, r=30),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(128,128,128,0.15)',
            tickformat=',.0f',
            tickfont=dict(color='#94a3b8', size=12)
        ),
        xaxis=dict(
            showgrid=False,
            tickfont=dict(color='#cbd5e1', size=12)
        )
    )

    return fig


def render_roas_attribution_bar(
    summary: Dict[str, Any],
    impact_df: pd.DataFrame,
    currency: str,
    canonical_metrics: Optional[Any] = None
):
    """
    Render ROAS attribution waterfall chart - matches legacy _render_roas_attribution_bar.
    
    Features:
    - Baseline → Combined Forces → Decisions → Actual waterfall
    - VALUE CREATED box
    - Full Breakdown expander with Market/Structural analysis

    Args:
        summary: Summary dict from backend
        impact_df: Impact DataFrame
        currency: Currency symbol
        canonical_metrics: ImpactMetrics object
    """
    # Chart icon (cyan)
    chart_icon = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#06B6D4" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline><polyline points="17 6 23 6 23 12"></polyline></svg>'
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(30, 41, 59, 0.95) 0%, rgba(15, 23, 42, 0.95) 100%); 
                border: 1px solid rgba(148, 163, 184, 0.15); 
                border-left: 3px solid #06B6D4;
                border-radius: 12px; padding: 16px; margin-bottom: 16px;
                box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);">
        <div style="display: flex; align-items: center; gap: 12px;">
            {chart_icon}
            <span style="font-weight: 700; font-size: 1.1rem; color: #F8FAFC; letter-spacing: 0.02em;">ROAS Attribution</span>
        </div>
        <div style="color: #64748B; font-size: 0.85rem; margin-top: 8px; margin-left: 32px;">
            Waterfall analysis of performance drivers
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if impact_df.empty:
        st.info("No data for attribution chart")
        return
    
    # Use attribution data from summary
    baseline_roas = summary.get('baseline_roas', 0)
    actual_roas = summary.get('actual_roas', 0)
    market_impact_roas = summary.get('market_impact_roas', 0)
    
    # Canonical metrics logic
    if canonical_metrics:
        decision_impact_value = canonical_metrics.attributed_impact
        total_spend = canonical_metrics.total_spend
        decision_impact_roas = decision_impact_value / total_spend if total_spend > 0 else 0
    else:
        # Fallback
        decision_impact_roas = 0.0
        decision_impact_value = 0.0

    # Structural components
    scale_effect = summary.get('scale_effect', 0.0)
    portfolio_effect = summary.get('portfolio_effect', 0.0)
    unexplained = summary.get('unexplained', 0.0)
    
    # Calculate Combined Forces
    combined_forces = actual_roas - baseline_roas - decision_impact_roas
    structural_total = scale_effect + portfolio_effect
    
    # Labels
    prior_label = "Baseline"
    actual_label = "Actual"
    
    # Bar Colors
    C_BASELINE = "#475569"   # Slate
    C_COMBINED_NEG = "#DC2626"  # Red
    C_COMBINED_POS = "#10B981"  # Emerald
    C_DECISIONS = "#10B981"  # Emerald (Hero)
    C_ACTUAL = "#06B6D4"     # Cyan (Result)
    
    combined_color = C_COMBINED_POS if combined_forces >= 0 else C_COMBINED_NEG
    
    x_labels = [prior_label, "Combined\nForces", "Decisions", actual_label]
    
    # Bar Values and Bases
    y_vals = []
    bases = []
    colors = []
    borders = []
    text_labels = []
    
    current_lvl = 0.0
    
    # 1. Baseline
    y_vals.append(baseline_roas)
    bases.append(0)
    colors.append(C_BASELINE)
    borders.append("rgba(148, 163, 184, 0.2)")
    text_labels.append(f"{baseline_roas:.2f}")
    current_lvl += baseline_roas
    
    # 2. Combined Forces
    y_vals.append(combined_forces)
    bases.append(current_lvl)
    colors.append(combined_color)
    borders.append("rgba(239, 68, 68, 0.4)" if combined_forces < 0 else "rgba(16, 185, 129, 0.4)")
    text_labels.append(f"{combined_forces:+.2f}")
    current_lvl += combined_forces
    
    # 3. Decisions
    y_vals.append(decision_impact_roas)
    bases.append(current_lvl)
    colors.append(C_DECISIONS)
    borders.append("rgba(16, 185, 129, 0.5)")
    text_labels.append(f"{decision_impact_roas:+.2f}")
    current_lvl += decision_impact_roas
    
    # 4. Actual
    y_vals.append(actual_roas)
    bases.append(0)
    colors.append(C_ACTUAL)
    borders.append("rgba(6, 182, 212, 0.3)")
    text_labels.append(f"{actual_roas:.2f}")
    
    # --- RENDER CHART ---
    fig = go.Figure()
    
    # Main Bars
    fig.add_trace(go.Bar(
        x=x_labels,
        y=y_vals,
        base=bases,
        marker_color=colors,
        marker_line=dict(width=1, color=borders),
        width=0.55,
        text=text_labels,
        textposition='outside',
        textfont=dict(color='white', size=14),
        hoverinfo='x+y+text',
        name=""
    ))
    
    # Connector lines
    conn_x = []
    conn_y = []
    
    # Path 1: Baseline Top to Combined Start
    conn_x.extend([x_labels[0], x_labels[1], None])
    conn_y.extend([baseline_roas, baseline_roas, None])
    
    # Path 2: Combined End to Decisions Start
    comb_end = baseline_roas + combined_forces
    conn_x.extend([x_labels[1], x_labels[2], None])
    conn_y.extend([comb_end, comb_end, None])
    
    # Path 3: Decisions End to Actual Start
    dec_end = comb_end + decision_impact_roas
    conn_x.extend([x_labels[2], x_labels[3], None])
    conn_y.extend([dec_end, dec_end, None])
    
    fig.add_trace(go.Scatter(
        x=conn_x,
        y=conn_y,
        mode='lines',
        line=dict(color='rgba(148, 163, 184, 0.4)', width=2, dash='dash'),
        hoverinfo='skip',
        showlegend=False
    ))
    
    # Dynamic Zoom
    data_points = [0, baseline_roas, baseline_roas + combined_forces, dec_end, actual_roas]
    min_val = min(data_points)
    max_val = max(data_points)
    
    y_range = None
    if max_val > 0:
        zoom_floor = max(0, min_val * 0.5)
        if min_val > 2.0:
            zoom_floor = max(0, min_val - 0.5)
        padding = (max_val - zoom_floor) * 0.15
        y_range = [max(0, zoom_floor - padding), max_val + padding]

    fig.update_layout(
        title="",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter, sans-serif", color='#E2E8F0'),
        showlegend=False,
        height=350,
        margin=dict(l=20, r=20, t=30, b=20),
        yaxis=dict(
            showgrid=True, 
            gridcolor='rgba(148, 163, 184, 0.08)', 
            zeroline=True, 
            zerolinecolor='rgba(148, 163, 184, 0.2)',
            title="ROAS",
            title_font=dict(size=12, color='#94A3B8'),
            tickfont=dict(color='#94A3B8', size=11),
            range=y_range
        ),
        xaxis=dict(
            showgrid=False,
            tickfont=dict(color='#E2E8F0', size=13),
        )
    )
    
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    # --- VISUAL EQUATION ---
    equation_html = (
        f"<div style='text-align: center; color: #E2E8F0; font-weight: 600; font-size: 1.1rem; "
        f"padding: 16px; background: rgba(30, 41, 59, 0.3); border-radius: 8px; margin-top: -10px; margin-bottom: 24px;'>"
        f"<span style='color: #94A3B8'>{baseline_roas:.2f}</span> "
        f"{'-' if combined_forces < 0 else '+'} <span style='color: {'#EF4444' if combined_forces < 0 else '#10B981'}'>{abs(combined_forces):.2f}</span> <span style='font-size: 0.85rem; color: #94A3B8'>(Market)</span> "
        f"{'-' if decision_impact_roas < 0 else '+'} <span style='color: {'#EF4444' if decision_impact_roas < 0 else '#10B981'}'>{abs(decision_impact_roas):.2f}</span> <span style='font-size: 0.85rem; color: #94A3B8'>(Decisions)</span> "
        f"→ <span style='color: #06B6D4'>{actual_roas:.2f} ROAS</span>"
        f"</div>"
    )
    st.markdown(equation_html, unsafe_allow_html=True)
    
    # --- VALUE CREATED BOX ---
    counterfactual_roas = max(0.01, baseline_roas + combined_forces)
    pct_improvement = (decision_impact_roas / counterfactual_roas) * 100 if counterfactual_roas > 0 else 0
    
    if decision_impact_value > 0:
        val_formatted = f"{currency}{decision_impact_value:,.0f}"
        
        value_box_html = (
            f'<div style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(16, 185, 129, 0.05) 100%); '
            f'border: 2px solid rgba(16, 185, 129, 0.4); border-radius: 12px; padding: 28px 32px; '
            f'box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3); margin-top: 24px; margin-bottom: 24px; text-align: center;">'
            f'<div style="color: #10B981; font-size: 0.85rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 12px;">VALUE CREATED</div>'
            f'<div style="color: #10B981; font-size: 2.5rem; font-weight: 800; letter-spacing: -1px; line-height: 1; margin-bottom: 12px;">{val_formatted}</div>'
            f'<div style="color: #94A3B8; font-size: 0.95rem; line-height: 1.5; margin-bottom: 4px;">Without optimizations, ROAS would have been {counterfactual_roas:.2f}</div>'
            f'<div style="color: #10B981; font-size: 0.9rem; font-weight: 600;">You improved performance by {pct_improvement:.0f}%</div>'
            f'</div>'
        )
        st.markdown(value_box_html, unsafe_allow_html=True)
    
    # --- Full Breakdown Expander ---
    with st.expander("Full Breakdown", expanded=False):
        # Data Prep for Text
        prior_metrics = summary.get('prior_metrics', {})
        current_metrics = summary.get('current_metrics', {})
        
        # Calculate % changes for text
        def get_pct_change(key):
            p = prior_metrics.get(key, 0)
            c = current_metrics.get(key, 0)
            return ((c - p) / p * 100) if p > 0 else 0

        cpc_pct = get_pct_change('cpc')
        cvr_pct = get_pct_change('cvr')
        aov_pct = get_pct_change('aov')
        
        cpc_impact = summary.get('cpc_impact', 0)
        cvr_impact = summary.get('cvr_impact', 0)
        aov_impact = summary.get('aov_impact', 0)
        
        col1, col2 = st.columns(2)
        
        # LEFT COLUMN: Market & Structural Forces
        with col1:
            st.markdown(f"**Market & Structural Forces: {combined_forces:+.2f} ROAS**")
            st.divider()
            
            st.markdown(f"""
            <div style="font-size: 14px; font-weight: 600; color: #cccccc; margin-bottom: 8px;">Market Impact: {market_impact_roas:+.2f}</div>
            
            <div style="font-size: 13px; color: #aaaaaa; line-height: 1.6;">
            • CPC {('increased' if cpc_pct >=0 else 'dropped')} {abs(cpc_pct):.1f}% → 
              <span style="color: {'#ff6b6b' if cpc_impact < 0 else '#2ed573'}">{cpc_impact:+.2f} ROAS impact</span><br>
              
            • CVR {('increased' if cvr_pct >=0 else 'dropped')} {abs(cvr_pct):.1f}% → 
              <span style="color: {'#ff6b6b' if cvr_impact < 0 else '#2ed573'}">{cvr_impact:+.2f} ROAS impact</span><br>
              
            • AOV {('increased' if aov_pct >=0 else 'dropped')} {abs(aov_pct):.1f}% → 
              <span style="color: {'#ff6b6b' if aov_impact < 0 else '#2ed573'}">{aov_impact:+.2f} ROAS impact</span>
            </div>
            
            <div style="font-size: 12px; color: #888888; margin-top: 4px;">
            Reconciliation: {cpc_impact:+.2f} {cvr_impact:+.2f} {aov_impact:+.2f} = {market_impact_roas:+.2f} ✓
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("")
            
            st.markdown(f"""
            <div style="font-size: 14px; font-weight: 600; color: #cccccc; margin-bottom: 8px;">Structural Effects: {structural_total:+.2f}</div>
            
            <div style="font-size: 13px; color: #aaaaaa; line-height: 1.6;">
            • Scale effect: {scale_effect:+.2f} (Spend change)<br>
            • Portfolio effect: {portfolio_effect:+.2f} (Campaign mix)<br>
            <span style="font-style: italic; color: #888888;">New campaigns in ramp-up phase (if any)</span>
            </div>
            """, unsafe_allow_html=True)

        # RIGHT COLUMN: Decision Impact
        with col2:
            action_count = 0
            if not impact_df.empty:
                if 'is_mature' in impact_df.columns and 'market_tag' in impact_df.columns:
                    action_count = len(impact_df[(impact_df['is_mature'] == True) & (impact_df['market_tag'] != 'Market Drag')])
                else:
                    action_count = len(impact_df)
                
            st.markdown(f"**Decision Impact: {decision_impact_roas:+.2f} ROAS**")
            st.divider()
            
            st.markdown(f"""
            <div style="font-size: 14px; font-weight: 600; color: #cccccc; margin-bottom: 8px;">Activity:</div>
            <div style="font-size: 13px; color: #aaaaaa; line-height: 1.6;">
            • {action_count} actions executed
            </div>
            
            <br>
            
            <div style="font-size: 14px; font-weight: 600; color: #cccccc; margin-bottom: 8px;">ROAS Contribution:</div>
            <div style="font-size: 13px; color: #aaaaaa; line-height: 1.6;">
            • Added {decision_impact_roas:+.2f} on top of market baseline<br>
            • Offset structural drag of {structural_total:+.2f}<br>
            • Net effect: Created value despite headwinds
            </div>
            """, unsafe_allow_html=True)
            
        # BOTTOM: Attribution Summary Box
        summary_html = "".join([
            '<div style="background-color: #0f1624; border: 1px solid #2d3748; border-radius: 8px; padding: 20px; margin-top: 20px;">',
            '  <div style="color: #cccccc; font-size: 13px; font-weight: 600; margin-bottom: 10px;">Attribution Summary</div>',
            '  <div style="display: flex; justify-content: space-between; margin-bottom: 15px;">',
            '    <div style="color: #aaaaaa; font-size: 13px;">',
            '      Counterfactual Analysis:<br>',
            f'      Without decisions → <b>{(baseline_roas + combined_forces):.2f} ROAS</b> (Market + Structural)<br>',
            f'      With decisions → <b>{actual_roas:.2f} ROAS</b> (Actual achieved)',
            '    </div>',
            '  </div>',
            '  <div style="color: #aaaaaa; font-size: 13px; line-height: 1.6; margin-bottom: 15px;">',
            f'    Explanation: Market conditions impact ({market_impact_roas:+.2f} ROAS) combined with structural effects from growth ',
            f'    ({structural_total:+.2f}) was offset by {action_count} optimizations ({decision_impact_roas:+.2f}), ',
            '    delivering result.',
            '  </div>',
            '  <div style="border-top: 1px solid #2d3748; padding-top: 10px; display: flex; justify-content: space-between; font-size: 12px; color: #888888;">',
            '    <div>Attribution Quality: <span style="color: #2ed573;">✓ Clean</span></div>',
            f'    <div>Unexplained residual: {unexplained:+.2f} ROAS</div>',
            '  </div>',
            '</div>'
        ])
        st.markdown(summary_html, unsafe_allow_html=True)
