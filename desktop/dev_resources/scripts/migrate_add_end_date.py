"""
Migration: Add end_date column to target_stats
==============================================
This script adds the end_date column and backfills from raw_search_term_data.

Run: python scripts/migrate_add_end_date.py
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../.env')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import psycopg2
from psycopg2.extras import RealDictCursor

def main():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not found")
        return
    
    print("=" * 60)
    print("MIGRATION: Add end_date column to target_stats")
    print("=" * 60)
    
    # Direct connection (not using pool)
    conn = psycopg2.connect(db_url)
    conn.autocommit = True  # Important for DDL statements
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Step 1: Check if column exists
        print("\n1. Checking if end_date column exists...")
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'target_stats' AND column_name = 'end_date'
        """)
        exists = cursor.fetchone()
        
        if exists:
            print("   ✅ end_date column already exists")
        else:
            print("   Adding end_date column...")
            cursor.execute("ALTER TABLE target_stats ADD COLUMN end_date DATE")
            print("   ✅ Column added")
        
        # Step 2: Backfill from raw_search_term_data
        print("\n2. Backfilling end_date from raw_search_term_data...")
        print("   This may take a moment...")
        
        cursor.execute("""
            UPDATE target_stats ts
            SET end_date = subq.max_date
            FROM (
                SELECT 
                    client_id,
                    date_trunc('week', report_date)::date as week_start,
                    MAX(report_date)::date as max_date
                FROM raw_search_term_data
                GROUP BY client_id, date_trunc('week', report_date)::date
            ) subq
            WHERE ts.client_id = subq.client_id 
              AND ts.start_date = subq.week_start
              AND (ts.end_date IS NULL OR ts.end_date != subq.max_date)
        """)
        updated = cursor.rowcount
        print(f"   ✅ Updated {updated} rows")
        
        # Step 3: Verify
        print("\n3. Verifying...")
        cursor.execute("""
            SELECT 
                start_date, 
                end_date, 
                COUNT(*) as rows
            FROM target_stats 
            WHERE client_id = 's2c_uae_test'
            GROUP BY start_date, end_date
            ORDER BY start_date DESC
            LIMIT 10
        """)
        rows = cursor.fetchall()
        
        print(f"\n   {'Week Start':<15} {'End Date':<15} {'Rows'}")
        print("   " + "-" * 45)
        for row in rows:
            start = row['start_date']
            end = row['end_date'] or "NULL"
            count = row['rows']
            print(f"   {str(start):<15} {str(end):<15} {count}")
        
        print("\n" + "=" * 60)
        print("MIGRATION COMPLETE")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()
