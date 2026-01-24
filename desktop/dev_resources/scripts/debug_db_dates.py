"""
Debug script to check database tables for recent data.
Run this from the desktop folder: python debug_db_dates.py
"""
import sys
import os
sys.path.insert(0, '.')

# Use PostgresManager directly
from core.postgres_manager import PostgresManager

def main():
    print("Connecting to PostgreSQL database...")
    
    # Get the DATABASE_URL from environment or use default
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("DATABASE_URL not found in environment. Using connection from running app...")
        # Try to read from .env or config
        try:
            with open('.env', 'r') as f:
                for line in f:
                    if line.startswith('DATABASE_URL='):
                        db_url = line.split('=', 1)[1].strip().strip('"').strip("'")
                        break
        except FileNotFoundError:
            pass
    
    if not db_url:
        print("❌ No DATABASE_URL found. Please run this while the app is running or set DATABASE_URL")
        print("   You can also check via the Streamlit app by adding a debug tab")
        return
    
    db = PostgresManager(db_url)
    
    client_id = 's2c_uae_test'
    
    print(f"\n=== Checking data for client: {client_id} ===\n")
    
    # Check raw_search_term_data
    print("1. RAW_SEARCH_TERM_DATA table:")
    try:
        with db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    MIN(date) as earliest_date,
                    MAX(date) as latest_date,
                    COUNT(*) as total_rows
                FROM raw_search_term_data 
                WHERE client_id = %s
            """, (client_id,))
            row = cursor.fetchone()
            if row:
                print(f"   Earliest: {row[0]}, Latest: {row[1]}, Rows: {row[2]}")
            
            # Check dates after Jan 10
            cursor.execute("""
                SELECT date, COUNT(*) as rows
                FROM raw_search_term_data 
                WHERE client_id = %s AND date >= '2026-01-10'
                GROUP BY date
                ORDER BY date
            """, (client_id,))
            rows = cursor.fetchall()
            if rows:
                print("   Recent dates (>= Jan 10):")
                for r in rows:
                    print(f"      {r[0]}: {r[1]} rows")
            else:
                print("   ⚠️ No data found after Jan 10!")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Check target_stats
    print("\n2. TARGET_STATS table:")
    try:
        with db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    MIN(start_date) as earliest_date,
                    MAX(start_date) as latest_date,
                    COUNT(*) as total_rows
                FROM target_stats 
                WHERE client_id = %s
            """, (client_id,))
            row = cursor.fetchone()
            if row:
                print(f"   Earliest: {row[0]}, Latest: {row[1]}, Rows: {row[2]}")
            
            # Check weeks after Jan 5
            cursor.execute("""
                SELECT start_date, COUNT(*) as rows, SUM(spend) as total_spend
                FROM target_stats 
                WHERE client_id = %s AND start_date >= '2026-01-05'
                GROUP BY start_date
                ORDER BY start_date
            """, (client_id,))
            rows = cursor.fetchall()
            if rows:
                print("   Recent weeks (>= Jan 5):")
                for r in rows:
                    print(f"      Week of {r[0]}: {r[1]} rows, Spend: {r[2]}")
            else:
                print("   ⚠️ No weekly data found after Jan 5!")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n=== Done ===")

if __name__ == "__main__":
    main()
