"""
Overview Tab Module - Optimization Summary Dashboard

Displays optimization overview with impact forecast and quick actions.
Separated from optimizer.py for cleaner maintenance and faster loading.
"""

import streamlit as st
import pandas as pd
from typing import Dict


def render_overview_tab(results: Dict) -> None:
    """
    Render the Overview/Dashboard tab with simulation and key metrics.
    
    Args:
        results: Dictionary containing optimization results including:
            - direct_bids, agg_bids: Bid recommendations
            - harvest: Harvest candidates
            - simulation: Impact forecast
            - df: Raw data DataFrame
            - neg_kw, neg_pt: Negative recommendations
    """
    icon_color = "#8F8CA3"
    overview_icon = f'<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="{icon_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 8px;"><rect width="18" height="18" x="3" y="3" rx="2"/><path d="M7 12v5"/><path d="M12 9v8"/><path d="M17 11v6"/></svg>'
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(124, 58, 237, 0.05) 0%, rgba(91, 33, 182, 0.05) 100%);
                border: 1px solid rgba(124, 58, 237, 0.1);
                border-radius: 12px;
                padding: 16px 20px;
                margin-bottom: 24px;
                display: flex;
                align-items: center;
                gap: 12px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
        {overview_icon}
        <div>
            <span style="color: #F5F5F7; font-size: 1.1rem; font-weight: 700; letter-spacing: 0.5px; display: block;">Optimization Overview</span>
            <span style="color: #8F8CA3; font-size: 0.85rem; font-weight: 400;">Performance snapshot & recommended actions</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Extract data
    direct_bids = results.get("direct_bids", pd.DataFrame())
    agg_bids = results.get("agg_bids", pd.DataFrame())
    harvest = results.get("harvest", pd.DataFrame())
    simulation = results.get("simulation")
    df = results.get("df", pd.DataFrame())
    neg_kw = results.get("neg_kw", pd.DataFrame())
    neg_pt = results.get("neg_pt", pd.DataFrame())
    
    # Calculate summary metrics
    total_bids = len(direct_bids) + len(agg_bids) if direct_bids is not None and agg_bids is not None else 0
    total_negatives = (len(neg_kw) if neg_kw is not None else 0) + (len(neg_pt) if neg_pt is not None else 0)
    total_harvests = len(harvest) if harvest is not None else 0
    
    # Current performance metrics
    if not df.empty:
        total_spend = df['Spend'].sum()
        total_sales = df['Sales'].sum()
        current_roas = total_sales / total_spend if total_spend > 0 else 0
        current_acos = (total_spend / total_sales * 100) if total_sales > 0 else 0
    else:
        total_spend = total_sales = current_roas = current_acos = 0
    
    # Display simulation if available and has data
    if simulation and simulation.get('summary'):
        st.markdown("### 📊 Impact Forecast")
        
        # Extract simulation metrics
        summary = simulation.get('summary', {})
        
        st.markdown("""
        <div style="background: rgba(255, 255, 255, 0.03); 
                    border: 1px solid rgba(255, 255, 255, 0.05); 
                    border-left: 4px solid #7C3AED; 
                    padding: 16px 24px; 
                    border-radius: 8px; 
                    margin-bottom: 24px;
                    backdrop-filter: blur(10px);">
            <p style="color: #B6B4C2; font-size: 0.95rem; margin: 0; display: flex; align-items: center; gap: 8px;">
                <span>📈</span>
                <strong>Projected Impact</strong>: Based on historical performance and bid elasticity modeling
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Display forecast metrics
        from utils.formatters import get_account_currency
        currency = get_account_currency()
        
        c1, c2, c3, c4 = st.columns(4)
        
        with c1:
            spend_change = summary.get('spend_change_pct', 0)
            st.metric("Spend Change", f"{spend_change:+.1f}%", 
                     delta=f"{currency}{summary.get('spend_change_abs', 0):,.2f}")
        
        with c2:
            sales_change = summary.get('sales_change_pct', 0)
            st.metric("Sales Change", f"{sales_change:+.1f}%",
                     delta=f"{currency}{summary.get('sales_change_abs', 0):,.2f}")
        
        with c3:
            roas_new = summary.get('roas_new', 0)
            roas_current = summary.get('roas_current', 0)
            roas_delta = roas_new - roas_current
            st.metric("Projected ROAS", f"{roas_new:.2f}x",
                     delta=f"{roas_delta:+.2f}x")
        
        with c4:
            profit_impact = summary.get('profit_impact', 0)
            st.metric("Profit Impact", f"{currency}{profit_impact:,.2f}",
                     delta="Estimated" if profit_impact > 0 else None)
        
        st.divider()
    
    # Quick actions
    st.markdown("### Quick Actions")
    st.markdown("""
    <p style="color: #B6B4C2; font-size: 0.9rem; margin-bottom: 16px;">
        Navigate to specific tabs above to review detailed recommendations
    </p>
    """, unsafe_allow_html=True)
    
    qa1, qa2, qa3 = st.columns(3)
    
    def render_card(icon, title, subtitle, border_color="#7C3AED"):
        st.markdown(f"""
        <div class="custom-metric-card" style="background: linear-gradient(135deg, rgba(255, 255, 255, 0.03) 0%, rgba(255, 255, 255, 0.01) 100%);
                    border: 1px solid rgba(255, 255, 255, 0.05);
                    border-radius: 12px;
                    padding: 20px;
                    height: 100%;
                    position: relative;
                    overflow: hidden;">
            <div style="position: absolute; top: 0; left: 0; width: 4px; height: 100%; background: {border_color}; opacity: 0.8;"></div>
            <div style="font-size: 1.8rem; margin-bottom: 12px;">{icon}</div>
            <div style="font-weight: 700; font-size: 1.1rem; color: #F5F5F7; margin-bottom: 6px;">{title}</div>
            <div style="font-size: 0.85rem; color: #8F8CA3; line-height: 1.4;">{subtitle}</div>
        </div>
        """, unsafe_allow_html=True)

    with qa1:
        if total_negatives > 0:
            render_card("🛡️", f"{total_negatives} Negatives", "Identified for removal to preserve budget. Review in Defence tab.", "#EF4444")
        else:
             render_card("🛡️", "No Negatives", "Your defence is optimized.", "#10B981")


    with qa2:
        if total_bids > 0:
            render_card("📊", f"{total_bids} Bid Updates", "Adjustments ready to optimize spend efficiency. Review in Bids tab.", "#3B82F6")
        else:
             render_card("📊", "Bids Optimized", "No bid changes recommended.", "#10B981")
    
    with qa3:
        if total_harvests > 0:
            render_card("🌱", f"{total_harvests} Harvests", "New high-performing targets found. Review in Harvest tab.", "#10B981")
        else:
             render_card("🌱", "No Harvests", "No new harvest candidates found.", "#8F8CA3")
