"""
Check Measured vs Pending Impact split
"""

import sys
import os
sys.path.append(os.getcwd())

from core.db_manager import get_db_manager
import pandas as pd

db = get_db_manager()
client_id = 'demo_account_2'

print("=" * 80)
print("MEASURED vs PENDING IMPACT BREAKDOWN")
print("=" * 80)

impact_df = db.get_action_impact(client_id, window_days=7)

if not impact_df.empty:
    # Same logic as impact_dashboard.py
    active_mask = (impact_df['before_spend'].fillna(0) + impact_df['after_spend'].fillna(0)) > 0
    active_df = impact_df[active_mask].copy()
    dormant_df = impact_df[~active_mask].copy()
    
    print(f"\n[WINDOWS USED]")
    print(f"  BEFORE: {impact_df['before_date'].iloc[0]} to {impact_df['before_end_date'].iloc[0]}")
    print(f"  AFTER:  {impact_df['after_date'].iloc[0]} to {impact_df['after_end_date'].iloc[0]}")
    
    print(f"\n[SPLIT SUMMARY]")
    print(f"  Total Actions:    {len(impact_df)}")
    print(f"  MEASURED (active): {len(active_df)} ({len(active_df)/len(impact_df)*100:.1f}%)")
    print(f"  PENDING (dormant): {len(dormant_df)} ({len(dormant_df)/len(impact_df)*100:.1f}%)")
    
    print(f"\n[MEASURED IMPACT BREAKDOWN]")
    print(f"  Total impact_score: ${active_df['impact_score'].sum():,.2f}")
    for at, grp in active_df.groupby('action_type'):
        print(f"    {at}: {len(grp)} actions, ${grp['impact_score'].sum():,.2f}")
    
    print(f"\n[PENDING IMPACT BREAKDOWN]")
    if dormant_df.empty:
        print("  No pending actions (all have traffic!)")
    else:
        for at, grp in dormant_df.groupby('action_type'):
            print(f"    {at}: {len(grp)} actions (waiting for traffic)")
        
        # Show sample pending actions
        print(f"\n  Sample pending actions:")
        sample_cols = ['action_date', 'action_type', 'target_text', 'before_spend', 'after_spend']
        avail = [c for c in sample_cols if c in dormant_df.columns]
        for _, row in dormant_df[avail].head(5).iterrows():
            print(f"    {row['action_date']:%Y-%m-%d} | {row['action_type']} | {str(row['target_text'])[:40]}")

print("=" * 80)
