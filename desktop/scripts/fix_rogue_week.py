import os
import sys
import psycopg2
from dotenv import load_dotenv

# Load env from parent (saddle/saddle/.env)
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../.env')))

def fix_rogue_week(client_id):
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not found in environment.")
        return

    print(f"🔌 Connecting to database for client: {client_id}")
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cur = conn.cursor()
        
        # 1. Verify existence first
        print("🔍 checking for rogue week (2025-12-30)...")
        cur.execute(
            "SELECT COUNT(*), SUM(spend) FROM target_stats WHERE client_id = %s AND start_date = '2025-12-30'",
            (client_id,)
        )
        row = cur.fetchone()
        count, spend = row
        
        if count == 0:
            print("✅ No rogue week found. Data is already clean.")
        else:
            print(f"⚠️ Found Rogue Week (2025-12-30): {count} rows, ${spend:,.2f} aggregate spend.")
            print("🗑️ Deleting rogue rows...")
            
            cur.execute(
                "DELETE FROM target_stats WHERE client_id = %s AND start_date = '2025-12-30'",
                (client_id,)
            )
            print("✅ Rogue week deleted.")
            
            # 2. Verify cleanup
            cur.execute(
                "SELECT COUNT(*) FROM target_stats WHERE client_id = %s AND start_date = '2025-12-30'",
                (client_id,)
            )
            final_count = cur.fetchone()[0]
            if final_count == 0:
                print("✨ Clean up confirmed success.")
            else:
                print("❌ Something went wrong. Rows still exist.")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    # Hardcoded for the verified test client
    fix_rogue_week("s2c_uae_test")
