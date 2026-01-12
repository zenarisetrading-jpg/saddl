from core.postgres_manager import PostgresManager
import pandas as pd
from tabulate import tabulate
import os
from dotenv import load_dotenv
from pathlib import Path

def check_max_str_date():
    # Force loading of secrets/env if needed, or just rely on OS env
    # Try to load secrets if available
    # Load .env from project root (parent of desktop)
    env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)
    
    # Try to load secrets if available (fallback)
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "DATABASE_URL" in st.secrets:
            os.environ["DATABASE_URL"] = st.secrets["DATABASE_URL"]
            print("Loaded DATABASE_URL from streamlit secrets")
    except:
        pass

    db_url = os.environ.get("DATABASE_URL") or os.environ.get("SUPABASE_DB_URL")
    if not db_url:
        print("❌ Error: DATABASE_URL not found in environment")
        return

    # Instantiate PostgresManager directly
    db = PostgresManager(db_url)
    print("Using PostgresManager directly.")

    try:
        with db._get_connection() as conn:
            with conn.cursor() as cursor:
                # 1. Check TARGET STATS
                query_target = """
                SELECT 
                    client_id, 
                    MAX(start_date) as max_date,
                    COUNT(*) as row_count
                FROM target_stats 
                GROUP BY client_id 
                ORDER BY max_date DESC;
                """
                cursor.execute(query_target)
                target_results = cursor.fetchall()

                # 2. Check WEEKLY STATS
                query_weekly = """
                SELECT 
                    client_id, 
                    MAX(start_date) as max_date,
                    COUNT(*) as row_count
                FROM weekly_stats 
                GROUP BY client_id 
                ORDER BY max_date DESC;
                """
                cursor.execute(query_weekly)
                weekly_results = cursor.fetchall()
                
                print("\n=== MAX DATE: TARGET_STATS (Granular) ===\n")
                if target_results:
                    data = []
                    for row in target_results:
                        if isinstance(row, dict):
                           data.append([row.get('client_id'), row.get('max_date'), row.get('row_count')])
                        else:
                           data.append([row[0], row[1], row[2]])
                    print(tabulate(data, headers=["Client ID", "Max Date", "Row Count"], tablefmt="grid"))
                else:
                    print("No data in target_stats.")

                print("\n=== MAX DATE: WEEKLY_STATS (Aggregated) ===\n")
                if weekly_results:
                    data = []
                    for row in weekly_results:
                        if isinstance(row, dict):
                           data.append([row.get('client_id'), row.get('max_date'), row.get('row_count')])
                        else:
                           data.append([row[0], row[1], row[2]])
                    print(tabulate(data, headers=["Client ID", "Max Date", "Row Count"], tablefmt="grid"))
                else:
                    print("No data in weekly_stats.")
                    
    except Exception as e:
        print(f"Error querying database: {e}")
        # Print full traceback
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_max_str_date()
