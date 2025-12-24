
import os
import sys
import pandas as pd
from datetime import datetime
import streamlit as st

# Mock Streamlit to prevent errors during script execution
class MockSessionState(dict):
    def __getattr__(self, item):
        return self.get(item)
    def __setattr__(self, item, value):
        self[item] = value

if not hasattr(st, 'session_state'):
    st.session_state = MockSessionState()

st.session_state.unified_data = {
    'search_term_report': None,
    'upload_status': {},
    'upload_timestamps': {}
}
st.session_state.test_mode = False

# Ensure active account is set
CLIENT_ID = 'demo_account_2'
st.session_state.active_account_id = CLIENT_ID

from core.data_hub import DataHub
from features.optimizer import OptimizerModule, _log_optimization_events

def run_quick_analysis():
    print(f"🚀 Starting Quick Run for {CLIENT_ID}...")
    
    hub = DataHub()
    
    # 1. Load data from database
    print("📥 Loading data from Postgres...")
    loaded = hub.load_from_database(CLIENT_ID)
    if not loaded:
        print("❌ Failed to load data from database. Ensure target_stats exists for demo_Account_2.")
        return

    df = hub.get_data('search_term_report')
    print(f"✅ Loaded {len(df)} rows.")

    # 2. Run Optimization
    print("🧠 Running optimization logic...")
    opt = OptimizerModule()
    # Explicitly run the analysis
    opt._run_analysis(df)
    
    results = st.session_state.get('optimizer_results')
    if not results:
        print("❌ Optimization results not found in session state.")
        return

    # 3. Log Actions
    print("📝 Logging actions to Postgres...")
    # Get the latest date from results for report_date
    date_info = results.get('date_info', {})
    report_date = date_info.get('start_date')
    if report_date and hasattr(report_date, 'strftime'):
        report_date = report_date.strftime('%Y-%m-%d')
    else:
        report_date = datetime.now().strftime('%Y-%m-%d')
        
    logged_count = _log_optimization_events(results, CLIENT_ID, report_date)
    
    print(f"✅ Run Complete!")
    print(f"📊 Actions Logged: {logged_count}")
    
    # Summary of generated actions
    print("\nBreakdown:")
    print(f"  - Harvests: {len(results.get('harvest', []))}")
    print(f"  - Negatives (KW): {len(results.get('neg_kw', []))}")
    print(f"  - Negatives (PT): {len(results.get('neg_pt', []))}")
    print(f"  - Bid Changes: {len(results.get('direct_bids', [])) + len(results.get('agg_bids', []))}")

if __name__ == "__main__":
    run_quick_analysis()
