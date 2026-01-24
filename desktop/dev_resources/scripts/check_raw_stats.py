
import os
import sys
import pandas as pd
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.postgres_manager import PostgresManager

# Load env from parent
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../.env')))

def check_raw_stats(client_id):
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not found")
        return

    db = PostgresManager(db_url)
    
    print(f"🔍 Checking Raw Data for Client: {client_id}")
    
    with db._get_connection() as conn:
        query = """
            SELECT 
                MIN(report_date) as min_date,
                MAX(report_date) as max_date,
                MAX(uploaded_at) as last_upload,
                COUNT(*) as total_rows,
                SUM(spend) as total_spend,
                SUM(sales) as total_sales,
                SUM(clicks) as total_clicks
            FROM raw_search_term_data
            WHERE client_id = %s
        """
        df = pd.read_sql(query, conn, params=(client_id,))
        
        # Check Actions Log
        query_actions = "SELECT MIN(action_date) as first_action, MAX(action_date) as last_action FROM actions_log WHERE client_id = %s"
        df_actions = pd.read_sql(query_actions, conn, params=(client_id,))
        last_action = df_actions['last_action'].iloc[0] if not df_actions.empty else "N/A"
        first_action = df_actions['first_action'].iloc[0] if not df_actions.empty else "N/A"

        if df.empty or df['total_rows'].iloc[0] == 0:
            print("⚠️ No raw data found for this client.")
        else:
            row = df.iloc[0]
        if df.empty or df['total_rows'].iloc[0] == 0:
            print("⚠️ No raw data found for this client.")
        else:
            row = df.iloc[0]
            print("\n📊 Topline Stats (Raw Data):")
            print(f"   • Date Range: {row['min_date']} to {row['max_date']}")
            print(f"   • Last Upload: {row['last_upload']}")
            print(f"   • Optimizer Actions: {first_action} to {last_action}")
            print(f"   • Total Rows: {row['total_rows']:,}")
            print(f"   • Total Spend: ${row['total_spend']:,.2f}")
            print(f"   • Total Sales: ${row['total_sales']:,.2f}")
            print(f"   • Total Clicks: {row['total_clicks']:,}")

        # Check Target Stats (Aggregated)
        print("\n📊 Target Stats (Aggregated for Optimizer):")
        query_ts = "SELECT MAX(start_date) as max_week_start, COUNT(*) as rows FROM target_stats WHERE client_id = %s"
        df_ts = pd.read_sql(query_ts, conn, params=(client_id,))
        if not df_ts.empty:
            print(f"   • Max Week Start: {df_ts['max_week_start'].iloc[0]}")
            print(f"   • Total Aggregated Rows: {df_ts['rows'].iloc[0]:,}")
        
        # Check ALL weeks > Dec 1
        query_weeks = """
            SELECT start_date, COUNT(*) as rows, SUM(spend) as spend 
            FROM target_stats 
            WHERE client_id = %s AND start_date >= '2025-12-01' 
            GROUP BY start_date 
            ORDER BY start_date
        """
        df_weeks = pd.read_sql(query_weeks, conn, params=(client_id,))
        if not df_weeks.empty:
            print("\n📊 Recent Weeks in Target Stats:")
            for _, row in df_weeks.iterrows():
                print(f"   • Week {row['start_date']}: {row['rows']} rows, ${row['spend']:,.2f}")
        else:
            print("\n❌ No recent weeks found in Target Stats (since Dec 1)")

if __name__ == "__main__":
    check_raw_stats("s2c_uae_test")
