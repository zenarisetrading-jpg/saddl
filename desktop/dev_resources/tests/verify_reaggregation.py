
import os
import sys
import pandas as pd
from datetime import date, timedelta
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.postgres_manager import PostgresManager

# Load env from parent (saddle/saddle/.env)
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../.env')))

def verify_reaggregation():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not found")
        return

    db = PostgresManager(db_url)
    client_id = "test_reagg_client"
    
    print(f"🧪 Starting Verification for Client: {client_id}")
    
    # Clean up previous test data
    with db._get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM raw_search_term_data WHERE client_id = %s", [client_id])
            cursor.execute("DELETE FROM target_stats WHERE client_id = %s", [client_id])
    
    # Week of Dec 29, 2025 (Monday)
    # Scenario: 
    # Batch 1: Dec 29, 30, 31 (Spend = 100 per day)
    # Batch 2: Jan 1, 2, 3 (Spend = 200 per day)
    
    # --- BATCH 1 ---
    print("\n--- BATCH 1: Uploading Dec 29-31 (Spend=100/day) ---")
    data1 = {
        'Date': ['2025-12-29', '2025-12-30', '2025-12-31'],
        'Campaign Name': ['Camp A'] * 3,
        'Ad Group Name': ['AG A'] * 3,
        'Targeting': ['targ'] * 3,
        'Customer Search Term': ['term'] * 3,
        'Match Type': ['EXACT'] * 3,
        'Impressions': [1000] * 3,
        'Clicks': [10] * 3,
        'Spend': [100.0] * 3,
        'Sales': [500.0] * 3,
        'Orders': [5] * 3
    }
    df1 = pd.DataFrame(data1)
    
    # 1. Save Raw
    db.save_raw_search_term_data(df1, client_id)
    
    # 2. Re-aggregate
    weeks = ['2025-12-29']
    db.reaggregate_target_stats(client_id, weeks)
    
    # Check Result
    stats1 = db.get_target_stats_df(client_id)
    spend1 = stats1['Spend'].sum()
    print(f"Batch 1 Stored Spend: {spend1} (Expected 300.0)")
    assert spend1 == 300.0, f"Batch 1 failed! Got {spend1}"
    
    # --- BATCH 2 ---
    print("\n--- BATCH 2: Uploading Jan 1-3 (Spend=200/day) ---")
    # This simulates a separate upload later in the week
    data2 = {
        'Date': ['2026-01-01', '2026-01-02', '2026-01-03'],
        'Campaign Name': ['Camp A'] * 3,
        'Ad Group Name': ['AG A'] * 3,
        'Targeting': ['targ'] * 3,
        'Customer Search Term': ['term'] * 3,
        'Match Type': ['EXACT'] * 3,
        'Impressions': [1000] * 3,
        'Clicks': [10] * 3,
        'Spend': [200.0] * 3,
        'Sales': [1000.0] * 3,
        'Orders': [10] * 3
    }
    df2 = pd.DataFrame(data2)
    
    # 1. Save Raw (Upsert/Append to Raw Table)
    db.save_raw_search_term_data(df2, client_id)
    
    # 2. Re-aggregate (Should combine Batch 1 + Batch 2)
    db.reaggregate_target_stats(client_id, weeks)
    
    # Check Result
    stats2 = db.get_target_stats_df(client_id)
    spend2 = stats2['Spend'].sum()
    print(f"Batch 2 Combined Spend: {spend2} (Expected 300+600=900.0)")
    
    if spend2 == 900.0:
        print("\n✅ VERIFICATION SUCCESSFUL!")
        print("The logic correctly combined partial week uploads.")
    else:
        print(f"\n❌ VERIFICATION FAILED. Got {spend2}, expected 900.0")
        print("It seems the data was overwritten instead of summed.")

if __name__ == "__main__":
    try:
        verify_reaggregation()
    except Exception as e:
        print(f"Error: {e}")
