
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Add local path to import postgres_manager
sys.path.append(os.getcwd())
from core.db_manager import get_db_manager

db = get_db_manager()
client_id = 'demo_account_2'

def check_data():
    print(f"Checking data for {client_id}...")
    
    # Check target_stats dates
    with db._get_connection() as conn:
        available_dates = pd.read_sql(f"SELECT DISTINCT start_date FROM target_stats WHERE client_id = '{client_id}' ORDER BY start_date DESC", conn)
    
    print("\nAvailable Dates in target_stats:")
    print(available_dates)
    
    if available_dates.empty:
        print("No target_stats found.")
        return
        
    latest_data_date = pd.to_datetime(available_dates.iloc[0,0])
    cutoff_date = latest_data_date - timedelta(days=30)
    
    print(f"\nLatest Data Date: {latest_data_date}")
    print(f"30D Cutoff Date: {cutoff_date}")
    
    # Check actions_log
    query = f"""
        SELECT action_date, action_type, target_text, campaign_name 
        FROM actions_log 
        WHERE client_id = '{client_id}'
        ORDER BY action_date DESC
    """
    with db._get_connection() as conn:
        actions = pd.read_sql(query, conn)
    
    print(f"\nTotal actions in log: {len(actions)}")
    
    # Actions within the window
    actions['action_date_dt'] = pd.to_datetime(actions['action_date'])
    window_actions = actions[(actions['action_date_dt'] >= cutoff_date) & 
                             (actions['action_date_dt'] <= latest_data_date)]
    
    print(f"Actions in 30D window (Dec 19 limit): {len(window_actions)}")
    
    # Actions AFTER the window
    after_actions = actions[actions['action_date_dt'] > latest_data_date]
    print(f"Actions AFTER window (should be excluded): {len(after_actions)}")
    
    if not after_actions.empty:
        print("\nRecent 'Today' Actions:")
        print(after_actions.head())

    # Get impact summary using our logic
    from features.impact_dashboard import get_recent_impact_summary
    import streamlit as st
    
    # Mock session state
    st.session_state['db_manager'] = db
    st.session_state['active_account_id'] = client_id
    
    summary = get_recent_impact_summary()
    print(f"\nCalculated Summary Metrics:")
    print(summary)
    
    # Debug the filter within the script itself
    cv = str(st.session_state.get('data_upload_timestamp', 'v1'))
    from features.impact_dashboard import _fetch_impact_data
    impact_df, _ = _fetch_impact_data(client_id, False, window_days=7, cache_version=cv)
    
    print(f"\nInternal Debug:")
    print(f"impact_df size: {len(impact_df)}")
    
    impact_df['action_date_dt'] = pd.to_datetime(impact_df['action_date'], errors='coerce')
    print(f"Sample action_date_dt: {impact_df['action_date_dt'].head()}")
    
    latest_data_date = pd.to_datetime(db.get_available_dates(client_id)[0])
    cutoff_date = latest_data_date - timedelta(days=30)
    
    print(f"Filter range: {cutoff_date} to {latest_data_date}")
    
    filtered_df = impact_df[(impact_df['action_date_dt'] >= cutoff_date) & 
                           (impact_df['action_date_dt'] <= latest_data_date)].copy()
    
    print(f"Filtered DF size: {len(filtered_df)}")
    if not filtered_df.empty:
        print(f"Filtered DF sales: {filtered_df['impact_score'].sum() if 'impact_score' in filtered_df.columns else filtered_df['delta_sales'].sum()}")
    
    after_filter_df = impact_df[impact_df['action_date_dt'] > latest_data_date]
    print(f"Excluded rows (after latest data): {len(after_filter_df)}")
    if not after_filter_df.empty:
        print(f"Excluded rows impact: {after_filter_df['impact_score'].sum() if 'impact_score' in after_filter_df.columns else after_filter_df['delta_sales'].sum()}")

if __name__ == "__main__":
    check_data()
