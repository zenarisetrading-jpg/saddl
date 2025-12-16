"""
Data Hub UI Page

Upload all files in one place, use everywhere.
"""

import streamlit as st
from core.data_hub import DataHub

def render_data_hub():
    """Render the data hub upload interface."""
    
    st.title("📂 Data Hub")
    st.markdown("Upload your files once, use across all features")
    
    # ===========================================
    # ACCOUNT CONTEXT BANNER
    # ===========================================
    active_account_id = st.session_state.get('active_account_id')
    active_account_name = st.session_state.get('active_account_name', 'No account selected')
    
    if not active_account_id:
        st.error("⚠️ **No account selected!** Please select or create an account in the sidebar.")
        return
    
    # Show active account with prominent styling
    st.info(f"📍 **Uploading to Account:** {active_account_name}")
    
    # Initialize data hub
    hub = DataHub()
    
    # Status overview at top
    status = hub.get_upload_status()
    summary = hub.get_summary()
    
    # Status cards
    st.markdown("### 📊 Upload Status")
    
    def _render_card(title, is_active, metric, is_required=False, icon="📄", upload_time=None):
        """Helper to render a file status card with staleness indicator."""
        from datetime import datetime, timedelta
        
        border_color = "#10b981" if is_active else "#334155"
        bg_color = "rgba(16, 185, 129, 0.1)" if is_active else "rgba(30, 41, 59, 0.5)"
        text_color = "#ffffff" if is_active else "#94a3b8"
        status_text = "ACTIVE" if is_active else "MISSING"
        status_color = "#10b981" if is_active else "#94a3b8"
        
        # Staleness check (>3 weeks = stale)
        stale_warning = ""
        time_badge = ""
        if upload_time:
            days_ago = (datetime.now() - upload_time).days
            if days_ago > 21:  # 3 weeks
                border_color = "#f59e0b"  # Orange for stale
                stale_warning = f'<div style="color: #f59e0b; font-size: 11px; margin-top: 5px;">⚠️ {days_ago}d old (stale)</div>'
                time_badge = f'<span style="background: #f59e0b; color: white; padding: 2px 6px; border-radius: 4px; font-size: 10px; margin-left: 4px;">STALE</span>'
            else:
                time_badge = f'<span style="color: #94a3b8; font-size: 10px; margin-left: 4px;">{days_ago}d ago</span>'
        
        req_badge = ""
        if is_required:
            req_badge = '<span style="background: #ef4444; color: white; padding: 2px 6px; border-radius: 4px; font-size: 10px; margin-left: 8px;">REQUIRED</span>'
        else:
            req_badge = '<span style="background: #475569; color: #cbd5e1; padding: 2px 6px; border-radius: 4px; font-size: 10px; margin-left: 8px;">OPTIONAL</span>'

        html = f"""
<div style="border: 1px solid {border_color}; background-color: {bg_color}; border-radius: 8px; padding: 15px; min-height: 140px;">
    <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 10px;">
        <span style="font-size: 24px;">{icon}</span>
        <span style="color: {status_color}; font-size: 11px; font-weight: bold; letter-spacing: 1px;">{status_text}</span>
    </div>
    <div style="font-weight: 600; font-size: 14px; margin-bottom: 8px; color: #ffffff;">{title}</div>
    <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 8px; flex-wrap: wrap;">{req_badge}{time_badge}</div>
    <div style="color: {text_color}; font-size: 13px; margin-top: 10px;">{metric}</div>
    {stale_warning}
</div>
"""
        return html

    # Get timestamps
    timestamps = st.session_state.unified_data.get('upload_timestamps', {})
    
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        if status['search_term_report']:
            metric = f"{summary.get('search_terms', 0):,} rows"
        else:
            metric = "No data"
        st.markdown(_render_card("Search Terms", status['search_term_report'], metric, True, "🔎", timestamps.get('search_term_report')), unsafe_allow_html=True)
        
    with c2:
        if status['advertised_product_report']:
            metric = f"{summary.get('unique_asins', 0):,} ASINs"
        else:
            metric = "No data"
        st.markdown(_render_card("Advertised Products", status['advertised_product_report'], metric, False, "📦", timestamps.get('advertised_product_report')), unsafe_allow_html=True)

    with c3:
        if status['bulk_id_mapping']:
            metric = f"{summary.get('mapped_campaigns', 0):,} Campaigns"
        else:
            metric = "No data"
        st.markdown(_render_card("Bulk ID Map", status['bulk_id_mapping'], metric, False, "🆔", timestamps.get('bulk_id_mapping')), unsafe_allow_html=True)
        
    with c4:
        if status['category_mapping']:
            metric = f"{summary.get('categorized_skus', 0):,} SKUs"
        else:
            metric = "No data"
        st.markdown(_render_card("Category Map", status['category_mapping'], metric, False, "🏷️", timestamps.get('category_mapping')), unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Upload sections
    st.markdown("### 📥 Upload Files")
    
    # Required: Search Term Report
    with st.expander("🔴 Search Term Report (Required)", expanded=not status['search_term_report']):
        st.markdown("""
        **What:** Your main advertising data with search terms and performance metrics
        
        **Where to get it:**
        1. Go to Amazon Advertising Console
        2. Navigate to: **Reports → Search Term Report**
        3. Select date range (recommended: last 30 days)
        4. Download as CSV or Excel
        
        **Contains:**
        - Search terms customers used
        - Impressions, Clicks, Spend, Orders
        - Campaign and Ad Group names
        - ACOS, ROAS metrics
        """)
        
        if status['search_term_report']:
            st.success(f"✅ Already loaded: {summary.get('search_terms', 0):,} rows")
            if st.button("🔄 Replace Search Term Report", key="replace_str"):
                st.session_state.unified_data['upload_status']['search_term_report'] = False
                st.rerun()
        else:
            str_file = st.file_uploader(
                "Upload Search Term Report",
                type=['csv', 'xlsx', 'xls'],
                key='str_upload',
                help="Amazon Advertising Console → Reports → Search Term Report"
            )
            
            if str_file:
                # SAFEGUARD: Upload confirmation checkbox
                st.warning(f"⚠️ **Confirm Upload Location**")
                st.markdown(f"You are uploading to account: **{active_account_name}**")
                
                confirm = st.checkbox(
                    f"✅ I confirm this data belongs to **{active_account_name}**",
                    key="confirm_str_upload",
                    help="This ensures data is not uploaded to the wrong account"
                )
                
                if confirm:
                    with st.spinner("Processing & validating..."):
                        success, message = hub.upload_search_term_report(str_file)
                        if success:
                            # CAMPAIGN VALIDATION
                            validation_result = _validate_campaigns(hub, active_account_id)
                            
                            if validation_result['needs_review']:
                                st.warning(f"⚠️ **Campaign Mismatch Detected**")
                                st.markdown(f"""
                                **Overlap:** {validation_result['overlap_pct']:.1f}%  
                                **New Campaigns:** {validation_result['new_count']}  
                                **Missing Campaigns:** {validation_result['missing_count']}
                                
                                This might indicate:
                                - Wrong account selected
                                - New campaign launches
                                - Renamed campaigns
                                """)
                                
                                proceed = st.checkbox("✅ This is correct, proceed anyway", key="override_validation")
                                if proceed:
                                    st.success(f"✅ {message}")
                                else:
                                    st.info("Upload paused - fix account selection or confirm to proceed")
                            else:
                                st.success(f"✅ {message}")
                                if validation_result['overlap_pct'] == 100:
                                    st.success(f"✅ All campaigns match historical data ({validation_result['total_historical']} campaigns)")
                        else:
                            st.error(f"❌ {message}")
                else:
                    st.info("👆 Please confirm the upload account to proceed")
    
    # Optional: Advertised Product Report
    with st.expander("🟡 Advertised Product Report (Optional)", expanded=False):
        st.markdown("""
        **What:** List of products you're advertising with their ASINs/SKUs
        
        **Where to get it:**
        1. Go to Amazon Advertising Console
        2. Navigate to: **Reports → Advertised Product Report**
        3. Select same date range as Search Term Report
        4. Download as CSV or Excel
        
        **Why upload:**
        - Links search terms to specific products
        - Enables product-level analysis
        - Shows which SKUs tie to which clusters
        - Helps categorize your ASINs vs competitors
        """)
        
        if status['advertised_product_report']:
            st.success(f"✅ Already loaded: {summary.get('unique_asins', 0):,} ASINs")
            if st.button("🔄 Replace Advertised Product Report", key="replace_adv"):
                st.session_state.unified_data['upload_status']['advertised_product_report'] = False
                st.rerun()
        else:
            adv_file = st.file_uploader(
                "Upload Advertised Product Report",
                type=['csv', 'xlsx', 'xls'],
                key='adv_upload',
                help="Amazon Advertising Console → Reports → Advertised Product Report"
            )
            
            if adv_file:
                with st.spinner("Processing..."):
                    success, message = hub.upload_advertised_product_report(adv_file)
                    if success:
                        st.success(f"✅ {message}")
                    else:
                        st.error(f"❌ {message}")
    
    # Optional: Bulk Upload ID Mapping
    with st.expander("🟡 Bulk Upload ID Mapping (Optional)", expanded=False):
        st.markdown("""
        **What:** File that maps Campaign Names/Ad Group Names to their IDs
        
        **Where to get it:**
        1. Go to Amazon Advertising Console
        2. Navigate to: **Bulk Operations → Download**
        3. Select campaigns you want to update
        4. Download the bulk file
        
        **Why upload:**
        - Enables bid updates (need Campaign ID, Ad Group ID)
        - Required for generating bulk upload files
        - Maps friendly names to numeric IDs
        """)
        
        if status['bulk_id_mapping']:
            st.success(f"✅ Already loaded: {summary.get('mapped_campaigns', 0):,} campaigns")
            if st.button("🔄 Replace Bulk ID Mapping", key="replace_bulk"):
                st.session_state.unified_data['upload_status']['bulk_id_mapping'] = False
                st.rerun()
        else:
            bulk_file = st.file_uploader(
                "Upload Bulk Upload File",
                type=['csv', 'xlsx', 'xls'],
                key='bulk_upload',
                help="Amazon Advertising Console → Bulk Operations → Download"
            )
            
            if bulk_file:
                with st.spinner("Processing..."):
                    success, message = hub.upload_bulk_id_mapping(bulk_file)
                    if success:
                        st.success(f"✅ {message}")
                    else:
                        st.error(f"❌ {message}")
    
    # Optional: Category Mapping
    with st.expander("🟡 Internal Category Mapping (Optional)", expanded=False):
        st.markdown("""
        **What:** Your internal SKU categorization (Category, Subcategory, Brand, etc.)
        
        **Where to get it:**
        - Your internal inventory system
        - Your product catalog spreadsheet
        - Any file mapping SKUs to categories
        
        **Why upload:**
        - Group performance by category
        - Analyze subcategory trends
        - Filter by product line
        """)
        
        if status['category_mapping']:
            st.success(f"✅ Already loaded: {summary.get('categorized_skus', 0):,} SKUs")
            if st.button("🔄 Replace Category Mapping", key="replace_cat"):
                st.session_state.unified_data['upload_status']['category_mapping'] = False
                st.rerun()
        else:
            cat_file = st.file_uploader(
                "Upload Category Mapping",
                type=['csv', 'xlsx', 'xls'],
                key='cat_upload',
                help="Your internal SKU categorization file"
            )
            
            if cat_file:
                with st.spinner("Processing..."):
                    success, message = hub.upload_category_mapping(cat_file)
                    if success:
                        st.success(f"✅ {message}")
                    else:
                        st.error(f"❌ {message}")
    
    st.markdown("---")
    
    # NEW Data Summary Dashboard
    if status['search_term_report']:
        st.subheader("📊 Dataset Overview")
        
        # Import styled component
        from ui.components import metric_card
        from utils.formatters import format_currency

        # Calculate Dataset Totals
        total_search_terms = len(summary.get('search_terms_list', [])) if summary.get('search_terms_list') else summary.get('search_terms', 0)
        total_campaigns = 0
        total_clicks = 0
        total_orders = 0
        
        # Get all metrics from enriched_data
        enriched = st.session_state.unified_data.get('enriched_data')
        if enriched is not None and not enriched.empty:
            # Use safe_numeric to handle any data type issues
            from core.data_loader import safe_numeric
            total_clicks = safe_numeric(enriched.get('Clicks', enriched.get('clicks', 0))).sum()
            total_orders = safe_numeric(enriched.get('Orders', enriched.get('orders', 0))).sum()
            
            # Count unique campaigns
            if 'Campaign Name' in enriched.columns:
                total_campaigns = enriched['Campaign Name'].nunique()
            elif 'campaign_name' in enriched.columns:
                total_campaigns = enriched['campaign_name'].nunique()
        
        # Spend robust parsing
        spend_val = summary.get('total_spend', 0)
        try:
            if isinstance(spend_val, str):
                spend_val = float(str(spend_val).replace(',', '').replace('AED', '').strip())
        except:
            spend_val = 0
            
        # Global CVR
        global_cvr = (total_orders / total_clicks * 100) if total_clicks > 0 else 0
        
        # Render Cards
        c1, c2, c3, c4 = st.columns(4)
        with c1: metric_card("Search Terms", f"{total_search_terms:,}", border_color="#6366f1")
        with c2: metric_card("Total Spend", format_currency(spend_val), border_color="#10b981")
        with c3: metric_card("Global CVR", f"{global_cvr:.2f}%", border_color="#f59e0b")
        with c4: metric_card("Campaigns", f"{total_campaigns:,}", border_color="#3b82f6")
        
        st.divider()

        # NEW "System Ready" Status Board
        st.subheader("🚀 System Readiness")
        
        status_col, action_col = st.columns([2, 1])
        
        with status_col:
            st.markdown("""
            <div style="background-color: rgba(16, 185, 129, 0.1); border: 1px solid #10b981; border-radius: 8px; padding: 20px;">
                <h3 style="color: #10b981; margin-top: 0;">✅ System Active & Ready</h3>
                <p>Your data has been processed and indexed. All features are now unlocked.</p>
                <ul style="list-style-type: none; padding-left: 0;">
                    <li>✅ <b>ASIN Intent Mapper</b> <span style="opacity:0.7"> (Uses STR + Products)</span></li>
                    <li>✅ <b>AI Campaign Insights</b> <span style="opacity:0.7"> (Uses Search Terms)</span></li>
                    <li>✅ <b>Optimization Engine</b> <span style="opacity:0.7"> (Uses Bids + Performance)</span></li>
                    <li>✅ <b>Campaign Launcher</b> <span style="opacity:0.7"> (Uses Harvest Logic)</span></li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
        with action_col:
            st.markdown("#### Instant Actions")
            if st.button("🔎 Analyze Intent (ASINs)", use_container_width=True):
                st.session_state['current_module'] = 'asin_mapper'
                st.rerun()
            
            if st.button("⚡ Run Optimizer", use_container_width=True):
                st.session_state['current_module'] = 'optimizer'
                st.rerun()
                
            if st.button("🧠 Ask AI Strategist", use_container_width=True):
                st.session_state['current_module'] = 'assistant'  # Triggers floating via main
                # We don't have a full page for assistant, but user can open bubble
                st.info("Click the chat bubble ↘️")

    else:
        # Empty State
        st.info("👋 **Start Here:** Upload your **Search Term Report** above to unlock the dashboard.")
    
    # DATA REASSIGNMENT TOOL
    st.markdown("---")
    with st.expander("🔧 **Admin Tools: Data Reassignment**", expanded=False):
        st.markdown("### Move Data Between Accounts")
        st.warning("⚠️ **Use with caution!** This permanently moves data from one account to another.")
        
        # Get all accounts (Registered + Historical)
        db = st.session_state.get('db_manager')
        if db:
            # 1. Registered Accounts
            registered_accounts = db.get_all_accounts()
            account_options = {name: acc_id for acc_id, name, _ in registered_accounts}
            
            # 2. Historical/Ghost Accounts (present in data but not registerd)
            with db._get_connection() as conn:
                cursor = conn.cursor()
                # Get IDs from stats
                cursor.execute("SELECT DISTINCT client_id FROM target_stats")
                stats_ids = {row[0] for row in cursor.fetchall()}
                # Get IDs from logs
                cursor.execute("SELECT DISTINCT client_id FROM actions_log")
                log_ids = {row[0] for row in cursor.fetchall()}
                
                ghost_ids = (stats_ids | log_ids) - set(account_options.values())
                
                for gid in ghost_ids:
                    account_options[f"{gid} (Legacy)"] = gid
            
            col1, col2 = st.columns(2)
            with col1:
                from_name = st.selectbox("From Account", list(account_options.keys()), key="reassign_from")
            with col2:
                to_name = st.selectbox("To Account", list(account_options.keys()), key="reassign_to")
            
            from_id = account_options[from_name]
            to_id = account_options[to_name]
            
            # Date range selection
            st.markdown("**Select Date Range to Move:**")
            col3, col4 = st.columns(2)
            with col3:
                start_date = st.date_input("Start Date", key="reassign_start")
            with col4:
                end_date = st.date_input("End Date", key="reassign_end")
            
            # Preview what will be moved
            if st.button("Preview Data to Move", key="preview_reassign"):
                st.session_state['reassign_preview_active'] = True
                
            if st.session_state.get('reassign_preview_active', False):
                try:
                    with db._get_connection() as conn:
                        cursor = conn.cursor()
                        # Count Stats
                        cursor.execute('''
                            SELECT COUNT(*), SUM(spend), SUM(sales)
                            FROM target_stats
                            WHERE client_id = ? AND start_date BETWEEN ? AND ?
                        ''', (from_id, str(start_date), str(end_date)))
                        count, spend, sales = cursor.fetchone()
                        
                        # Count Actions
                        cursor.execute('''
                            SELECT COUNT(*)
                            FROM actions_log
                            WHERE client_id = ? AND DATE(action_date) BETWEEN ? AND ?
                        ''', (from_id, str(start_date), str(end_date)))
                        actions_count = cursor.fetchone()[0]
                        
                    if (count and count > 0) or (actions_count and actions_count > 0):
                        st.info(f"""
                        **Preview:**
                        - **{count:,} rows** of performance data
                        - **{actions_count:,} optimization actions**
                        - **AED {spend:,.2f}** total spend
                        - **AED {sales:,.2f}** total sales
                        - From: **{from_name}** → To: **{to_name}**
                        """)
                        
                        col_confirm_1, col_confirm_2 = st.columns([3, 1])
                        
                        with col_confirm_1:
                            # Final confirmation
                            confirm_move = st.checkbox(f"✅ I confirm moving this data", key="final_reassign_confirm")
                            
                            if confirm_move and st.button("Execute Move", type="primary", key="execute_reassign"):
                                success = db.reassign_data(from_id, to_id, str(start_date), str(end_date))
                                if success:
                                    st.success(f"✅ Moved {count:,} stats and {actions_count:,} actions!")
                                    st.info("💡 Switch accounts to see the updated data")
                                    # Clear state after success so it resets
                                    del st.session_state['reassign_preview_active']
                                    st.button("Close") # Trigger rerun to clean up
                                else:
                                    st.error("❌ Failed to reassign data")
                        
                        with col_confirm_2:
                            if st.button("Cancel & Clear"):
                                del st.session_state['reassign_preview_active']
                                st.rerun()
                                
                    else:
                        st.warning(f"No data found for **{from_name}** in the selected date range")
                        if st.button("Close"):
                            del st.session_state['reassign_preview_active']
                            st.rerun()
                            
                except Exception as e:
                    st.error(f"Error: {e}")
    
    # Clear all button (Footer)
    if any(status.values()):
        st.markdown("---")
        if st.button("🗑️ Reset & Clear Data", type="secondary"):
            hub.clear_all()
            st.success("Data cleared.")
            st.rerun()


def _validate_campaigns(hub: DataHub, account_id: str) -> dict:
    """
    Validate uploaded campaigns against historical data for this account.
    Returns dict with validation results.
    """
    from core.db_manager import get_db_manager
    
    # Get newly uploaded campaigns
    uploaded_data = hub.get_data('search_term_report')
    if uploaded_data is None or 'Campaign Name' not in uploaded_data.columns:
        return {'needs_review': False, 'overlap_pct': 100}
    
    uploaded_campaigns = set(uploaded_data['Campaign Name'].dropna().unique())
    
    # Get historical campaigns for this account from database
    try:
        db = get_db_manager(st.session_state.get('test_mode', False))
        with db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT DISTINCT campaign_name 
                FROM target_stats 
                WHERE client_id = ?
            ''', (account_id,))
            historical_campaigns = set(row[0] for row in cursor.fetchall())
    except:
        # No historical data or error - skip validation
        return {'needs_review': False, 'overlap_pct': 100}
    
    if not historical_campaigns:
        # First upload for this account - no validation needed
        return {'needs_review': False, 'overlap_pct': 100, 'first_upload': True}
    
    # Calculate overlap
    overlap = uploaded_campaigns & historical_campaigns
    new_campaigns = uploaded_campaigns - historical_campaigns
    missing_campaigns = historical_campaigns - uploaded_campaigns
    
    overlap_pct = (len(overlap) / len(historical_campaigns) * 100) if historical_campaigns else 100
    
    # Flag for review if overlap is less than 30%
    needs_review = overlap_pct < 30
    
    return {
        'needs_review': needs_review,
        'overlap_pct': overlap_pct,
        'new_count': len(new_campaigns),
        'missing_count': len(missing_campaigns),
        'total_uploaded': len(uploaded_campaigns),
        'total_historical': len(historical_campaigns),
        'overlap_campaigns': overlap,
        'new_campaigns': new_campaigns,
        'missing_campaigns': missing_campaigns
    }
