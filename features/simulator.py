import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Optional, Dict, Any
from ui.components import metric_card

from features._base import BaseFeature

class SimulatorModule(BaseFeature):
    """Standalone module for Bid Change Simulation and Forecasting."""
    
    def validate_data(self, data: pd.DataFrame) -> tuple[bool, str]:
        """Validate input data - Simulator relies on Optimizer state, not direct input."""
        if 'latest_optimizer_run' in st.session_state:
            return True, ""
        return False, "Optimizer validation needed"

    def analyze(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze data - Simulator uses pre-computed optimization data."""
        return {}

    def render_ui(self):
        """Render the Simulator UI."""
        self.render_header("Simulator", "simulator")
        # Logic from previous run() method will be moved here or called from here
        self._run_logic()

    def run(self):
        """Main execution method for the Simulator module."""
        self.render_ui()

    def _run_logic(self):
        """Internal logic for the simulator UI components."""
        
        # Dependency Check
        if 'latest_optimizer_run' not in st.session_state:
            self._render_empty_state()
            return
            
        # Retrieve optimization data
        r = st.session_state['latest_optimizer_run']
        sim = r.get("simulation")
        date_info = r.get("date_info", {})
        
        # Check if simulation data exists within the run
        if sim is None:
            st.warning("⚠️ Simulation data not found in the latest optimization run.")
            st.info("Go to **Optimizer**, ensure 'Include Simulation' is checked in Settings, and click 'Run Optimization'.")
            if st.button("Go to Optimizer", type="primary"):
                st.session_state['current_module'] = 'optimizer'
                st.rerun()
            return
            
        self._display_simulation(sim, date_info)

    def _render_empty_state(self):
        """Render prompt when no data is available."""
        st.warning("⚠️ No optimization data available.")
        st.markdown("""
        The Simulator requires an active optimization run to forecast changes.
        
        **Steps to Activate:**
        1. Go to **Optimizer**
        2. Configure your settings (Bids, Harvest, Negatives)
        3. Ensure **"Include Simulation"** is checked
        4. Click **"Run Optimization"**
        """)
        
        if st.button("Go to Optimizer", type="primary"):
            st.session_state['current_module'] = 'optimizer'
            st.rerun()

    def _display_simulation(self, sim: dict, date_info: dict):
        """Display advanced simulation results."""
        


        
        # Diagnostics
        diag = sim.get("diagnostics", {})
        c1, c2, c3, c4 = st.columns(4)
        with c1: metric_card("📝 Bid Recommendations", f"{diag.get('total_recommendations', 0):,}")
        with c2: metric_card("✅ Actual Changes", f"{diag.get('actual_changes', 0):,}")
        with c3: metric_card("⏸️ Hold (No Change)", f"{diag.get('hold_count', 0):,}")
        with c4: metric_card("💎 Harvest Campaigns", f"{diag.get('harvest_count', 0):,}")
        
        st.divider()
        
        # Performance Forecast
        st.subheader("📈 Performance Forecast")
        st.info(f"📅 **Data Period:** {date_info.get('label', 'Unknown')} — All metrics projected to **monthly** estimates")
        
        scenarios = sim.get("scenarios", {})
        current = scenarios.get("current", {})
        expected = scenarios.get("expected", {})
        
        # Convert weekly to monthly (multiply by 4.33)
        weekly_to_monthly = 4.33
        
        # Monthly figures
        current_monthly = {
            "spend": current.get("spend", 0) * weekly_to_monthly,
            "sales": current.get("sales", 0) * weekly_to_monthly,
            "orders": current.get("orders", 0) * weekly_to_monthly,
            "roas": current.get("roas", 0)  # ROAS doesn't change with scale
        }
        expected_monthly = {
            "spend": expected.get("spend", 0) * weekly_to_monthly,
            "sales": expected.get("sales", 0) * weekly_to_monthly,
            "orders": expected.get("orders", 0) * weekly_to_monthly,
            "roas": expected.get("roas", 0)
        }
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Current Performance (Monthly Estimate)**")
            m1, m2 = st.columns(2)
            with m1: metric_card("Monthly Spend", f"AED {current_monthly['spend']:,.0f}")
            with m2: metric_card("Monthly Sales", f"AED {current_monthly['sales']:,.0f}")
            m3, m4 = st.columns(2)
            with m3: metric_card("ROAS", f"{current_monthly['roas']:.2f}x")
            with m4: metric_card("Monthly Orders", f"{current_monthly['orders']:.0f}")
        
        with col2:
            st.markdown("**Forecasted Performance (Monthly Estimate)**")
            
            def pct_change(new, old):
                return ((new - old) / old * 100) if old > 0 else 0
            
            m1, m2 = st.columns(2)
            spend_chg = pct_change(expected_monthly["spend"], current_monthly["spend"])
            sales_chg = pct_change(expected_monthly["sales"], current_monthly["sales"])
            
            with m1: metric_card("Monthly Spend", f"AED {expected_monthly['spend']:,.0f}", delta=f"{spend_chg:+.1f}%", border_color="#3b82f6")
            with m2: metric_card("Monthly Sales", f"AED {expected_monthly['sales']:,.0f}", delta=f"{sales_chg:+.1f}%", border_color="#3b82f6")
            
            m3, m4 = st.columns(2)
            roas_chg = pct_change(expected_monthly["roas"], current_monthly["roas"])
            orders_chg = pct_change(expected_monthly["orders"], current_monthly["orders"])
            
            with m3: metric_card("ROAS", f"{expected_monthly['roas']:.2f}x", delta=f"{roas_chg:+.1f}%", border_color="#3b82f6")
            with m4: metric_card("Monthly Orders", f"{expected_monthly['orders']:.0f}", delta=f"{orders_chg:+.1f}%", border_color="#3b82f6")
            
            st.caption(f"Confidence: 70% probability | Based on {date_info.get('weeks', 1):.1f} weeks of data")
        
        st.divider()
        
        # Scenario Analysis (monthly)
        st.markdown("### 📉 Scenario Analysis (Monthly Estimates)")
        
        conservative = scenarios.get("conservative", {})
        aggressive = scenarios.get("aggressive", {})
        
        # Convert all to monthly
        scenario_df = pd.DataFrame({
            "Scenario": ["Current", "Conservative (15%)", "Expected (70%)", "Aggressive (15%)"],
            "Spend (AED)": [
                current.get("spend", 0) * weekly_to_monthly,
                conservative.get("spend", 0) * weekly_to_monthly,
                expected.get("spend", 0) * weekly_to_monthly,
                aggressive.get("spend", 0) * weekly_to_monthly
            ],
            "Sales (AED)": [
                current.get("sales", 0) * weekly_to_monthly,
                conservative.get("sales", 0) * weekly_to_monthly,
                expected.get("sales", 0) * weekly_to_monthly,
                aggressive.get("sales", 0) * weekly_to_monthly
            ],
            "ROAS": [current.get("roas", 0), conservative.get("roas", 0), expected.get("roas", 0), aggressive.get("roas", 0)],
            "Orders": [
                current.get("orders", 0) * weekly_to_monthly,
                conservative.get("orders", 0) * weekly_to_monthly,
                expected.get("orders", 0) * weekly_to_monthly,
                aggressive.get("orders", 0) * weekly_to_monthly
            ],
            "ACoS": [current.get("acos", 0), conservative.get("acos", 0), expected.get("acos", 0), aggressive.get("acos", 0)]
        })
        
        st.dataframe(
            scenario_df.style.format({
                "Spend (AED)": "{:,.0f}",
                "Sales (AED)": "{:,.0f}",
                "ROAS": "{:.2f}x",
                "Orders": "{:.0f}",
                "ACoS": "{:.1f}%"
            }),
            use_container_width=True,
            hide_index=True
        )
        
        st.info("**Expected scenario** has the highest probability (70%) and represents typical market conditions.")
        
        st.divider()
        
        # Sensitivity Analysis
        sensitivity_df = sim.get("sensitivity", pd.DataFrame())
        if not sensitivity_df.empty:
            st.markdown("### 🎚️ Sensitivity Analysis")
            st.markdown("See how different bid adjustment levels would impact performance:")
            
            st.dataframe(
                sensitivity_df.style.format({
                    "Spend": "${:,.0f}",
                    "Sales": "${:,.0f}",
                    "ROAS": "{:.2f}x",
                    "Orders": "{:.0f}",
                    "ACoS": "{:.1f}%"
                }),
                use_container_width=True,
                hide_index=True
            )
            
            # Chart
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=sensitivity_df["Spend"],
                y=sensitivity_df["ROAS"],
                mode="lines+markers",
                name="ROAS vs Spend",
                text=sensitivity_df["Bid_Adjustment"],
                hovertemplate="<b>%{text}</b><br>Spend: $%{x:,.0f}<br>ROAS: %{y:.2f}x<extra></extra>"
            ))
            fig.update_layout(
                title="ROAS vs Spend Trade-off",
                xaxis_title="Avg Weekly Spend ($)",
                yaxis_title="ROAS",
                hovermode="closest",
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
            st.caption("💡 **Tip:** Look for the sweet spot where ROAS is maximized without excessive spend.")
        
        st.divider()
        
        # Risk Analysis
        risk = sim.get("risk_analysis", {})
        summary = risk.get("summary", {})
        
        st.markdown("### ⚠️ Risk Analysis")
        c1, c2, c3 = st.columns(3)
        with c1: metric_card("🔴 High Risk", summary.get("high_risk_count", 0))
        with c2: metric_card("🟡 Medium Risk", summary.get("medium_risk_count", 0))
        with c3: metric_card("🟢 Low Risk", summary.get("low_risk_count", 0))
        
        high_risk = risk.get("high_risk", [])
        if high_risk:
            st.markdown("#### 🔴 High Risk Changes (Review Carefully)")
            risk_df = pd.DataFrame(high_risk)
            st.dataframe(risk_df, use_container_width=True, hide_index=True)
            st.warning("⚠️ Consider testing these changes on a smaller scale first.")
        else:
            st.success("✅ No high-risk changes detected. All bid adjustments are within safe parameters.")
