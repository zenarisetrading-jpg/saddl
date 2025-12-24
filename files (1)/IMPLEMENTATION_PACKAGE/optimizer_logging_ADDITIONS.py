"""
Additions to features/optimizer.py for tracking harvest winner source.

Find where harvest actions are logged and add these fields.
"""

# ==========================================
# Example 1: In identify_harvest_candidates()
# ==========================================

def identify_harvest_candidates(df, config, matcher):
    """
    Identify high-performing search terms to harvest.
    
    ADDITION: Track which campaign was the winner source for each harvest.
    """
    
    # ... existing harvest detection logic ...
    
    # When multiple campaigns have the same search term,
    # select winner based on performance score
    grouped = df.groupby('Customer Search Term').apply(
        lambda x: x.loc[x['Performance_Score'].idxmax()]
    ).reset_index(drop=True)
    
    # ADD: Store winner campaign metadata
    harvest_candidates = grouped.copy()
    harvest_candidates['winner_source_campaign'] = grouped['Campaign Name']
    harvest_candidates['before_match_type'] = grouped['Match Type']
    harvest_candidates['after_match_type'] = 'exact'  # Harvest always goes to exact
    
    # NEW: If you're creating a new campaign name for harvest
    # You can either use a naming convention or store it for later
    harvest_candidates['new_campaign_name'] = harvest_candidates.apply(
        lambda row: f"Harvest_Exact_{row['SKU_advertised']}" if 'SKU_advertised' in row else None,
        axis=1
    )
    
    return harvest_candidates


# ==========================================
# Example 2: In _log_optimization_events()
# ==========================================

def _log_optimization_events(results_dict, client_id, report_date):
    """
    Log optimization actions to database.
    
    ADDITION: Pass winner source metadata for harvest actions.
    """
    
    db_manager = st.session_state.get('db_manager')
    if not db_manager:
        return
    
    # ... existing code ...
    
    # When logging harvest actions:
    if 'harvest' in results_dict and not results_dict['harvest'].empty:
        harvest_df = results_dict['harvest']
        
        for _, row in harvest_df.iterrows():
            db_manager.log_action(
                client_id=client_id,
                action_type='harvest',
                entity_name='keyword',
                campaign_name=row.get('Campaign Name'),  # This is the SOURCE campaign
                ad_group_name=row.get('Ad Group Name'),
                target_text=row.get('Customer Search Term'),
                match_type='exact',  # After harvest
                old_value=row.get('CPC'),  # Old CPC in source campaign
                new_value=row.get('New Bid'),  # New bid in harvest campaign
                reason=f"Harvest from {row.get('Campaign Name')} (winner)",
                action_date=report_date,
                # NEW FIELDS:
                winner_source_campaign=row.get('Campaign Name'),  # Or row.get('winner_source_campaign')
                new_campaign_name=row.get('new_campaign_name', 'Harvest_Exact_Campaign'),
                before_match_type=row.get('Match Type', 'broad'),  # Original match type
                after_match_type='exact'
            )


# ==========================================
# Example 3: Update log_action() signature in db_manager.py
# ==========================================

def log_action(
    self,
    client_id: str,
    action_type: str,
    entity_name: str,
    campaign_name: str,
    ad_group_name: str,
    target_text: str,
    match_type: str,
    old_value: Any,
    new_value: Any,
    reason: str,
    action_date: Union[date, str],
    batch_id: Optional[str] = None,
    # NEW PARAMETERS:
    winner_source_campaign: Optional[str] = None,
    new_campaign_name: Optional[str] = None,
    before_match_type: Optional[str] = None,
    after_match_type: Optional[str] = None
) -> int:
    """Log an optimization action with metadata."""
    
    with self._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO actions_log (
                client_id, action_type, entity_name, batch_id,
                campaign_name, ad_group_name, target_text, match_type,
                old_value, new_value, reason, action_date,
                winner_source_campaign, new_campaign_name, 
                before_match_type, after_match_type
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            client_id, action_type, entity_name, batch_id,
            campaign_name, ad_group_name, target_text, match_type,
            str(old_value), str(new_value), reason, str(action_date),
            winner_source_campaign, new_campaign_name,
            before_match_type, after_match_type
        ))
        return cursor.lastrowid


# ==========================================
# Example 4: For Isolation Negatives
# ==========================================

def log_isolation_negatives(harvest_df, losing_campaigns, client_id, report_date):
    """
    Log negative keywords added to losing campaigns (isolation negatives).
    
    These should have reason containing 'isolation' or 'harvest' so impact
    analyzer knows not to give them separate credit.
    """
    
    db_manager = st.session_state.get('db_manager')
    
    for _, harvest_row in harvest_df.iterrows():
        search_term = harvest_row['Customer Search Term']
        winner_campaign = harvest_row['Campaign Name']
        
        # Add as negative in all other campaigns that had this term
        for losing_campaign in losing_campaigns:
            if losing_campaign != winner_campaign:
                db_manager.log_action(
                    client_id=client_id,
                    action_type='negative_add',
                    entity_name='keyword',
                    campaign_name=losing_campaign,
                    ad_group_name='',
                    target_text=search_term,
                    match_type='negative_exact',
                    old_value='active',
                    new_value='negatived',
                    reason=f"Isolation - harvested to {winner_campaign} (winner)",  # KEY: Include 'isolation'
                    action_date=report_date,
                    winner_source_campaign=winner_campaign,
                    new_campaign_name=harvest_row.get('new_campaign_name')
                )


# ==========================================
# Quick Reference: Action Type Metadata
# ==========================================

"""
Action Type           | winner_source_campaign | new_campaign_name | before_match_type | after_match_type
----------------------|------------------------|-------------------|-------------------|------------------
harvest               | SOURCE campaign name   | NEW campaign name | broad/phrase/auto | exact
negative_add (iso)    | WINNER campaign        | NEW harvest camp  | N/A              | N/A
negative_add (bleeder)| NULL                   | NULL              | N/A              | N/A
bid_increase          | NULL                   | NULL              | N/A              | N/A
bid_decrease          | NULL                   | NULL              | N/A              | N/A
hold                  | NULL                   | NULL              | N/A              | N/A (filtered out)
"""
