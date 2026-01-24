
import sys
import os
import pandas as pd
from datetime import date
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.postgres_manager import PostgresManager
from core.utils import get_maturity_status
from features.impact_metrics import ImpactMetrics

load_dotenv()

def simulate_home_tile(client_id):
    print(f"--- Simulating Home Tile for {client_id} ---")
    
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("No DATABASE_URL")
        return
        
    db = PostgresManager(db_url)
    
    # 1. Fetch Data
    impact_df = db.get_action_impact(client_id, before_days=14, after_days=14)
    print(f"Fetched {len(impact_df)} rows from get_action_impact.")
    
    summary = db.get_impact_summary(client_id, before_days=14, after_days=14)
    total_actions = summary.get('all', {}).get('total_actions', 0)
    print(f"Summary Total Actions: {total_actions}")
    
    if len(impact_df) == 0:
        print("No data.")
        return

    # 2. Fetch Latest Date (The Fix)
    latest_data_date = db.get_latest_raw_data_date(client_id)
    print(f"Latest Data Date from DB: {latest_data_date}")
    
    if not latest_data_date:
        print("Using fallback (simulated)...")
        # In real code fallback comes from summary, here we just warn
        latest_data_date = date(2026, 1, 12) # Old date simulation
        
    # 3. Calculate Maturity
    if 'action_date' in impact_df.columns:
        impact_df['is_mature'] = impact_df['action_date'].apply(
            lambda d: get_maturity_status(d, latest_data_date, horizon='14D')['is_mature']
        )
        print(f"Mature Actions: {impact_df['is_mature'].sum()}")
        
    # 4. Metrics
    canonical_filters = {'validated_only': True, 'mature_only': True}
    metrics = ImpactMetrics.from_dataframe(impact_df, horizon_days=14, filters=canonical_filters)
    
    print(f"Attributed Impact: {metrics.attributed_impact:,.0f}")
    if abs(metrics.attributed_impact - 14986) < 100:
        print("SUCCESS: Matches 14.9k target.")
    elif abs(metrics.attributed_impact - 16903) < 100:
        print("FAILURE: Still matches 16.9k (Old result).")
    else:
        print(f"RESULT: {metrics.attributed_impact}")

if __name__ == "__main__":
    simulate_home_tile('s2c_test')
