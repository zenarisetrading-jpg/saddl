"""
Compare Dashboard Logic
=======================
Simulates data loading for Executive vs Impact dashboards to check for discrepancies.
"""
import os
import sys
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../.env')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.postgres_manager import PostgresManager
from features.impact_metrics import ImpactMetrics

# Hardcoded Logic matching impact_dashboard.py
def get_maturity_status(action_date, latest_data_date, horizon="14D"):
    if horizon == "14D":
        days = 14
    elif horizon == "30D":
        days = 30
    elif horizon == "60D":
        days = 60
    else:
        days = 14
        
    buffer = 3
    
    # Parse dates
    if isinstance(action_date, str):
        action_date = pd.to_datetime(action_date).date()
    elif hasattr(action_date, 'date'):
        action_date = action_date.date()
        
    if isinstance(latest_data_date, str):
        latest_data_date = pd.to_datetime(latest_data_date).date()
    elif hasattr(latest_data_date, 'date'):
        latest_data_date = latest_data_date.date()
        
    maturity_date = action_date + timedelta(days=days + buffer)
    is_mature = maturity_date <= latest_data_date
    
    return {'is_mature': is_mature}

def main():
    db_url = os.environ.get("DATABASE_URL")
    db = PostgresManager(db_url)
    client_id = 's2c_uae_test'
    
    print("\n=== COMPARISON START ===")
    
    # 1. Fetch Raw Impact Data (Shared Base)
    impact_df = db.get_action_impact(client_id, before_days=14, after_days=14)
    print(f"Base Impact DF Rows: {len(impact_df)}")
    
    # Get Real Latest Date
    latest_date = None
    if hasattr(db, 'get_latest_raw_data_date'):
        latest_date = db.get_latest_raw_data_date(client_id)
    
    if not latest_date:
        latest_date = datetime.now().date()
        
    print(f"Latest Date from DB: {latest_date}")
    
    # 2. EMULATE WITH METRICS Breakdown
    print("\n--- METRICS BREAKDOWN (Using DB Date) ---")
    exec_df = impact_df.copy()
    exec_df['is_mature'] = exec_df['action_date'].apply(
         lambda d: get_maturity_status(d, latest_date, horizon='14D')['is_mature']
    )
    
    metrics = ImpactMetrics.from_dataframe(
        exec_df,
        filters={'validated_only': True, 'mature_only': True},
        horizon_days=14
    )
    
    print(f"Attributed Impact: {metrics.attributed_impact:,.0f}")
    print(f"Decision Impact (Raw): {metrics.decision_impact:,.0f}")
    print("\n--- BREAKDOWN ---")
    print(f"Offensive: {metrics.offensive_value:,.0f} ({metrics.offensive_actions} actions)")
    print(f"Defensive: {metrics.defensive_value:,.0f} ({metrics.defensive_actions} actions)")
    print(f"Gap:       {metrics.gap_value:,.0f} ({metrics.gap_actions} actions)")
    
    # Check specifically for that 3000 Defensive Action
    if metrics.defensive_actions > 0:
        print("\nChecking TOP Defensive Actions:")
        # Identify columns
        imp_col = 'final_decision_impact' if 'final_decision_impact' in exec_df.columns else 'decision_impact'
        
        # Filter dataframe for Validated Defensive Wins
        if 'market_tag' in exec_df.columns:
            def_df = exec_df[(exec_df['market_tag'] == 'Defensive Win') & 
                             (exec_df['is_mature'] == True) &
                             (exec_df['validation_status'].str.contains('✓|CPC Validated|CPC Match|Directional|Confirmed|Normalized|Volume', na=False, regex=True))].copy()
            
            # Sort by impact
            def_df = def_df.sort_values(by=imp_col, ascending=False)
            print(f"Found {len(def_df)} Defensive Actions in DF.")
            if not def_df.empty:
                print(def_df[[imp_col, 'target_text', 'action_type', 'validation_status', 'action_date']].to_string())

if __name__ == "__main__":
    main()
