"""
Verify Impact Values by Action Window (14D Attribution)
========================================================
This script verifies the impact calculation per action window,
showing the breakdown for 14D horizon.

Run from desktop folder: python tests/verify_impact_by_window.py
"""
import sys
import os
sys.path.insert(0, '.')

from datetime import date, timedelta
import pandas as pd

def main():
    # Use PostgresManager directly
    from core.postgres_manager import PostgresManager
    
    print("=" * 60)
    print("Impact Verification by Action Window (14D)")
    print("=" * 60)
    
    # Get DATABASE_URL
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        try:
            with open('.env', 'r') as f:
                for line in f:
                    if line.startswith('DATABASE_URL='):
                        db_url = line.split('=', 1)[1].strip().strip('"').strip("'")
                        break
        except FileNotFoundError:
            pass
    
    if not db_url:
        print("❌ DATABASE_URL not found. Set it as environment variable or in .env file")
        return
    
    db = PostgresManager(db_url)
    client_id = 's2c_uae_test'
    
    # 1. Get actual latest raw data date
    print("\n1. LATEST DATA DATE:")
    try:
        latest_raw = db.get_latest_raw_data_date(client_id)
        print(f"   From raw_search_term_data: {latest_raw}")
    except Exception as e:
        print(f"   Error getting raw date: {e}")
        latest_raw = date.today()
    
    # 2. Get impact data
    print("\n2. FETCHING IMPACT DATA (14D before/after)...")
    impact_df = db.get_action_impact(client_id, before_days=14, after_days=14)
    print(f"   Total actions: {len(impact_df)}")
    
    if impact_df.empty:
        print("   ❌ No impact data found!")
        return
    
    # 3. Show action windows
    print("\n3. ACTION WINDOWS:")
    if 'action_date' in impact_df.columns:
        from features.impact_dashboard import get_maturity_status
        
        impact_df['action_date'] = pd.to_datetime(impact_df['action_date'])
        
        # Determine impact column
        impact_col = 'final_decision_impact' if 'final_decision_impact' in impact_df.columns else 'decision_impact'
        
        # Group by action date
        windows = impact_df.groupby(impact_df['action_date'].dt.date).agg({
            impact_col: 'sum',
            'action_date': 'count'
        }).rename(columns={'action_date': 'action_count'})
        
        print(f"\n   {'Action Date':<15} {'Actions':<10} {'Impact':<15} Maturity (as of {latest_raw})")
        print("   " + "-" * 70)
        
        total_mature_impact = 0
        total_pending_impact = 0
        mature_count = 0
        pending_count = 0
        
        for action_date in sorted(windows.index):
            count = int(windows.loc[action_date, 'action_count'])
            impact = float(windows.loc[action_date, impact_col])
            
            # Calculate maturity
            if latest_raw:
                maturity = get_maturity_status(
                    pd.Timestamp(action_date), 
                    latest_raw, 
                    horizon='14D'
                )
                status = "MATURE ✓" if maturity['is_mature'] else f"PENDING ({maturity['status']})"
                if maturity['is_mature']:
                    total_mature_impact += impact
                    mature_count += count
                else:
                    total_pending_impact += impact
                    pending_count += count
            else:
                status = "UNKNOWN"
            
            print(f"   {action_date} {count:<10} {impact:>+14,.0f}  {status}")
        
        print("   " + "-" * 70)
        print(f"   MATURE ({mature_count} actions):      {total_mature_impact:>+14,.0f}")
        print(f"   PENDING ({pending_count} actions):     {total_pending_impact:>+14,.0f}")
        print(f"   COMBINED TOTAL:              {total_mature_impact + total_pending_impact:>+14,.0f}")
    
    # 4. Breakdown by market_tag (Mature Only)
    print("\n4. MARKET TAG BREAKDOWN (Mature Only):")
    if 'market_tag' in impact_df.columns and latest_raw:
        from features.impact_dashboard import get_maturity_status
        
        impact_df['is_mature'] = impact_df['action_date'].apply(
            lambda d: get_maturity_status(d, latest_raw, horizon='14D')['is_mature']
        )
        
        mature_df = impact_df[impact_df['is_mature'] == True]
        impact_col = 'final_decision_impact' if 'final_decision_impact' in mature_df.columns else 'decision_impact'
        
        by_tag = mature_df.groupby('market_tag')[impact_col].sum()
        
        for tag, val in by_tag.items():
            print(f"   {tag:<20} {val:>+14,.0f}")
        
        print("   " + "-" * 35)
        attributed = by_tag.get('Offensive Win', 0) + by_tag.get('Defensive Win', 0) + by_tag.get('Gap', 0)
        print(f"   ATTRIBUTED IMPACT:  {attributed:>+14,.0f}  (excludes Market Drag)")
    
    print("\n" + "=" * 60)
    print("Done.")

if __name__ == "__main__":
    main()
