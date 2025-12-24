
import os
import pandas as pd
from datetime import datetime
from core.db_manager import get_db_manager
from core.postgres_manager import PostgresManager

def check_db():
    print("--- Database Status Check ---")
    db = get_db_manager()
    status, color = db.get_connection_status()
    print(f"Status: {status} ({color})")
    
    use_postgres = isinstance(db, PostgresManager)
    
    tables = [
        "target_stats", 
        "actions_log", 
        "advertised_product_cache", 
        "bulk_mappings", 
        "accounts", 
        "account_health_metrics",
        "category_mappings"
    ]
    
    with db._get_connection() as conn:
        if use_postgres:
            from psycopg2.extras import RealDictCursor
            cursor = conn.cursor(cursor_factory=RealDictCursor)
        else:
            cursor = conn.cursor()
            
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                row = cursor.fetchone()
                count = row[0] if not use_postgres else row['count']
                
                # Date cols
                date_col = 'updated_at'
                if table == 'target_stats': date_col = 'start_date'
                elif table == 'actions_log': date_col = 'action_date'
                
                cursor.execute(f"SELECT MAX({date_col}) FROM {table}")
                row = cursor.fetchone()
                latest = row[0] if not use_postgres else row['max']
                
                print(f"Table: {table:25} | Count: {count:6} | Latest: {latest}")
            except Exception as e:
                print(f"Error checking {table}: {e}")

    print("\n--- Summary for demo_account_2 ---")
    try:
        with db._get_connection() as conn:
            if use_postgres:
                from psycopg2.extras import RealDictCursor
                cursor = conn.cursor(cursor_factory=RealDictCursor)
            else:
                cursor = conn.cursor()
                
            for table in tables:
                if table == 'accounts': continue
                cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE client_id = 'demo_account_2'")
                row = cursor.fetchone()
                count = row[0] if not use_postgres else row['count']
                
                date_col = 'updated_at'
                if table == 'target_stats': date_col = 'start_date'
                elif table == 'actions_log': date_col = 'action_date'
                
                cursor.execute(f"SELECT MAX({date_col}) FROM {table} WHERE client_id = 'demo_account_2'")
                row = cursor.fetchone()
                latest = row[0] if not use_postgres else row['max']
                
                print(f"Table: {table:25} | Count: {count:6} | Latest: {latest}")
                
            # Date distribution of target_stats for demo_account_2
            print("\nTarget Stats Dates (demo_account_2):")
            cursor.execute("SELECT start_date, COUNT(*) as c FROM target_stats WHERE client_id = 'demo_account_2' GROUP BY start_date ORDER BY start_date")
            rows = cursor.fetchall()
            for r in rows:
                d = r[0] if not use_postgres else r['start_date']
                c = r[1] if not use_postgres else r['c']
                print(f"  {d}: {c}")
                
            # Date distribution of actions_log for demo_account_2
            print("\nActions Log Dates (demo_account_2):")
            cursor.execute("SELECT DATE(action_date) as d, COUNT(*) as c FROM actions_log WHERE client_id = 'demo_account_2' GROUP BY d ORDER BY d DESC LIMIT 5")
            rows = cursor.fetchall()
            for r in rows:
                d = r[0] if not use_postgres else r['d']
                c = r[1] if not use_postgres else r['c']
                print(f"  {d}: {c}")

    except Exception as e:
        print(f"Error auditing demo_account_2: {e}")

if __name__ == "__main__":
    check_db()
