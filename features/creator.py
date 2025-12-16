"""
Creator Module (Launch & Harvest)

Handles creation of:
1. New Product Launches (Cold Start)
2. Harvest Campaigns (Scaling Winners)
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date
from io import BytesIO
import plotly.graph_objects as go

from features._base import BaseFeature
from core.data_loader import SmartMapper, safe_numeric, is_asin, load_uploaded_file
from utils.formatters import to_excel_download

# ==========================================
# CONSTANTS (LaunchPad)
# ==========================================
AUTO_PT_MULTIPLIERS = {
    "close-match": 1.5,
    "loose-match": 1.2,
    "substitutes": 0.8,
    "complements": 1.0
}
DEFAULT_EXACT_TOP = 5
DEFAULT_PHRASE_NEXT = 7

# Amazon Bulk File Standard Columns (Universal)
COLUMN_ORDER = [
    "Product", "Entity", "Operation", "Campaign ID", "Ad Group ID", "Portfolio ID", "Ad ID", "Keyword ID",
    "Product Targeting ID", "Campaign Name", "Ad Group Name", "Start Date", "End Date", "Targeting Type",
    "State", "Daily Budget", "SKU", "Ad Group Default Bid", "Bid", "Keyword Text",
    "Native Language Keyword", "Native Language Locale", "Match Type", "Bidding Strategy", "Placement", "Percentage",
    "Product Targeting Expression", "Audience ID", "Shopper Cohort Percentage", "Shopper Cohort Type",
    "Creative ID", "Tactic"
]

class CreatorModule(BaseFeature):
    """Unified Campaign Creator (Launch + Harvest)."""
    
    def render_ui(self):
        """Render main UI with tabs."""
        self.render_header("Campaign Launcher", "launcher")
        
        tab_launch, tab_harvest = st.tabs(["Launch New Product", "Harvest Winners"])
        
        with tab_launch:
            self._render_launch_tab()
            
        with tab_harvest:
            self._render_harvest_tab()

    # =========================================================================
    # TAB 1: LAUNCH NEW PRODUCT (Ported from app_v11.py)
    # =========================================================================
    def _render_launch_tab(self):
        """Render the cold start launch UI."""
        st.markdown("### 🚀 New Campaign Launcher")
        st.info("Generates a full-funnel structure (Auto + Manual + PT) with smart budget allocation.")

        # --- INPUTS ---
        col1, col2 = st.columns([1, 1])
        with col1:
            sku_input = st.text_input("Advertised SKU(s) (comma separated)", key="launch_skus")
            price = st.number_input("Product Price (AED)", min_value=1.0, value=99.0, step=0.5, key="launch_price")
            acos = st.slider("Target ACoS %", 5, 40, 20, key="launch_acos")
            
        with col2:
            asin_input = st.text_input("Competitor ASINs (comma separated)", key="launch_asins")
            total_budget = st.number_input("Total Daily Budget (AED)", min_value=10.0, value=200.0, step=10.0, key="launch_budget")
            cvr = st.selectbox("Est. Conversion Rate %", [6, 9, 12, 15, 20], index=2, key="launch_cvr")

        # Optional Keyword Upload
        uploaded_kw = st.file_uploader("Upload Keyword List (Optional CSV/XLSX)", type=['csv','xlsx'], key="launch_kw_file")
        
        with st.expander("⚙️ Advanced Configuration", expanded=False):
            c1, c2 = st.columns(2)
            with c1:
                campaign_types = st.multiselect(
                    "Campaign Tactics (Ordered by Priority)",
                    ["Auto", "Manual: Keywords", "Manual: ASIN/Product", "Category"],
                    default=["Auto", "Manual: Keywords", "Manual: ASIN/Product"]
                )
                bid_strategy = st.selectbox("Bidding Strategy", 
                    ["Dynamic bids - down only", "Dynamic bids - up and down", "Fixed bids"], index=0)
            with c2:
                use_auto_pt = st.checkbox("Enable Auto-PT Multipliers", value=True)
                top_n_kw = st.number_input("Limit Keywords (0=All)", 0, 500, 0)
        
        if st.button("Generate Launch Campaigns", type="primary"):
            if not sku_input:
                st.error("Please enter at least one SKU.")
                return

            # Process Inputs
            skus = [s.strip() for s in sku_input.split(",") if s.strip()]
            asins = [s.strip() for s in asin_input.split(",") if s.strip()]
            keywords = self._parse_keywords(uploaded_kw)
            if top_n_kw > 0 and keywords:
                keywords = keywords[:top_n_kw]
            
            # Calculate Base Bid
            base_bid = self._calc_base_bid(price, acos, cvr)
            st.success(f"🎯 Calculated Base Bid: **AED {base_bid:.2f}** (Price {price} * CVR {cvr}% * ACoS {acos}%)")
            
            # Allocate Budget
            allocation = self._allocate_budget(total_budget, campaign_types)
            st.info(f"💰 Budget Split: {', '.join([f'{k}: {v} AED' for k,v in allocation.items()])}")
            
            # Generate Rows
            bulk_df = self._generate_launch_bulk_rows(
                skus, keywords, asins, base_bid, allocation, 
                campaign_types, bid_strategy, use_auto_pt
            )
            
            # Preview & Export
            st.dataframe(bulk_df.head(100), use_container_width=True)
            
            # Download
            metadata = {
                "date": date.today().isoformat(),
                "skus": ",".join(skus),
                "base_bid": base_bid,
                "total_budget": total_budget
            }
            excel_data = self._to_excel_with_metadata(bulk_df, metadata)
            st.download_button(
                "📥 Download Bulk File (.xlsx)",
                data=excel_data,
                file_name=f"launch_campaigns_{date.today().isoformat()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    def _calc_base_bid(self, price, acos, cvr):
        """Calculate strategic base bid."""
        base = price * (cvr/100.0) * (acos/100.0)
        return round(max(0.5, base), 2)

    def _allocate_budget(self, total_budget, tactics):
        """Weighted budget allocation based on priority order."""
        n = len(tactics)
        if n == 0: return {}
        weights = [n - i for i in range(n)] # e.g. 3, 2, 1
        total_weight = sum(weights)
        return {tactics[i]: round(total_budget * (weights[i]/total_weight), 2) for i in range(n)}

    def _parse_keywords(self, uploaded_file):
        """Extract keywords from first column of uploaded file."""
        if uploaded_file is None: return []
        try:
            df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
            if df.empty: return []
            return [str(x).strip() for x in df.iloc[:, 0].dropna() if str(x).strip()]
        except:
            return []

    def _generate_launch_bulk_rows(self, skus, keywords, asins, base_bid, allocation, tactics, bid_strategy, use_auto_pt):
        """Generate bulk file rows for launch structure."""
        entities = []
        ts = date.today().strftime("%Y%m%d")
        advertised_sku = skus[0] # Primary SKU
        
        # Default keywords if none provided
        if not keywords:
            keywords = ["generic keyword 1", "generic keyword 2"]

        for tactic in tactics:
            campaign_id = f"ZEN_{advertised_sku}_{tactic.replace(' ','')}_{ts}"
            adgroup_id = f"{campaign_id}_AG"
            
            # 1. Campaign Row
            entities.append({
                "Product": "Sponsored Products", "Entity": "Campaign", "Operation": "Create",
                "Campaign ID": campaign_id, "Campaign Name": campaign_id,
                "Start Date": ts, "State": "enabled",
                "Daily Budget": f"{allocation.get(tactic, 10):.2f}",
                "Targeting Type": "Auto" if tactic == "Auto" else "Manual",
                "Bidding Strategy": bid_strategy, "Tactic": tactic
            })
            
            # 2. Ad Group Row
            entities.append({
                "Product": "Sponsored Products", "Entity": "Ad Group", "Operation": "Create",
                "Campaign ID": campaign_id, "Ad Group ID": adgroup_id,
                "Campaign Name": campaign_id, "Ad Group Name": adgroup_id,
                "Start Date": ts, "State": "enabled",
                "Ad Group Default Bid": f"{base_bid:.2f}",
                "Tactic": tactic
            })
            
            # 3. Product Ad Row (For EACH SKU)
            for sku in skus:
                entities.append({
                    "Product": "Sponsored Products", "Entity": "Product Ad", "Operation": "Create",
                    "Campaign ID": campaign_id, "Ad Group ID": adgroup_id,
                    "Campaign Name": campaign_id, "Ad Group Name": adgroup_id,
                    "SKU": sku, "State": "enabled",
                    "Tactic": tactic
                })
            
            # 4. Targeting Rows
            if tactic == "Auto":
                # Add Auto-Targeting modifiers if enabled
                if use_auto_pt:
                    for pt_type, mult in AUTO_PT_MULTIPLIERS.items():
                        bid = round(base_bid * mult, 2)
                        entities.append({
                            "Product": "Sponsored Products", "Entity": "Product Targeting", "Operation": "Create",
                            "Campaign ID": campaign_id, "Ad Group ID": adgroup_id,
                            "Campaign Name": campaign_id, "Ad Group Name": adgroup_id,
                            "Bid": f"{bid:.2f}", "Product Targeting Expression": pt_type,
                            "State": "enabled", "Tactic": f"Auto-{pt_type}"
                        })
            
            elif tactic == "Manual: Keywords":
                # Waterfall Strategy: Exact -> Phrase -> Broad
                idx = 0
                kw_len = len(keywords)
                
                # Exact (Top 5) - High Bid
                for _ in range(min(DEFAULT_EXACT_TOP, kw_len - idx)):
                    kw = keywords[idx]
                    entities.append(self._make_kw_row(campaign_id, adgroup_id, kw, "exact", base_bid * 1.5))
                    idx += 1
                
                # Phrase (Next 7) - Medium Bid
                for _ in range(min(DEFAULT_PHRASE_NEXT, kw_len - idx)):
                    kw = keywords[idx]
                    entities.append(self._make_kw_row(campaign_id, adgroup_id, kw, "phrase", base_bid * 1.2))
                    idx += 1
                
                # Broad (Rest) - Low Bid
                while idx < kw_len:
                    kw = keywords[idx]
                    entities.append(self._make_kw_row(campaign_id, adgroup_id, kw, "broad", base_bid * 0.9))
                    idx += 1

            elif tactic == "Manual: ASIN/Product":
                if not asins: continue
                for asin in asins:
                     entities.append({
                        "Product": "Sponsored Products", "Entity": "Product Targeting", "Operation": "Create",
                        "Campaign ID": campaign_id, "Ad Group ID": adgroup_id,
                        "Campaign Name": campaign_id, "Ad Group Name": adgroup_id,
                        "Bid": f"{base_bid * 1.1:.2f}", 
                        "Product Targeting Expression": f'ASIN="{asin}"',
                        "State": "enabled", "Tactic": "Manual-ASIN"
                    })

        # Convert to DataFrame
        df = pd.DataFrame(entities)
        # Ensure all standard columns exist
        for col in COLUMN_ORDER:
            if col not in df.columns:
                df[col] = ""
        
        return df[COLUMN_ORDER]

    def _make_kw_row(self, cid, agid, text, match, bid):
        return {
            "Product": "Sponsored Products", "Entity": "Keyword", "Operation": "Create",
            "Campaign ID": cid, "Ad Group ID": agid,
            "Campaign Name": cid, "Ad Group Name": agid,
            "Keyword Text": text, "Match Type": match, "Bid": f"{bid:.2f}",
            "State": "enabled", "Tactic": "Manual-Keywords"
        }

    def _to_excel_with_metadata(self, df, metadata):
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Bulk Template")
            pd.DataFrame(list(metadata.items()), columns=["Key","Value"]).to_excel(writer, index=False, sheet_name="Metadata")
        return output.getvalue()

    # =========================================================================
    # TAB 2: HARVEST WINNERS (Existing Harvest Logic)
    # =========================================================================
    def _render_harvest_tab(self):
        """Render the harvest winners UI."""
        # Access harvest candidates from Session State
        if 'harvest_payload' not in st.session_state or st.session_state['harvest_payload'] is None:
             st.info("👈 No harvest candidates found. Go to 'Optimization Engine' -> 'Harvest' tab to identify winners first.")
             return
             
        df_harvest = st.session_state['harvest_payload']
        st.success(f"🌾 Loaded {len(df_harvest)} harvest candidates from Optimizer")

        with st.expander("⚙️ Harvest Configuration", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                portfolio_id = st.text_input("Portfolio ID (Optional)", key="harvest_pid")
                launch_date = st.date_input("Launch Date", datetime.today(), key="harvest_date")
            with col2:
                daily_budget = st.number_input("Budget per Campaign (AED)", value=20.0, min_value=1.0, key="harvest_budget")
            
            # SKU Mapping Logic (Preserved)
            # Ensure Advertised SKU column exists
            if "Advertised SKU" not in df_harvest.columns:
                if "SKU_advertised" in df_harvest.columns:
                    df_harvest["Advertised SKU"] = df_harvest["SKU_advertised"].apply(
                        lambda x: str(x).split(',')[0].strip() if pd.notna(x) and str(x).strip() != "" else "SKU_NEEDED"
                    )
                else:
                    df_harvest["Advertised SKU"] = "SKU_NEEDED"

            if "Advertised SKU" not in df_harvest.columns or df_harvest["Advertised SKU"].eq("SKU_NEEDED").all():
                # TRY TO PRE-FILL FROM SESSION STATE FIRST
                data_hub = st.session_state.get('data', {})
                purchased_report = data_hub.get('purchased_product')
                
                if purchased_report is not None:
                     df_harvest, msg = self.map_skus_from_df(df_harvest, purchased_report)
                     if "Matches found" in msg:
                        st.success(f"✅ Auto-mapped SKUs using Data Hub: {msg}")
                        st.session_state['harvest_payload'] = df_harvest
                     else:
                        st.warning("⚠️ SKUs missing. Detailed SKU mapping required.")
                        sku_file = st.file_uploader("Upload SKU Map (Purchased Product Report)", type=['csv', 'xlsx'], key="harvest_sku_map")
                        if sku_file:
                            df_harvest, msg = self.map_skus_from_file(df_harvest, sku_file)
                            st.success(msg)
                            st.session_state['harvest_payload'] = df_harvest
                else:
                    st.warning("⚠️ SKUs missing. detailed SKU mapping required.")
                    sku_file = st.file_uploader("Upload SKU Map (Purchased Product Report)", type=['csv', 'xlsx'], key="harvest_sku_map")
                    if sku_file:
                        df_harvest, msg = self.map_skus_from_file(df_harvest, sku_file)
                        st.success(msg)
                        st.session_state['harvest_payload'] = df_harvest # Save back
            
        st.subheader("📋 Verify Candidates")
        st.dataframe(df_harvest, use_container_width=True)
        
        if st.button("Generate Harvest Campaigns", type="primary", key="btn_gen_harvest"):
            bulk_df = self.generate_harvest_bulk_file(df_harvest, portfolio_id, daily_budget, launch_date)
            
            st.success(f"✅ Generated {len(bulk_df)} bulk file rows")
            
            # Preview
            with st.expander("👁️ Preview Rows", expanded=False):
                st.dataframe(bulk_df, use_container_width=True)
            
            st.download_button(
                "📥 Download Harvest File (.xlsx)",
                data=to_excel_download(bulk_df, "harvest_campaigns"),
                file_name=f"harvest_campaigns_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    def map_skus_from_df(self, harvest_df: pd.DataFrame, camp_df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
        """Resolves SKUs from a pre-loaded Advertised Product Report DataFrame."""
        try:
            col_map = SmartMapper.map_columns(camp_df)
            
            c_col = col_map.get("Campaign Name")
            s_col = col_map.get("SKU")
            ag_col = col_map.get("Ad Group Name")  # Add ad group for better matching
            
            if not (c_col and s_col):
                return harvest_df, "❌ Missing Campaign or SKU columns in report"
            
            # Create normalized lookup with Campaign + Ad Group (more precise)
            camp_df = camp_df.copy()
            camp_df['_camp_norm'] = camp_df[c_col].astype(str).str.strip().str.lower()
            
            # If Ad Group exists, use it for better precision
            if ag_col and ag_col in camp_df.columns:
                camp_df['_ag_norm'] = camp_df[ag_col].astype(str).str.strip().str.lower()
                
                # Create composite key: campaign|adgroup -> SKU
                camp_df['_composite_key'] = camp_df['_camp_norm'] + '|' + camp_df['_ag_norm']
                
                # Aggregate SKUs (in case multiple SKUs per campaign/adgroup)
                sku_lookup = camp_df.groupby('_composite_key')[s_col].apply(
                    lambda x: ', '.join(x.dropna().astype(str).unique())
                ).to_dict()
                
                # Also create campaign-only fallback
                sku_lookup_camp = camp_df.groupby('_camp_norm')[s_col].apply(
                    lambda x: ', '.join(x.dropna().astype(str).unique())
                ).to_dict()
            else:
                # Campaign-only lookup
                sku_lookup_camp = camp_df.groupby('_camp_norm')[s_col].apply(
                    lambda x: ', '.join(x.dropna().astype(str).unique())
                ).to_dict()
                sku_lookup = {}
            
            def resolve(row):
                # If already has SKU, keep it
                existing = str(row.get("Advertised SKU", "")).strip()
                if existing and existing != "SKU_NEEDED":
                    return existing
                
                # Normalize search keys
                c_name = str(row.get("Campaign Name", "")).strip().lower()
                ag_name = str(row.get("Ad Group Name", "")).strip().lower()
                
                # Try composite key first (most precise)
                if sku_lookup:
                    composite_key = f"{c_name}|{ag_name}"
                    found = sku_lookup.get(composite_key)
                    if found:
                        return found
                
                # Fallback to campaign-only
                found = sku_lookup_camp.get(c_name)
                if found:
                    return found
                
                return "SKU_NEEDED"
            
            harvest_df["Advertised SKU"] = harvest_df.apply(resolve, axis=1)
            
            # Stats
            found = len(harvest_df[harvest_df["Advertised SKU"] != "SKU_NEEDED"])
            total = len(harvest_df)
            missing = total - found
            
            msg = f"✅ Matched {found}/{total} SKUs"
            if missing > 0:
                msg += f" | ⚠️ {missing} still need manual mapping"
            
            return harvest_df, msg
            
        except Exception as e:
            return harvest_df, f"❌ Error mapping SKUs: {str(e)}"

    def map_skus_from_file(self, harvest_df: pd.DataFrame, campaigns_file) -> tuple[pd.DataFrame, str]:
        """Resolves SKUs from Purchased Product Report (Preserved Logic)."""
        try:
            camp_df = load_uploaded_file(campaigns_file)
            if camp_df is None: return harvest_df, "❌ Failed to load file"

            col_map = SmartMapper.map_columns(camp_df)
            c_col = col_map.get("Campaign Name")
            s_col = col_map.get("SKU")
            
            if not (c_col and s_col):
                return harvest_df, "❌ Missing Campaign or SKU columns in file"
                
            camp_df['_key'] = camp_df[c_col].astype(str).str.strip()
            sku_map = pd.Series(camp_df[s_col].values, index=camp_df['_key']).to_dict()
            
            def resolve(row):
                c_name = str(row.get("Campaign Name", "")).strip()
                return sku_map.get(c_name, "SKU_NEEDED")
                
            harvest_df["Advertised SKU"] = harvest_df.apply(resolve, axis=1)
            found = len(harvest_df[harvest_df["Advertised SKU"] != "SKU_NEEDED"])
            
            return harvest_df, f"✅ Mapped SKUs for {found} terms"
        except Exception as e:
            return harvest_df, f"❌ Error: {str(e)}"

    def generate_harvest_bulk_file(self, df_harvest, portfolio_id, total_daily_budget, launch_date):
        """Generate bulk file for Harvest campaigns (Weekly Consolidated)."""
        # Safety check for SKU column
        if "Advertised SKU" not in df_harvest.columns:
            df_harvest = df_harvest.copy()
            df_harvest["Advertised SKU"] = "SKU_NEEDED"

        rows = []
        start_date_str = launch_date.strftime("%Y%m%d")
        iso_week = launch_date.isocalendar()[1]
        iso_year = launch_date.isocalendar()[0]
        campaign_name = f"HarvestExact_WK{iso_week:02d}_{iso_year}" # Logic: Weekly Campaign
        
        # Momentum Bidding Logic (Preserved)
        if "CPC_Source" not in df_harvest.columns:
            if "Spend" in df_harvest.columns and "Clicks" in df_harvest.columns:
                df_harvest["CPC_Source"] = df_harvest.apply(lambda r: r["Spend"]/r["Clicks"] if r["Clicks"] > 0 else 0, axis=1)
            else:
                df_harvest["CPC_Source"] = 0.0
                
        def calc_momentum_bid(row):
            src_cpc = pd.to_numeric(row.get("CPC_Source"), errors='coerce')
            if pd.isna(src_cpc) or src_cpc <= 0:
                return float(row.get("New Bid", 0.50))
            return max(src_cpc * 1.1, 0.10) # 10% bump
            
        df_harvest["_Momentum_Bid"] = df_harvest.apply(calc_momentum_bid, axis=1)
        df_harvest["_is_asin"] = df_harvest["Customer Search Term"].apply(lambda x: is_asin(str(x)))
        
        # 1. Campaign Row (Single Weekly Campaign)
        rows.append({
            "Product": "Sponsored Products", "Entity": "Campaign", "Operation": "create",
            "Campaign ID": campaign_name, "Campaign Name": campaign_name,
            "Start Date": start_date_str, "State": "enabled", "Daily Budget": f"{total_daily_budget:.2f}",
            "Bidding Strategy": "Dynamic bids - down only", "Portfolio ID": portfolio_id or ""
        })
        
        # 2. Group by SKU
        grouped = df_harvest.groupby("Advertised SKU")
        for sku, sku_group in grouped:
            kw_items = sku_group[~sku_group["_is_asin"]]
            pt_items = sku_group[sku_group["_is_asin"]]
            
            # Helper to add AG structure
            def add_ad_group_structure(items, suffix="KW"):
                if items.empty: return
                ag_name = f"AG_{suffix}_Exact_{sku}_WK{iso_week:02d}_{iso_year}"
                avg_bid = items["_Momentum_Bid"].mean() if "_Momentum_Bid" in items.columns else 1.0
                
                # AD GROUP
                rows.append({
                    "Product": "Sponsored Products", "Entity": "Ad Group", "Operation": "create",
                    "Campaign ID": campaign_name, "Ad Group ID": ag_name,
                    "Campaign Name": campaign_name, "Ad Group Name": ag_name,
                    "Start Date": start_date_str, "State": "enabled",
                    "Ad Group Default Bid": f"{avg_bid:.2f}"
                })
                # PRODUCT AD
                rows.append({
                    "Product": "Sponsored Products", "Entity": "Product Ad", "Operation": "create",
                    "Campaign ID": campaign_name, "Ad Group ID": ag_name,
                    "Campaign Name": campaign_name, "Ad Group Name": ag_name,
                    "SKU": sku, "State": "enabled"
                })
                # TARGETS
                for _, row in items.iterrows():
                    bid = float(row["_Momentum_Bid"])
                    target_row = {
                        "Product": "Sponsored Products", "Entity": "Keyword" if suffix=="KW" else "Product Targeting",
                        "Operation": "create", "Campaign ID": campaign_name, "Ad Group ID": ag_name,
                        "Campaign Name": campaign_name, "Ad Group Name": ag_name,
                        "Bid": f"{bid:.2f}", "State": "enabled"
                    }
                    if suffix == "KW":
                        target_row["Keyword Text"] = row["Customer Search Term"]
                        target_row["Match Type"] = "exact"
                    else:
                        target_row["Product Targeting Expression"] = f'ASIN="{row["Customer Search Term"]}"'
                    rows.append(target_row)

            add_ad_group_structure(kw_items, "KW")
            add_ad_group_structure(pt_items, "PT")
            
        # Convert to DataFrame
        bulk_df = pd.DataFrame(rows)
        
        # Ensure all required columns exist (fill missing with empty strings)
        for col in COLUMN_ORDER:
            if col not in bulk_df.columns:
                bulk_df[col] = ""
        
        # Reorder to match Amazon's expected column order
        bulk_df = bulk_df[COLUMN_ORDER]
        
        return bulk_df


    def validate_data(self, data):
        return True, "" # Not used directly
    
    def analyze(self, data):
        pass
