"""
Diagnostic script to show action windows used in Impact Dashboard calculation.
Shows: Action Date | Before Start | Before End | After Start | After End | Is Mature
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

def show_action_windows(client_id: str, horizon_days: int = 14, buffer_days: int = 3):
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not found in environment.")
        return
    db = PostgresManager(db_url)
    
    print(f"📊 Impact Dashboard Action Windows for: {client_id}")
    print(f"   Horizon: {horizon_days}D + {buffer_days}D buffer = {horizon_days + buffer_days}D maturity requirement")
    print()
    
    # Use the actual get_action_impact method which returns full details
    impact_df = db.get_action_impact(client_id, before_days=14, after_days=horizon_days)
    
    if impact_df.empty:
        print("❌ No impact data found.")
        return
    
    # DEBUG: Show available columns
    print("🔍 DEBUG: Available Columns in impact_df:")
    print(f"   {list(impact_df.columns)}")
    print()
    
    # Check key columns
    has_mature = 'is_mature' in impact_df.columns
    has_market_tag = 'market_tag' in impact_df.columns
    has_final_impact = 'final_decision_impact' in impact_df.columns
    has_decision_impact = 'decision_impact' in impact_df.columns
    
    print(f"   is_mature: {'✅' if has_mature else '❌'}")
    print(f"   market_tag: {'✅' if has_market_tag else '❌'}")
    print(f"   final_decision_impact: {'✅' if has_final_impact else '❌'}")
    print(f"   decision_impact: {'✅' if has_decision_impact else '❌'}")
    print()
    
    # Use same logic as dashboard
    impact_col = 'final_decision_impact' if has_final_impact else 'decision_impact'
    
    if has_mature:
        mature_df = impact_df[impact_df['is_mature'] == True].copy()
        pending_df = impact_df[impact_df['is_mature'] != True].copy()
    else:
        print("⚠️ No 'is_mature' column - assuming all mature")
        mature_df = impact_df.copy()
        pending_df = pd.DataFrame()
    
    print(f"   Total Actions: {len(impact_df)}")
    print(f"   Mature: {len(mature_df)} | Pending: {len(pending_df)}")
    print()
    
    # Market Drag Exclusion (same as dashboard)
    if has_market_tag:
        drag_count = (mature_df['market_tag'] == 'Market Drag').sum()
        print(f"   Market Drag Actions (excluded): {drag_count}")
        mature_no_drag = mature_df[mature_df['market_tag'] != 'Market Drag']
    else:
        print("   market_tag not available - no drag exclusion")
        mature_no_drag = mature_df
    
    # Calculate attributed impact
    if impact_col in mature_no_drag.columns:
        total_impact = mature_no_drag[impact_col].sum()
    else:
        print(f"⚠️ Column '{impact_col}' not found. Showing raw 'decision_impact' calculation.")
        # Recalculate
        mature_no_drag['decision_impact'] = mature_no_drag['observed_after_sales'] - mature_no_drag['expected_sales']
        total_impact = mature_no_drag['decision_impact'].sum()
    
    print()
    print("=" * 80)
    print(f"ATTRIBUTED IMPACT UNIVERSAL (Dashboard Equivalent): {total_impact:,.2f} AED")
    print("=" * 80)
    print()
    
    # Group by action week for breakdown
    mature_no_drag['action_week'] = pd.to_datetime(mature_no_drag['action_date']).dt.to_period('W-MON').dt.start_time
    
    week_summary = mature_no_drag.groupby('action_week').agg({
        'action_date': 'count',
        impact_col: 'sum'
    }).rename(columns={'action_date': 'action_count', impact_col: 'decision_impact'})
    
    print(f"{'Week Of':<12} | {'Actions':<8} | {'Decision Impact':<15}")
    print("-" * 50)
    
    for week, row in week_summary.iterrows():
        impact = row['decision_impact'] if pd.notna(row['decision_impact']) else 0
        print(f"{str(week)[:10]:<12} | {row['action_count']:<8} | {impact:>12,.2f} AED")
    
    print("-" * 50)
    print(f"{'TOTAL':<12} | {len(mature_no_drag):<8} | {total_impact:>12,.2f} AED")

if __name__ == "__main__":
    show_action_windows("s2c_uae_test", horizon_days=14, buffer_days=3)
