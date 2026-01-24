
import sys
import os
from datetime import date, timedelta
import pandas as pd
import numpy as np

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.postgres_manager import PostgresManager

# Use the Env var if available, else hardcode (copied from analyze_stats.py)
DB_URL = os.environ.get("DATABASE_URL", "postgresql://postgres.wuakeiwxkjvhsnmkzywz:Zen%40rise%40123%21@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres")

def calc_insights():
    print("--- Starting Key Insights Debug ---")
    
    db_manager = PostgresManager(DB_URL)
    
    # getting client
    print("Checking for clients...")
    clients = db_manager.get_unique_clients()
    
    client_id = None
    if clients:
        client_id = clients[0]['client_id']
        print(f"Found client in weekly_stats: {client_id}")
    else:
        print("No clients in weekly_stats. Checking target_stats...")
        with db_manager._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT DISTINCT client_id FROM target_stats LIMIT 1")
                res = cur.fetchone()
                if res:
                    client_id = res[0]
                    print(f"Found client in target_stats: {client_id}")
    
    if not client_id:
        print("No clients found in DB.")
        return
        
    print(f"Using Client ID: {client_id}")

    try:
        # Fetch all data 
        print("Fetching target_stats_df...")
        df_all = db_manager.get_target_stats_df(client_id)
        
        if df_all is None or df_all.empty:
            print("df_all is Empty or None")
            return

        print(f"Total Rows: {len(df_all)}")
        print(f"Columns: {list(df_all.columns)}")
        
        if 'Date' not in df_all.columns:
            print("Column 'Date' not found. Available:", df_all.columns)
            # Try lowercase 'date' just in case
            if 'date' in df_all.columns:
                 df_all['Date'] = df_all['date']
            else:
                return

        df_all['Date'] = pd.to_datetime(df_all['Date'])
        max_date = df_all['Date'].max().date()
        print(f"Max Date in DB: {max_date}")
        
        end_curr = max_date
        start_curr = max_date - timedelta(days=14)
        end_prev = start_curr - timedelta(days=1)
        start_prev = end_prev - timedelta(days=13)
        
        print(f"Current Window: {start_curr} to {end_curr}")
        print(f"Previous Window: {start_prev} to {end_prev}")

        # Filter
        df_curr = df_all[(df_all['Date'].dt.date >= start_curr) & (df_all['Date'].dt.date <= end_curr)]
        df_prev = df_all[(df_all['Date'].dt.date >= start_prev) & (df_all['Date'].dt.date <= end_prev)]
        
        print(f"Rows Curr: {len(df_curr)}")
        print(f"Rows Prev: {len(df_prev)}")
        
        if df_curr.empty:
            print("Current window empty. Exiting.")
            return

        # 1. ROAS
        curr_spend = df_curr['Spend'].sum() if 'Spend' in df_curr.columns else 0
        curr_sales = df_curr['Sales'].sum() if 'Sales' in df_curr.columns else 0
        roas_curr = curr_sales / curr_spend if curr_spend > 0 else 0
        
        roas_prev = 0
        if not df_prev.empty:
            prev_spend = df_prev['Spend'].sum() if 'Spend' in df_prev.columns else 0
            prev_sales = df_prev['Sales'].sum() if 'Sales' in df_prev.columns else 0
            roas_prev = prev_sales / prev_spend if prev_spend > 0 else 0
        
        roas_delta = ((roas_curr - roas_prev) / roas_prev * 100) if roas_prev > 0 else 0
        
        print(f"\n--- ROAS ---")
        print(f"Curr Spend: {curr_spend:.2f}, Sales: {curr_sales:.2f}, ROAS: {roas_curr:.3f}")
        if not df_prev.empty:
            print(f"Prev Spend: {prev_spend:.2f}, Sales: {prev_sales:.2f}, ROAS: {roas_prev:.3f}")
        print(f"ROAS Delta: {roas_delta:.2f}%")

        # 2. Efficiency
        def calc_efficiency(df):
            if 'Ad Group Name' in df.columns:
                agg = df.groupby('Ad Group Name').agg({'Spend': 'sum', 'Sales': 'sum'}).reset_index()
                agg['ROAS'] = (agg['Sales'] / agg['Spend']).replace([np.inf, -np.inf], 0).fillna(0)
                eff_spend = agg[agg['ROAS'] >= 2.5]['Spend'].sum()
                total = agg['Spend'].sum()
                return (eff_spend / total * 100) if total > 0 else 0
            return 0
            
        eff_curr = calc_efficiency(df_curr)
        eff_prev = calc_efficiency(df_prev) if not df_prev.empty else 0
        eff_delta = eff_curr - eff_prev
        
        print(f"\n--- Efficiency ---")
        print(f"Efficiency Curr: {eff_curr:.1f}%")
        print(f"Efficiency Prev: {eff_prev:.1f}%")
        print(f"Efficiency Delta: {eff_delta:.1f}%")

        # 3. Top Campaign
        print(f"\n--- Top Campaign ---")
        if not df_prev.empty and 'Campaign Name' in df_curr.columns:
            camp_curr = df_curr.groupby('Campaign Name')['Sales'].sum()
            camp_prev = df_prev.groupby('Campaign Name')['Sales'].sum()
            camp_delta = camp_curr.subtract(camp_prev, fill_value=0)
            if not camp_delta.empty and camp_delta.max() > 0:
                print(f"Top Campaign: {camp_delta.idxmax()}")
                print(f"Growth: {camp_delta.max():.2f}")
            else:
                print("No growing campaigns.")
        else:
            print("Cannot calc top campaign (missing prev data or column)")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    calc_insights()
