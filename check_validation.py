"""Quick check of old_value/new_value in actions_log"""
import pandas as pd
from core.postgres_manager import PostgresManager

db_url = 'postgresql://postgres.wuakeiwxkjvhsnmkzywz:Zen%40rise%40123%21@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres'

pm = PostgresManager(db_url)
df = pm.get_action_impact('demo_account_2', window_days=30)

print("Columns:", df.columns.tolist())
print("\nSample of old_value/new_value:")
bid_df = df[df['action_type'].str.contains('BID', na=False)]
print(bid_df[['action_type', 'old_value', 'new_value', 'validation_status']].head(20).to_string())

print("\n\nValidation Status Distribution:")
print(df['validation_status'].value_counts())
