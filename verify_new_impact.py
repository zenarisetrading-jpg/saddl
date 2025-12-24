"""
Verify the new clean fixed-window impact calculation
"""

import sys
import os
sys.path.append(os.getcwd())

from core.db_manager import get_db_manager
import pandas as pd

db = get_db_manager()
client_id = 'demo_account_2'

# Get the impact data
print("=" * 100)
print("NEW CLEAN FIXED-WINDOW IMPACT CALCULATION")
print("=" * 100)

impact_df = db.get_action_impact(client_id, window_days=7)

if not impact_df.empty:
    # Show the windows being used
    print(f"\n[WINDOWS USED]")
    print(f"  BEFORE window: {impact_df['before_date'].iloc[0]} to {impact_df['before_end_date'].iloc[0]}")
    print(f"  AFTER window:  {impact_df['after_date'].iloc[0]} to {impact_df['after_end_date'].iloc[0]}")
    
    # Show action date range
    print(f"\n[ELIGIBLE ACTIONS]")
    print(f"  Action dates in result: {impact_df['action_date'].min()} to {impact_df['action_date'].max()}")
    print(f"  Total actions: {len(impact_df)}")
    
    # Breakdown
    print(f"\n[BREAKDOWN BY ACTION TYPE]")
    for at, count in impact_df['action_type'].value_counts().items():
        impact = impact_df[impact_df['action_type'] == at]['impact_score'].sum()
        print(f"  {at}: {count} actions, ${impact:,.2f} impact")
    
    # Summary
    print(f"\n[IMPACT SUMMARY]")
    print(f"  Total impact_score: ${impact_df['impact_score'].sum():,.2f}")
    print(f"  Winners (positive): {(impact_df['impact_score'] > 0).sum()}")
    print(f"  Losers (negative):  {(impact_df['impact_score'] < 0).sum()}")
    print(f"  Neutral (zero):     {(impact_df['impact_score'] == 0).sum()}")
    
    # NOT IMPLEMENTED breakdown
    print(f"\n[VALIDATION STATUS]")
    for status, count in impact_df['validation_status'].value_counts().items():
        impact = impact_df[impact_df['validation_status'] == status]['impact_score'].sum()
        print(f"  {status}: {count} actions, ${impact:,.2f} impact")

print("=" * 100)
