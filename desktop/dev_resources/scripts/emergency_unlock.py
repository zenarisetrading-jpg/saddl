
import sys
import os
import psycopg2
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv(project_root / '.env')

def kill_locking_sessions():
    """
    Kill sessions that might be locking target_stats.
    """
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("❌ DATABASE_URL not found")
        return

    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cur = conn.cursor()
        
        print("🔍 Searching for blocking sessions...")
        
        # 1. Check strict locks on target_stats
        cur.execute("""
            SELECT pid, usename, state, query_start, query
            FROM pg_stat_activity
            WHERE pid != pg_backend_pid()
            AND query ILIKE '%target_stats%'
            AND (state = 'idle in transaction' OR state = 'active')
        """)
        
        rows = cur.fetchall()
        
        if not rows:
            print("✅ No obvious locks found on 'target_stats'.")
            print("Checking for general 'idle in transaction' sessions that might hold unrelated locks...")
            
            cur.execute("""
                SELECT pid, usename, state, query_start, query
                FROM pg_stat_activity
                WHERE pid != pg_backend_pid()
                AND state = 'idle in transaction'
                AND datname = current_database()
            """)
            rows = cur.fetchall()
            
        if not rows:
            print("✅ No blocking sessions found.")
            return

        print(f"⚠️ Found {len(rows)} potentially blocking sessions:")
        for row in rows:
            print(f"   PID: {row[0]} | User: {row[1]} | State: {row[2]} | Time: {row[3]}")
            print(f"   Query: {row[4][:100]}...")
            
        # confirm = input("\n🔴 Terminate these sessions? [y/N]: ")
        confirm = 'y'

        print("\n🔪 Terminating sessions...")
        for row in rows:
            pid = row[0]
            try:
                cur.execute(f"SELECT pg_terminate_backend({pid})")
                print(f"   ✅ Killed PID {pid}")
            except Exception as e:
                print(f"   ❌ Failed to kill PID {pid}: {e}")
                
        print("\n✅ Cleanup complete. Try running the migration now.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    kill_locking_sessions()
