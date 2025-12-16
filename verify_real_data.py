
import pandas as pd
import sys
import os

# Add current dict to path
sys.path.append(os.getcwd())

from core.data_loader import SmartMapper, load_uploaded_file
from core.data_hub import DataHub
# Mock Streamlit for DataHub
import streamlit as st
if 'unified_data' not in st.session_state:
    st.session_state.unified_data = {
        'search_term_report': None,
        'advertised_product_report': None,
        'bulk_id_mapping': None,
        'upload_status': {'search_term_report': False, 'bulk_id_mapping': False}
    }
    
# Mock config for Optimizer
class MockOptimizer:
    def __init__(self):
        self.config = {
            'TARGET_ROAS': 2.5,
            'MIN_CLICKS': 5,
            'MAX_BID_CHANGE': 0.2,
            'NEGATIVE_CLICKS_THRESHOLD': 10,
            'NEGATIVE_SPEND_THRESHOLD': 10.0,
            'HARVEST_CLICKS': 2,
            'HARVEST_ORDERS': 1,
            'HARVEST_SALES': 50.0,
            'HARVEST_ROAS_MULT': 0.8,
            'DEDUPE_SIMILARITY': 0.90
        }

def load_real_file(filepath):
    print(f"Loading {filepath}...")
    try:
        return pd.read_excel(filepath)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None

def verify_real_data():
    import streamlit as st
    print("=== STARTING REAL DATA VERIFICATION ===")
    
    # 1. Define File Paths
    search_term_path = "Sponsored_Products_Search_term_report (4).xlsx"
    bulk_path = "Bulk-SP.xlsx"
    product_path = "Sponsored_Products_Advertised_product_report.xlsx"
    
    # 2. Load & Map Search Term Report
    df_st = load_real_file(search_term_path)
    if df_st is None: return
    
    print("RAW COLUMNS: " + str(list(df_st.columns)))
    
    st_map = SmartMapper.map_columns(df_st)
    df_st_renamed = df_st.rename(columns={v: k for k, v in st_map.items()})
    print(f"Search Term Report: {len(df_st_renamed)} rows")
    print(f"Mapped Columns: {list(df_st_renamed.columns)}")
    
    # 3. Load & Map Bulk Filect Auto Campaign Targeting
    if 'Targeting' in df_st_renamed.columns:
        # Check for Auto match type
        auto_mask = df_st_renamed['Match Type'].astype(str).str.lower().str.contains('auto')
        if auto_mask.any():
            print("\n--- DEBUG: Auto Campaign Data Sample ---")
            cols_to_show = ['Campaign Name', 'Targeting', 'Match Type']
            if 'TargetingExpression' in df_st_renamed.columns:
                cols_to_show.append('TargetingExpression')
            print(df_st_renamed[auto_mask][cols_to_show].head(10).to_string())
            print("----------------------------------------\n")
            return # EXIT EARLY FOR DEBUGGING
    
    # 3. Load & Map Bulk File
    df_bulk = load_real_file(bulk_path)
    if df_bulk is None: return
    
    # print("RAW BULK COLUMNS: " + str(list(df_bulk.columns)))
    # if 'Product' in df_bulk.columns:
    #    print(f"Unique PRODUCT values: {df_bulk['Product'].unique()[:10]}")
    # exit() # EXIT DEBUG to see columns
    
    bulk_map = SmartMapper.map_columns(df_bulk)
    df_bulk_renamed = df_bulk.rename(columns={v: k for k, v in bulk_map.items()})
    
    # Fallback Logic Test
    if 'Campaign Name' not in df_bulk_renamed.columns:
        print("Trigerring Bulk ID Fallback...")
        candidates = [c for c in df_bulk.columns if 'Campaign' in c and 'Name' in c]
        if candidates:
            df_bulk_renamed['Campaign Name'] = df_bulk[candidates[0]]
            print(f"Fallback: Mapped 'Campaign Name' from '{candidates[0]}'")
            
    print(f"Bulk File: {len(df_bulk_renamed)} rows")
    print(f"Mapped Columns: {list(df_bulk_renamed.columns)}")
    
    # Initialize DataHub with the loaded dataframes
    hub = DataHub()
    # DataHub uses st.session_state.unified_data
    st.session_state.unified_data['search_term_report'] = df_st_renamed
    st.session_state.unified_data['bulk_id_mapping'] = df_bulk_renamed
    
    hub._enrich_data()
    print("DEBUG: Data Enrichment Complete.")
    
    # Check enriched data columns
    # enriched = st.session_state.unified_data.get('enriched_data')
    # if enriched is not None:
    #      print(f"DEBUG: Enriched Columns: {list(enriched.columns)}")
    #      if 'KeywordId' in enriched.columns:
    #          print(f"DEBUG: Final KeywordId count: {enriched['KeywordId'].notna().sum()}")
    #      if 'TargetingId' in enriched.columns:
    #          print(f"DEBUG: Final TargetingId count: {enriched['TargetingId'].notna().sum()}")
             
    # print("EXITING DEBUG verify_real_data.py after enrichment")
    # return
    
    # 4. Enrich Data (Manual Merge)
    print("\nEnriching Data...")
    enriched = df_st_renamed.copy()
    
    # Merge Bulk IDs
    if 'Campaign Name' in enriched.columns and 'Campaign Name' in df_bulk_renamed.columns:
        print("Merging Bulk IDs...")
        id_subset = df_bulk_renamed[['Campaign Name', 'CampaignId']].drop_duplicates()
        if 'Ad Group Name' in df_bulk_renamed.columns and 'AdGroupId' in df_bulk_renamed.columns:
             id_subset = df_bulk_renamed[['Campaign Name', 'CampaignId', 'Ad Group Name', 'AdGroupId']].drop_duplicates()
             enriched = enriched.merge(id_subset, on=['Campaign Name', 'Ad Group Name'], how='left')
        else:
             enriched = enriched.merge(id_subset, on=['Campaign Name'], how='left')
             
    print(f"Enriched Data: {len(enriched)} rows")
    print(f"Enriched Columns: {list(enriched.columns)}")
    if 'CampaignId' in enriched.columns:
        mapped_count = enriched['CampaignId'].notna().sum()
        print(f"Campaign IDs Mapped: {mapped_count} / {len(enriched)}")
    else:
        print("❌ CampaignId NOT found in enriched data!")

    # 5. Verify SKU Mapping Logic (Simulate CreatorModule)
    print("\n--- Verifying SKU Mapping Logic ---")
    df_prod = load_real_file(product_path)
    if df_prod is not None:
        p_map = SmartMapper.map_columns(df_prod)
        df_prod_renamed = df_prod.rename(columns={v: k for k, v in p_map.items()})
        
        c_col = "Campaign Name"
        s_col = "SKU" # Mapped name
        
        if c_col in df_prod_renamed.columns and s_col in df_prod_renamed.columns:
            st_campaigns = set(df_st_renamed[c_col].unique())
            prod_campaigns = set(df_prod_renamed[c_col].unique())
            
            overlap = st_campaigns.intersection(prod_campaigns)
            print(f"Search Term Campaigns: {len(st_campaigns)}")
            print(f"Product Report Campaigns: {len(prod_campaigns)}")
            print(f"Overlap: {len(overlap)}")
            
            if len(overlap) == 0:
                print("DEBUG: NO OVERLAP!")
                print("Sample ST Campaigns:", list(st_campaigns)[:5])
                print("Sample Prod Campaigns:", list(prod_campaigns)[:5])
            else:
                print(f"Sample Overlap: {list(overlap)[:3]}")
                
            # Simulate Mapping
            sku_map = pd.Series(df_prod_renamed[s_col].values, index=df_prod_renamed[c_col]).to_dict()
            mapped_count = df_st_renamed[c_col].map(sku_map).notna().sum()
            print(f"Rows theoretically map-able: {mapped_count} / {len(df_st_renamed)}")
        else:
             print(f"Missing Columns in Product Report. Found: {list(df_prod_renamed.columns)}")
             print(f"Expected: {c_col}, {s_col}")
    
    # exit() # EXIT DEBUG to check SKU overlap

    # 5. Run Optimizer Logic
    print("\nRunning Optimizer Logic...")
    from features.optimizer import OptimizerModule, identify_negative_candidates, calculate_bid_optimizations, identify_harvest_candidates, prepare_data
    from utils.matchers import ExactMatcher
    
    opt = OptimizerModule()
    
    # Prepare Data (add derived columns like ROAS, CPC)
    enriched, date_info = prepare_data(enriched, opt.config)
    print(f"Data Prepared: {len(enriched)} rows, Period: {date_info.get('label')}")
    
    # Harvest (Required for Negatives & Bids)
    matcher = ExactMatcher(enriched)
    harvest_df = identify_harvest_candidates(enriched, opt.config, matcher)
    print(f"Harvest Candidates: {len(harvest_df)}")
    
    # Negatives
    neg_kw, neg_pt = identify_negative_candidates(enriched, opt.config, harvest_df)
    print(f"Negative Keywords: {len(neg_kw)}")
    print(f"Negative Targets: {len(neg_pt)}")
    
    # Bids
    harvested_terms = set(harvest_df["Customer Search Term"].str.lower()) if not harvest_df.empty else set()
    direct, agg = calculate_bid_optimizations(enriched, opt.config, harvested_terms)
    print(f"Direct Bid Suggestions: {len(direct)}")
    print(f"Aggregated Bid Suggestions: {len(agg)}")
    
    if not neg_kw.empty:
        # Check for Isolation Negatives and verify aggregation
        isolation_negs = [n for n in neg_kw.to_dict('records') if n.get('Type') == 'Isolation']
        if isolation_negs:
            print(f"Found {len(isolation_negs)} Isolation Negatives")
            example = isolation_negs[0]
            print(f"Example Isolation Negative: {example['Term']} | Clicks: {example['Clicks']} | Spend: {example['Spend']}")
            
            # Check if original data has multiple rows for this term
            term_rows = enriched[
                (enriched['Customer Search Term'].astype(str).str.lower().str.strip() == example['Term']) &
                (enriched['Campaign Name'] == example['Campaign Name'])
            ]
            print(f"Original Data Rows for '{example['Term']}': {len(term_rows)}")
            print(f"Total Clicks in Data: {term_rows['Clicks'].sum()}")
            
            if abs(term_rows['Clicks'].sum() - example['Clicks']) < 0.01:
                print("✅ Aggregation Verified: Clicks match total in data.")
            else:
                print("❌ Aggregation Failed: Clicks do not match total.")
        else:
            print("No Isolation Negatives found to verify.")

    # 6. Verify Bulk Generation (New Feature)
    print("\nVerifying Bulk Generation...")
    from features.optimizer import generate_negatives_bulk, generate_bids_bulk
    
    # Negative Bulk Check
    if len(neg_kw) > 0 or len(neg_pt) > 0:
        bulk_df = generate_negatives_bulk(neg_kw, neg_pt)
        print(f"Generated {len(bulk_df)} negative bulk rows")
        
        # Check for IDs
        if 'Campaign ID' in bulk_df.columns and 'Ad Group ID' in bulk_df.columns:
             missing_ids = bulk_df[
                 (bulk_df['Campaign ID'] == "") | (bulk_df['Campaign ID'].isnull())
             ]
             if len(missing_ids) > 0:
                 print(f"⚠️ Warning: {len(missing_ids)} negative rows missing Campaign ID")
             else:
                 print("✅ All negative rows have Campaign ID")
        else:
            print("❌ 'Campaign ID' missing from negative bulk!")
            
    # Bid Bulk Check (New)
    all_bids = pd.concat([direct, agg]) if not direct.empty or not agg.empty else pd.DataFrame()
    if not all_bids.empty:
        bids_bulk, skipped_bids = generate_bids_bulk(all_bids)
        print(f"Generated {len(bids_bulk)} bid bulk rows")
        
        # Check for Keyword ID / Product Targeting ID
        # 1. Keywords
        kw_rows = bids_bulk[bids_bulk['Entity'] == 'Keyword']
        if not kw_rows.empty:
            missing_kw_ids = kw_rows[(kw_rows['Keyword ID'] == "") | (kw_rows['Keyword ID'].isnull())]
            if len(missing_kw_ids) > 0:
                 print(f"⚠️ Warning: {len(missing_kw_ids)}/{len(kw_rows)} keywords missing Keyword ID")
            else:
                 print(f"✅ All {len(kw_rows)} keywords have Keyword ID")
                 
        # 2. Product Targets
        pt_rows = bids_bulk[bids_bulk['Entity'] == 'Product Targeting']
        if not pt_rows.empty:
            missing_pt_ids = pt_rows[(pt_rows['Product Targeting ID'] == "") | (pt_rows['Product Targeting ID'].isnull())]
            if len(missing_pt_ids) > 0:
                 print(f"⚠️ Warning: {len(missing_pt_ids)}/{len(pt_rows)} targets missing Product Targeting ID")
            else:
                 print(f"✅ All {len(pt_rows)} targets have Product Targeting ID")
                 
                 
    # Verify Auto/Category Granularity
    print("\nVerifying Auto/Category Granularity...")
    auto_cat_bids = bids_bulk[
        bids_bulk['Product Targeting Expression'].str.contains('category=|close-match|loose-match', case=False, na=False)
    ]
    if not auto_cat_bids.empty:
        print(f"Found {len(auto_cat_bids)} Auto/Category Bid Updates")
        # Check if we have multiple entries for same ad group (proof of granularity)
        grouped = auto_cat_bids.groupby(['Campaign Name', 'Ad Group Name']).size()
        multi_target_groups = grouped[grouped > 1]
        if not multi_target_groups.empty:
            print(f"✅ Confirmed granular targeting: {len(multi_target_groups)} Ad Groups have multiple Auto/Category updates.")
            print(multi_target_groups.head())
        else:
            print("⚠️ All Ad Groups have single Auto/Category update (Could be data distribution or aggregation issue)")
            # Print sample to inspect
            print(auto_cat_bids[['Campaign Name', 'Ad Group Name', 'Product Targeting Expression']].head())
    else:
        print("No Auto/Category bids found to verify granularity.")
                 
    if not harvest_df.empty:
        print("\nTop 5 Harvest Candidates:")
        print(harvest_df[['Customer Search Term', 'Sales', 'ROAS', 'New Bid']].head().to_string())

    # 6. Verify ASIN Mapper Logic
    print("\nVerifying ASIN Mapper...")
    from features.asin_mapper import ASINMapperModule
    try:
        asin_mapper = ASINMapperModule()
        # Mock st.secrets for checking config load
        import streamlit as st
        # We can't easily mock secrets but we can check validate_data
        is_valid, msg = asin_mapper.validate_data(enriched)
        print(f"ASIN Mapper Validation: {'✅ Passed' if is_valid else '❌ Failed'}")
        if not is_valid:
            print(f"Error: {msg}")
        else:
            # Run simple analysis (headless)
            res = asin_mapper.analyze(enriched)
            print(f"ASINs Found: {res.get('asins_found', 0)}")
    except Exception as e:
        print(f"❌ ASIN Mapper Test Failed: {e}")

    # 7. Verify AI Insights Logic
    print("\nVerifying AI Insights (Clustering)...")
    from features.ai_insights import AIInsightsModule
    try:
        ai_module = AIInsightsModule()
        is_valid, msg = ai_module.validate_data(enriched)
        print(f"AI Insights Validation: {'✅ Passed' if is_valid else '❌ Failed'}")
        if not is_valid:
             print(f"Error: {msg}")
        # Note: We skip full analyze() here as it relies on sklearn/API which might be slow or fail without keys
    except Exception as e:
        print(f"❌ AI Insights Test Failed: {e}")

if __name__ == "__main__":
    verify_real_data()
