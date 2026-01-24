"""
Locate Complements Target
=========================
Find full details for the high-impact complements target.
"""
import os
import sys
import pandas as pd
import psycopg2
from dotenv import load_dotenv

load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../.env')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def main():
    db_url = os.environ.get("DATABASE_URL")
    
    # Just get the names directly
    query = """
    SELECT 
        campaign_name,
        ad_group_name,
        target_text,
        action_date,
        original_value,
        new_value,
        action_type
    FROM actions_log
    WHERE 
        client_id = 's2c_uae_test'
        AND target_text = 'complements'
        AND action_date >= '2025-11-01'
    ORDER BY action_date DESC
    LIMIT 5;
    """
    
    conn = psycopg2.connect(db_url)
    try:
        df = pd.read_sql(query, conn)
        print("=" * 80)
        print("DETAILS FOR 'complements' TARGET")
        print("=" * 80)
        print(df.to_string())
    finally:
        conn.close()

if __name__ == "__main__":
    main()
