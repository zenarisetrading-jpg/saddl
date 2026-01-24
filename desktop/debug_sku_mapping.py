
import sys
import os
import pandas as pd
import sqlite3

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.db_manager import get_db_manager
from core.data_loader import SmartMapper

def check_db(client_id, is_test):
    db_label = "TEST" if is_test else "PROD"
    try:
        db_mgr = get_db_manager(test_mode=is_test)
        print(f"\n--- Checking {db_label} DB: {db_mgr.db_path} ---")
        
        # Check if table exists
        with sqlite3.connect(db_mgr.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='advertised_product_cache'")
            if not cursor.fetchone():
                print(f"❌ Table 'advertised_product_cache' does not exist in {db_label} DB")
                return None
                
            # Count rows for client
            cursor.execute("SELECT count(*) FROM advertised_product_cache WHERE client_id = ?", (client_id,))
            count = cursor.fetchone()[0]
            print(f"Found {count} rows for client_id='{client_id}' in {db_label} DB")
            
            if count == 0:
                # List all clients
                cursor.execute("SELECT DISTINCT client_id FROM advertised_product_cache")
                clients = [r[0] for r in cursor.fetchall()]
                print(f"Available clients in {db_label} DB: {clients}")
                return None

        # Fetch DataFrame
        purchased_report = db_mgr.get_advertised_product_map(client_id)
        print(f"DataFrame Columns: {list(purchased_report.columns)}")
        print(f"DataFrame Head:\n{purchased_report.head()}")
        return purchased_report

    except Exception as e:
        print(f"❌ Error checking {db_label} DB: {e}")
        return None

def debug_sku_mapping(client_id="s2c_test"):
    print(f"--- Debugging SKU Mapping for {client_id} ---")
    
    purchased_report = None
    
    # 1. Fetch from DB (Check PROD then TEST)
    for is_test in [False, True]:
        report = check_db(client_id, is_test)
        if report is not None and not report.empty:
            purchased_report = report
            break
            
    if purchased_report is None or purchased_report.empty:
        print("\n❌ Could not find valid reported data in any DB")
        return

    # 2. Check for Specific Campaigns from User Screenshot
    target_campaigns = [
        "SSWB GRPUPED BROAD Campaign - 15/09/2025 10:48:17.950",
        "Dental flosser BROAD KT Campaign - 12/04/2025 19:46:26.311",
        "b0ccd1fmsq spa campaign - 26/03/2025 12:13:48.934",
        "SHWER CADDY PRODUCT TARGET Campaign - 06/07/2025 09:50:27.572"
    ]
    
    print("\n--- Checking for Target Campaigns ---")
    
    # Check matching logic
    c_col = 'Campaign Name' if 'Campaign Name' in purchased_report.columns else None
    
    if not c_col:
        print("❌ 'Campaign Name' column not found in DF")
        return
        
    cached_campaigns = set(purchased_report[c_col].astype(str).str.strip().str.lower())
    
    for target in target_campaigns:
        normalized_target = target.strip().lower()
        if normalized_target in cached_campaigns:
            print(f"✅ Found match for: {target}")
            # Show the SKU
            match = purchased_report[purchased_report[c_col].str.lower() == normalized_target]
            print(f"   Mapped SKU: {match.iloc[0].get('SKU', 'N/A')}")
        else:
            print(f"❌ No match for: {target}")
            # Try partial match
            partial = [c for c in cached_campaigns if normalized_target in c or c in normalized_target]
            if partial:
                print(f"   ⚠️ Potential partial matches: {partial[:3]}")

if __name__ == "__main__":
    client = sys.argv[1] if len(sys.argv) > 1 else "s2c_test"
    debug_sku_mapping(client)
