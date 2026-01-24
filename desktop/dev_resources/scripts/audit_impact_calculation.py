"""
DEEP AUDIT: Impact Dashboard vs Script Calculation
===================================================
This script audits EXACTLY what the dashboard calculates step by step
to identify any discrepancies.

Compares:
1. Total actions in DB
2. Which reference date is used for maturity
3. Mature vs Pending split
4. Validation filtering
5. Market Drag exclusion
6. Final attributed impact
"""
import os
import sys
import pandas as pd
from dotenv import load_dotenv
from datetime import date, timedelta

# Load env from parent (saddle/saddle/.env)
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../.env')))

# Add parent to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.postgres_manager import PostgresManager
from features.impact_dashboard import get_maturity_status

def main():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not found in environment.")
        return
    db = PostgresManager(db_url)
    
    client_id = 's2c_uae_test'
    horizon = '14D'
    buffer_days = 3
    
    print("=" * 80)
    print("DEEP AUDIT: Impact Dashboard Calculation")
    print("=" * 80)
    
    # =====================================================
    # STEP 1: Get reference dates
    # =====================================================
    print("\n" + "=" * 80)
    print("STEP 1: REFERENCE DATES")
    print("=" * 80)
    
    # New method (raw data)
    latest_raw = db.get_latest_raw_data_date(client_id)
    print(f"   get_latest_raw_data_date(): {latest_raw}")
    
    # Old method (target_stats)
    with db._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT MAX(start_date) as max_date FROM target_stats WHERE client_id = %s
        """, (client_id,))
        row = cursor.fetchone()
        max_target_stats = row[0] if row else None
    print(f"   target_stats MAX(start_date): {max_target_stats}")
    
    print(f"\n   ⚠️ DIFFERENCE: {(latest_raw - max_target_stats).days if latest_raw and max_target_stats else 'N/A'} days")
    
    # =====================================================
    # STEP 2: Get raw impact data from DB
    # =====================================================
    print("\n" + "=" * 80)
    print("STEP 2: RAW IMPACT DATA FROM DB")
    print("=" * 80)
    
    impact_df = db.get_action_impact(client_id, before_days=14, after_days=14)
    print(f"   Total actions from get_action_impact(): {len(impact_df)}")
    
    if impact_df.empty:
        print("   ❌ No data!")
        return
    
    impact_df['action_date'] = pd.to_datetime(impact_df['action_date'])
    
    # =====================================================
    # STEP 3: Maturity calculation with BOTH reference dates
    # =====================================================
    print("\n" + "=" * 80)
    print("STEP 3: MATURITY CALCULATION (Compare Reference Dates)")
    print("=" * 80)
    
    # Calculate with OLD reference (target_stats max)
    impact_df['is_mature_OLD'] = impact_df['action_date'].apply(
        lambda d: get_maturity_status(d, max_target_stats, horizon=horizon)['is_mature']
    )
    
    # Calculate with NEW reference (raw data max)
    impact_df['is_mature_NEW'] = impact_df['action_date'].apply(
        lambda d: get_maturity_status(d, latest_raw, horizon=horizon)['is_mature']
    )
    
    # What's stored in DB?
    db_mature = impact_df['is_mature'].sum() if 'is_mature' in impact_df.columns else "N/A"
    
    old_mature = impact_df['is_mature_OLD'].sum()
    new_mature = impact_df['is_mature_NEW'].sum()
    
    print(f"   Using OLD ref ({max_target_stats}): {old_mature} mature, {len(impact_df) - old_mature} pending")
    print(f"   Using NEW ref ({latest_raw}): {new_mature} mature, {len(impact_df) - new_mature} pending")
    print(f"   Stored in DB (is_mature):  {db_mature} mature")
    print(f"\n   ⚠️ DIFFERENCE: {new_mature - old_mature} more actions mature with new reference")
    
    # =====================================================
    # STEP 4: Show actions that CHANGE maturity status
    # =====================================================
    print("\n" + "=" * 80)
    print("STEP 4: ACTIONS THAT CHANGE STATUS (Old=Pending → New=Mature)")
    print("=" * 80)
    
    changed_df = impact_df[(impact_df['is_mature_OLD'] == False) & (impact_df['is_mature_NEW'] == True)]
    
    print(f"   Actions that become mature with new date: {len(changed_df)}")
    
    if len(changed_df) > 0:
        impact_col = 'final_decision_impact' if 'final_decision_impact' in changed_df.columns else 'decision_impact'
        changed_impact = changed_df[impact_col].sum()
        print(f"   Their combined impact: {changed_impact:+,.0f}")
        
        # Group by action date
        by_date = changed_df.groupby(changed_df['action_date'].dt.date)[impact_col].agg(['sum', 'count'])
        print(f"\n   {'Action Date':<15} {'Count':<8} {'Impact':<15}")
        print("   " + "-" * 45)
        for dt, row in by_date.iterrows():
            print(f"   {str(dt):<15} {int(row['count']):<8} {row['sum']:>+14,.0f}")
    
    # =====================================================
    # STEP 5: Validation filtering
    # =====================================================
    print("\n" + "=" * 80)
    print("STEP 5: VALIDATION FILTERING")
    print("=" * 80)
    
    if 'validation_status' in impact_df.columns:
        validated_mask = impact_df['validation_status'].str.contains(
            '✓|CPC Validated|CPC Match|Directional|Confirmed|Normalized|Volume', 
            na=False, regex=True
        )
        validated_count = validated_mask.sum()
        not_validated = len(impact_df) - validated_count
        print(f"   Validated: {validated_count}")
        print(f"   Not Validated: {not_validated}")
    else:
        print("   ⚠️ No validation_status column")
        validated_mask = pd.Series([True] * len(impact_df))
    
    # =====================================================
    # STEP 6: Calculate final impact BOTH ways
    # =====================================================
    print("\n" + "=" * 80)
    print("STEP 6: FINAL IMPACT CALCULATION")
    print("=" * 80)
    
    impact_col = 'final_decision_impact' if 'final_decision_impact' in impact_df.columns else 'decision_impact'
    
    # OLD WAY: Using target_stats date
    old_filtered = impact_df[
        (impact_df['is_mature_OLD'] == True) & 
        validated_mask &
        (impact_df['market_tag'] != 'Market Drag')
    ]
    old_impact = old_filtered[impact_col].sum()
    
    # NEW WAY: Using raw data date
    new_filtered = impact_df[
        (impact_df['is_mature_NEW'] == True) & 
        validated_mask &
        (impact_df['market_tag'] != 'Market Drag')
    ]
    new_impact = new_filtered[impact_col].sum()
    
    print(f"   OLD method (ref={max_target_stats}): {len(old_filtered)} actions → {old_impact:+,.0f} AED")
    print(f"   NEW method (ref={latest_raw}): {len(new_filtered)} actions → {new_impact:+,.0f} AED")
    print(f"\n   ⚠️ DIFFERENCE: {new_impact - old_impact:+,.0f} AED")
    
    # =====================================================
    # STEP 7: Dashboard comparison
    # =====================================================
    print("\n" + "=" * 80)
    print("STEP 7: DASHBOARD COMPARISON")
    print("=" * 80)
    
    print(f"   Dashboard shows: +16,568 AED")
    print(f"   Executive Dashboard shows: +19,021 AED")
    print(f"   Script OLD method: {old_impact:+,.0f} AED")
    print(f"   Script NEW method: {new_impact:+,.0f} AED")
    
    if abs(new_impact - 16568) < 10:
        print(f"\n   ✅ NEW method matches Impact Dashboard!")
    elif abs(old_impact - 16568) < 10:
        print(f"\n   ⚠️ Dashboard is using OLD reference date")
    else:
        print(f"\n   ❓ Neither matches exactly - need deeper investigation")
    
    print("\n" + "=" * 80)
    print("AUDIT COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
