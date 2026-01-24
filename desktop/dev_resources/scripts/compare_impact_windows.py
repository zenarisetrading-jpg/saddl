"""
Compare Impact Before and After Dec 30 Window
==============================================
This script verifies that previous windows haven't changed
and shows the incremental impact of the Dec 30 window.

Expected: 
- Windows up to Dec 08 = 18.7K (stable)
- Dec 30 window alone = -6.7K
- Total should be 18.7K + (-6.7K) = ~12K
"""
import os
import sys
import pandas as pd
from dotenv import load_dotenv

# Load env from parent (saddle/saddle/.env)
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../.env')))

# Add parent to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.postgres_manager import PostgresManager
from datetime import date

def main():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not found in environment.")
        return
    db = PostgresManager(db_url)
    
    client_id = 's2c_uae_test'
    
    print("=" * 70)
    print("IMPACT COMPARISON: Before vs After Dec 30 Window")
    print("=" * 70)
    
    # 1. Get latest raw data date
    latest_raw = db.get_latest_raw_data_date(client_id)
    print(f"\n1. Latest Raw Data Date: {latest_raw}")
    
    # 2. Get all impact data
    impact_df = db.get_action_impact(client_id, before_days=14, after_days=14)
    print(f"2. Total Actions in DB: {len(impact_df)}")
    
    if impact_df.empty:
        print("❌ No impact data found!")
        return
    
    # Determine impact column
    impact_col = 'final_decision_impact' if 'final_decision_impact' in impact_df.columns else 'decision_impact'
    
    # Convert action_date
    impact_df['action_date'] = pd.to_datetime(impact_df['action_date'])
    impact_df['action_week'] = impact_df['action_date'].dt.to_period('W-MON').dt.start_time.dt.date
    
    # 3. Separate windows BEFORE and AFTER Dec 29
    cutoff_date = date(2025, 12, 29)
    
    before_dec29 = impact_df[impact_df['action_date'].dt.date < cutoff_date].copy()
    dec30_window = impact_df[impact_df['action_date'].dt.date >= cutoff_date].copy()
    
    print(f"\n3. Actions BEFORE Dec 29: {len(before_dec29)}")
    print(f"   Actions ON/AFTER Dec 29: {len(dec30_window)}")
    
    # 4. Show impact by window (BEFORE Dec 29)
    print("\n" + "=" * 70)
    print("SECTION A: Windows BEFORE Dec 29 (Should Total ~18.7K)")
    print("=" * 70)
    
    # Filter to mature + validated + exclude market drag
    def filter_for_impact(df):
        """Apply same filters as dashboard"""
        filtered = df.copy()
        
        # Validated only
        if 'validation_status' in filtered.columns:
            validated_mask = filtered['validation_status'].str.contains(
                '✓|CPC Validated|CPC Match|Directional|Confirmed|Normalized|Volume', 
                na=False, regex=True
            )
            filtered = filtered[validated_mask]
        
        # Mature only
        if 'is_mature' in filtered.columns:
            filtered = filtered[filtered['is_mature'] == True]
        
        # Exclude market drag
        if 'market_tag' in filtered.columns:
            filtered = filtered[filtered['market_tag'] != 'Market Drag']
        
        return filtered
    
    before_filtered = filter_for_impact(before_dec29)
    
    print(f"\n   After filtering (validated + mature + no drag): {len(before_filtered)}")
    
    # Group by week
    if len(before_filtered) > 0:
        week_summary = before_filtered.groupby('action_week').agg({
            impact_col: 'sum',
            'action_date': 'count'
        }).rename(columns={'action_date': 'count'})
        
        print(f"\n   {'Week Of':<12} | {'Count':<8} | {'Impact':<15}")
        print("   " + "-" * 45)
        
        total_before = 0
        for week, row in week_summary.iterrows():
            impact = row[impact_col]
            total_before += impact
            print(f"   {str(week):<12} | {int(row['count']):<8} | {impact:>+14,.0f}")
        
        print("   " + "-" * 45)
        print(f"   {'SUBTOTAL':<12} | {len(before_filtered):<8} | {total_before:>+14,.0f}")
    else:
        total_before = 0
        print("   No filtered actions found before Dec 29")
    
    # 5. Show Dec 30 window impact
    print("\n" + "=" * 70)
    print("SECTION B: Dec 30 Window ONLY")
    print("=" * 70)
    
    dec30_filtered = filter_for_impact(dec30_window)
    
    print(f"\n   Total in window: {len(dec30_window)}")
    print(f"   After filtering: {len(dec30_filtered)}")
    
    if len(dec30_filtered) > 0:
        dec30_impact = dec30_filtered[impact_col].sum()
        print(f"   Dec 30 Window Impact: {dec30_impact:>+14,.0f}")
    else:
        dec30_impact = 0
        print("   Dec 30 Window Impact: (none mature/validated)")
    
    # 6. Show raw Dec 30 data (before filtering)
    print("\n   Raw Dec 30 window breakdown (ALL, before filtering):")
    if 'is_mature' in dec30_window.columns:
        mature_in_dec30 = dec30_window['is_mature'].sum()
        pending_in_dec30 = len(dec30_window) - mature_in_dec30
        print(f"   - Mature: {mature_in_dec30}")
        print(f"   - Pending: {pending_in_dec30}")
    
    if 'market_tag' in dec30_window.columns:
        drag_in_dec30 = (dec30_window['market_tag'] == 'Market Drag').sum()
        print(f"   - Market Drag: {drag_in_dec30}")
    
    # 7. Calculate expected vs actual
    print("\n" + "=" * 70)
    print("SECTION C: RECONCILIATION")
    print("=" * 70)
    
    expected_total = total_before + dec30_impact
    
    print(f"\n   Windows before Dec 29:  {total_before:>+14,.0f}")
    print(f"   Dec 30 window:          {dec30_impact:>+14,.0f}")
    print("   " + "-" * 40)
    print(f"   EXPECTED TOTAL:         {expected_total:>+14,.0f}")
    
    # Get actual from full calculation
    all_filtered = filter_for_impact(impact_df)
    actual_total = all_filtered[impact_col].sum()
    
    print(f"\n   ACTUAL TOTAL (all filtered): {actual_total:>+14,.0f}")
    print(f"   DISCREPANCY:             {actual_total - expected_total:>+14,.0f}")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
