"""
Analyze Impact Breakdown (Updated)
==================================
Analysis of impact with new logic:
1. Spend Eliminated (Pauses) now calculated as (Spend Saved - Sales Lost).
2. Outlier Targets (loose-match) now capped by ROAS Efficiency.
3. Negatives now count Spend Saved.
"""
import os
import sys
import pandas as pd
from dotenv import load_dotenv

load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../.env')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.postgres_manager import PostgresManager

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

def main():
    db_url = os.environ.get("DATABASE_URL")
    db = PostgresManager(db_url)
    client_id = 's2c_uae_test'
    
    print("Fetching Impact Data...")
    # Get impact with CURRENT logic
    df = db.get_action_impact(client_id, before_days=14, after_days=14)
    
    # Filter for Mature only for fair comparison with old output
    mature_df = df[df['is_mature'] == True]
    
    print("\n" + "="*80)
    print("SECTION 1: IMPACT BY ACTION TYPE (Mature Only)")
    print("="*80)
    type_group = mature_df.groupby('action_type')[['final_decision_impact', 'target_text']].agg(
        Count=('target_text', 'count'),
        Impact=('final_decision_impact', 'sum')
    ).sort_values('Impact', ascending=False)
    print(type_group)
    print("-" * 40)
    print(f"TOTAL MATURE IMPACT: {mature_df['final_decision_impact'].sum():,.0f}")
    
    print("\n" + "="*80)
    print("SECTION 2: VALIDATION STATUS BREAKDOWN (Focus on Spend Eliminated)")
    print("="*80)
    status_group = mature_df.groupby('validation_status')[['final_decision_impact', 'target_text']].agg(
        Count=('target_text', 'count'),
        Impact=('final_decision_impact', 'sum')
    ).sort_values('Impact', ascending=True) # Bottom up to see negatives
    print(status_group)
    
    
    print("\n" + "="*80)
    print("SECTION 3: PAUSES DEEP DIVE ('Spend Eliminated')")
    print("="*80)
    # Filter for Spend Eliminated
    pauses = mature_df[mature_df['validation_status'].str.contains('Spend Eliminated', na=False)].sort_values('final_decision_impact')
    
    if len(pauses) > 0:
        print("Top 5 Negative Pauses (Profit Lost):")
        cols = ['target_text', 'campaign_name', 'before_spend', 'before_sales', 'final_decision_impact']
        print(pauses[cols].head(5).to_string(index=False))
        
        # Specifically highlight 'complements' info for user
        comps = pauses[pauses['target_text'] == 'complements']
        if not comps.empty:
            print("\n>> Complements Details:")
            print(comps[['action_date', 'campaign_name', 'ad_group_name', 'before_sales', 'before_spend']].to_string(index=False))
    
    print("\n" + "="*80)
    print("SECTION 4: OUTLIER CHECK ('loose-match')")
    print("="*80)
    lm = mature_df[mature_df['target_text'] == 'loose-match'].sort_values('final_decision_impact').head(1)
    if not lm.empty:
        print(lm[['target_text', 'action_date', 'spc_before', 'cpc_before', 'final_decision_impact']].to_string(index=False))
        print("(Note: SPC is Capped by ROAS Limit)")

if __name__ == "__main__":
    main()
