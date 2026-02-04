import streamlit as st
import pandas as pd
from .components import render_metric_card
from .charts import render_spend_reallocation_chart, render_action_distribution_chart
from utils.formatters import get_account_currency, format_currency, dataframe_to_excel

def render_results_dashboard(results: dict):
    """
    Renders the post-optimization results dashboard.

    Args:
        results (dict): Dictionary containing optimization results (df, harvest, neg_kw, etc.)
    """
    # 1. Extract Data
    # === PREMIUM STYLES ===
    st.markdown("""
    <style>
    /* Global Background & Typography */
    .stApp {
        background-color: #0a0f1a;
        background-image: 
            radial-gradient(at 0% 0%, rgba(45, 212, 191, 0.03) 0px, transparent 50%),
            radial-gradient(at 100% 0%, rgba(6, 182, 212, 0.03) 0px, transparent 50%);
    }

    /* Glassmorphic Card Base (Linear-style) */
    .glass-card {
        background: rgba(30, 41, 59, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
        backdrop-filter: blur(10px);
        margin-bottom: 24px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .glass-card:hover {
        border-color: rgba(255, 255, 255, 0.08);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.3);
    }

    /* Save Run Hero Section - Special Glow */
    .save-run-container {
        position: relative;
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.6) 0%, rgba(15, 23, 42, 0.8) 100%);
        border: 1px solid rgba(45, 212, 191, 0.2);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 40px;
        box-shadow: 0 0 0 1px rgba(45, 212, 191, 0.1), 0 10px 40px rgba(0, 0, 0, 0.4);
        overflow: hidden;
    }

    /* Subtle pulsing accent line for Save Run */
    .save-run-container::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
        background: linear-gradient(to bottom, #2dd4bf, #06b6d4);
        box-shadow: 0 0 15px rgba(45, 212, 191, 0.6);
    }

    /* Typography Hierarchy */
    h2, h3, h4 {
        color: #f8fafc !important;
        font-family: 'Inter', sans-serif;
        letter-spacing: -0.01em;
    }

    .metric-label {
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #64748b;
        margin-bottom: 8px;
    }

    .metric-value-hero {
        font-size: 32px;
        font-weight: 700;
        background: linear-gradient(135deg, #2dd4bf 0%, #06b6d4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.02em;
        text-shadow: 0 10px 30px rgba(45, 212, 191, 0.2);
    }

    .metric-value-primary {
        font-size: 24px;
        font-weight: 600;
        color: #f1f5f9;
        letter-spacing: -0.01em;
    }

    .metric-subtext {
        font-size: 13px;
        color: #94a3b8;
        font-weight: 500;
        display: flex;
        align-items: center;
        gap: 6px;
        margin-top: 4px;
    }

    /* Tabs - Pill Style */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
    }

    .stTabs [data-baseweb="tab"] {
        height: 40px;
        white-space: nowrap;
        background-color: rgba(30, 41, 59, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        color: #94a3b8;
        padding: 0 20px;
        font-size: 13px;
        font-weight: 500;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(45, 212, 191, 0.15) 0%, rgba(6, 182, 212, 0.1) 100%);
        border-color: rgba(45, 212, 191, 0.3);
        color: #2dd4bf;
        text-shadow: 0 0 20px rgba(45, 212, 191, 0.4);
    }
    </style>
    """, unsafe_allow_html=True)
    harvest = results.get("harvest", pd.DataFrame())
    neg_kw = results.get("neg_kw", pd.DataFrame())
    neg_pt = results.get("neg_pt", pd.DataFrame())
    bids_ex = results.get("bids_exact", pd.DataFrame())
    bids_pt = results.get("bids_pt", pd.DataFrame())
    bids_agg = results.get("bids_agg", pd.DataFrame())
    bids_auto = results.get("bids_auto", pd.DataFrame())
    simulation = results.get("simulation", {})

    # Consolidate Bids
    direct_bids = pd.concat([bids_ex, bids_pt]) if not bids_ex.empty or not bids_pt.empty else pd.DataFrame()
    agg_bids = pd.concat([bids_agg, bids_auto]) if not bids_agg.empty or not bids_auto.empty else pd.DataFrame()

    all_bids = pd.concat([direct_bids, agg_bids]) if not direct_bids.empty or not agg_bids.empty else pd.DataFrame()

    # 2. Calculate Display Metrics (Aggregation only - NO new logic)
    action_count = len(harvest) + len(neg_kw) + len(neg_pt) + len(all_bids)

    bid_count = len(all_bids)
    neg_count = len(neg_kw) + len(neg_pt)
    harv_count = len(harvest)

    # Calculate Savings / Waste Prevented
    neg_spend_saving = 0
    if not neg_kw.empty and "Spend" in neg_kw.columns:
        neg_spend_saving += neg_kw["Spend"].sum()
    if not neg_pt.empty and "Spend" in neg_pt.columns:
        neg_spend_saving += neg_pt["Spend"].sum()

    # Calculate bid impact
    bid_saving = 0
    reallocated = 0
    net_velocity = 0

    if not all_bids.empty and "New Bid" in all_bids.columns and "Clicks" in all_bids.columns:
        # Determine which column to use for current bid
        current_bid_col = None
        if "Current Bid" in all_bids.columns:
            current_bid_col = "Current Bid"
        elif "CPC" in all_bids.columns:
            current_bid_col = "CPC"

        if current_bid_col:
            # Simple projection: (Old Bid - New Bid) * Clicks
            all_bids["_diff"] = (all_bids[current_bid_col] - all_bids["New Bid"]) * all_bids["Clicks"]
            bid_saving = all_bids[all_bids["_diff"] > 0]["_diff"].sum()
            reallocated = abs(all_bids[all_bids["_diff"] < 0]["_diff"].sum())
            
            # Net Velocity Calculation
            velocity_series = (all_bids["New Bid"] - all_bids[current_bid_col]) * all_bids["Clicks"]
            net_velocity = velocity_series.sum()

    total_waste_prevented = neg_spend_saving + bid_saving

    # Calculate Total Spend Reference (Moved Up for Efficiency Calc)
    total_spend_ref = 0
    if "df" in results and isinstance(results["df"], pd.DataFrame) and "Spend" in results["df"].columns:
        total_spend_ref = results["df"]["Spend"].sum()

    # Calculate Total Impact
    total_impact = neg_spend_saving + bid_saving - reallocated
    
    # Calculate Efficiency % (Priority: Forecasted ROAS Lift)
    # User Request: "efficiency gain should be based on the forecasted ROAS"
    impact_pct = 0
    used_simulation_metric = False

    if simulation and "scenarios" in simulation:
        scenarios = simulation["scenarios"]
        
        # Structure check: is it 'current'/'expected' or 'balanced'/'aggressive'?
        # Assuming typical structure where "expected" is the chosen outcome
        current_metrics = scenarios.get("current", {})
        expected_metrics = scenarios.get("expected", {})
        
        # If 'expected' missing, try 'balanced' as default
        if not expected_metrics:
            expected_metrics = scenarios.get("balanced", {})

        current_roas = float(current_metrics.get("roas", 0) or 0)
        expected_roas = float(expected_metrics.get("roas", 0) or 0)

        if current_roas > 0 and expected_roas > 0:
            impact_pct = (expected_roas - current_roas) / current_roas
            used_simulation_metric = True

    # Fallback: if simulation didn't work, calculate from spend share
    if not used_simulation_metric:
        if total_spend_ref > 0:
            impact_pct = (total_impact / total_spend_ref)

    # 3. Save Run Tile (Refactored to include buttons inside)
    # Using specific container for CSS targeting
    # 3. Save Run Tile (Refactored to include buttons inside)
    # Using specific container for CSS targeting
    # 3. Save Run Tile - Native Layout Implementation
    st.markdown("""
    <style>
    /* Target ONLY the innermost container that holds our marker */
    /* This prevents parents from also getting the style */
    div[data-testid="stVerticalBlock"]:has(.save-run-marker):not(:has(div[data-testid="stVerticalBlock"])) {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.6) 0%, rgba(15, 23, 42, 0.8) 100%);
        border: 1px solid rgba(45, 212, 191, 0.2) !important;
        border-radius: 16px !important;
        padding: 24px !important;
        margin-bottom: 40px;
        box-shadow: 0 0 0 1px rgba(45, 212, 191, 0.1), 0 10px 40px rgba(0, 0, 0, 0.4);
        overflow: hidden;
        position: relative;
    }

    /* Accent line pseudo-element */
    div[data-testid="stVerticalBlock"]:has(.save-run-marker):not(:has(div[data-testid="stVerticalBlock"]))::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
        background: linear-gradient(to bottom, #2dd4bf, #06b6d4);
        box-shadow: 0 0 15px rgba(45, 212, 191, 0.6);
        z-index: 1;
    }
    
    /* Ensure content is above background */
    div[data-testid="stVerticalBlock"]:has(.save-run-marker) > div {
        position: relative;
        z-index: 2;
    }
    </style>
    """, unsafe_allow_html=True)

    with st.container():
        # Marker to trigger the CSS styling on this specific container
        st.markdown('<span class="save-run-marker"></span>', unsafe_allow_html=True)
        
        c_content, c_btns = st.columns([3, 1], gap="large")
        
        with c_content:
            st.markdown("""
            <div style="display: flex; gap: 16px; align-items: flex-start;">
                <div style="
                    width: 48px; height: 48px; 
                    background: radial-gradient(circle at center, rgba(45, 212, 191, 0.2), transparent 70%); 
                    border: 1px solid rgba(45, 212, 191, 0.3);
                    border-radius: 12px; 
                    display: flex; align-items: center; justify-content: center; 
                    font-size: 20px; color: #2dd4bf; 
                    box-shadow: 0 0 15px rgba(45, 212, 191, 0.2);
                    flex-shrink: 0;">
                    🏁
                </div>
                <div>
                    <h3 style="margin: 0 0 8px 0; font-size: 18px; font-weight: 600; letter-spacing: -0.01em; color: #f8fafc;">Save This Optimization Run</h3>
                    <p style="color: #cbd5e1; margin: 0; font-size: 15px; line-height: 1.5; font-weight: 600;">
                        After downloading your files, save this run to track actual vs. predicted performance in Impact Analysis.
                    </p>
                    <div style="
                        display: inline-flex; align-items: center; gap: 6px;
                        background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.2);
                        color: #fbbf24; padding: 4px 10px; border-radius: 6px; 
                        font-size: 12px; font-weight: 500; margin-top: 12px;">
                        ⚠️ Unsaved runs cannot be measured
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with c_btns:
            # Buttons are now natively in the same container/row
            st.markdown('<div style="height: 4px"></div>', unsafe_allow_html=True) # Visual alignment tweak
            if st.button("💾 Save to History", type="primary", use_container_width=True, key="btn_save_run_hero"):
                st.session_state["trigger_save"] = True
                st.toast("Saving run...", icon="💾")
            
            st.markdown('<div style="height: 6px"></div>', unsafe_allow_html=True)
            
            if st.button("🔄 Rerun Optimizer", type="secondary", use_container_width=True, key="btn_rerun_opt"):
                if 'optimizer_results_refactored' in st.session_state:
                    del st.session_state['optimizer_results_refactored']
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # 4. Metrics Dashboard Header
    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;">
        <h2 style="margin: 0; color: #f1f5f9; font-size: 20px; font-weight: 600;">Optimization Summary</h2>
        <div style="display: flex; align-items: center; gap: 12px;">
            <span style="color: #94a3b8; font-size: 13px;">Last run: Just now</span>
            <span style="background: rgba(34, 197, 94, 0.1); color: #22c55e; padding: 4px 12px; border-radius: 100px; font-size: 12px; font-weight: 500;">✓ Complete</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 5. Metrics Grid (4 Columns as requested)
    m1, m2, m3, m4 = st.columns([1.5, 1, 1, 1])

    # Calculate bid increase/decrease counts safely
    bid_inc_count = 0
    bid_dec_count = 0
    if not all_bids.empty and "New Bid" in all_bids.columns:
        if "Current Bid" in all_bids.columns:
            bid_inc_count = len(all_bids[all_bids['New Bid'] > all_bids['Current Bid']])
            bid_dec_count = len(all_bids[all_bids['New Bid'] < all_bids['Current Bid']])
        elif "CPC" in all_bids.columns:
            bid_inc_count = len(all_bids[all_bids['New Bid'] > all_bids['CPC']])
            bid_dec_count = len(all_bids[all_bids['New Bid'] < all_bids['CPC']])

    # Get currency symbol for other cards
    currency = get_account_currency()

    with m1:
        # HERO CARD: EFFICIENCY (ROAS LIFT)
        eff_color = "#2dd4bf" if impact_pct > 0 else "#f59e0b"
        st.markdown(f"""
        <div class="glass-card" style="height: 100%; display: flex; flex-direction: column; justify-content: center; border-left: 3px solid {eff_color};">
            <div class="metric-label">Projected Efficiency</div>
            <div class="metric-value-hero">{impact_pct:+.1%}</div>
            <div class="metric-subtext" style="color: {eff_color};">Forecasted ROAS Lift</div>
        </div>
        """, unsafe_allow_html=True)

    with m2:
        # BID ACTIONS
        velocity_color = "#fbbf24" if net_velocity > 0 else "#22c55e" # Orange if invest, Green if save
        velocity_label = f"+{currency}{net_velocity:,.0f} Invest" if net_velocity > 0 else f"-{currency}{abs(net_velocity):,.0f} Savings"
        st.markdown(f"""
        <div class="glass-card" style="height: 100%;">
            <div class="metric-label">Bid Actions</div>
            <div class="metric-value-primary">{bid_count:,}</div>
            <div class="metric-subtext">
                <span style="color: {velocity_color};">{velocity_label}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with m3:
        # NEGATIVES
        st.markdown(f"""
        <div class="glass-card" style="height: 100%;">
            <div class="metric-label">Negatives</div>
            <div class="metric-value-primary">{neg_count:,}</div>
            <div class="metric-subtext">
                <span style="color: #94a3b8;">{currency}{neg_spend_saving:,.0f}</span> Waste Blocked
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with m4:
        # HARVEST
        harvest_value = harvest["Sales"].sum() if not harvest.empty and "Sales" in harvest.columns else 0
        st.markdown(f"""
        <div class="glass-card" style="height: 100%;">
            <div class="metric-label">Harvest</div>
            <div class="metric-value-primary">{harv_count:,}</div>
            <div class="metric-subtext">
                <span style="color: #94a3b8;">{currency}{harvest_value:,.0f}</span> Sales Vol
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 6. Visual Impact Analysis (Header Removed)
    vc1, vc2 = st.columns([1.5, 1])

    # Calculate total spend reference
    total_spend_ref = 500000  # Default/Fallback
    if "df" in results and isinstance(results["df"], pd.DataFrame) and "Spend" in results["df"].columns:
        total_spend_ref = results["df"]["Spend"].sum()

    with vc1:
        render_spend_reallocation_chart(total_spend_ref, neg_spend_saving, bid_saving, reallocated, currency)
    with vc2:
        render_action_distribution_chart(action_count, bid_count, neg_count, harv_count)

    st.divider()

    # 7. Tab Navigation
    tabs = ["Overview", "Negatives", "Bids", "Harvest", "Audit", "Downloads"]

    # Active tab state handling
    if "active_opt_tab" not in st.session_state:
        st.session_state["active_opt_tab"] = "Overview"

    # Render Custom Tab Bar
    st.markdown("""
    <div style="background: rgba(30, 41, 59, 0.3); padding: 6px; border-radius: 12px; margin-bottom: 24px;">
    </div>
    """, unsafe_allow_html=True)

    t_cols = st.columns(len(tabs))
    for i, tab in enumerate(tabs):
        with t_cols[i]:
            # Style button based on active state
            if st.button(tab, key=f"tab_{tab}", use_container_width=True,
                        type="primary" if st.session_state["active_opt_tab"] == tab else "secondary"):
                st.session_state["active_opt_tab"] = tab
                st.rerun()

    # 8. Tab Content
    active = st.session_state["active_opt_tab"]

    if active == "Overview":
        st.markdown("### Overview")
        st.caption("Detailed breakdown by campaign type")

        # Create overview summary
        if not all_bids.empty or not neg_kw.empty or not neg_pt.empty or not harvest.empty:
            overview_data = {
                "Category": ["Bid Adjustments", "Negative Keywords", "Negative ASINs", "Harvest Targets"],
                "Count": [bid_count, len(neg_kw), len(neg_pt), harv_count],
                "Status": ["Ready", "Ready", "Ready", "Ready"]
            }
            st.dataframe(pd.DataFrame(overview_data), use_container_width=True, hide_index=True)
        else:
            st.info("No optimization actions generated.")

    elif active == "Negatives":
        st.markdown("### Negative Keywords & ASINs")

        # Combine negatives
        all_negs = pd.concat([neg_kw, neg_pt]) if not neg_kw.empty or not neg_pt.empty else pd.DataFrame()

        if not all_negs.empty:
            # Mini stats
            nc1, nc2, nc3, nc4 = st.columns(4)
            with nc1:
                st.metric("Keyword Negatives", len(neg_kw))
            with nc2:
                st.metric("ASIN Negatives", len(neg_pt))
            with nc3:
                total_neg_spend = neg_spend_saving
                st.metric("Waste Blocked", f"{currency}{total_neg_spend:,.0f}")
            with nc4:
                avg_clicks = all_negs["Clicks"].mean() if "Clicks" in all_negs.columns else 0
                st.metric("Avg. Clicks", f"{avg_clicks:.1f}")

            st.markdown("<br>", unsafe_allow_html=True)
            st.dataframe(all_negs, use_container_width=True)
        else:
            st.info("No negative recommendations generated.")

    elif active == "Bids":
        st.markdown("### Bid Adjustments")

        if not all_bids.empty:
            # Mini stats
            bc1, bc2, bc3, bc4 = st.columns(4)
            with bc1:
                st.metric("Total Adjustments", bid_count)
            with bc2:
                st.metric("Bid Increases", bid_inc_count, delta="Growth")
            with bc3:
                st.metric("Bid Decreases", bid_dec_count, delta="Savings", delta_color="inverse")
            with bc4:
                avg_roas = all_bids["ROAS"].mean() if "ROAS" in all_bids.columns else 0
                st.metric("Avg. ROAS", f"{avg_roas:.2f}x")

            st.markdown("<br>", unsafe_allow_html=True)
            st.dataframe(all_bids, use_container_width=True)
        else:
            st.info("No bid adjustments generated.")

    elif active == "Harvest":
        st.markdown("### Harvest Candidates")

        if not harvest.empty:
            # Mini stats
            hc1, hc2, hc3, hc4 = st.columns(4)
            with hc1:
                st.metric("Harvest Targets", harv_count)
            with hc2:
                total_harv_spend = harvest["Spend"].sum() if "Spend" in harvest.columns else 0
                st.metric("Potential Shift", f"{currency}{total_harv_spend:,.0f}")
            with hc3:
                avg_cr = harvest["CR7"].mean() if "CR7" in harvest.columns else 0
                st.metric("Avg. Conv. Rate", f"{avg_cr:.1%}")
            with hc4:
                # Link to Campaign Creator
                if st.button("🚀 Launch in Campaign Creator", key="btn_goto_harvest_creator", use_container_width=True, type="primary"):
                    st.session_state['harvest_payload'] = harvest
                    st.session_state['active_creator_tab'] = "Harvest Winners"
                    st.session_state['current_module'] = 'creator'
                    st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)
            st.dataframe(harvest, use_container_width=True)
        else:
            st.info("No harvest candidates identified.")

    elif active == "Audit":
        # Reuse the comprehensive Legacy Audit Tab renderer
        from features.audit_tab import render_audit_tab
        
        # Check if audit/heatmap data exists
        if "heatmap" in results and isinstance(results["heatmap"], pd.DataFrame):
            render_audit_tab(results["heatmap"])
        else:
            st.info("Audit data not available in this optimization run.")

    elif active == "Downloads":
        st.markdown("### Export Results")
        st.caption("Download optimization actions as Amazon-ready bulk files")

        # Import bulk export functions
        from features.bulk_export import generate_negatives_bulk, generate_bids_bulk, generate_harvest_bulk

        # Export Cards Grid
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("""
            <div style="background: rgba(30, 41, 59, 0.4); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 16px; padding: 24px; height: 280px; display: flex; flex-direction: column;">
                <div style="width: 48px; height: 48px; background: rgba(45, 212, 191, 0.1); border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 24px; margin-bottom: 16px;">
                    🛡️
                </div>
                <h4 style="margin: 0 0 8px 0; color: #f1f5f9; font-size: 16px; font-weight: 600;">Negative Keywords</h4>
                <div style="display: flex; align-items: center; gap: 8px; font-size: 14px; color: #94a3b8; margin-bottom: 16px;">
                    <span style="color: #22c55e;">✓</span>
                    <span>{neg_count:,} terms ready</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if not neg_kw.empty or not neg_pt.empty:
                neg_bulk_df, neg_issues = generate_negatives_bulk(neg_kw, neg_pt)
                
                # Preview Window
                with st.expander("👁️ Preview File", expanded=False):
                    st.dataframe(neg_bulk_df, use_container_width=True, height=200)

                neg_xlsx = dataframe_to_excel(neg_bulk_df)
                st.download_button(
                    "📥 Download Negatives (.xlsx)",
                    neg_xlsx,
                    "negatives_bulk.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
                if neg_issues:
                    with st.expander(f"⚠️ {len(neg_issues)} validation issues"):
                        for issue in neg_issues[:5]:  # Show first 5
                            st.caption(f"• {issue.get('msg', 'Unknown issue')}")
            else:
                st.button("📥 Download Negatives", disabled=True, use_container_width=True)

        with col2:
            st.markdown(f"""
            <div style="background: rgba(30, 41, 59, 0.4); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 16px; padding: 24px; height: 280px; display: flex; flex-direction: column;">
                <div style="width: 48px; height: 48px; background: rgba(45, 212, 191, 0.1); border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 24px; margin-bottom: 16px;">
                    📈
                </div>
                <h4 style="margin: 0 0 8px 0; color: #f1f5f9; font-size: 16px; font-weight: 600;">Bid Adjustments</h4>
                <div style="display: flex; align-items: center; gap: 8px; font-size: 14px; color: #94a3b8; margin-bottom: 16px;">
                    <span style="color: #22c55e;">✓</span>
                    <span>{bid_count:,} bids ready</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if not all_bids.empty:
                bids_bulk_df, bids_issues = generate_bids_bulk(all_bids)
                
                # Preview Window
                with st.expander("👁️ Preview File", expanded=False):
                    st.dataframe(bids_bulk_df, use_container_width=True, height=200)

                bids_xlsx = dataframe_to_excel(bids_bulk_df)
                st.download_button(
                    "📥 Download Bids (.xlsx)",
                    bids_xlsx,
                    "bids_bulk.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
                if bids_issues:
                    with st.expander(f"⚠️ {len(bids_issues)} validation issues"):
                        for issue in bids_issues[:5]:
                            st.caption(f"• {issue.get('msg', 'Unknown issue')}")
            else:
                st.button("📥 Download Bids", disabled=True, use_container_width=True)

        with col3:
            st.markdown(f"""
            <div style="background: rgba(30, 41, 59, 0.4); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 16px; padding: 24px; height: 280px; display: flex; flex-direction: column;">
                <div style="width: 48px; height: 48px; background: rgba(45, 212, 191, 0.1); border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 24px; margin-bottom: 16px;">
                    🌾
                </div>
                <h4 style="margin: 0 0 8px 0; color: #f1f5f9; font-size: 16px; font-weight: 600;">Harvest Targets</h4>
                <div style="display: flex; align-items: center; gap: 8px; font-size: 14px; color: #94a3b8; margin-bottom: 16px;">
                    <span style="color: #22c55e;">✓</span>
                    <span>{harv_count:,} targets ready</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if not harvest.empty:
                harv_bulk_df = generate_harvest_bulk(harvest)

                # Preview Window
                with st.expander("👁️ Preview File", expanded=False):
                    st.dataframe(harv_bulk_df, use_container_width=True, height=200)

                harv_xlsx = dataframe_to_excel(harv_bulk_df)
                st.download_button(
                    "📥 Download Harvest (.xlsx)",
                    harv_xlsx,
                    "harvest_bulk.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            else:
                st.button("📥 Download Harvest", disabled=True, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Bulk Download All
        st.markdown("""
        <div style="text-align: center; padding-top: 24px; border-top: 1px solid rgba(255, 255, 255, 0.06);">
            <p style="color: #94a3b8; font-size: 13px; margin-bottom: 16px;">Download all optimization files at once</p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("📦 Download All Files (ZIP)", type="primary", use_container_width=True):
            st.info("Bulk download feature coming soon!")
