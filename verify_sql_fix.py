import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(os.getcwd())

from core.db_manager import get_db_manager
from core.data_hub import DataHub
import streamlit as st

def test_sql_fix():
    print("=== Testing SQL Placeholder Fix ===\n")
    
    # 1. Check Placeholder Property
    db = get_db_manager(test_mode=True)
    print(f"Database Type: {type(db).__name__}")
    print(f"Placeholder: {db.placeholder}")
    
    assert db.placeholder == "?", f"Expected '?' for SQLite, got {db.placeholder}"
    print("✅ Placeholder property correctly identifies SQLite dialact.")

    # 2. Mock Session State for DataHub
    if 'unified_data' not in st.session_state:
        st.session_state.unified_data = {
            'upload_status': {}
        }
    
    hub = DataHub()
    print("\nAttempting to run load_from_database with mock account...")
    
    # This might return False if no data exists, but we want to check for CRASHES
    # specifically SyntaxError
    try:
        success = hub.load_from_database("test_account")
        print(f"Load finished without crash. Data found: {success}")
        print("✅ SQL Query executed without SyntaxError.")
    except Exception as e:
        print(f"❌ Crash detected: {e}")
        if "syntax error" in str(e).lower():
            print("FAILURE: SQL Syntax Error detected!")
        sys.exit(1)

    print("\n✅ SQL PLACEHOLDER FIX VERIFIED (Local Environment)")

if __name__ == "__main__":
    test_sql_fix()
