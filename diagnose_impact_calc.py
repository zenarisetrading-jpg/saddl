"""
Comprehensive Impact Calculation Diagnostics for demo_account_2

Shows:
1. What's in the database (target_stats)
2. Before/After calculation windows
3. Step-by-step impact calculations
4. Why we get +194 for 30 days with only 28 actions
"""

import sys
import os
sys.path.append(os.getcwd())

from core.db_manager import get_db_manager
import pandas as pd
from datetime import timedelta

from psycopg2.extras import RealDictCursor

db = get_db_manager()
client_id = 'demo_account_2'

print("=" * 100)
print("IMPACT CALCULATION DIAGNOSTICS FOR demo_account_2")
print("=" * 100)

# 1. Get available dates in target_stats
print("\n[1] AVAILABLE DATA DATES (target_stats)")
print("-" * 100)
with db._get_connection() as conn:
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("""
            SELECT DISTINCT start_date, COUNT(*) as row_count
            FROM target_stats
            WHERE client_id = %s
            GROUP BY start_date
            ORDER BY start_date DESC
        """, (client_id,))
        
        dates = cursor.fetchall()
        for row in dates:
            start_date = row['start_date']
            count = row['row_count']
            print(f"  {start_date}: {count:,} rows")

latest_data_date = pd.to_datetime(dates[0]['start_date'])
cutoff_date = latest_data_date - timedelta(days=30)

print(f"\n  Latest Data Date: {latest_data_date.strftime('%Y-%m-%d')}")
print(f"  30D Cutoff Date:  {cutoff_date.strftime('%Y-%m-%d')}")

# 2. Get all actions in the 30D window
print("\n[2] ACTIONS IN 30D WINDOW (actions_log)")
print("-" * 100)
with db._get_connection() as conn:
    actions_df = pd.read_sql("""
        SELECT 
            action_date,
            action_type,
            target_text,
            campaign_name,
            ad_group_name,
            match_type,
            reason
        FROM actions_log
        WHERE client_id = %s
        AND DATE(action_date) >= %s
        AND DATE(action_date) <= %s
        ORDER BY action_date DESC, action_type
    """, conn, params=(client_id, cutoff_date.date().isoformat(), latest_data_date.date().isoformat()))

print(f"  Total actions in window: {len(actions_df)}")
print(f"\n  Breakdown by type:")
for action_type, count in actions_df['action_type'].value_counts().items():
    print(f"    {action_type}: {count}")

# 3. Show deduplication logic
print("\n[3] DEDUPLICATION (Campaign + AdGroup + Target + Action)")
print("-" * 100)
before_dedup = len(actions_df)
actions_df['dedup_key'] = (
    actions_df['campaign_name'].fillna('').str.lower() + '|' +
    actions_df['ad_group_name'].fillna('').str.lower() + '|' +
    actions_df['target_text'].fillna('').str.lower() + '|' +
    actions_df['action_type'].fillna('')
)
actions_df_dedup = actions_df.drop_duplicates(subset='dedup_key', keep='first')
after_dedup = len(actions_df_dedup)

print(f"  Before dedup: {before_dedup}")
print(f"  After dedup:  {after_dedup}")
print(f"  Removed:      {before_dedup - after_dedup}")

# 4. Get the impact summary directly from DB
print("\n[4] RAW IMPACT DATA from get_action_impact()")
print("-" * 100)
impact_df = db.get_action_impact(client_id, window_days=7)
print(f"  Total records returned: {len(impact_df)}")

if not impact_df.empty:
    # Filter to 30D window
    impact_df['action_date_dt'] = pd.to_datetime(impact_df['action_date'], errors='coerce')
    impact_30d = impact_df[
        (impact_df['action_date_dt'] >= cutoff_date) & 
        (impact_df['action_date_dt'] <= latest_data_date)
    ].copy()
    
    print(f"  Records in 30D window: {len(impact_30d)}")
    
    # Show impact score calculation
    if 'impact_score' in impact_30d.columns:
        print(f"\n  Impact Score Stats:")
        print(f"    Total impact_score: ${impact_30d['impact_score'].sum():,.2f}")
        print(f"    Mean impact_score:  ${impact_30d['impact_score'].mean():,.2f}")
        print(f"    Positive actions:   {(impact_30d['impact_score'] > 0).sum()}")
        print(f"    Negative actions:   {(impact_30d['impact_score'] < 0).sum()}")
        print(f"    Zero impact:        {(impact_30d['impact_score'] == 0).sum()}")

# 5. Detailed breakdown of top 10 actions
print("\n[5] TOP 10 ACTIONS BY IMPACT")
print("-" * 100)
if not impact_30d.empty and 'impact_score' in impact_30d.columns:
    top_actions = impact_30d.nlargest(10, 'impact_score')[
        ['action_date', 'action_type', 'target_text', 'before_spend', 'after_spend', 
         'before_sales', 'after_sales', 'impact_score', 'validation_status']
    ]
    
    for idx, row in top_actions.iterrows():
        print(f"\n  Action: {row['action_type']} - {row['target_text'][:50]}")
        print(f"    Date: {row['action_date']}")
        print(f"    Before: ${row['before_spend']:.2f} spend, ${row['before_sales']:.2f} sales")
        print(f"    After:  ${row['after_spend']:.2f} spend, ${row['after_sales']:.2f} sales")
        print(f"    Impact: ${row['impact_score']:.2f}")
        print(f"    Status: {row['validation_status']}")

# 6. Show the calculation windows
print("\n[6] BEFORE/AFTER CALCULATION WINDOWS")
print("-" * 100)
print(f"  The 'before' window is the 7 days BEFORE the action date")
print(f"  The 'after' window is the 7 days AFTER the action date")
print(f"\n  Example for an action on {cutoff_date.strftime('%Y-%m-%d')}:")
print(f"    Before window: {(cutoff_date - timedelta(days=7)).strftime('%Y-%m-%d')} to {cutoff_date.strftime('%Y-%m-%d')}")
print(f"    After window:  {(cutoff_date + timedelta(days=1)).strftime('%Y-%m-%d')} to {(cutoff_date + timedelta(days=7)).strftime('%Y-%m-%d')}")

# 7. Check for data gaps
print("\n[7] DATA AVAILABILITY CHECK")
print("-" * 100)
if not impact_30d.empty:
    actions_with_no_before = impact_30d[impact_30d['before_spend'].isna() | (impact_30d['before_spend'] == 0)]
    actions_with_no_after = impact_30d[impact_30d['after_spend'].isna()]
    
    print(f"  Actions with no 'before' data: {len(actions_with_no_before)}")
    print(f"  Actions with no 'after' data:  {len(actions_with_no_after)}")
    
    if len(actions_with_no_after) > 0:
        print(f"\n  Sample actions with no 'after' data:")
        for idx, row in actions_with_no_after.head(5).iterrows():
            print(f"    {row['action_date']} - {row['action_type']} - {row['target_text'][:50]}")

print("\n" + "=" * 100)
print("SUMMARY")
print("=" * 100)
print(f"Data window:     {cutoff_date.strftime('%Y-%m-%d')} to {latest_data_date.strftime('%Y-%m-%d')}")
print(f"Actions logged:  {len(actions_df)}")
print(f"After dedup:     {len(actions_df_dedup)}")
print(f"Impact records:  {len(impact_30d) if not impact_30d.empty else 0}")
if not impact_30d.empty and 'impact_score' in impact_30d.columns:
    print(f"Total impact:    ${impact_30d['impact_score'].sum():,.2f}")
print("=" * 100)
