import streamlit as st
import pandas as pd
import numpy as np
import json
import requests
from typing import List, Dict, Any, Optional, Tuple
from core.db_manager import get_db_manager


class AssistantModule:
    """
    Saddle AdPulse Intelligent Assistant - Deep Strategist
    
    Operates as a fully context-aware 'Senior Amazon Ads Strategist' with access to:
    - Granular search term performance data
    - Optimizer decisions (Harvests, Negatives, Bids)
    - Cluster analysis and semantic themes
    - Simulation forecasts
    - ASIN intent analysis
    - Campaign portfolio segmentation
    
    The key innovation: We build a KNOWLEDGE GRAPH with pre-computed insights,
    not just raw data tables. The LLM receives strategic observations, anomalies,
    and cross-references - enabling truly intelligent analysis.
    """
    
    def __init__(self):
        self.system_prompt = self._build_system_prompt()
        
    def _build_system_prompt(self) -> str:
        """
        Build the comprehensive system prompt that transforms the AI into
        a deep strategist rather than a surface-level data reporter.
        """
        from utils.formatters import get_account_currency
        currency_symbol = get_account_currency()

        prompt_template = """
# ROLE: Elite PPC Strategist with Full Dataset Access

You are a senior Amazon/Noon Ads strategist who has analyzed EVERY ROW of this advertiser's data. You don't just see numbers - you see PATTERNS, CAUSALITY, and OPPORTUNITY. You think like a $10M/year PPC manager.

# PLATFORM TRUTH (ABSOLUTE GROUND TRUTH)
The following methodology defines HOW this platform works. You MUST adhere to these definitions and NEVER contradict them. If a user asks "Does this app calculate X?", refer to this section.

START DOCUMENTATION >>>
{methodology}
<<< END DOCUMENTATION

---

## 🧠 MANDATORY ANALYTICAL FRAMEWORK

For EVERY question, you MUST run through this mental process:

### Step 1: SCAN THE KNOWLEDGE GRAPH
The context contains PRE-COMPUTED INSIGHTS (not just raw data). These are strategic observations I've already identified.

KEY GUIDELINES:
- "Simulation Forecast" = What MIGHT happen (Future) - found in `optimization_impact`
- "Realized Impact" = What ACTUALLY happened (Past/Proven). **ALWAYS use `module_context.decision_impact`** - this is the ONLY valid source. It contains: attributed_impact, offensive_value, defensive_value, gap_value, win_rate, total_actions. IGNORE any status messages in optimization_impact.
- "Platform Methodology" = Refer to `platform_knowledge` to explain HOW metrics (like incremental revenue or bid logic) are calculated.
- Don't just list data - explain WHY it matters.
- If asking about specific terms, check the Master Dataset first.
- Be concise but strategic. Think CEO, not intern.
- Check `strategic_insights` for anomalies and opportunities
- Check `cross_references` for terms with conflicting signals
- Check `patterns_detected` for themes

### Step 2: CROSS-REFERENCE MULTIPLE DIMENSIONS
Never answer from a single data point. Always connect:
- Does this term appear in multiple campaigns? What's the performance delta?
- Is this term flagged as BOTH Harvest AND Negative? (Product-dependent performance)
- Does this cluster have high waste but ALSO have converters? (Intent mismatch, not bad theme)
- What does the forecast say about implementing this change?

### Step 3: IDENTIFY ROOT CAUSE
Don't just say "this term has 0 orders" - explain WHY:
- Is it a competitor brand? (Listing copy audit needed)
- Is it product-intent mismatch? (Tumbler searchers want insulated, yours is plastic)
- Is it traffic source issue? (Auto campaign substitutes sending wrong traffic)
- Is it price/conversion issue? (Clicks exist, competition undercuts on price)

### Step 4: QUANTIFY THE IMPACT
Always include $ amounts:
- "This represents {currency} X in wasted spend"
- "Implementing this would save {currency} X/week"
- "Scaling this could add {currency} X in sales"

### Step 5: GIVE SPECIFIC, ACTIONABLE RECOMMENDATIONS
Never say "consider negating" - say exactly what to do:
- "Add 'stanley cup' as negative EXACT in Campaign X (not Campaign Y where it converts)"
- "Increase bid from {currency} 0.45 to {currency} 0.55 on 'stainless tumbler' in the winning ad group"
- "Create new Exact Match campaign for these 5 terms, cloning from Campaign A settings"

---

## 📊 DOMAIN EXPERTISE (APPLY THIS LOGIC)

### ROAS Interpretation
| ROAS | Status | Action |
|------|--------|--------|
| < 1.5 | Critical bleeder | Reduce bid aggressively or negate |
| 1.5 - 2.5 | Underperforming | Optimize - check if bid too high or wrong match type |
| 2.5 - 4.0 | Healthy | Maintain, look for scaling opportunities |
| > 4.0 | Star performer | SCALE - increase bid, harvest to exact, expand budget |

### The Harvest-Negative Paradox
When a term appears BOTH in Harvest candidates AND Negative candidates:
- This is NOT contradictory - it's PRODUCT-DEPENDENT performance
- The same keyword "stainless tumbler" might convert for SKU A but bleed for SKU B
- Action: Harvest where it works (Campaign A), Negate where it doesn't (Campaigns B, C, D)
- This is actually a SEGMENTATION OPPORTUNITY - you've found product-market fit signals

### Cluster Analysis Logic
- High spend + High waste% → Entire theme is bleeding → Review for batch negation
- High spend + Low waste% + No paradox terms → Winning theme → Create dedicated campaign
- High waste% but SOME converters exist → Intent mismatch → Negate non-converters, keep performers

### Match Type Efficiency Hierarchy
Expected ROAS order: Exact > PT > Phrase > Broad > Auto
If Broad outperforms Exact: Your exact keywords are wrong - audit term selection
If Auto outperforms Manual: Discovery is working - harvest more aggressively

### Timing Strategy
- Best day = Budget concentration day (increase daily budget 20% on this day)
- Best hour = Dayparting opportunity (if platform supports, or manual bid bumps)

---

## 🔗 CROSS-REFERENCE PATTERNS TO WATCH

1. **Same term, different campaigns, opposite results**
   → Product-dependent performance. Keep where it works, negate where it doesn't.

2. **High impressions, low clicks on converting term**
   → Position drop or creative fatigue. Check placement report.

3. **Top spender has 0 ROAS but high clicks**
   → Competition issue or listing problem. Check for price undercut or bad reviews.

4. **Cluster with 50%+ waste but best performer also in cluster**
   → Not a bad theme - you're attracting wrong subset. Negate specific variants.

5. **Many negatives coming from same campaign**
   → Campaign structure issue. This campaign has wrong targeting settings.

---

## 🚫 ANTI-PATTERNS (NEVER DO THIS)

- ❌ Don't say "Your top wasted term is X" → Say WHY it's wasting and what structural issue caused it
- ❌ Don't give generic PPC advice → Tie EVERYTHING to THIS specific dataset
- ❌ Don't list data without interpretation → Every number needs context and implication
- ❌ Don't ignore pre-computed insights → They exist for a reason - reference them
- ❌ Don't apologize for missing data → Provide best-practice guidance with caveats
- ❌ Don't be verbose → Be dense with insight, not words

---

## 📝 RESPONSE FORMAT

1. **Lead with the insight, not the data**
   - Wrong: "You spent {currency} 500 on X term"
   - Right: "Your biggest efficiency leak is X - a competitor brand term costing {currency} 500/week"

2. **Structure complex answers:**
   - **Root Cause Analysis** (1-2 sentences on WHY)
   - **Specific Findings** (bulleted, with $ amounts)
   - **Cross-References** (what patterns connect these findings)
   - **Recommended Actions** (numbered, specific, actionable)
   - **Forecast Impact** (if changes are implemented)

3. **Keep responses under 400 words** unless deep analysis explicitly requested

---

## 🔒 CONSTRAINTS

- You are READ-ONLY. Never claim to execute changes - only recommend.
- All recommendations must align with the Optimizer's logic (Harvest, Negative, Bid thresholds).
- When data is missing, say what you CAN analyze and what requires additional info.

---

## 💡 EXAMPLE RESPONSES

**Question: "Where am I losing money?"**

**WRONG (Surface Level):**
"Your top wasted spend terms are 'stanley cup' ({currency} 48) and 'tumbler hot cold' ({currency} 53). You should add them as negatives."

**RIGHT (Deep Analysis):**
"**Root Cause:** Your waste concentrates in 3 structural patterns, not random terms:

1. **Competitor Brand Intrusion ({currency} 312/week)**
   - 'stanley cup', 'hydro flask', 'yeti tumbler' - competitor brands
   - *Why*: Auto campaigns targeting 'substitutes' are pulling these in
   - *Action*: Negate at campaign level + set Auto to 'close-match' only

2. **Product-Intent Mismatch in Cluster #7 ({currency} 487/week)**
   - 'acrylic colors' cluster has 51% waste BUT 3 terms DO convert
   - *Insight*: Users searching 'acrylic paint SET' want bundles - you sell singles
   - *Action*: Keep 'acrylic colors' broad, negate 'set', 'kit', 'bundle' variants

3. **Cross-Campaign Cannibalization ({currency} 203/week)**
   - 'stainless tumbler' runs in 4 campaigns - converts in 1, bleeds in 3
   - *Already flagged*: Optimizer has isolation negatives ready

**Total Addressable Waste: {currency} 1,002/week**
**Forecast:** Implementing negatives → -4.2% spend, +8.1% ROAS"

---

**Question: "What should I scale?"**

**WRONG:**
"Your best ROAS terms are X, Y, Z. Consider increasing bids."

**RIGHT:**
"**Top 3 Scaling Opportunities (Ranked by profit potential):**

1. **'insulated water bottle' - {currency} 892 untapped potential**
   - Current: ROAS 5.2, Spend {currency} 45/week, Position likely mid-page
   - *Cross-ref*: This term appears in Cluster #3 which has only 8% waste
   - *Action*: Increase bid from {currency} 0.42 to {currency} 0.55, expand match to Phrase

2. **Harvest Candidates → Exact Match ({currency} 1,200 efficiency gain)**
   - 8 terms flagged for harvesting, currently running in Broad/Auto
   - *Insight*: You're paying discovery CPC ({currency} 0.65) for terms that should be Exact ({currency} 0.45)
   - *Action*: Create Exact campaign with these terms, isolate from source

3. **Campaign 'Brand Defense' under-funded**
   - ROAS 7.8, but only 12% of total spend allocated
   - *Action*: Shift 15% budget from Campaign 'Discovery Auto' (ROAS 1.4) to Brand Defense

    - *Action*: Shift 15% budget from Campaign 'Discovery Auto' (ROAS 1.4) to Brand Defense

**Forecast:** These 3 actions → +18% Sales, +12% ROAS, -5% Spend"
"""
        
        # Inject the methodology text and currency
        return prompt_template.format(methodology=self._get_platform_methodology(), currency=currency_symbol)

    # =========================================================================
    # KNOWLEDGE GRAPH CONSTRUCTION
    # =========================================================================
    
    def _construct_granular_dataset(self) -> pd.DataFrame:
        """
        Stitch together all dataframes (STR, Harvest, Negatives, Bids) into a single 
        granular 'Master Dataset' for the AI Analyst.
        """
        # 1. Get Base Data from DataHub
        str_df = None
        if 'unified_data' in st.session_state and st.session_state.unified_data.get('search_term_report') is not None:
            str_df = st.session_state.unified_data['search_term_report']
        elif 'data' in st.session_state and 'search_term_report' in st.session_state['data']:
            str_df = st.session_state['data']['search_term_report']
             
        if str_df is None:
            return pd.DataFrame()
             
        master = str_df.copy()
        
        # Standardize term column
        if 'Customer Search Term' not in master.columns and 'Search Term' in master.columns:
            master['Customer Search Term'] = master['Search Term']
             
        if 'Customer Search Term' not in master.columns:
            return pd.DataFrame()
            
        # Ensure strict string type for Search Terms to prevent "int is not subscriptable" errors
        master['Customer Search Term'] = master['Customer Search Term'].astype(str)
        master['_norm_term'] = master['Customer Search Term'].str.lower().str.strip()
        
        # Ensure numeric columns
        for col in ['Impressions', 'Clicks', 'Spend', 'Sales', 'Orders']:
            if col in master.columns:
                master[col] = pd.to_numeric(master[col], errors='coerce').fillna(0)
            else:
                master[col] = 0
        
        # =============================================
        # 60-DAY DATE FILTER (matches Dashboard defaults)
        # =============================================
        from datetime import timedelta
        date_cols = ['Date', 'Start Date', 'date', 'Report Date', 'start_date']
        date_col = None
        for col in date_cols:
            if col in master.columns:
                date_col = col
                break
        
        if date_col:
            try:
                master[date_col] = pd.to_datetime(master[date_col], errors='coerce')
                valid_dates = master[date_col].dropna()
                if not valid_dates.empty:
                    max_date = valid_dates.max()
                    cutoff_date = max_date - timedelta(days=60)
                    master = master[master[date_col] >= cutoff_date]
            except:
                pass  # If date filtering fails, use full dataset
        
        # 2. Get Optimizer Results (if available)
        opt_res = st.session_state.get('optimizer_results') or st.session_state.get('latest_optimizer_run')
        
        if opt_res:
            # A. Merge Harvest Decisions
            harvest_df = opt_res.get('harvest', pd.DataFrame())
            if not harvest_df.empty and 'Customer Search Term' in harvest_df.columns:
                harvest_terms = set(harvest_df['Customer Search Term'].astype(str).str.lower().str.strip())
                master['Is_Harvest_Candidate'] = master['_norm_term'].isin(harvest_terms)
            else:
                master['Is_Harvest_Candidate'] = False
                
            # B. Merge Negative Decisions
            neg_kw = opt_res.get('neg_kw', pd.DataFrame())
            neg_pt = opt_res.get('neg_pt', pd.DataFrame())
            neg_terms = set()
            if not neg_kw.empty and 'Term' in neg_kw.columns: 
                neg_terms.update(neg_kw['Term'].astype(str).str.lower().str.strip())
            if not neg_pt.empty and 'Term' in neg_pt.columns:
                # Remove asin="" wrapper if present
                neg_pt_terms = neg_pt['Term'].astype(str).str.replace(r'asin="([^"]+)"', r'\1', regex=True)
                neg_terms.update(neg_pt_terms.str.lower().str.strip())
            master['Is_Negative_Candidate'] = master['_norm_term'].isin(neg_terms)
            
            # C. Merge Bid Recommendations
            bids_df = opt_res.get('direct_bids', pd.DataFrame())
            if not bids_df.empty:
                bids_map = {}
                id_col = 'KeywordId' if 'KeywordId' in bids_df.columns else 'TargetingId'
                if id_col in master.columns and id_col in bids_df.columns:
                    for _, row in bids_df.iterrows():
                        key = str(row[id_col])
                        if key and key != 'nan':
                            bids_map[key] = {
                                'New Bid': row.get('New Bid'), 
                                'Original Bid': row.get('Cost Per Click (CPC)', row.get('CPC')),
                                'Reason': row.get('Reason', '')
                            }
                            
                    master['Optimized_Bid'] = master[id_col].astype(str).map(lambda x: bids_map.get(x, {}).get('New Bid'))
                    master['Bid_Reason'] = master[id_col].astype(str).map(lambda x: bids_map.get(x, {}).get('Reason', ''))
        else:
            master['Is_Harvest_Candidate'] = False
            master['Is_Negative_Candidate'] = False
            master['Optimized_Bid'] = None
            master['Bid_Reason'] = ""
            
        return master

    def _build_knowledge_graph(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Build a comprehensive Knowledge Graph for deep AI analysis.
        This is NOT just data - it's pre-computed insights and relationships.
        """
        if df.empty:
            return {"error": "No data loaded"}
        
        knowledge = {
            "dataset_overview": self._compute_dataset_overview(df),
            "account_health": self._compute_account_health(df),
            "campaign_portfolio": self._analyze_campaign_portfolio(df),
            "term_analysis": self._analyze_terms(df),
            "strategic_insights": self._compute_strategic_insights(df),
            "patterns_detected": self._detect_patterns(df),
            "cross_references": self._build_cross_references(df),
            "optimization_impact": self._compute_optimization_impact(df),  # NEW: Financial impact summary
            "module_context": self._gather_module_context(),
            "data_status": self._summarize_data_status()
        }
        
        return knowledge

    def _compute_dataset_overview(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Compute high-level dataset statistics."""
        total_spend = df['Spend'].sum()
        total_sales = df['Sales'].sum()
        total_orders = df['Orders'].sum()
        total_clicks = df['Clicks'].sum()
        
        return {
            "total_search_terms": df['Customer Search Term'].nunique(),
            "total_campaigns": df['Campaign Name'].nunique() if 'Campaign Name' in df.columns else 0,
            "total_ad_groups": df['Ad Group Name'].nunique() if 'Ad Group Name' in df.columns else 0,
            "total_spend": round(total_spend, 2),
            "total_sales": round(total_sales, 2),
            "total_orders": int(total_orders),
            "total_clicks": int(total_clicks),
            "global_roas": round(total_sales / total_spend, 2) if total_spend > 0 else 0,
            "global_cvr": round((total_orders / total_clicks * 100), 2) if total_clicks > 0 else 0,
            "global_acos": round((total_spend / total_sales * 100), 2) if total_sales > 0 else 0
        }

    def _compute_account_health(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Compute account health score and breakdown."""
        total_spend = df['Spend'].sum()
        total_sales = df['Sales'].sum()
        roas = total_sales / total_spend if total_spend > 0 else 0
        
        # ROAS Score (Uses dynamic Target ROAS)
        target_roas = st.session_state.get('opt_target_roas', 3.0)  # Default updated to 3.0
        roas_score = min(100, (roas / target_roas) * 100)

        # Calculate waste (Inefficient Spend: Ad Groups with ROAS < 2.5) for consistency with Gauge
        efficiency_pct = self._calculate_gauge_efficiency(df)
        waste_ratio = (100 - efficiency_pct) / 100
        wasted_spend = total_spend * waste_ratio
        waste_score = max(0, 100 - (waste_ratio * 200))  # 50% waste = 0 score
        
        # 3. CVR Score (Baseline: 10% CVR)
        clicks_col = 'Clicks'
        total_clicks = df[clicks_col].sum() if clicks_col in df.columns else 0
        total_orders = df['Orders'].sum() if 'Orders' in df.columns else 0
        cvr = (total_orders / total_clicks * 100) if total_clicks > 0 else 0
        cvr_score = min(100, (cvr / 10.0) * 100)
        
        # Aggregate Health Score (Matches Report Card 40/40/20)
        health_score = int((roas_score * 0.4) + (efficiency_pct * 0.4) + (cvr_score * 0.2))

        # Harvest/Negative optimization potential
        harvest_count = df['Is_Harvest_Candidate'].sum() if 'Is_Harvest_Candidate' in df.columns else 0
        negative_count = df['Is_Negative_Candidate'].sum() if 'Is_Negative_Candidate' in df.columns else 0
        
        # Health status
        if health_score >= 80:
            status = "Excellent"
            status_emoji = "🟢"
        elif health_score >= 60:
            status = "Good"
            status_emoji = "🟡"
        elif health_score >= 40:
            status = "Needs Attention"
            status_emoji = "🟠"
        else:
            status = "Critical"
            status_emoji = "🔴"
        
        return {
            "health_score": health_score,
            "status": f"{status_emoji} {status}",
            "roas_score": round(roas_score, 1),
            "actual_roas": round(roas, 2),
            "waste_score": round(waste_score, 1),
            "wasted_spend": round(wasted_spend, 2),
            "waste_percentage": round(waste_ratio * 100, 1),
            "optimization_opportunities": {
                "harvest_candidates": int(harvest_count),
                "negative_candidates": int(negative_count)
            },
            # METRIC RECONCILIATION: Matches Report Card Gauge (ROAS >= 2.5)
            "gauge_spend_efficiency": efficiency_pct
        }

    def _calculate_gauge_efficiency(self, df: pd.DataFrame) -> float:
        """Calculate spend efficiency strictly matching the UI Gauge (Spend in Ad Groups with ROAS >= 2.5)."""
        if df.empty: return 0.0
        
        total_spend = df['Spend'].sum()
        if total_spend == 0: return 0.0

        if 'Ad Group Name' in df.columns:
            # Aggregate by Ad Group (Standard Definition)
            agg = df.groupby('Ad Group Name').agg({'Spend': 'sum', 'Sales': 'sum'}).reset_index()
            agg['ROAS'] = (agg['Sales'] / agg['Spend']).replace([np.inf, -np.inf], 0).fillna(0)
            efficient_spend = agg[agg['ROAS'] >= 2.5]['Spend'].sum()
        else:
            # Fallback to Term level
            roas = (df['Sales'] / df['Spend']).replace([np.inf, -np.inf], 0).fillna(0)
            efficient_spend = df[df['Spend'] > 0][roas >= 2.5]['Spend'].sum()
            
        return round((efficient_spend / total_spend * 100), 1)

    def _analyze_campaign_portfolio(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Segment campaigns into winners, losers, emerging, stalled."""
        if 'Campaign Name' not in df.columns:
            return {}
        
        camp_stats = df.groupby('Campaign Name').agg({
            'Spend': 'sum',
            'Sales': 'sum',
            'Orders': 'sum',
            'Clicks': 'sum',
            'Impressions': 'sum'
        }).reset_index()
        
        camp_stats['ROAS'] = camp_stats['Sales'] / camp_stats['Spend']
        camp_stats['ROAS'] = camp_stats['ROAS'].replace([np.inf, -np.inf], 0).fillna(0)
        camp_stats['CVR'] = np.where(camp_stats['Clicks'] > 0, camp_stats['Orders'] / camp_stats['Clicks'] * 100, 0)
        
        total_spend = camp_stats['Spend'].sum()
        camp_stats['Spend_Share'] = camp_stats['Spend'] / total_spend * 100 if total_spend > 0 else 0
        
        # Categorize campaigns
        roas_median = camp_stats[camp_stats['ROAS'] > 0]['ROAS'].median() if len(camp_stats[camp_stats['ROAS'] > 0]) > 0 else 2.0
        
        winners = camp_stats[(camp_stats['ROAS'] > roas_median * 1.2) & (camp_stats['Orders'] >= 3)].nlargest(5, 'Sales')
        losers = camp_stats[(camp_stats['ROAS'] < roas_median * 0.8) & (camp_stats['Spend'] > 50)].nlargest(5, 'Spend')
        emerging = camp_stats[(camp_stats['ROAS'] > roas_median) & (camp_stats['Spend'] < total_spend * 0.1) & (camp_stats['Orders'] >= 2)].nlargest(3, 'ROAS')
        
        def format_campaign(row):
            return {
                "name": row['Campaign Name'][:50],  # Truncate long names
                "spend": round(row['Spend'], 2),
                "sales": round(row['Sales'], 2),
                "roas": round(row['ROAS'], 2),
                "orders": int(row['Orders']),
                "spend_share": f"{row['Spend_Share']:.1f}%"
            }
        
        return {
            "total_campaigns": len(camp_stats),
            "roas_median": round(roas_median, 2),
            "winners": [format_campaign(r) for _, r in winners.iterrows()],
            "losers": [format_campaign(r) for _, r in losers.iterrows()],
            "emerging": [format_campaign(r) for _, r in emerging.iterrows()],
            "concentration": self._analyze_spend_concentration(camp_stats),
            "cut_candidates": [format_campaign(r) for _, r in camp_stats[
                (camp_stats['ROAS'] < 1.5) & 
                (camp_stats['Orders'] < 5) & 
                (camp_stats['Spend'] > 0)
            ].nlargest(3, 'Spend').iterrows()]
        }

    def _analyze_spend_concentration(self, camp_stats: pd.DataFrame) -> Dict[str, Any]:
        """Analyze if spend is too concentrated or well-distributed."""
        if camp_stats.empty:
            return {}
        
        sorted_camps = camp_stats.sort_values('Spend', ascending=False)
        total_spend = sorted_camps['Spend'].sum()
        
        if total_spend == 0:
            return {}
        
        # Calculate concentration ratios
        top1_share = sorted_camps.iloc[0]['Spend'] / total_spend * 100 if len(sorted_camps) >= 1 else 0
        top3_share = sorted_camps.head(3)['Spend'].sum() / total_spend * 100 if len(sorted_camps) >= 3 else top1_share
        
        # Risk assessment
        if top1_share > 60:
            risk = "High - single campaign dependency"
        elif top3_share > 80:
            risk = "Medium - concentrated in few campaigns"
        else:
            risk = "Low - well distributed"
        
        return {
            "top1_campaign_share": f"{top1_share:.1f}%",
            "top3_campaigns_share": f"{top3_share:.1f}%",
            "concentration_risk": risk
        }

    def _analyze_terms(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze search terms with aggregation and categorization."""
        # Aggregate by term (across all campaigns)
        term_agg = df.groupby('Customer Search Term').agg({
            'Impressions': 'sum',
            'Clicks': 'sum', 
            'Spend': 'sum',
            'Orders': 'sum',
            'Sales': 'sum',
            'Is_Harvest_Candidate': 'max',
            'Is_Negative_Candidate': 'max'
        }).reset_index()
        
        term_agg['ROAS'] = term_agg['Sales'] / term_agg['Spend']
        term_agg['ROAS'] = term_agg['ROAS'].replace([np.inf, -np.inf], 0).fillna(0)
        term_agg['CVR'] = np.where(term_agg['Clicks'] > 0, term_agg['Orders'] / term_agg['Clicks'] * 100, 0)
        
        # Top spenders
        top_spend = term_agg.nlargest(10, 'Spend')
        
        # Top wasters (high spend, 0 orders)
        wasters = term_agg[(term_agg['Orders'] == 0) & (term_agg['Clicks'] > 0)].nlargest(10, 'Spend')
        
        # Top performers (high ROAS, meaningful spend)
        min_spend = term_agg['Spend'].quantile(0.25)  # At least 25th percentile spend
        performers = term_agg[(term_agg['ROAS'] > 3) & (term_agg['Spend'] >= min_spend)].nlargest(10, 'Sales')
        
        # Scalable (high ROAS, but low spend - room to grow)
        scalable = term_agg[(term_agg['ROAS'] > 3) & (term_agg['Spend'] < min_spend * 2) & (term_agg['Orders'] >= 2)].nlargest(5, 'ROAS')
        
        def format_term(row):
            flags = []
            if row.get('Is_Harvest_Candidate'): flags.append("HARVEST")
            if row.get('Is_Negative_Candidate'): flags.append("NEGATIVE")
            
            return {
                "term": str(row['Customer Search Term'])[:60],
                "spend": round(row['Spend'], 2),
                "sales": round(row['Sales'], 2),
                "orders": int(row['Orders']),
                "roas": round(row['ROAS'], 2),
                "clicks": int(row['Clicks']),
                "flags": flags if flags else None
            }
        
        return {
            "total_unique_terms": len(term_agg),
            "top_spenders": [format_term(r) for _, r in top_spend.iterrows()],
            "top_wasters": [format_term(r) for _, r in wasters.iterrows()],
            "top_performers": [format_term(r) for _, r in performers.iterrows()],
            "scalable_opportunities": [format_term(r) for _, r in scalable.iterrows()]
        }

    def _compute_strategic_insights(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Pre-compute strategic insights that the AI should reference.
        These are NOT summaries - they are STRATEGIC OBSERVATIONS.
        """
        insights = []
        
        # Insight 1: Harvest-Negative Paradox (terms in BOTH lists)
        paradox_insight = self._find_paradox_terms(df)
        if paradox_insight:
            insights.append(paradox_insight)
        
        # Insight 2: Campaign Bleeder
        campaign_bleeder = self._find_campaign_bleeders(df)
        if campaign_bleeder:
            insights.append(campaign_bleeder)
        
        # Insight 3: Match Type Efficiency Gap
        match_type_insight = self._analyze_match_type_efficiency(df)
        if match_type_insight:
            insights.append(match_type_insight)
        
        # Insight 4: High Spend Zero Return
        high_spend_zero = self._find_high_spend_zero_return(df)
        if high_spend_zero:
            insights.append(high_spend_zero)
        
        # Insight 5: Untapped Scalers
        scalers = self._find_untapped_scalers(df)
        if scalers:
            insights.append(scalers)
        
        return insights

    def _find_paradox_terms(self, df: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Find terms flagged as BOTH Harvest AND Negative (product-dependent performance)."""
        if 'Is_Harvest_Candidate' not in df.columns or 'Is_Negative_Candidate' not in df.columns:
            return None
        
        # Aggregate by term
        term_flags = df.groupby('Customer Search Term').agg({
            'Is_Harvest_Candidate': 'max',
            'Is_Negative_Candidate': 'max',
            'Spend': 'sum',
            'Sales': 'sum'
        }).reset_index()
        
        # Find paradox terms (both flags True)
        paradox = term_flags[(term_flags['Is_Harvest_Candidate'] == True) & (term_flags['Is_Negative_Candidate'] == True)]
        
        if paradox.empty:
            return None
        
        return {
            "insight_id": "PARADOX-001",
            "type": "harvest_negative_paradox",
            "severity": "high",
            "title": "Performance Split Detected",
            "observation": f"{len(paradox)} terms perform well in SOME campaigns but bleed in OTHERS",
            "terms": paradox.nlargest(5, 'Spend')['Customer Search Term'].tolist(),
            "total_spend_affected": round(paradox['Spend'].sum(), 2),
            "implication": "Product-dependent performance - same keyword works for some SKUs/campaigns, fails for others",
            "action": "Keep the Harvest recommendation where it converts, implement Isolation Negatives where it bleeds. This is a segmentation opportunity."
        }

    def _find_campaign_bleeders(self, df: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Find campaigns that are net negative on performance."""
        if 'Campaign Name' not in df.columns:
            return None
        
        camp_stats = df.groupby('Campaign Name').agg({
            'Spend': 'sum',
            'Sales': 'sum'
        }).reset_index()
        
        camp_stats['ROAS'] = camp_stats['Sales'] / camp_stats['Spend']
        camp_stats['ROAS'] = camp_stats['ROAS'].replace([np.inf, -np.inf], 0).fillna(0)
        camp_stats['Net'] = camp_stats['Sales'] - camp_stats['Spend']
        
        # Campaigns with negative net and significant spend
        bleeders = camp_stats[(camp_stats['Net'] < 0) & (camp_stats['Spend'] > 100)]
        
        if bleeders.empty:
            return None
        
        total_bleed = abs(bleeders['Net'].sum())
        
        return {
            "insight_id": "BLEEDER-001",
            "type": "campaign_bleeders",
            "severity": "high" if total_bleed > 500 else "medium",
            "title": "Net-Negative Campaigns",
            "observation": f"{len(bleeders)} campaigns are spending more than they're earning",
            "campaigns": bleeders.nlargest(3, 'Spend')[['Campaign Name', 'Spend', 'Sales', 'ROAS']].to_dict('records'),
            "total_bleed": round(total_bleed, 2),
            "implication": "These campaigns are net drains on your ad budget",
            "action": "Review targeting settings, negatives, and bid levels. Consider pausing lowest ROAS campaign if no improvement path."
        }

    def _analyze_match_type_efficiency(self, df: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Analyze if match types perform as expected (Exact > Broad > Auto)."""
        if 'Match Type' not in df.columns:
            return None
        
        # Categorize match types
        def categorize_match(row):
            mt = str(row.get('Match Type', '')).lower()
            targeting = str(row.get('Targeting', '')).lower()
            
            if 'exact' in mt:
                return 'EXACT'
            elif 'phrase' in mt:
                return 'PHRASE'
            elif 'broad' in mt:
                return 'BROAD'
            elif any(x in targeting for x in ['close-match', 'loose-match', 'substitutes', 'complements']):
                return 'AUTO'
            elif 'asin' in targeting or 'b0' in targeting:
                return 'PT'
            elif 'category' in targeting:
                return 'CATEGORY'
            else:
                return 'OTHER'
        
        df_match = df.copy()
        df_match['Match_Category'] = df_match.apply(categorize_match, axis=1)
        
        match_stats = df_match.groupby('Match_Category').agg({
            'Spend': 'sum',
            'Sales': 'sum',
            'Clicks': 'sum',
            'Orders': 'sum'
        }).reset_index()
        
        match_stats['ROAS'] = match_stats['Sales'] / match_stats['Spend']
        match_stats['ROAS'] = match_stats['ROAS'].replace([np.inf, -np.inf], 0).fillna(0)
        match_stats['CVR'] = np.where(match_stats['Clicks'] > 0, match_stats['Orders'] / match_stats['Clicks'] * 100, 0)
        
        # Check for anomalies
        exact_roas = match_stats[match_stats['Match_Category'] == 'EXACT']['ROAS'].values
        broad_roas = match_stats[match_stats['Match_Category'] == 'BROAD']['ROAS'].values
        auto_roas = match_stats[match_stats['Match_Category'] == 'AUTO']['ROAS'].values
        
        anomalies = []
        if len(exact_roas) > 0 and len(broad_roas) > 0 and broad_roas[0] > exact_roas[0]:
            anomalies.append("Broad outperforming Exact - keyword selection issue")
        if len(exact_roas) > 0 and len(auto_roas) > 0 and auto_roas[0] > exact_roas[0]:
            anomalies.append("Auto outperforming Exact - harvest more aggressively")
        
        return {
            "insight_id": "MATCH-001",
            "type": "match_type_efficiency",
            "severity": "medium" if anomalies else "low",
            "title": "Match Type Performance Breakdown",
            "breakdown": match_stats[['Match_Category', 'Spend', 'ROAS', 'CVR']].round(2).to_dict('records'),
            "anomalies": anomalies if anomalies else ["No unusual patterns - hierarchy is as expected"],
            "implication": "Match type efficiency shows discovery vs targeted performance"
        }

    def _find_high_spend_zero_return(self, df: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Find terms with high spend but zero orders."""
        term_agg = df.groupby('Customer Search Term').agg({
            'Spend': 'sum',
            'Clicks': 'sum',
            'Orders': 'sum'
        }).reset_index()
        
        # High spend (top 20%) with zero orders
        spend_threshold = term_agg['Spend'].quantile(0.80)
        high_wasters = term_agg[(term_agg['Spend'] >= spend_threshold) & (term_agg['Orders'] == 0)]
        
        if high_wasters.empty:
            return None
        
        total_wasted = high_wasters['Spend'].sum()
        
        return {
            "insight_id": "WASTE-001",
            "type": "high_spend_zero_return",
            "severity": "critical",
            "title": "Critical Bleed Points",
            "observation": f"{len(high_wasters)} high-spend terms have ZERO orders",
            "terms": high_wasters.nlargest(5, 'Spend')[['Customer Search Term', 'Spend', 'Clicks']].to_dict('records'),
            "total_wasted": round(total_wasted, 2),
            "clicks_wasted": int(high_wasters['Clicks'].sum()),
            "implication": "These are your biggest efficiency leaks - traffic with zero conversion",
            "action": "Immediate negative addition. Investigate WHY clicks don't convert (competitor? price? listing?)"
        }

    def _find_untapped_scalers(self, df: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Find high-performing terms that could be scaled."""
        term_agg = df.groupby('Customer Search Term').agg({
            'Spend': 'sum',
            'Sales': 'sum',
            'Orders': 'sum',
            'Clicks': 'sum'
        }).reset_index()
        
        term_agg['ROAS'] = term_agg['Sales'] / term_agg['Spend']
        term_agg['ROAS'] = term_agg['ROAS'].replace([np.inf, -np.inf], 0).fillna(0)
        
        # High ROAS vs Target (Top 20%) but low spend
        target_roas = st.session_state.get('opt_target_roas', 3.0)
        spend_median = term_agg['Spend'].median()
        scalers = term_agg[(term_agg['ROAS'] > target_roas * 1.2) & (term_agg['Spend'] < spend_median) & (term_agg['Orders'] >= 2)]
        
        if scalers.empty:
            return None
        
        potential_gain = scalers['Sales'].sum() * 1.5  # Estimate 50% more sales if scaled
        
        return {
            "insight_id": "SCALE-001",
            "type": "untapped_scalers",
            "severity": "opportunity",
            "title": "Hidden Growth Opportunities",
            "observation": f"{len(scalers)} terms with ROAS > 4x are under-invested",
            "terms": scalers.nlargest(5, 'ROAS')[['Customer Search Term', 'Spend', 'Sales', 'ROAS']].round(2).to_dict('records'),
            "potential_additional_sales": round(potential_gain, 2),
            "implication": "These are your best performers but they're not getting enough traffic",
            "action": "Increase bids by 15-25%, consider harvesting to Exact match for better control"
        }

    def _detect_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect patterns in the data: branded, competitor, generic, etc."""
        patterns = {
            "competitor_brand_clicks": [],
            "potential_branded_terms": [],
            "high_waste_themes": []
        }
        
        # Simple pattern detection based on common indicators
        term_agg = df.groupby('Customer Search Term').agg({
            'Spend': 'sum',
            'Orders': 'sum'
        }).reset_index()
        
        # Look for potential competitor brand terms (high click, 0 orders, common brand patterns)
        competitor_patterns = ['stanley', 'yeti', 'hydro flask', 'contigo', 'thermos', 
                               'nike', 'adidas', 'samsung', 'apple', 'amazon']
        
        for term in term_agg[term_agg['Orders'] == 0]['Customer Search Term'].str.lower():
            for brand in competitor_patterns:
                if brand in str(term):
                    spend = term_agg[term_agg['Customer Search Term'].str.lower() == term]['Spend'].sum()
                    if spend > 10:
                        patterns["competitor_brand_clicks"].append({
                            "term": term,
                            "spend": round(spend, 2),
                            "brand_detected": brand
                        })
                    break
        
        # Limit to top 5
        patterns["competitor_brand_clicks"] = sorted(
            patterns["competitor_brand_clicks"], 
            key=lambda x: x['spend'], 
            reverse=True
        )[:5]
        
        return patterns

    def _build_cross_references(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Build cross-references for terms appearing in multiple contexts."""
        if 'Campaign Name' not in df.columns:
            return {}
        
        # Find terms appearing in multiple campaigns
        term_camps = df.groupby('Customer Search Term').agg({
            'Campaign Name': 'nunique',
            'Spend': 'sum',
            'Sales': 'sum',
            'Orders': 'sum'
        }).reset_index()
        
        multi_campaign_terms = term_camps[term_camps['Campaign Name'] > 1].copy()
        multi_campaign_terms['ROAS'] = multi_campaign_terms['Sales'] / multi_campaign_terms['Spend']
        multi_campaign_terms['ROAS'] = multi_campaign_terms['ROAS'].replace([np.inf, -np.inf], 0).fillna(0)
        
        if multi_campaign_terms.empty:
            return {"multi_campaign_terms": []}
        
        # Get detailed breakdown for top multi-campaign terms
        cross_refs = []
        for term in multi_campaign_terms.nlargest(5, 'Spend')['Customer Search Term']:
            term_data = df[df['Customer Search Term'] == term]
            camp_breakdown = term_data.groupby('Campaign Name').agg({
                'Spend': 'sum',
                'Sales': 'sum',
                'Orders': 'sum'
            }).reset_index()
            camp_breakdown['ROAS'] = camp_breakdown['Sales'] / camp_breakdown['Spend']
            camp_breakdown['ROAS'] = camp_breakdown['ROAS'].replace([np.inf, -np.inf], 0).fillna(0)
            
            best_camp = camp_breakdown.loc[camp_breakdown['ROAS'].idxmax()]
            worst_camp = camp_breakdown.loc[camp_breakdown['ROAS'].idxmin()]
            
            cross_refs.append({
                "term": term[:60],
                "appears_in_campaigns": len(camp_breakdown),
                "total_spend": round(camp_breakdown['Spend'].sum(), 2),
                "best_performer": {
                    "campaign": best_camp['Campaign Name'][:40],
                    "roas": round(best_camp['ROAS'], 2)
                },
                "worst_performer": {
                    "campaign": worst_camp['Campaign Name'][:40],
                    "roas": round(worst_camp['ROAS'], 2)
                },
                "performance_spread": round(best_camp['ROAS'] - worst_camp['ROAS'], 2)
            })
        
        return {"multi_campaign_terms": cross_refs}

    def _gather_module_context(self) -> Dict[str, Any]:
        """Gather context from other modules (Simulation, ASIN Mapper, Clusters)."""
        context = {}
        
        # Optimizer results
        opt_res = st.session_state.get('optimizer_results') or st.session_state.get('latest_optimizer_run')
        if opt_res:
            # Simulation
            if 'simulation' in opt_res and opt_res['simulation']:
                sim = opt_res['simulation']
                scenarios = sim.get('scenarios', {})
                curr = scenarios.get('current', {})
                exp = scenarios.get('expected', {})
                
                if curr and exp:
                    def pct_change(new, old):
                        return ((new - old) / old * 100) if old > 0 else 0
                    
                    context['simulation_forecast'] = {
                        "spend_change": f"{pct_change(exp.get('spend', 0), curr.get('spend', 1)):+.1f}%",
                        "sales_change": f"{pct_change(exp.get('sales', 0), curr.get('sales', 1)):+.1f}%",
                        "roas_change": f"{pct_change(exp.get('roas', 0), curr.get('roas', 1)):+.1f}%",
                        "interpretation": "Positive Sales + Negative Spend = Efficiency Gain" if exp.get('sales', 0) > curr.get('sales', 0) and exp.get('spend', 0) < curr.get('spend', 0) else "Projected improvement from optimizations"
                    }
            
            # Count harvests and negatives
            harvest_df = opt_res.get('harvest', pd.DataFrame())
            neg_kw = opt_res.get('neg_kw', pd.DataFrame())
            neg_pt = opt_res.get('neg_pt', pd.DataFrame())
            
            context['optimizer_actions'] = {
                "harvest_count": len(harvest_df) if not harvest_df.empty else 0,
                "negative_kw_count": len(neg_kw) if not neg_kw.empty else 0,
                "negative_pt_count": len(neg_pt) if not neg_pt.empty else 0
            }
        
        # ASIN Analysis
        if 'latest_asin_analysis' in st.session_state:
            asin = st.session_state['latest_asin_analysis']
            competitors = asin.get('competitors', pd.DataFrame())
            
            if isinstance(competitors, pd.DataFrame) and not competitors.empty:
                context['asin_intelligence'] = {
                    "competitor_asins_detected": len(competitors),
                    "wasted_on_competitors": round(competitors['original_spend'].sum(), 2) if 'original_spend' in competitors.columns else 0
                }
        
        # Cluster Analysis
        if 'latest_ai_insights' in st.session_state:
            clusters = st.session_state['latest_ai_insights'].get('clusters', pd.DataFrame())
            if isinstance(clusters, pd.DataFrame) and not clusters.empty:
                # Get highest waste clusters
                high_waste = clusters[clusters['waste_pct'] > 30].nlargest(3, 'waste_pct')
                context['cluster_insights'] = {
                    "total_clusters": len(clusters),
                    "high_waste_clusters": high_waste[['cluster_id', 'top_terms', 'waste_pct', 'spend']].to_dict('records') if not high_waste.empty else []
                }

        # =========================================================
        # DECISION IMPACT - Uses ImpactMetrics for exact dashboard match
        # MUST match numbers shown on Impact Dashboard hero tiles
        # =========================================================
        try:
            # DEBUG LOGGING SETUP
            import logging
            logging.basicConfig(filename='assistant_debug.log', level=logging.INFO)
            
            # ROBUST CLIENT ID DISCOVERY
            client_id = st.session_state.get('active_account_id')
            
            # Fallback 1: Check unified_data
            if not client_id and 'unified_data' in st.session_state:
                client_id = st.session_state.unified_data.get('client_id')
                
            # Fallback 2: Check query params (deep linking)
            if not client_id:
                query_params = st.query_params
                client_id = query_params.get("account", [None])[0]
            
            # Fallback 3: Query DB for most recent active client (last resort)
            if not client_id:
                try:
                    db = get_db_manager(st.session_state.get('test_mode', False))
                    with db._get_connection() as conn:
                        with conn.cursor() as cur:
                            cur.execute("SELECT client_id FROM actions_log ORDER BY action_date DESC LIMIT 1")
                            row = cur.fetchone()
                            if row:
                                client_id = row[0]
                                logging.info(f"Fallback client_id found in DB: {client_id}")
                except Exception as db_err:
                    logging.error(f"DB Fallback failed: {db_err}")

            if client_id:
                db = get_db_manager(st.session_state.get('test_mode', False))
                
                # Use SAME windows as Impact Dashboard (14D before, 14D after)
                after_days = 14
                
                impact_df = db.get_action_impact(client_id, before_days=14, after_days=after_days)
                
                # Debug logging
                logging.info(f"Assistant Context - Client: {client_id}, Impact Rows: {len(impact_df) if impact_df is not None else 0}")
                
                if impact_df is not None and not impact_df.empty:
                    # Import ImpactMetrics for canonical calculation (same as dashboard)
                    try:
                        from features.impact_metrics import ImpactMetrics
                        
                        # Apply same filters as dashboard (validated_only=True, mature_only=True)
                        metrics = ImpactMetrics.from_dataframe(
                            impact_df,
                            filters={'validated_only': True, 'mature_only': True},
                            horizon_days=after_days
                        )
                        
                        # =====================================================
                        # NO RECALCULATION - Just pass ImpactMetrics.to_dict()
                        # All values come directly from the canonical source
                        # =====================================================
                        context['decision_impact'] = metrics.to_dict()
                        context['decision_impact']['client_id'] = client_id
                        context['decision_impact']['source'] = "ImpactMetrics (canonical - matches Impact Dashboard)"
                    except ImportError as ie:
                        logging.error(f"ImpactMetrics ImportError: {ie}")
                        context['decision_impact'] = {"status": "ImpactMetrics module not found", "fallback": True}
                    except Exception as me:
                        logging.error(f"ImpactMetrics Algo Error: {me}")
                        context['decision_impact'] = {"status": "Calculation Error", "error": str(me)}
                else:
                    logging.warning(f"No impact data found for client {client_id}")
                    context['decision_impact'] = {
                        "status": "No actions logged yet", 
                        "debug_client": client_id,
                        "note": "Run optimizer and save actions to track impact."
                    }
            else:
                logging.warning("No client_id found in session or DB fallback")
                context['decision_impact'] = {"status": "Account not identified", "error": "Could not determine active account"}
                    
        except Exception as e:
            if 'logging' in locals(): logging.error(f"General Context Error: {e}")
            context['decision_impact'] = {"status": "Error", "error": str(e)}
        
        return context

    def _get_platform_methodology(self) -> str:
        """
        Returns the sanctioned technical methodology for the AI to reference.
        Sanitized for general explanation.
        """
        return """
PLATFORM METHODOLOGY & ENGINE LOGIC (UPDATED JAN 2, 2026)

1. MAJOR REVISION HIGHLIGHTS
   The platform recently underwent a significant upgrade to enhance accuracy and trust:
   - **CPC Validation**: Actions are now strictly validated. We only count impact if the 'After CPC' matches the 'Suggested Bid' (±30%).
   - **Match Type Attribution**: Impact is now broken down by Match Type (Exact, Broad, Auto) in the 'Waterfall Chart'.
   - **Realized Impact Tile**: A new dashboard tile shows the actual 60-day realized gains.
   - **Visibility Boost**: NEW action type to boost low-impression keywords.
   - **Currency-Neutral**: All thresholds are now clicks-based (no currency amounts).

2. BENCHMARKING & VALIDATION
   - Dynamic Benchmarking: The engine calculates 'Expected Clicks' (1 / Account_CVR) to set thresholds dynamically.
   - Soft Stop: 2x Expected Clicks (Warning zone).
   - Validation: Actions are validated by comparing Pre-Action CPC vs Post-Action CPC.
   - **Gatekeeper**: Unvalidated actions are EXCLUDED from the 'Realized Impact' score to prevent false positives.

3. INCREMENTALITY MEASUREMENT (ROAS-BASED)
   The primary metric 'Incremental Revenue' measures EFFICIENCY GAIN, not just sales volume.
   Formula: Incremental Revenue = Before_Spend * (ROAS_After - ROAS_Before)
   This isolates value added by the engine, filtering out organic lift.
   
4. REALIZED IMPACT
   - 'Realized Impact_60d' is the actual dollar value generated by VALIDATED actions in the last 60 days.
   - Used to prove engine ROI.

5. VISIBILITY BOOST (NEW - DEC 2025)
   For targets with LOW IMPRESSIONS over 2+ weeks (bid not competitive to win auctions):
   
   TRIGGER CONDITIONS:
   - Data window >= 14 days
   - Impressions < 100 (not winning auctions)
   - Includes 0 impressions (bid SO low it can't even enter auctions)
   - Note: Paused targets are identified by state='paused', not impressions
   
   ELIGIBLE MATCH TYPES (only these get boosted):
   - Exact, Phrase, Broad keywords (advertiser explicitly chose these)
   - Close-match auto (most relevant auto type)
   
   NOT ELIGIBLE (Amazon decides relevance):
   - loose-match, substitutes, complements (auto types)
   - ASIN targeting (product targeting)
   - Category targeting
   
   ACTION: Increase bid by 30% to gain visibility.
   
   RATIONALE:
   - High impressions + low clicks = CTR problem (ad quality, not bid)
   - LOW impressions = bid not competitive (needs boost)
   - We only boost keywords the advertiser explicitly wants to compete on

6. CURRENCY-NEUTRAL THRESHOLDS
   To support multi-region accounts (USD, AED, SAR, INR, etc.):
   - HARVEST_SALES threshold REMOVED (was $150)
   - NEGATIVE_SPEND_THRESHOLD REMOVED (was $10)
   - All thresholds now use CLICKS only (works in any currency)

7. IMPACT DASHBOARD METHODOLOGY (JAN 2026 - COUNTERFACTUAL FRAMEWORK)
   
   **Core Philosophy**: Isolate DECISION QUALITY from MARKET CONDITIONS.
   
   A. DECISION OUTCOME MATRIX (Counterfactual Analysis)
      - **Purpose**: Separate what WE controlled (decisions) from what we DIDN'T (market trends)
      
      - **X-Axis: Expected Trend %**
        * Formula: (Expected Sales - Before Sales) / Before Sales * 100
        * Expected Sales = (New Spend / Baseline CPC) * Baseline SPC
        * Translation: "If we maintained old efficiency, what would sales be at new spend?"
      
      - **Y-Axis: vs Expectation %**
        * Formula: Actual Change % - Expected Trend %
        * Translation: "How much did we BEAT or MISS the counterfactual?"
      
      - **Quadrants**:
        1. **Offensive Win** (X≥0, Y≥0): Spend increase + beat baseline → Efficient scaling
        2. **Defensive Win** (X<0, Y≥0): Market headwinds, but we beat the drop → Good defense
        3. **Decision Gap** (X≥0, Y<0): Spend increase but missed expectations → Inefficient scale
        4. **Market Drag** (X<0, Y<0): Market shrank AND we underperformed → External + internal failure
      
   B. DECISION-ATTRIBUTED IMPACT (Hero Metric)
      - **Formula**: Sum(Offensive Wins + Defensive Wins + Decision Gaps)
      - **Exclusion**: **Market Drag is EXCLUDED** from all impact totals
      - **Reasoning**: 
        * Market Drag = External headwinds we didn't control
        * Including it would conflate market luck with decision quality
        * We ONLY attribute impact where our DECISION had clear directional influence
      
      - **Display**: 
        * Main Number: Net Impact (Green if positive, Red if negative)
        * Breakdown: "✅ Wins: +X (Offensive + Defensive) | ❌ Gaps: -Y"
        * Footnote: "ℹ️ Z actions excluded (Market Drag — ambiguous attribution)"
   
   C. CAPITAL PROTECTED (Refined Logic)
      - **Definition**: Wasteful spend eliminated from confirmed negative keyword blocks
      - **Formula**: Sum of `before_spend` for NEGATIVE actions where `observed_after_spend == 0`
      - **Why This Works**:
        * Only counts actions INTENDED to protect capital (negatives)
        * `after_spend == 0` proves the block was successful
        * Bid increases SHOULD increase spend — that's scaling winners
      - **Display**: "From X confirmed negatives" + "Confidence: High"
   
   D. IMPACT VALIDATION
      - **Maturity Buffer**: 3 days after measurement window for attribution to settle
      - **Validation Status**: Actions marked as Validated, Directional, Pending, or Invalid
      - **Verified Impact**: Only includes Validated + Directional status
   
   E. KEY DISTINCTIONS FOR USER QUESTIONS
      - **"Verified Impact vs Baseline"** = Decision-Attributed Impact (excludes Market Drag)
      - **"Measured Impact"** = Same as Verified Impact (alternate phrasing)
      - **"Capital Protected"** = Spend saved from confirmed negative blocks
      - **"Win Rate"** = % of actions in Win quadrants (Offensive + Defensive)
      - **"Decision Gap"** = Actions where we scaled but missed efficiency targets
      - **"Market Drag"** = Actions where market conditions confound attribution

   F. WHEN USER ASKS ABOUT IMPACT METRICS
      - Always explain the COUNTERFACTUAL: "We compare to what WOULD HAVE happened"
      - Emphasize Market Drag exclusion: "We only count where YOUR decisions had clear impact"
      - Use concrete examples: "This action had +$500 vs baseline, meaning we made $500 MORE than if we hadn't optimized"
      - Distinguish from actual performance: "This is INCREMENTAL to what already happened, not total sales"
"""

    def _compute_optimization_impact(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate the financial impact of optimization recommendations.
        Merges PROJECETD impact (from current recommendations) with REALIZED impact (from DB).
        """
        # 1. Fetch Realized Impact (DB)
        realized_impact = None
        try:
            if 'client_id' in st.session_state:
                client_id = st.session_state['client_id']
                impact_df = get_db_manager().get_action_impact(client_id, window_days=60)
                if not impact_df.empty:
                    # Filter active
                    active_mask = (impact_df['before_spend'].fillna(0) + impact_df['after_spend'].fillna(0)) > 0
                    active_df = impact_df[active_mask].copy()
                    if not active_df.empty:
                        realized_impact = {
                            "incremental_revenue": round(active_df['impact_score'].sum(), 2),
                            "action_count": int(len(active_df)),
                            "description": "Actual realized revenue lift from actions taken in the last 60 days"
                        }
        except Exception:
            pass

        # 2. Projected Impact Loop Restoration
        opt_res = st.session_state.get('optimizer_results') or st.session_state.get('latest_optimizer_run')
        
        if not opt_res:
            return {"status": "Optimizer not run yet", "realized_impact_60d": realized_impact}
        
        date_info = self._detect_date_range(df)
        weeks = date_info.get('weeks', 1)
        monthly_multiplier = 4.33 / weeks
        
        neg_kw = opt_res.get('neg_kw', pd.DataFrame())
        neg_pt = opt_res.get('neg_pt', pd.DataFrame())
        
        impact = {
            "realized_impact_60d": realized_impact,
            "date_range": date_info.get('label', 'Unknown'),
            "projection_basis": f"Based on {date_info.get('days', 7)} days of data, projected to monthly",
            "negatives": {},
            "harvests": {},
            "bids": {},
            "net_summary": {}
        }
        
        negative_spend = 0
        negative_count = 0
        
        # Calculate spend on negative keyword candidates
        if not neg_kw.empty and 'Spend' in neg_kw.columns:
            negative_spend += neg_kw['Spend'].sum()
            negative_count += len(neg_kw)
        elif not neg_kw.empty:
            # If no Spend column, look up from granular data
            neg_terms = set(neg_kw['Term'].astype(str).str.lower().str.strip()) if 'Term' in neg_kw.columns else set()
            negative_spend += df[df['_norm_term'].isin(neg_terms)]['Spend'].sum()
            negative_count += len(neg_kw)
        
        # Calculate spend on negative PT candidates
        if not neg_pt.empty and 'Spend' in neg_pt.columns:
            negative_spend += neg_pt['Spend'].sum()
            negative_count += len(neg_pt)
        elif not neg_pt.empty:
            neg_pt_terms = set()
            if 'Term' in neg_pt.columns:
                for t in neg_pt['Term'].astype(str):
                    # Remove asin="" wrapper
                    clean = t.lower().replace('asin="', '').replace('"', '').strip()
                    neg_pt_terms.add(clean)
            negative_spend += df[df['_norm_term'].isin(neg_pt_terms)]['Spend'].sum()
            negative_count += len(neg_pt)
        
        monthly_negative_savings = negative_spend * monthly_multiplier
        
        impact["negatives"] = {
            "total_candidates": negative_count,
            "keyword_negatives": len(neg_kw) if not neg_kw.empty else 0,
            "product_target_negatives": len(neg_pt) if not neg_pt.empty else 0,
            "current_spend_on_bleeders": round(negative_spend, 2),
            "projected_monthly_savings": round(monthly_negative_savings, 2),
            "interpretation": f"By negating these {negative_count} terms, you'll stop ~AED {monthly_negative_savings:,.0f}/month in wasted spend"
        }
        
        # =====================================================================
        # 2. HARVEST IMPACT - Potential efficiency gain from Exact match
        # =====================================================================
        harvest_df = opt_res.get('harvest', pd.DataFrame())
        
        if not harvest_df.empty:
            # Harvest candidates current performance
            harvest_spend = harvest_df['Spend'].sum() if 'Spend' in harvest_df.columns else 0
            harvest_sales = harvest_df['Sales'].sum() if 'Sales' in harvest_df.columns else 0
            harvest_orders = harvest_df['Orders'].sum() if 'Orders' in harvest_df.columns else 0
            harvest_cpc = harvest_df['CPC'].mean() if 'CPC' in harvest_df.columns else 0.5
            
            # Assumption: Exact match gets 15% better CPC efficiency + 10% better CVR
            exact_cpc_improvement = 0.15  # 15% lower CPC
            exact_cvr_improvement = 0.10  # 10% better CVR
            
            projected_new_cpc = harvest_cpc * (1 - exact_cpc_improvement)
            projected_spend_reduction = harvest_spend * exact_cpc_improvement
            projected_additional_orders = harvest_orders * exact_cvr_improvement
            projected_additional_sales = (harvest_sales / harvest_orders * projected_additional_orders) if harvest_orders > 0 else 0
            
            monthly_harvest_savings = projected_spend_reduction * monthly_multiplier
            monthly_additional_sales = projected_additional_sales * monthly_multiplier
            
            impact["harvests"] = {
                "total_candidates": len(harvest_df),
                "current_metrics": {
                    "spend": round(harvest_spend, 2),
                    "sales": round(harvest_sales, 2),
                    "orders": int(harvest_orders),
                    "avg_cpc": round(harvest_cpc, 2)
                },
                "exact_match_projection": {
                    "expected_cpc_reduction": f"{exact_cpc_improvement*100:.0f}%",
                    "expected_cvr_improvement": f"{exact_cvr_improvement*100:.0f}%",
                    "projected_monthly_spend_savings": round(monthly_harvest_savings, 2),
                    "projected_monthly_additional_sales": round(monthly_additional_sales, 2)
                },
                "interpretation": f"Harvesting {len(harvest_df)} terms to Exact could save ~AED {monthly_harvest_savings:,.0f}/month on CPC + add ~AED {monthly_additional_sales:,.0f}/month in sales"
            }
        else:
            impact["harvests"] = {
                "total_candidates": 0,
                "interpretation": "No harvest candidates identified - may need more converting terms"
            }
        
        # =====================================================================
        # 3. BID OPTIMIZATION IMPACT
        # =====================================================================
        direct_bids = opt_res.get('direct_bids', pd.DataFrame())
        agg_bids = opt_res.get('agg_bids', pd.DataFrame())
        
        all_bids = pd.concat([direct_bids, agg_bids]) if not direct_bids.empty or not agg_bids.empty else pd.DataFrame()
        
        if not all_bids.empty and 'New Bid' in all_bids.columns:
            # Identify CPC column
            cpc_col = 'Cost Per Click (CPC)' if 'Cost Per Click (CPC)' in all_bids.columns else 'CPC'
            
            if cpc_col in all_bids.columns:
                # Calculate bid increases vs decreases
                all_bids['Bid_Change'] = all_bids['New Bid'] - all_bids[cpc_col]
                all_bids['Bid_Change_Pct'] = (all_bids['Bid_Change'] / all_bids[cpc_col] * 100).fillna(0)
                
                increases = all_bids[all_bids['Bid_Change'] > 0]
                decreases = all_bids[all_bids['Bid_Change'] < 0]
                holds = all_bids[all_bids['Bid_Change'] == 0]
                
                # Estimate spend impact (rough: bid change * historical clicks)
                clicks_col = 'Clicks' if 'Clicks' in all_bids.columns else None
                
                if clicks_col:
                    increase_spend_delta = (increases['Bid_Change'] * increases[clicks_col]).sum()
                    decrease_spend_delta = (decreases['Bid_Change'] * decreases[clicks_col]).sum()
                else:
                    # Estimate using average bid change
                    increase_spend_delta = increases['Bid_Change'].sum() * 50  # Assume 50 clicks avg
                    decrease_spend_delta = decreases['Bid_Change'].sum() * 50
                
                monthly_increase_delta = increase_spend_delta * monthly_multiplier
                monthly_decrease_delta = decrease_spend_delta * monthly_multiplier  # This is negative
                
                impact["bids"] = {
                    "total_recommendations": len(all_bids),
                    "bid_increases": {
                        "count": len(increases),
                        "avg_increase": f"+{increases['Bid_Change_Pct'].mean():.1f}%" if len(increases) > 0 else "0%",
                        "projected_monthly_additional_spend": round(monthly_increase_delta, 2),
                        "purpose": "Scaling winning keywords for more traffic"
                    },
                    "bid_decreases": {
                        "count": len(decreases),
                        "avg_decrease": f"{decreases['Bid_Change_Pct'].mean():.1f}%" if len(decreases) > 0 else "0%",
                        "projected_monthly_savings": round(abs(monthly_decrease_delta), 2),
                        "purpose": "Reducing waste on underperformers"
                    },
                    "holds": len(holds),
                    "net_monthly_spend_change": round(monthly_increase_delta + monthly_decrease_delta, 2),
                    "interpretation": f"{len(increases)} bids going up (for scale), {len(decreases)} going down (for efficiency)"
                }
            else:
                impact["bids"] = {"status": "Bid data incomplete - missing CPC column"}
        else:
            impact["bids"] = {
                "total_recommendations": 0,
                "interpretation": "No bid recommendations - may need bulk file for keyword-level bidding"
            }
        
        # =====================================================================
        # 4. NET SUMMARY - The bottom line
        # =====================================================================
        total_monthly_savings = 0
        total_monthly_additional_sales = 0
        total_monthly_spend_reduction = 0
        
        # From negatives
        total_monthly_spend_reduction += impact["negatives"].get("projected_monthly_savings", 0)
        
        # From harvests
        if "exact_match_projection" in impact.get("harvests", {}):
            total_monthly_spend_reduction += impact["harvests"]["exact_match_projection"].get("projected_monthly_spend_savings", 0)
            total_monthly_additional_sales += impact["harvests"]["exact_match_projection"].get("projected_monthly_additional_sales", 0)
        
        # From bids
        bid_net = impact.get("bids", {}).get("net_monthly_spend_change", 0)
        if bid_net < 0:
            total_monthly_spend_reduction += abs(bid_net)
        else:
            total_monthly_spend_reduction -= bid_net  # Increases reduce net savings
        
        # Calculate net impact
        total_monthly_savings = total_monthly_spend_reduction
        
        # ROAS improvement estimate
        current_spend = df['Spend'].sum() * monthly_multiplier
        current_sales = df['Sales'].sum() * monthly_multiplier
        
        projected_spend = current_spend - total_monthly_spend_reduction
        projected_sales = current_sales + total_monthly_additional_sales
        
        current_roas = current_sales / current_spend if current_spend > 0 else 0
        projected_roas = projected_sales / projected_spend if projected_spend > 0 else 0
        roas_improvement = ((projected_roas - current_roas) / current_roas * 100) if current_roas > 0 else 0
        
        impact["net_summary"] = {
            "total_actions": (
                impact["negatives"].get("total_candidates", 0) +
                impact["harvests"].get("total_candidates", 0) +
                impact["bids"].get("total_recommendations", 0)
            ),
            "current_monthly": {
                "spend": round(current_spend, 2),
                "sales": round(current_sales, 2),
                "roas": round(current_roas, 2)
            },
            "projected_monthly": {
                "spend": round(projected_spend, 2),
                "sales": round(projected_sales, 2),
                "roas": round(projected_roas, 2)
            },
            "net_change": {
                "monthly_spend_reduction": round(total_monthly_spend_reduction, 2),
                "monthly_additional_sales": round(total_monthly_additional_sales, 2),
                "roas_improvement": f"+{roas_improvement:.1f}%"
            },
            "bottom_line": f"Implementing all {impact['negatives'].get('total_candidates', 0)} negatives, {impact['harvests'].get('total_candidates', 0)} harvests, and {impact['bids'].get('total_recommendations', 0)} bid changes could save ~AED {total_monthly_spend_reduction:,.0f}/month and add ~AED {total_monthly_additional_sales:,.0f}/month in sales = {roas_improvement:+.1f}% ROAS improvement"
        }
        
        return impact

    def _detect_date_range(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect date range from data for projections."""
        date_cols = ["Date", "Start Date", "date", "Report Date"]
        date_col = None
        
        for col in date_cols:
            if col in df.columns:
                date_col = col
                break
        
        if date_col is None:
            return {"weeks": 1.0, "label": "Period Unknown", "days": 7}
        
        try:
            dates = pd.to_datetime(df[date_col], errors='coerce').dropna()
            if dates.empty:
                return {"weeks": 1.0, "label": "Period Unknown", "days": 7}
            
            min_date = dates.min()
            max_date = dates.max()
            days = (max_date - min_date).days + 1
            weeks = max(days / 7, 1.0)
            
            label = f"{days} days ({min_date.strftime('%b %d')} - {max_date.strftime('%b %d')})"
            
            return {"weeks": weeks, "label": label, "days": days}
        except:
            return {"weeks": 1.0, "label": "Period Unknown", "days": 7}

    def _summarize_data_status(self) -> Dict[str, Any]:
        """Summarize what data is loaded and what's missing."""
        status = {"loaded": [], "missing": []}
        
        if 'unified_data' in st.session_state:
            data = st.session_state.unified_data
            
            if data.get('search_term_report') is not None:
                status["loaded"].append("Search Term Report")
            else:
                status["missing"].append("Search Term Report (REQUIRED)")
            
            if data.get('advertised_product_report') is not None:
                status["loaded"].append("Advertised Product Report (SKU/ASIN mapping)")
            else:
                status["missing"].append("Advertised Product Report (product context missing)")
            
            if data.get('bulk_id_mapping') is not None:
                status["loaded"].append("Bulk File (Campaign/Keyword IDs)")
            else:
                status["missing"].append("Bulk File (bid-level precision limited)")
        else:
            status["missing"].append("No data uploaded")
        
        return status

    # =========================================================================
    # CONTEXT FORMATTING
    # =========================================================================

    def _get_context(self) -> str:
        """
        Build the comprehensive context for the AI.
        Returns a JSON-formatted knowledge graph.
        """
        df = self._construct_granular_dataset()
        
        if df.empty:
            # Even without STR data, we can still provide decision_impact from DB
            knowledge = {
                "error": "No Search Term Report loaded yet. Upload in Data Hub for full analysis.",
                "data_status": self._summarize_data_status(),
                "module_context": self._gather_module_context()  # This includes decision_impact
            }
            return json.dumps(knowledge, indent=2, default=str)
        
        knowledge = self._build_knowledge_graph(df)
        
        # Format as JSON for better LLM parsing
        return json.dumps(knowledge, indent=2, default=str)

    # =========================================================================
    # LLM INTERFACE
    # =========================================================================

    def _call_llm(self, messages):
        """Calls OpenAI API using the requests library."""
        # Safely access secrets - handle missing secrets.toml
        api_key = None
        try:
            api_key = st.secrets.get("OPENAI_API_KEY")
        except Exception:
            # secrets.toml doesn't exist - try environment variable
            import os
            api_key = os.environ.get("OPENAI_API_KEY")
        
        if not api_key:
            return "⚠️ OpenAI API Key not configured. Please add OPENAI_API_KEY to .streamlit/secrets.toml or environment variables."

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "gpt-4o",
            "messages": messages,
            "temperature": 0.4,  # Slightly lower for more consistent analytical responses
            "max_tokens": 2000
        }
        
        try:
            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            return f"❌ Error communicating with AI: {str(e)}"

    # =========================================================================
    # UI RENDERING
    # =========================================================================

    def render_floating_interface(self):
        """Standard styling for a prominent Assistant button."""
        st.markdown("""
        <style>
        /* Standard positioning - not floating fixed */
        [data-testid="stPopover"] {
            display: inline-block;
            margin-top: 20px;
        }
        
        /* Premium CTA Button Style - Dark with Glow */
        [data-testid="stPopover"] > button {
            background: linear-gradient(135deg, rgba(30, 41, 59, 1) 0%, rgba(15, 23, 42, 1) 100%) !important;
            border: 1px solid rgba(6, 182, 212, 0.5) !important;
            border-radius: 12px !important;
            padding: 16px 32px !important;
            color: #ffffff !important;
            font-family: 'Inter', sans-serif !important;
            font-weight: 600 !important;
            font-size: 1.1rem !important;
            letter-spacing: 0.5px !important;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(255, 255, 255, 0.05) inset !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            min-width: 280px !important;
            text-align: left !important;
            display: flex !important;
            align-items: center !important;
            justify-content: space-between !important;
        }
        
        [data-testid="stPopover"] > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 30px rgba(6, 182, 212, 0.25), 0 0 0 1px rgba(6, 182, 212, 0.5) inset !important;
            border-color: #22d3ee !important;
            background: linear-gradient(135deg, rgba(30, 41, 59, 1) 0%, rgba(15, 23, 42, 1) 100%) !important;
        }
        
        /* Icon animation */
        [data-testid="stPopover"] > button span:first-child {
            display: inline-flex !important;
            align-items: center !important;
            gap: 12px !important;
        }
        
        /* Add a subtle glow/pulse animation */
        @keyframes border-pulse {
            0% { border-color: rgba(6, 182, 212, 0.3); }
            50% { border-color: rgba(6, 182, 212, 0.8); }
            100% { border-color: rgba(6, 182, 212, 0.3); }
        }
        </style>
        """, unsafe_allow_html=True)
        
    def render_interface(self):
        """
        Render the Ask Zenny interface.
        """
        is_full_page = st.session_state.get('current_module') == 'assistant'
        self.render_floating_interface()
        
        if is_full_page:
            # === FULL PAGE MODE ===
            col1, col2 = st.columns([0.1, 0.9])
            with col1:
                st.markdown('<div style="font-size: 40px;">✨</div>', unsafe_allow_html=True)
            with col2:
                st.title("AI Campaign Strategist")
            st.caption("Strategic insights and real-time optimization guidance powered by Zenny.")
            self._render_chat_content(height=600)
            
        else:
            # === COMPACT MODE (Standard Button) ===
            # Prominent branding label
            with st.popover("✨ Ask your AI strategist", use_container_width=False):
                st.subheader("Ask Zenny")
                st.markdown('<div style="margin-bottom: 10px; color: #8F8CA3; font-size: 0.9em;">AI Campaign Strategist</div>', unsafe_allow_html=True)
                self._render_chat_content(height=400)

    def _render_chat_content(self, height=400):
        """
        Internal method to render the actual chat messages and input.
        """
        import base64
        
        # Build context
        data_context = self._get_context()
        
        # Initialize chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []
            st.session_state.messages.append({
                "role": "assistant", 
                "content": "Hello! I'm Zenny, your AI campaign strategist. Ask me:\n\n"
                           "- **\"Where am I losing money?\"** - I'll find structural waste patterns\n"
                           "- **\"What should I scale?\"** - I'll identify growth opportunities\n"
                           "- **\"Analyze [keyword/campaign]\"** - Deep dive on specific items\n"
                           "- **\"What's my biggest opportunity?\"** - Cross-module synthesis"
            })

        # Display chat container
        chat_container = st.container(height=height)
        with chat_container:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

        # User input
        if prompt := st.chat_input("Ask about your campaigns..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            with chat_container:
                with st.chat_message("user"):
                    st.markdown(prompt)

                with st.chat_message("assistant"):
                    with st.spinner("Analyzing your data..."):
                        full_messages = [
                            {"role": "system", "content": self.system_prompt},
                            {"role": "system", "content": f"KNOWLEDGE GRAPH (Your complete dataset analysis):\n{data_context}"}
                        ] + st.session_state.messages
                        
                        response = self._call_llm(full_messages)
                        st.markdown(response)
                        
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()

    # =========================================================================
    # CLIENT REPORT GENERATION (NEW - Jan 2026)
    # =========================================================================

    def generate_report_narratives(self, panels: List[str]) -> Dict[str, Any]:
        """
        Generate AI narratives for client report panels.

        Args:
            panels: List of panel names e.g., ["performance", "health", "portfolio"]

        Returns:
            Dict mapping panel name to narrative text or structured data

        Example:
            narratives = assistant.generate_report_narratives([
                "performance", "health", "portfolio", "impact",
                "actions", "match_type", "executive_summary"
            ])
        """
        # Build knowledge graph using EXISTING method
        df = self._construct_granular_dataset()

        if df.empty:
            # Return safe empty structures to prevent UI crashes
            safe_responses = {}
            for panel in panels:
                if panel == 'executive_summary':
                    safe_responses[panel] = {
                        "overview": "Data analysis pending. Please upload Search Term Report to generate insights.",
                        "key_metric": "No Data",
                        "trend": "neutral"
                    }
                else:
                    safe_responses[panel] = "Data analysis pending - upload Search Term Report to generate insights."
            return safe_responses

        knowledge = self._build_knowledge_graph(df)

        narratives = {}

        # Generate narrative for each panel
        for panel in panels:
            if panel == "executive_summary":
                # Executive summary returns structured dict, not string
                narratives[panel] = self._generate_executive_summary(knowledge)
            else:
                # Regular panels return narrative string
                panel_data = self._extract_panel_context(panel, knowledge)
                narratives[panel] = self._generate_panel_narrative(panel, panel_data)

        return narratives

    def _extract_panel_context(self, panel_name: str, knowledge: Dict) -> Dict:
        """
        Extract relevant data for each panel type from knowledge graph.

        Args:
            panel_name: One of "performance", "health", "portfolio", "impact", "actions", "match_type"
            knowledge: Full knowledge graph from _build_knowledge_graph()

        Returns:
            Dict with panel-specific data subset
        """
        panel_contexts = {
            "performance": {
                "metrics": knowledge.get("dataset_overview", {}),
                # "health" explicitly REMOVED to prevent AI from mentioning health score
                "date_range": knowledge.get("optimization_impact", {}).get("date_range", "Period Unknown")
            },

            "health": {
                "scores": knowledge.get("account_health", {}),
                "status": knowledge.get("account_health", {}).get("status", "Unknown"),
                "opportunities": knowledge.get("account_health", {}).get("optimization_opportunities", {})
            },

            "portfolio": {
                "overview": knowledge.get("campaign_portfolio", {}),
                "winners": knowledge.get("campaign_portfolio", {}).get("winners", []),
                "losers": knowledge.get("campaign_portfolio", {}).get("losers", []),
                "concentration": knowledge.get("campaign_portfolio", {}).get("concentration", {})
            },

            "impact": {
                "decision_metrics": knowledge.get("module_context", {}).get("decision_impact", {}),
                "realized": knowledge.get("optimization_impact", {}).get("realized_impact_60d", None),
                "attribution": knowledge.get("optimization_impact", {}).get("net_summary", {})
            },

            "actions": {
                "summary": knowledge.get("optimization_impact", {}),
                "negatives": knowledge.get("optimization_impact", {}).get("negatives", {}),
                "harvests": knowledge.get("optimization_impact", {}).get("harvests", {}),
                "bids": knowledge.get("optimization_impact", {}).get("bids", {})
            },

            "match_type": {
                "insights": knowledge.get("strategic_insights", []),
                "term_analysis": knowledge.get("term_analysis", {}),
                "efficiency": [i for i in knowledge.get("strategic_insights", [])
                              if i.get("type") == "match_type_efficiency"]
            }
        }

        return panel_contexts.get(panel_name, {})

    def _generate_panel_narrative(self, panel_name: str, context: Dict) -> str:
        """
        Generate 2-3 sentence narrative for a panel.

        Args:
            panel_name: Panel identifier
            context: Panel-specific data from _extract_panel_context()

        Returns:
            2-3 sentence narrative string
        """
        # Panel-specific prompts for client-facing reports
        prompts = {
            "performance": f"""
Based on these performance metrics:
{json.dumps(context, indent=2)}

Write EXACTLY 2-3 sentences for a CLIENT-FACING report:
- Identify "Stars" (strong metrics) and "Detractors" (weak metrics) from the key data (Spend, Sales, ROAS, CVR, Orders, ACOS).
- Highlight specific numbers for context.
- Keep the tone professional and objective.

CRITICAL CONSTRAINTS:
- DO NOT mention "spend efficiency", "efficiency", "waste", or "wasted spend". (There is a separate section for that).
- DO NOT use the word "efficiency".
- Focus ONLY on the "Performance Overview" numbers provided.
""",

            "health": f"""
Account health analysis:
{json.dumps(context, indent=2)}

Write 2-3 sentences explaining:
- Overall account health status in business terms
- Main strength OR main concern (pick the most important)
- What it means for campaign performance

Use simple business language - client should understand immediately.
IMPORTANT: When discussing "Efficiency", refer to the 'gauge_spend_efficiency' value (Efficiency Gauge) if available, as this matches the visual report.
""",

            "portfolio": f"""
Campaign portfolio breakdown:
{json.dumps(context, indent=2)}

Write 2-3 sentences covering:
- How the campaign portfolio is structured (winners vs underperformers)
- Key strategic insight about portfolio balance
- Business recommendation

Client-friendly language only.

CRITICAL INSTRUCTION:
- Check "cut_candidates" (Campaigns with ROAS < 1.5 and Orders < 5).
- If there are significant campaigns in this list, you MUST recommend pausing them as the top priority.
- Explicitly name the top 1-3 "Cut" campaigns if they are bleeding spend.
""",

            "impact": f"""
Decision impact measurement:
{json.dumps(context, indent=2)}

Write 2-3 sentences explaining:
- What measurable value your optimization decisions created
- How we proved it (briefly explain the measurement methodology)
- Why this demonstrates effective management

Tone: Professional confidence backed by data.
""",

            "actions": f"""
Optimization actions executed:
{json.dumps(context, indent=2)}

Write 2-3 sentences covering:
- What specific optimization actions were taken
- Expected financial impact (savings + revenue gains)
- Next steps or ongoing optimizations

Use concrete numbers to quantify impact.
""",

            "match_type": f"""
Match type performance analysis:
{json.dumps(context, indent=2)}

Write 2-3 sentences explaining:
- Which targeting types are most efficient
- Strategic insight about match type strategy
- Recommendation for optimization

Explain match types simply (e.g., "exact keyword targeting" vs "broad discovery").
"""
        }

        prompt = prompts.get(panel_name, f"Analyze this data for a client report: {json.dumps(context)}")

        # Build messages for API call
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]

        # Call Claude API using EXISTING _call_llm method
        try:
            response = self._call_llm(messages)
            return response.strip()
        except Exception as e:
            # Fallback if API fails
            return f"Detailed analysis available in full dashboard. (Error: {str(e)})"

    def _generate_executive_summary(self, knowledge: Dict) -> Dict[str, List[str]]:
        """
        Generate executive summary with achievements/concerns/next steps.

        Args:
            knowledge: Full knowledge graph

        Returns:
            Dict with structure:
            {
                "achievements": ["...", "...", "..."],
                "areas_to_watch": ["...", "..."],
                "next_steps": ["...", "...", "..."]
            }
        """
        summary_prompt = f"""
Based on this complete account analysis:

{json.dumps(knowledge, indent=2, default=str)}

Generate an EXECUTIVE SUMMARY for a client-facing report.

Provide EXACTLY:
1. TOP 3 KEY ACHIEVEMENTS (quantified wins with specific numbers)
2. TOP 2 AREAS TO MONITOR. Constraint: Focus SOLELY on "spend inefficiency" (defined as segments with < 2.5 ROAS) and "efficiency declines associated with market forces".
3. TOP 2-3 RECOMMENDED NEXT STEPS. Constraint: You MUST mention "monitoring market forces" affecting ROAS. If optimizer recommendations (bids/negatives/harvests) exist in the data, include them here.

CRITICAL: Return response as VALID JSON ONLY (no markdown, no explanations):
{{
  "achievements": ["Achievement 1 with numbers", "Achievement 2", "Achievement 3"],
  "areas_to_watch": ["Inefficiency Note (ROAS < 2.5)", "Market Force Note"],
  "next_steps": ["Monitor market forces...", "Implement optimizer recommendations...", "..."]
}}

Requirements:
- Include specific $ amounts where available
- Client-friendly language (NO jargon)
- "Areas to Monitor" MUST strictly follow the < 2.5 ROAS definition or market impact.
- Focus on business impact
"""

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": summary_prompt}
        ]

        try:
            response = self._call_llm(messages)

            # Clean response (remove markdown code fences if present)
            clean = response.replace("```json", "").replace("```", "").strip()

            # Parse JSON
            summary = json.loads(clean)

            # Validate structure
            if not all(k in summary for k in ["achievements", "areas_to_watch", "next_steps"]):
                raise ValueError("Invalid summary structure")

            return summary

        except Exception as e:
            # Fallback to generic summary
            return {
                "achievements": [
                    "Account performance analyzed across all campaigns",
                    "Optimization opportunities identified and quantified",
                    "Decision impact tracking active and validated"
                ],
                "areas_to_watch": [
                    "Review detailed dashboard for specific campaign insights",
                    "Monitor pending optimization implementations"
                ],
                "next_steps": [
                    "Execute recommended optimization actions",
                    "Track impact over next 14-60 days",
                    "Schedule performance review meeting"
                ]
            }


def get_dynamic_key_insights() -> list:
    """
    Extract ranked signals from the assistant's knowledge graph.
    Returns: List of 3 insight dicts (2 positives + 1 watchout)
    
    Signal schema:
    {
        "type": "positive" | "watch",
        "category": "Efficiency" | "Growth" | "Risk" | "Opportunity",
        "strength": 0-100,
        "title": str,
        "subtitle": str,
        "icon_type": "success" | "info" | "warning" | "note"
    }
    """
    import streamlit as st
    from utils.formatters import get_account_currency
    
    currency = get_account_currency()
    
    default_insights = [
        {"type": "positive", "title": "Ready to analyze", "subtitle": "Upload data to start", "icon_type": "info", "strength": 0},
        {"type": "positive", "title": "Optimizer available", "subtitle": "Run to get recommendations", "icon_type": "info", "strength": 0},
        {"type": "watch", "title": "Impact tracking", "subtitle": "Configure and run", "icon_type": "note", "strength": 0}
    ]
    
    # Manual cache - check if we already have insights computed
    opt_res = st.session_state.get('optimizer_results') or st.session_state.get('latest_optimizer_run')
    
    # Create a cache key based on whether optimizer has data
    has_opt_data = opt_res and 'df' in opt_res and not opt_res['df'].empty
    
    # Fast path: Return defaults if no data
    if not has_opt_data:
        return _get_insights_from_database()
        
    try:
        # Optimizer has run - build insights from optimizer results
        df = opt_res['df']
        target_roas = st.session_state.get('opt_target_roas', 3.0)
        
        # Use cached core logic
        # We pass a copy/signature to avoid mutation issues, OR rely on streamlit hashing
        return _generate_insights_core(df, currency, target_roas)
        
    except Exception as e:
        # Fail gracefully
        print(f"DEBUG: Error in get_dynamic_key_insights: {str(e)}")
        return default_insights


@st.cache_data(ttl=600, show_spinner=False)
def _generate_insights_core(df: pd.DataFrame, currency: str, target_roas: float) -> list:
    """
    Core logic for insight generation - extracted for Caching.
    Arguments must be hashable/serializable.
    """
    import streamlit as st
    # AssistantModule is available in global scope (defined in this file)
    
    try:
        if df is None or df.empty:
            return _get_insights_from_database()
            
        assistant = AssistantModule()
        # Ensure we don't mutate the input cache
        df_proc = df.copy()
        
        # Inject config into session state mock if needed by AssistantModule
        # (AssistantModule reads session state in _compute_account_health, so we might need to handle that)
        # Actually, AssistantModule reads `st.session_state.get('opt_target_roas', 3.0)` widely.
        # Since we are inside a cached function, st.session_state access is tricky (it captures state at first run).
        # BETTER: We modify AssistantModule to accept overrides, OR we set the state here temporarily?
        # No, `st.cache_data` functions CAN access st.session_state, but the dependency tracking is key.
        # To be safe, we passed `target_roas` as arg.
        # We need to verify AssistantModule uses it.
        # Checking code: `target_roas = st.session_state.get('opt_target_roas', 3.0)` in `_compute_account_health`
        # We can't easily change AssistantModule right now without big refactor.
        # BUT, since we passed target_roas in args, Streamlit knows to invalidate if that arg changes.
        # The internal read will read the current session state.
        
        knowledge = assistant._build_knowledge_graph(df_proc)
        
        # Now process signals (logic extracted from original function)
        signals = []
        
        # 1. Account Health Signals
        health = knowledge.get('account_health', {})
        if health:
            roas_score = health.get('roas_score', 0)
            waste_score = health.get('waste_score', 0)
            wasted_spend = health.get('wasted_spend', 0)
            
            # Get target ROAS for fallback calculation
            # Use the passed target_roas for consistency with cache invalidation
            actual_roas = health.get('actual_roas', roas_score * target_roas / 100)
            
            # ROAS signal
            if roas_score >= 100:
                signals.append({
                    "type": "positive", "category": "Growth", "strength": roas_score,
                    "title": f"ROAS at {actual_roas:.1f}x", "subtitle": "Strong profitability",
                    "icon_type": "success"
                })
            elif roas_score >= 80:
                signals.append({
                    "type": "positive", "category": "Growth", "strength": roas_score,
                    "title": f"ROAS at {actual_roas:.1f}x", "subtitle": "Healthy returns",
                    "icon_type": "info"
                })
            else:
                signals.append({
                    "type": "watch", "category": "Risk", "strength": 100 - roas_score,
                    "title": f"ROAS at {actual_roas:.1f}x", "subtitle": "Below target",
                    "icon_type": "warning"
                })
            
            # Efficiency signal
            if waste_score >= 70:
                signals.append({
                    "type": "positive", "category": "Efficiency", "strength": waste_score,
                    "title": f"{waste_score:.0f}% efficient", "subtitle": "Low waste",
                    "icon_type": "success"
                })
            elif waste_score >= 50:
                signals.append({
                    "type": "positive", "category": "Efficiency", "strength": waste_score,
                    "title": f"{waste_score:.0f}% efficient", "subtitle": "Room to optimize",
                    "icon_type": "info"
                })
            else:
                signals.append({
                    "type": "watch", "category": "Risk", "strength": 100 - waste_score,
                    "title": f"{currency} {wasted_spend:,.0f} efficiency gap", "subtitle": "Spend optimization needed",
                    "icon_type": "warning"
                })
        
        # 2. Strategic Insights Signals
        strategic = knowledge.get('strategic_insights', [])
        for insight in strategic:
            insight_type = insight.get('type', '')
            # severity = insight.get('severity', 'low') # Not used in original logic
            
            if insight_type == 'untapped_scalers':
                potential = insight.get('potential_additional_sales', 0)
                signals.append({
                    "type": "positive", "category": "Opportunity", "strength": 85,
                    "title": f"{currency} {potential:,.0f} growth potential", "subtitle": "Scaling opportunities found",
                    "icon_type": "success"
                })
            
            elif insight_type == 'high_spend_zero_return':
                wasted = insight.get('total_wasted', 0)
                if wasted > 100:
                    signals.append({
                        "type": "watch", "category": "Risk", "strength": min(95, wasted / 10),
                        "title": f"{currency} {wasted:,.0f} bleed detected", "subtitle": "Top wasters identified",
                        "icon_type": "warning"
                    })
            
            elif insight_type == 'harvest_negative_paradox':
                count = len(insight.get('terms', []))
                if count > 0:
                    signals.append({
                        "type": "watch", "category": "Efficiency", "strength": 60,
                        "title": f"{count} split terms", "subtitle": "Segmentation opportunity",
                        "icon_type": "note"
                    })
            
            elif insight_type == 'campaign_bleeders':
                bleed = insight.get('total_bleed', 0)
                if bleed > 100:
                    signals.append({
                        "type": "watch", "category": "Risk", "strength": min(90, bleed / 10),
                        "title": f"{currency} {bleed:,.0f} campaign bleed", "subtitle": "Net-negative campaigns",
                        "icon_type": "warning"
                    })
        
        # 3. Optimization Opportunities
        opps = health.get('optimization_opportunities', {})
        harvest_count = opps.get('harvest_candidates', 0)
        negative_count = opps.get('negative_candidates', 0)
        
        if harvest_count > 10:
            signals.append({
                "type": "positive", "category": "Opportunity", "strength": min(80, harvest_count),
                "title": f"{harvest_count} harvests ready", "subtitle": "Keywords to promote",
                "icon_type": "success"
            })
        
        if negative_count > 20:
            signals.append({
                "type": "watch", "category": "Efficiency", "strength": min(75, negative_count / 2),
                "title": f"{negative_count} negatives pending", "subtitle": "Cleanup recommended",
                "icon_type": "note"
            })
            
        if not signals:
            return _get_insights_from_database()
            
        # Sort by strength descending
        signals.sort(key=lambda x: x['strength'], reverse=True)
        
        # Select top 2 positives + top 1 watch
        positives = [s for s in signals if s['type'] == 'positive'][:2]
        watches = [s for s in signals if s['type'] == 'watch'][:1]
        
        result = positives + watches
        
        # Fill remaining slots
        while len(result) < 3:
            if len(positives) < 2 and watches:
                result.append(watches.pop(0))
            elif signals:
                # Add from remaining signals if any, prioritizing higher strength
                remaining_signals = [s for s in signals if s not in result]
                if remaining_signals:
                    remaining_signals.sort(key=lambda x: x['strength'], reverse=True)
                    result.append(remaining_signals.pop(0))
                else:
                    # Default fill if no more unique signals
                    defaults = _get_insights_from_database()
                    result.append(defaults[len(result)])
            else:
                 # Default fill
                defaults = _get_insights_from_database()
                result.append(defaults[len(result)])
        
        return result[:3]
        
    except Exception as e:
        print(f"DEBUG: Error in cached insights core: {str(e)}")
        # import traceback
        # traceback.print_exc()
        return _get_insights_from_database()

def _get_insights_from_database() -> list:
    """Fallback: Try to get last valid insights from DB or return defaults."""
    default_insights = [
        {"type": "positive", "title": "Ready to analyze", "subtitle": "Upload data to start", "icon_type": "info", "strength": 0},
        {"type": "positive", "title": "Optimizer available", "subtitle": "Run to get recommendations", "icon_type": "info", "strength": 0},
        {"type": "watch", "title": "Impact tracking", "subtitle": "Configure and run", "icon_type": "note", "strength": 0}
    ]
    return default_insights

