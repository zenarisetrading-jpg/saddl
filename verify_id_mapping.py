import pandas as pd
import numpy as np
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from features.optimizer import identify_negative_candidates, calculate_bid_optimizations
from core.data_hub import DataHub
import streamlit as st

# Mock Streamlit session state
if 'unified_data' not in st.session_state:
    st.session_state.unified_data = {
        'bulk_id_mapping': None
    }

def test_id_mapping():
    print("=== Testing ID Mapping Hardening ===\n")
    
    # 1. Setup Mock Bulk File
    bulk_data = {
        'Campaign Name': ['Campaign A', 'Campaign A', 'Campaign B'],
        'Ad Group Name': ['AG 1', 'AG 1', 'AG 2'],
        'Keyword Text': ['keyword 1', 'keyword 2', None],
        'Product Targeting Expression': [None, None, 'asin="B001"'],
        'CampaignId': ['CAMP_111', 'CAMP_111', 'CAMP_222'],
        'AdGroupId': ['AG_111', 'AG_111', 'AG_222'],
        'KeywordId': ['KW_111', 'KW_222', None],
        'TargetingId': [None, None, 'PT_222'],
        'Match Type': ['exact', 'exact', 'target-match']
    }
    bulk_df = pd.DataFrame(bulk_data)
    st.session_state.unified_data['bulk_id_mapping'] = bulk_df
    print("Mock Bulk File setup with IDs for Campaign A/AG 1 and Campaign B/AG 2.")

    # 2. Setup Mock Search Term Report (NO IDs)
    str_data = {
        'Campaign Name': ['Campaign A', 'Campaign A', 'Campaign B'],
        'Ad Group Name': ['AG 1', 'AG 1', 'AG 2'],
        'Customer Search Term': ['keyword 1', 'keyword 2', 'asin="B001"'],
        'Targeting': ['keyword 1', 'keyword 2', 'asin="B001"'],
        'Match Type': ['exact', 'exact', 'target-match'],
        'Impressions': [100, 100, 100],
        'Clicks': [20, 20, 20],
        'Spend': [10.0, 10.0, 10.0],
        'Sales': [0.0, 0.0, 0.0],  # All bleeders to trigger negatives
        'Orders': [0, 0, 0],
        'ROAS': [0, 0, 0]
    }
    str_df = pd.DataFrame(str_data)
    
    config = {
        "NEGATIVE_CLICKS_THRESHOLD": 5,
        "NEGATIVE_SPEND_THRESHOLD": 5.0,
        "TARGET_ROAS": 2.5,
        "HARVEST_ORDERS": 3
    }

    # 3. Test Negative Candidates Mapping
    print("\n--- Testing Negative Candidates Mapping ---")
    harvest_empty = pd.DataFrame(columns=["Customer Search Term", "Campaign Name"])
    neg_kw, neg_pt, _ = identify_negative_candidates(str_df, config, harvest_empty)
    
    print(f"Generated {len(neg_kw)} neg keywords and {len(neg_pt)} neg PTs.")
    
    for df_name, df in [("neg_kw", neg_kw), ("neg_pt", neg_pt)]:
        print(f"\nChecking {df_name}:")
        for idx, row in df.iterrows():
            print(f"  Term: {row.get('Term') or row.get('Customer Search Term')}")
            print(f"    CampaignId: {row.get('CampaignId')} (Expected: populated)")
            print(f"    AdGroupId: {row.get('AdGroupId')} (Expected: populated)")
            if df_name == "neg_kw":
                print(f"    KeywordId: {row.get('KeywordId')} (Expected: populated)")
            else:
                print(f"    TargetingId: {row.get('TargetingId')} (Expected: populated)")
            
            # Assertions
            id_val = row.get('CampaignId')
            assert pd.notna(id_val) and str(id_val) != "", f"Missing CampaignId for {row.get('Term')}"
            
            id_val = row.get('AdGroupId')
            assert pd.notna(id_val) and str(id_val) != "", f"Missing AdGroupId for {row.get('Term')}"

    # 4. Test Bid Optimization Mapping
    print("\n--- Testing Bid Optimization Mapping ---")
    # Mocking some sales to trigger optimizations instead of just 0 bids
    str_df_bids = str_df.copy()
    str_df_bids['Sales'] = [50.0, 50.0, 50.0]
    str_df_bids['ROAS'] = 5.0
    
    b_ex, b_pt, b_agg, b_auto = calculate_bid_optimizations(str_df_bids, config)
    
    for name, df in [("Exact", b_ex), ("PT", b_pt)]:
        print(f"\nChecking {name} Bids:")
        if df.empty:
            print("  (Empty)")
            continue
        for idx, row in df.iterrows():
            print(f"  Target: {row.get('Targeting')}")
            print(f"    CampaignId: {row.get('CampaignId')} (Expected: populated)")
            print(f"    AdGroupId: {row.get('AdGroupId')} (Expected: populated)")
            if name == "Exact":
                print(f"    KeywordId: {row.get('KeywordId')} (Expected: populated)")
            else:
                print(f"    TargetingId: {row.get('TargetingId')} (Expected: populated)")
            
            # Assertions
            assert pd.notna(row.get('CampaignId')), f"Missing CampaignId for {row.get('Targeting')}"
            assert pd.notna(row.get('AdGroupId')), f"Missing AdGroupId for {row.get('Targeting')}"

    print("\n✅ ALL ID MAPPING TESTS PASSED")

if __name__ == "__main__":
    test_id_mapping()
