"""
Test Cases for Impact Analyzer Fix

Run these tests after implementation to verify the fix works correctly.
"""

import pandas as pd
from datetime import datetime, timedelta
from core.db_manager import get_db_manager

# ==========================================
# Test 1: Comparison Windows Match Upload Duration
# ==========================================

def test_comparison_windows():
    """
    Verify that before/after periods match upload duration, not action weeks.
    """
    print("Test 1: Comparison Windows")
    print("-" * 50)
    
    db = get_db_manager(test_mode=True)
    client_id = 'test_client'
    
    # Setup: Create action on Nov 20
    action_date = datetime(2024, 11, 20).date()
    db.log_action(
        client_id=client_id,
        action_type='bid_increase',
        entity_name='keyword',
        campaign_name='Test Campaign',
        ad_group_name='Test AG',
        target_text='test keyword',
        match_type='exact',
        old_value='1.50',
        new_value='2.00',
        reason='ROAS above target',
        action_date=action_date
    )
    
    # Create target stats for 15-day period (upload simulation)
    upload_start = datetime(2024, 12, 1).date()
    upload_end = datetime(2024, 12, 15).date()
    
    for day_offset in range(15):
        stat_date = upload_start + timedelta(days=day_offset)
        db.save_target_stats(
            client_id=client_id,
            campaign_name='Test Campaign',
            ad_group_name='Test AG',
            target_text='test keyword',
            start_date=stat_date,
            spend=10.0,
            sales=50.0,
            clicks=5,
            impressions=100
        )
    
    # Get impact
    impact_df = db.get_action_impact(client_id)
    
    # Verify
    assert not impact_df.empty, "Impact data should not be empty"
    
    row = impact_df.iloc[0]
    before_period = row['before_period']
    after_period = row['after_period']
    comparison_days = row['comparison_days']
    
    print(f"Action Date: {action_date}")
    print(f"Upload Period: {upload_start} to {upload_end} (15 days)")
    print(f"Before Period: {before_period}")
    print(f"After Period: {after_period}")
    print(f"Comparison Days: {comparison_days}")
    
    # Expected: Before = Nov 6-20 (15 days), After = Nov 21-Dec 5 (15 days)
    assert comparison_days == 15, f"Expected 15-day comparison, got {comparison_days}"
    assert '2024-11-06' in before_period, f"Before should start Nov 6, got {before_period}"
    assert '2024-11-20' in before_period, f"Before should end Nov 20, got {before_period}"
    
    print("✅ PASS: Comparison windows match upload duration (15 days)")
    print()


# ==========================================
# Test 2: Holds Are Excluded
# ==========================================

def test_holds_excluded():
    """
    Verify that hold actions are excluded from impact calculation.
    """
    print("Test 2: Holds Excluded")
    print("-" * 50)
    
    db = get_db_manager(test_mode=True)
    client_id = 'test_client'
    action_date = datetime(2024, 11, 20).date()
    
    # Log a hold action
    db.log_action(
        client_id=client_id,
        action_type='hold',  # Should be filtered out
        entity_name='keyword',
        campaign_name='Test Campaign',
        ad_group_name='Test AG',
        target_text='hold keyword',
        match_type='exact',
        old_value='1.50',
        new_value='1.50',
        reason='Performance optimal',
        action_date=action_date
    )
    
    # Get impact
    impact_df = db.get_action_impact(client_id)
    
    # Verify
    assert impact_df.empty or 'hold' not in impact_df['action_type'].values, \
        "Hold actions should be excluded"
    
    print("✅ PASS: Hold actions excluded from impact")
    print()


# ==========================================
# Test 3: Preventative Negatives Get No Credit
# ==========================================

def test_preventative_negatives():
    """
    Verify that negatives with $0 before spend show no impact.
    """
    print("Test 3: Preventative Negatives")
    print("-" * 50)
    
    db = get_db_manager(test_mode=True)
    client_id = 'test_client'
    action_date = datetime(2024, 11, 20).date()
    
    # Log negative action
    db.log_action(
        client_id=client_id,
        action_type='negative_add',
        entity_name='keyword',
        campaign_name='Test Campaign',
        ad_group_name='Test AG',
        target_text='preventative negative',
        match_type='negative_exact',
        old_value='active',
        new_value='negatived',
        reason='Prevent wasteful spend',
        action_date=action_date
    )
    
    # NOTE: No target_stats created = $0 before spend
    
    # Get impact
    impact_df = db.get_action_impact(client_id)
    
    # Verify
    if not impact_df.empty:
        row = impact_df[impact_df['target_text'] == 'preventative negative'].iloc[0]
        assert row['attribution'] == 'preventative', \
            f"Expected 'preventative' attribution, got {row['attribution']}"
        assert row['impact_score'] == 0, \
            f"Expected 0 impact, got {row['impact_score']}"
    
    print("✅ PASS: Preventative negatives show zero impact")
    print()


# ==========================================
# Test 4: Isolation Negatives Get No Separate Credit
# ==========================================

def test_isolation_negatives():
    """
    Verify that isolation negatives (from harvest) show no separate impact.
    """
    print("Test 4: Isolation Negatives")
    print("-" * 50)
    
    db = get_db_manager(test_mode=True)
    client_id = 'test_client'
    action_date = datetime(2024, 11, 20).date()
    
    # Log isolation negative
    db.log_action(
        client_id=client_id,
        action_type='negative_add',
        entity_name='keyword',
        campaign_name='Losing Campaign',
        ad_group_name='Test AG',
        target_text='isolation negative',
        match_type='negative_exact',
        old_value='active',
        new_value='negatived',
        reason='Isolation - harvested to Winner Campaign',  # KEY: Contains 'isolation'
        action_date=action_date
    )
    
    # Get impact
    impact_df = db.get_action_impact(client_id)
    
    # Verify
    if not impact_df.empty:
        row = impact_df[impact_df['target_text'] == 'isolation negative'].iloc[0]
        assert row['attribution'] == 'isolation_negative', \
            f"Expected 'isolation_negative' attribution, got {row['attribution']}"
        assert row['impact_score'] == 0, \
            f"Expected 0 impact, got {row['impact_score']}"
    
    print("✅ PASS: Isolation negatives show zero impact (harvest gets credit)")
    print()


# ==========================================
# Test 5: Harvest Uses Winner Source
# ==========================================

def test_harvest_winner_source():
    """
    Verify that harvest compares winner source campaign only, not all campaigns.
    """
    print("Test 5: Harvest Winner Source")
    print("-" * 50)
    
    db = get_db_manager(test_mode=True)
    client_id = 'test_client'
    action_date = datetime(2024, 11, 20).date()
    
    # Create stats in multiple campaigns for same keyword
    # Campaign A (Winner): Good performance
    for day in range(15):
        db.save_target_stats(
            client_id=client_id,
            campaign_name='Campaign A',
            ad_group_name='AG',
            target_text='harvest keyword',
            start_date=(action_date - timedelta(days=14-day)),
            spend=10.0,
            sales=50.0,  # 5.0 ROAS
            clicks=5,
            impressions=100
        )
    
    # Campaign B (Loser): Bad performance
    for day in range(15):
        db.save_target_stats(
            client_id=client_id,
            campaign_name='Campaign B',
            ad_group_name='AG',
            target_text='harvest keyword',
            start_date=(action_date - timedelta(days=14-day)),
            spend=10.0,
            sales=20.0,  # 2.0 ROAS
            clicks=5,
            impressions=100
        )
    
    # Log harvest action with winner source
    db.log_action(
        client_id=client_id,
        action_type='harvest',
        entity_name='keyword',
        campaign_name='Campaign A',  # Source
        ad_group_name='AG',
        target_text='harvest keyword',
        match_type='exact',
        old_value='1.50',
        new_value='2.00',
        reason='Harvest from Campaign A',
        action_date=action_date,
        winner_source_campaign='Campaign A',  # NEW
        new_campaign_name='Harvest Exact Campaign'  # NEW
    )
    
    # Create after stats in new harvest campaign
    for day in range(15):
        db.save_target_stats(
            client_id=client_id,
            campaign_name='Harvest Exact Campaign',
            ad_group_name='AG',
            target_text='harvest keyword',
            start_date=(action_date + timedelta(days=1+day)),
            spend=12.0,
            sales=60.0,  # 5.0 ROAS
            clicks=6,
            impressions=120
        )
    
    # Get impact
    impact_df = db.get_action_impact(client_id)
    
    # Verify
    if not impact_df.empty:
        row = impact_df[impact_df['action_type'] == 'harvest'].iloc[0]
        
        # Before should ONLY be from Campaign A (winner), not A+B
        expected_before_spend = 150.0  # 10.0 * 15 days from Campaign A only
        expected_before_sales = 750.0  # 50.0 * 15 days from Campaign A only
        
        # If it was summing both campaigns, it would be:
        # wrong_before_spend = 300.0  # 10.0 * 15 * 2 campaigns
        # wrong_before_sales = 1050.0  # (50.0 + 20.0) * 15
        
        assert abs(row['before_spend'] - expected_before_spend) < 1.0, \
            f"Before spend should be {expected_before_spend} (Campaign A only), got {row['before_spend']}"
        assert abs(row['before_sales'] - expected_before_sales) < 1.0, \
            f"Before sales should be {expected_before_sales} (Campaign A only), got {row['before_sales']}"
    
    print("✅ PASS: Harvest compares winner source only, not all campaigns")
    print()


# ==========================================
# Test 6: Regular Negatives With Spend Get Credit
# ==========================================

def test_regular_negatives_with_spend():
    """
    Verify that bleeder negatives with spend get cost avoidance credit.
    """
    print("Test 6: Regular Negatives With Spend")
    print("-" * 50)
    
    db = get_db_manager(test_mode=True)
    client_id = 'test_client'
    action_date = datetime(2024, 11, 20).date()
    
    # Create before stats with spend
    for day in range(15):
        db.save_target_stats(
            client_id=client_id,
            campaign_name='Test Campaign',
            ad_group_name='AG',
            target_text='bleeder keyword',
            start_date=(action_date - timedelta(days=14-day)),
            spend=5.0,  # $75 total wasted
            sales=0.0,  # No sales
            clicks=3,
            impressions=50
        )
    
    # Log negative action
    db.log_action(
        client_id=client_id,
        action_type='negative_add',
        entity_name='keyword',
        campaign_name='Test Campaign',
        ad_group_name='AG',
        target_text='bleeder keyword',
        match_type='negative_exact',
        old_value='active',
        new_value='negatived',
        reason='Bleeder - 0 sales',
        action_date=action_date
    )
    
    # Get impact
    impact_df = db.get_action_impact(client_id)
    
    # Verify
    if not impact_df.empty:
        row = impact_df[impact_df['target_text'] == 'bleeder keyword'].iloc[0]
        assert row['attribution'] == 'cost_avoidance', \
            f"Expected 'cost_avoidance' attribution, got {row['attribution']}"
        assert row['attributed_delta_spend'] < 0, \
            f"Expected negative spend delta (savings), got {row['attributed_delta_spend']}"
        assert abs(row['attributed_delta_spend'] + 75.0) < 1.0, \
            f"Expected -$75 savings, got {row['attributed_delta_spend']}"
    
    print("✅ PASS: Regular negatives with spend get cost avoidance credit")
    print()


# ==========================================
# Run All Tests
# ==========================================

def run_all_tests():
    """Run all test cases."""
    print("=" * 50)
    print("IMPACT ANALYZER FIX - TEST SUITE")
    print("=" * 50)
    print()
    
    try:
        test_comparison_windows()
        test_holds_excluded()
        test_preventative_negatives()
        test_isolation_negatives()
        test_harvest_winner_source()
        test_regular_negatives_with_spend()
        
        print("=" * 50)
        print("ALL TESTS PASSED ✅")
        print("=" * 50)
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        return False
    except Exception as e:
        print(f"\n❌ TEST ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    run_all_tests()
