
import sys
import os
import pandas as pd
import numpy as np
import streamlit as st

# Mock Streamlit session state
if not hasattr(st, 'session_state'):
    st.session_state = {}

# Add current directory to path
sys.path.append(os.getcwd())

from features.optimizer import OptimizerModule
from features.creator import CreatorModule

def verify_optimizer():
    print("--- Verifying OptimizerModule ---")
    opt = OptimizerModule()
    
    # Create sample data
    df = pd.DataFrame({
        'Campaign Name': ['Camp A', 'Camp A', 'Camp B', 'Camp B'],
        'Ad Group Name': ['AG 1', 'AG 1', 'AG 2', 'AG 2'],
        'Targeting': ['keyword1', 'keyword2', 'asin1', 'keyword1'],
        'Match Type': ['EXACT', 'BROAD', 'ASIN', 'PHRASE'],
        'Customer Search Term': ['term1', 'term2', 'term3', 'term4'],
        'Impressions': [1000, 2000, 500, 1500],
        'Clicks': [50, 20, 5, 100],
        'Spend': [50.0, 10.0, 5.0, 150.0],
        'Sales': [200.0, 0.0, 0.0, 400.0],
        'Orders': [10, 0, 0, 20]
    })
    
    # Mock config
    opt.config['TARGET_ROAS'] = 2.5
    opt.config['MIN_CLICKS'] = 5
    
    print("1. Running calculate_bid_suggestions...")
    direct, agg = opt.calculate_bid_suggestions(df)
    print(f"   Direct Bids Generated: {len(direct)}")
    print(f"   Aggregated Bids Generated: {len(agg)}")
    
    print("2. Running identify_negative_candidates...")
    # Add a bleeder
    df.loc[4] = ['Camp C', 'AG 3', 'bleed', 'EXACT', 'bad term', 1000, 20, 50.0, 0.0, 0]
    neg_kw, neg_pt = opt.identify_negative_candidates(df)
    print(f"   Negative Keywords Found: {len(neg_kw)}")
    print(f"   Negative ASINs Found: {len(neg_pt)}")
    
    print("3. Running detect_asin_cannibalization...")
    # Add cannibalization case
    df.loc[5] = ['Camp D (B012345678)', 'AG X', 'term_can', 'EXACT', 'term_can', 100, 10, 10.0, 20.0, 1]
    df.loc[6] = ['Camp E (B012345678)', 'AG Y', 'term_can', 'EXACT', 'term_can', 100, 10, 10.0, 10.0, 1]
    can_df = opt.detect_asin_cannibalization(df)
    print(f"   Cannibalization Issues: {len(can_df)}")
    
    print("4. Running heatmap...")
    hm = opt.create_wasted_spend_heatmap(df, neg_kw, direct, agg)
    print(f"   Heatmap Rows: {len(hm)}")
    
    print("5. Running Harvest Identification...")
    # Add Harvest Candidate (High Sales, Broad Match)
    df.loc[7] = ['Camp F', 'AG Z', 'winner', 'BROAD', 'winner_term', 1000, 50, 20.0, 200.0, 10]
    # Add Existing Exact (to test Dedupe)
    df.loc[8] = ['Camp G', 'AG Z', 'winner_term', 'EXACT', 'winner_term', 100, 10, 5.0, 50.0, 2]
    
    from features.optimizer import ExactMatcher
    matcher = ExactMatcher(df)
    harvest_df = opt.identify_harvest_candidates(df, matcher)
    print(f"   Harvest Candidates: {len(harvest_df)} (Expected 1: 'winner_term' should be excluded by dedupe? No, 'winner_term' is the EXACT one. Wait. 'winner_term' is present as EXACT, so the BROAD instance should be deduped? Yes.)")
    # Actually, if 'winner_term' exists as EXACT, the finder should see it in ExactMatcher and REJECT the broad match candidate.
    # Let's verify logic: ExactMatcher builds set from 'EXACT' rows. 'winner_term' is in that set.
    # The candidate from row 7 (BROAD) has term 'winner_term'.
    # matcher.find_match('winner_term') will return True.
    # So it should be rejected.
    # Let's add a TRUE winner (no exact match)
    df.loc[9] = ['Camp H', 'AG W', 'super_winner', 'PHRASE', 'super_winner', 1000, 50, 20.0, 200.0, 10]
    
    # Re-run
    matcher = ExactMatcher(df) 
    harvest_df = opt.identify_harvest_candidates(df, matcher)
    print(f"   Harvest Candidates Found: {len(harvest_df)}")
    if not harvest_df.empty:
        print(f"   Candidates: {harvest_df['Customer Search Term'].tolist()}")

    print("6. Running Simulation...")
    st.session_state['simulation_results'] = None
    opt.simulate_impact(direct, agg)
    res = st.session_state.get('simulation_results')
    print(f"   Simulation Results: {'Success' if res else 'Failed'}")

def verify_creator():
    print("\n--- Verifying CreatorModule ---")
    creator = CreatorModule()
    
    # Mock payload
    harvest_df = pd.DataFrame({
        'Customer Search Term': ['winner1', 'winner2'],
        'Advertised SKU': ['SKU_A', 'SKU_B'],
        'Match Type': ['PHRASE', 'EXACT'],
        'New Bid': [1.5, 2.0]
    })
    
    print("1. Generating Bulk File...")
    from datetime import date
    bulk = creator.generate_bulk_file(harvest_df, "PORT123", 10.0, date.today())
    print(f"   Bulk File Rows: {len(bulk)}")
    print(f"   Columns: {list(bulk.columns)}")

if __name__ == "__main__":
    verify_optimizer()
    verify_creator()
