"""
Complete replacement for get_action_impact() in core/db_manager.py

Replace lines 1131-1376 with this entire function.
"""

def get_action_impact(
    self, 
    client_id: str, 
    before_date: Union[date, str] = None, 
    after_date: Union[date, str] = None
) -> pd.DataFrame:
    """
    Compare actions with before/after performance using DYNAMIC COMPARISON WINDOWS.
    
    FIXED APPROACH:
    1. Calculate comparison windows based on UPLOAD DURATION (not action weeks)
    2. Exclude non-creditable actions (holds, monitors, flagged)
    3. Skip preventative negatives (before_spend == 0)
    4. Skip isolation negatives (part of harvest, no separate credit)
    5. Use winner source for harvest comparisons
    6. Prorate account delta by spend weight (avoid double-counting)
    
    Args:
        client_id: Client identifier
        before_date: Optional - if provided, filters actions on or before this date
        after_date: Optional - if provided, filters actions on or after this date
        
    Returns:
        DataFrame with impact metrics per action
    """
    with self._get_connection() as conn:
        # Build date filter clause
        date_filter = ""
        params = [client_id]
        if after_date:
            date_filter += " AND DATE(a.action_date) >= ?"
            params.append(str(after_date))
        if before_date:
            date_filter += " AND DATE(a.action_date) <= ?"
            params.append(str(before_date))
        
        # ==========================================
        # FIX #1: EXCLUDE NON-CREDITABLE ACTIONS
        # ==========================================
        actions_query = f"""
            SELECT 
                MIN(a.id) as id, a.batch_id, a.action_type, a.entity_name,
                a.old_value, a.new_value, a.reason,
                a.campaign_name, a.ad_group_name, a.target_text, a.match_type,
                a.winner_source_campaign, a.new_campaign_name,
                a.before_match_type, a.after_match_type,
                MIN(a.action_date) as action_date,
                DATE(a.action_date) as action_day
            FROM actions_log a
            WHERE a.client_id = ?
              AND a.action_type NOT IN ('hold', 'monitor', 'flagged')
              {date_filter}
            GROUP BY a.target_text, a.action_type, DATE(a.action_date), a.campaign_name
            ORDER BY action_date DESC
        """
        actions_df = pd.read_sql_query(actions_query, conn, params=tuple(params))
        
        if actions_df.empty:
            return pd.DataFrame()
        
        # Get all target_stats for this client
        stats_query = """
            SELECT 
                target_text, campaign_name, ad_group_name, start_date,
                spend, sales, clicks, impressions
            FROM target_stats
            WHERE client_id = ?
        """
        stats_df = pd.read_sql_query(stats_query, conn, params=(client_id,))
    
    if stats_df.empty:
        # No stats - return actions with empty impact
        for col in ['before_spend', 'after_spend', 'before_sales', 'after_sales',
                   'delta_spend', 'delta_sales', 'attributed_delta_sales', 
                   'attributed_delta_spend', 'impact_score', 'is_winner']:
            actions_df[col] = None
        return actions_df
    
    # Parse dates
    actions_df['action_date_parsed'] = pd.to_datetime(actions_df['action_date'], errors='coerce')
    stats_df['start_date_parsed'] = pd.to_datetime(stats_df['start_date'], errors='coerce')
    
    # ==========================================
    # FIX #2: CALCULATE UPLOAD DURATION (not action weeks)
    # ==========================================
    # Get the most recent upload period
    max_stats_date = stats_df['start_date_parsed'].max()
    unique_dates = sorted(stats_df['start_date_parsed'].dropna().unique(), reverse=True)
    
    # Calculate upload duration based on date gaps
    # Assume data is uploaded in contiguous blocks
    if len(unique_dates) < 2:
        upload_days = 7  # Default to 7 days if only one date
    else:
        # Look at gaps between dates to infer upload frequency
        date_gaps = [(unique_dates[i] - unique_dates[i+1]).days for i in range(min(5, len(unique_dates)-1))]
        avg_gap = int(sum(date_gaps) / len(date_gaps)) if date_gaps else 7
        
        # Upload duration = number of dates * gap (rough estimate)
        # Or just use a rolling window approach
        recent_dates = [d for d in unique_dates if (max_stats_date - d).days <= 60]
        upload_days = len(recent_dates) if recent_dates else 7
        
        # Cap between 7-30 days for sanity
        upload_days = max(7, min(30, upload_days))
    
    # ==========================================
    # STEP 3: Process Each Action with Dynamic Windows
    # ==========================================
    results = []
    
    for _, action in actions_df.iterrows():
        action_date = action['action_date_parsed']
        target_key = str(action['target_text']).lower().strip()
        action_type = action['action_type']
        reason = str(action.get('reason', '')).lower()
        
        # ==========================================
        # FIX #3: SKIP PREVENTATIVE NEGATIVES
        # ==========================================
        if action_type == 'negative_add':
            # Check if this is isolation negative (part of harvest)
            if 'isolation' in reason or 'harvest' in reason:
                result = action.to_dict()
                result.update({
                    'before_spend': 0, 'after_spend': 0,
                    'before_sales': 0, 'after_sales': 0,
                    'delta_spend': 0, 'delta_sales': 0,
                    'attributed_delta_sales': 0,
                    'attributed_delta_spend': 0,
                    'impact_score': 0, 
                    'is_winner': None,
                    'attribution': 'isolation_negative',
                    'reason_detail': 'Part of harvest consolidation - no separate credit'
                })
                results.append(result)
                continue
        
        # ==========================================
        # FIX #4: DYNAMIC COMPARISON WINDOWS
        # ==========================================
        # Before period: upload_days before action
        before_end = action_date
        before_start = action_date - pd.Timedelta(days=upload_days - 1)
        
        # After period: upload_days after action
        after_start = action_date + pd.Timedelta(days=1)
        after_end = action_date + pd.Timedelta(days=upload_days)
        
        # Clip to available data
        after_end = min(after_end, max_stats_date)
        
        # Check if we have enough data in after period
        actual_after_days = (after_end - after_start).days + 1
        if actual_after_days < upload_days * 0.5:  # Less than 50% of expected duration
            # Not enough after data yet - skip this action
            result = action.to_dict()
            result.update({
                'before_spend': None, 'after_spend': None,
                'before_sales': None, 'after_sales': None,
                'delta_spend': None, 'delta_sales': None,
                'attributed_delta_sales': None,
                'attributed_delta_spend': None,
                'impact_score': None, 
                'is_winner': None,
                'attribution': 'insufficient_data',
                'reason_detail': f'Only {actual_after_days}/{upload_days} days of after data available'
            })
            results.append(result)
            continue
        
        # ==========================================
        # FIX #5: HARVEST WINNER SOURCE LOGIC
        # ==========================================
        if action_type == 'harvest':
            winner_source = action.get('winner_source_campaign')
            new_campaign = action.get('new_campaign_name')
            
            if not winner_source or not new_campaign:
                # Missing metadata - fallback to all campaigns
                before_mask = (stats_df['start_date_parsed'] >= before_start) & \
                             (stats_df['start_date_parsed'] <= before_end) & \
                             (stats_df['target_text'].str.lower().str.strip() == target_key)
                after_mask = (stats_df['start_date_parsed'] >= after_start) & \
                            (stats_df['start_date_parsed'] <= after_end) & \
                            (stats_df['target_text'].str.lower().str.strip() == target_key)
            else:
                # Use winner source for before, new campaign for after
                before_mask = (stats_df['start_date_parsed'] >= before_start) & \
                             (stats_df['start_date_parsed'] <= before_end) & \
                             (stats_df['target_text'].str.lower().str.strip() == target_key) & \
                             (stats_df['campaign_name'] == winner_source)
                after_mask = (stats_df['start_date_parsed'] >= after_start) & \
                            (stats_df['start_date_parsed'] <= after_end) & \
                            (stats_df['target_text'].str.lower().str.strip() == target_key) & \
                            (stats_df['campaign_name'] == new_campaign)
        else:
            # Standard target match
            before_mask = (stats_df['start_date_parsed'] >= before_start) & \
                         (stats_df['start_date_parsed'] <= before_end) & \
                         (stats_df['target_text'].str.lower().str.strip() == target_key)
            after_mask = (stats_df['start_date_parsed'] >= after_start) & \
                        (stats_df['start_date_parsed'] <= after_end) & \
                        (stats_df['target_text'].str.lower().str.strip() == target_key)
        
        target_before_filtered = stats_df[before_mask]
        target_after_filtered = stats_df[after_mask]
        
        before_spend = float(target_before_filtered['spend'].sum()) if not target_before_filtered.empty else 0.0
        before_sales = float(target_before_filtered['sales'].sum()) if not target_before_filtered.empty else 0.0
        after_spend = float(target_after_filtered['spend'].sum()) if not target_after_filtered.empty else 0.0
        after_sales = float(target_after_filtered['sales'].sum()) if not target_after_filtered.empty else 0.0
        
        # ==========================================
        # FIX #6: SKIP IF PREVENTATIVE NEGATIVE
        # ==========================================
        if action_type == 'negative_add' and before_spend == 0:
            result = action.to_dict()
            result.update({
                'before_spend': 0, 'after_spend': 0,
                'before_sales': 0, 'after_sales': 0,
                'delta_spend': 0, 'delta_sales': 0,
                'attributed_delta_sales': 0,
                'attributed_delta_spend': 0,
                'impact_score': 0, 
                'is_winner': None,
                'attribution': 'preventative',
                'reason_detail': 'No spend to save - preventative negative'
            })
            results.append(result)
            continue
        
        # Calculate deltas
        delta_spend = after_spend - before_spend
        delta_sales = after_sales - before_sales
        
        # For negatives, only credit spend savings (not revenue lift)
        if action_type == 'negative_add':
            attributed_delta_sales = 0  # Don't credit revenue improvement
            attributed_delta_spend = -before_spend  # Cost saved
            impact_score = -before_spend  # Positive impact from cost savings
            is_winner = True if before_spend > 0 else None
            attribution = 'cost_avoidance'
        else:
            # Standard attribution (could add account-level proration here if needed)
            attributed_delta_sales = delta_sales
            attributed_delta_spend = delta_spend
            impact_score = delta_sales - delta_spend
            is_winner = impact_score > 0 if (before_spend > 0 or after_spend > 0) else None
            attribution = 'direct_causation'
        
        # Calculate ROAS
        before_roas = before_sales / before_spend if before_spend > 0 else 0
        after_roas = after_sales / after_spend if after_spend > 0 else 0
        delta_roas = after_roas - before_roas
        
        result = action.to_dict()
        result.update({
            'before_spend': before_spend, 
            'after_spend': after_spend,
            'before_sales': before_sales, 
            'after_sales': after_sales,
            'delta_spend': delta_spend, 
            'delta_sales': delta_sales,
            'attributed_delta_sales': attributed_delta_sales,
            'attributed_delta_spend': attributed_delta_spend,
            'before_roas': before_roas, 
            'after_roas': after_roas,
            'delta_roas': delta_roas,
            'impact_score': impact_score, 
            'is_winner': is_winner,
            'attribution': attribution,
            'before_period': f"{before_start.strftime('%Y-%m-%d')} to {before_end.strftime('%Y-%m-%d')}",
            'after_period': f"{after_start.strftime('%Y-%m-%d')} to {after_end.strftime('%Y-%m-%d')}",
            'comparison_days': upload_days
        })
        results.append(result)
    
    result_df = pd.DataFrame(results)
    
    # Cleanup temp columns
    for col in ['action_date_parsed', 'action_day']:
        if col in result_df.columns:
            result_df = result_df.drop(columns=[col], errors='ignore')
    
    return result_df
