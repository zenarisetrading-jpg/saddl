
import os
import psycopg2
from psycopg2.extras import RealDictCursor

db_url = os.getenv('DATABASE_URL', 'postgresql://postgres.wuakeiwxkjvhsnmkzywz:Zen%40rise%40123%21@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres')
CLIENT_ID = 'demo_account_2'

def verify_raw_data():
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # 1. Target Stats (Sample)
    print(f"\n{'='*20} TABLE: target_stats (Samples) {'='*20}")
    cursor.execute("SELECT * FROM target_stats WHERE client_id = %s LIMIT 3", (CLIENT_ID,))
    [print(f"\nRow:\n {row}") for row in cursor.fetchall()]

    # 2. Account Health (Latest)
    print(f"\n{'='*20} TABLE: account_health_metrics (Latest) {'='*20}")
    cursor.execute("SELECT * FROM account_health_metrics WHERE client_id = %s", (CLIENT_ID,))
    [print(f"\nRow:\n {row}") for row in cursor.fetchall()]

    # 3. Actions Log (Latest 5 - proving metadata fix)
    print(f"\n{'='*20} TABLE: actions_log (LATEST 5) {'='*20}")
    cursor.execute("SELECT * FROM actions_log WHERE client_id = %s ORDER BY id DESC LIMIT 5", (CLIENT_ID,))
    rows = cursor.fetchall()
    for row in rows:
        print(f"\nAction ID: {row['id']}")
        print(f"  Type: {row['action_type']}")
        print(f"  Target: {row['target_text']}")
        print(f"  Winner Campaign: {row['winner_source_campaign']}")
        print(f"  New Campaign: {row['new_campaign_name']}")
        print(f"  Match Type: {row['before_match_type']} -> {row['after_match_type']}")
            
    cursor.close()
    conn.close()

if __name__ == "__main__":
    verify_raw_data()
