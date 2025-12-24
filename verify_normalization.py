"""
Verification Script: Compare Current vs Normalized Implementation Rate

This script compares:
1. Current logic: Is after_spend == $0 (for NEG) or has observed data (for BID)?
2. Normalized logic: Is the target's change significantly different from account baseline?
"""

import pandas as pd
from core.postgres_manager import PostgresManager

db_url = 'postgresql://postgres.wuakeiwxkjvhsnmkzywz:Zen%40rise%40123%21@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres'

def analyze_normalization(client_id='demo_account_2', window_days=30):
    pm = PostgresManager(db_url)
    
    # Get action impact data
    df = pm.get_action_impact(client_id, window_days=window_days)
    
    if df.empty:
        print("No data found.")
        return
    
    print(f"\n{'='*60}")
    print(f"NORMALIZATION ANALYSIS FOR {client_id} ({window_days}D WINDOW)")
    print(f"{'='*60}")
    
    # ==========================================
    # 1. CALCULATE ACCOUNT BASELINE
    # ==========================================
    total_before_spend = df['before_spend'].sum()
    total_after_spend = df['observed_after_spend'].sum()
    total_before_sales = df['before_sales'].sum()
    total_after_sales = df['observed_after_sales'].sum()
    
    baseline_spend_change = (total_after_spend / total_before_spend - 1) * 100 if total_before_spend > 0 else 0
    baseline_roas_before = total_before_sales / total_before_spend if total_before_spend > 0 else 0
    baseline_roas_after = total_after_sales / total_after_spend if total_after_spend > 0 else 0
    baseline_roas_change = ((baseline_roas_after / baseline_roas_before) - 1) * 100 if baseline_roas_before > 0 else 0
    
    print(f"\n📊 ACCOUNT BASELINE:")
    print(f"   Before Spend: ${total_before_spend:,.2f} | After Spend: ${total_after_spend:,.2f}")
    print(f"   Spend Change: {baseline_spend_change:+.1f}%")
    print(f"   ROAS Before: {baseline_roas_before:.2f} | ROAS After: {baseline_roas_after:.2f}")
    print(f"   ROAS Change: {baseline_roas_change:+.1f}%")
    
    # ==========================================
    # 2. ANALYZE NEGATIVE ACTIONS
    # ==========================================
    neg_df = df[df['action_type'].str.contains('NEG', na=False)].copy()
    
    if len(neg_df) > 0:
        # Current logic: after_spend == 0
        current_confirmed_neg = (neg_df['observed_after_spend'] == 0).sum()
        
        # Normalized logic: spend dropped MORE than baseline
        # If baseline dropped 30%, a target must drop >80% to be "significantly different"
        threshold = max(baseline_spend_change - 50, -95)  # At least 50% below baseline, max 95% drop
        neg_df['spend_change_pct'] = (neg_df['observed_after_spend'] / neg_df['before_spend'] - 1) * 100
        neg_df['spend_change_pct'] = neg_df['spend_change_pct'].fillna(-100)  # If before=0, treat as -100%
        
        normalized_confirmed_neg = (neg_df['spend_change_pct'] < threshold).sum()
        
        print(f"\n🚫 NEGATIVE ACTIONS ({len(neg_df)} total):")
        print(f"   Current Logic (after_spend == $0): {current_confirmed_neg} confirmed ({current_confirmed_neg/len(neg_df)*100:.1f}%)")
        print(f"   Normalized Logic (drop > {threshold:.0f}%): {normalized_confirmed_neg} confirmed ({normalized_confirmed_neg/len(neg_df)*100:.1f}%)")
        
        # Show distribution
        print(f"\n   Spend Change Distribution:")
        print(f"     100% drop (to $0): {(neg_df['spend_change_pct'] == -100).sum()}")
        print(f"     50-99% drop: {((neg_df['spend_change_pct'] < -50) & (neg_df['spend_change_pct'] > -100)).sum()}")
        print(f"     0-50% drop: {((neg_df['spend_change_pct'] < 0) & (neg_df['spend_change_pct'] >= -50)).sum()}")
        print(f"     Increased: {(neg_df['spend_change_pct'] > 0).sum()}")
    
    # ==========================================
    # 3. ANALYZE BID CHANGES
    # ==========================================
    bid_df = df[df['action_type'].str.contains('BID', na=False)].copy()
    bid_df = bid_df[(bid_df['before_spend'] > 0) & (bid_df['observed_after_spend'] > 0)]
    
    if len(bid_df) > 0:
        # Current logic: has observed data (always true if we filtered)
        current_confirmed_bid = len(bid_df)
        
        # Normalized logic: ROAS improved MORE than baseline
        bid_df['roas_before'] = bid_df['before_sales'] / bid_df['before_spend']
        bid_df['roas_after'] = bid_df['observed_after_sales'] / bid_df['observed_after_spend']
        bid_df['roas_change_pct'] = ((bid_df['roas_after'] / bid_df['roas_before']) - 1) * 100
        
        # Normalized: Did this target beat the baseline?
        normalized_winners_bid = (bid_df['roas_change_pct'] > baseline_roas_change).sum()
        
        print(f"\n📈 BID CHANGES ({len(bid_df)} with valid data):")
        print(f"   Current Logic (has observed data): {current_confirmed_bid} confirmed ({100:.1f}%)")
        print(f"   Normalized Logic (beat baseline {baseline_roas_change:+.1f}%): {normalized_winners_bid} ({normalized_winners_bid/len(bid_df)*100:.1f}%)")
        
        # Win Rate comparison
        current_winners = (bid_df['roas_after'] > bid_df['roas_before']).sum()
        print(f"\n   Win Rate Comparison:")
        print(f"     Absolute (ROAS improved): {current_winners} ({current_winners/len(bid_df)*100:.1f}%)")
        print(f"     Normalized (beat baseline): {normalized_winners_bid} ({normalized_winners_bid/len(bid_df)*100:.1f}%)")
    
    # ==========================================
    # 4. OVERALL SUMMARY
    # ==========================================
    print(f"\n{'='*60}")
    print(f"SUMMARY COMPARISON")
    print(f"{'='*60}")
    
    # Current Implementation Rate
    current_confirmed = df['validation_status'].str.contains('✓|Observed', na=False, regex=True).sum()
    current_not_impl = df['validation_status'].str.contains('NOT IMPLEMENTED', na=False).sum()
    current_impl_rate = current_confirmed / (current_confirmed + current_not_impl) * 100 if (current_confirmed + current_not_impl) > 0 else 0
    
    print(f"\nCurrent Implementation Rate: {current_impl_rate:.1f}% ({current_confirmed}/{current_confirmed + current_not_impl})")
    
    # Estimated Normalized Rate (rough)
    if len(neg_df) > 0 and len(bid_df) > 0:
        est_normalized = (normalized_confirmed_neg + normalized_winners_bid) / (len(neg_df) + len(bid_df)) * 100
        print(f"Estimated Normalized Rate: {est_normalized:.1f}%")
    
    print(f"\n💡 KEY INSIGHT:")
    print(f"   Account spend dropped {baseline_spend_change:.1f}% naturally.")
    print(f"   Many 'confirmed' actions are likely just riding this trend.")

if __name__ == "__main__":
    analyze_normalization('demo_account_2', window_days=30)
    print("\n")
    analyze_normalization('demo_account_2', window_days=7)
