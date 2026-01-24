
import sys
import os
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.db_manager import get_db_manager
from core.postgres_manager import PostgresManager

load_dotenv()

def check_db_date(client_id):
    print(f"Checking for {client_id}...")
    
    # 1. Check if PostgresManager has the method
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        pg = PostgresManager(db_url)
        if hasattr(pg, 'get_latest_raw_data_date'):
            print("PostgresManager has get_latest_raw_data_date.")
            try:
                date = pg.get_latest_raw_data_date(client_id)
                print(f"Date for {client_id}: {date}")
            except Exception as e:
                print(f"Error calling method: {e}")
        else:
            print("PostgresManager DOES NOT have get_latest_raw_data_date.")
            
    # 2. Check SQLite
    lite = get_db_manager(False)
    if hasattr(lite, 'get_latest_raw_data_date'):
        print("SQLite has get_latest_raw_data_date.")
    else:
        print("SQLite DOES NOT have get_latest_raw_data_date.")

if __name__ == "__main__":
    check_db_date('s2c_test')
