"""
Check impact analysis for demo_Account_2 in Supabase
"""
import os
import psycopg2
import pandas as pd
from datetime import datetime, timedelta

db_url = os.getenv('DATABASE_URL', 'postgresql://postgres.wuakeiwxkjvhsnmkzywz:Zen%40rise%40123%21@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres')

print("=" * 80)
print("IMPACT ANALYSIS - demo_Account_2")
print("=" * 80)

conn = psycopg2.connect(db_url)
cursor = conn.cursor()

try:
    CLIENT_ID = 'demo_account_2'
    
    # 1. Check ALL actions for this account
    print(f"\n1. ALL ACTIONS FOR {CLIENT_ID}")
    print("-" * 80)
    
    cursor.execute("""
        SELECT 
            MIN(action_date) as earliest,
            MAX(action_date) as latest,
            COUNT(*) as total,
            COUNT(DISTINCT batch_id) as batches,
            COUNT(CASE WHEN action_type = 'HARVEST' THEN 1 END) as harvests,
            COUNT(CASE WHEN action_type = 'NEGATIVE' THEN 1 END) as negatives,
            COUNT(CASE WHEN action_type = 'BID_CHANGE' THEN 1 END) as bid_changes
        FROM actions_log
        WHERE client_id = %s
    """, (CLIENT_ID,))
    
    stats = cursor.fetchone()
    if stats[0]:
        earliest, latest, total, batches, harvests, negatives, bid_changes = stats
        print(f"\nDate Range: {earliest} to {latest}")
        print(f"Total Actions: {total:,}")
        print(f"Optimization Batches: {batches}")
        print(f"  - Harvests: {harvests}")
        print(f"  - Negatives: {negatives}")
        print(f"  - Bid Changes: {bid_changes}")
    else:
        print(f"\n❌ No actions found for {CLIENT_ID}")
        print("   The optimizer may not have logged actions yet.")
        cursor.close()
        conn.close()
        exit(0)
    
    # 2. Check recent batches with new field metadata
    print(f"\n\n2. RECENT OPTIMIZATION BATCHES")
    print("-" * 80)
    
    cursor.execute("""
        SELECT 
            batch_id,
            DATE(MIN(action_date)) as batch_date,
            COUNT(*) as actions,
            COUNT(CASE WHEN action_type = 'HARVEST' THEN 1 END) as harvests,
            COUNT(CASE WHEN winner_source_campaign IS NOT NULL THEN 1 END) as with_winner,
            COUNT(CASE WHEN new_campaign_name IS NOT NULL THEN 1 END) as with_new_camp
        FROM actions_log
        WHERE client_id = %s
        GROUP BY batch_id
        ORDER BY MIN(action_date) DESC
        LIMIT 5
    """, (CLIENT_ID,))
    
    print(f"\n{'Batch ID':<10} {'Date':<12} {'Actions':>8} {'Harvests':>9} {'W/Winner':>10} {'W/NewCamp':>11}")
    print("-" * 80)
    for row in cursor.fetchall():
        batch_id, batch_date, actions, harvests, with_winner, with_new_camp = row
        print(f"{batch_id:<10} {str(batch_date):<12} {actions:>8} {harvests:>9} {with_winner:>10} {with_new_camp:>11}")
    
    # 3. Detailed harvest actions
    print(f"\n\n3. HARVEST ACTIONS DETAIL")
    print("-" * 80)
    
    cursor.execute("""
        SELECT 
            action_date,
            target_text,
            campaign_name,
            winner_source_campaign,
            new_campaign_name,
            before_match_type,
            after_match_type,
            reason
        FROM actions_log
        WHERE client_id = %s
        AND action_type = 'HARVEST'
        ORDER BY action_date DESC
        LIMIT 10
    """, (CLIENT_ID,))
    
    harvest_actions = cursor.fetchall()
    if harvest_actions:
        print(f"\nFound {len(harvest_actions)} harvest actions:\n")
        for i, row in enumerate(harvest_actions, 1):
            action_date, target, campaign, winner, new_camp, before_mt, after_mt, reason = row
            print(f"#{i} Action Date: {action_date}")
            print(f"   Search Term: {target[:60]}")
            print(f"   Campaign: {campaign or 'NULL'}")
            print(f"   Winner Source: {winner or 'NULL'}")
            print(f"   New Campaign: {new_camp or 'NULL'}")
            print(f"   Match Type: {before_mt or 'NULL'} → {after_mt or 'NULL'}")
            print(f"   Reason: {reason}")
            print("-" * 80)
        
        # Check if new fields are populated
        has_metadata = sum(1 for row in harvest_actions if row[3] is not None)  # winner_source_campaign
        if has_metadata == len(harvest_actions):
            print(f"\n✅ ALL harvest actions have winner source metadata!")
        elif has_metadata > 0:
            print(f"\n⚠️  {has_metadata}/{len(harvest_actions)} harvest actions have winner source metadata")
        else:
            print(f"\n❌ NO harvest actions have winner source metadata (using old code)")
    else:
        print("\nNo harvest actions found")
    
    # 4. Available performance data
    print(f"\n\n4. AVAILABLE PERFORMANCE DATA FOR {CLIENT_ID}")
    print("-" * 80)
    
    cursor.execute("""
        SELECT 
            start_date,
            COUNT(*) as rows,
            SUM(spend) as total_spend,
            SUM(sales) as total_sales
        FROM target_stats
        WHERE client_id = %s
        GROUP BY start_date
        ORDER BY start_date DESC
        LIMIT 10
    """, (CLIENT_ID,))
    
    perf_data = cursor.fetchall()
    if perf_data:
        print(f"\n{'Date':<12} {'Rows':>8} {'Spend':>12} {'Sales':>12}")
        print("-" * 80)
        dates_list = []
        for row in perf_data:
            start_date, rows, spend, sales = row
            dates_list.append(start_date)
            print(f"{str(start_date):<12} {rows:>8,} ${spend:>11,.2f} ${sales:>11,.2f}")
        
        # Calculate upload frequency
        if len(dates_list) >= 2:
            gaps = [(dates_list[i] - dates_list[i+1]).days for i in range(len(dates_list)-1)]
            avg_gap = sum(gaps) / len(gaps) if gaps else 0
            print(f"\nDate gaps: {gaps}")
            print(f"Average upload frequency: {avg_gap:.1f} days")
            print(f"✓ Impact analyzer will use {int(avg_gap)}-day comparison windows")
    else:
        print(f"\n❌ No performance data found for {CLIENT_ID}")
    
    # 5. Sample impact calculation
    print(f"\n\n5. SAMPLE IMPACT CALCULATION")
    print("-" * 80)
    
    cursor.execute("""
        SELECT 
            a.action_date,
            a.action_type,
            a.target_text,
            a.campaign_name,
            a.winner_source_campaign,
            a.new_campaign_name
        FROM actions_log a
        WHERE a.client_id = %s
        AND a.action_type NOT IN ('hold', 'monitor', 'flagged')
        ORDER BY a.action_date DESC
        LIMIT 1
    """, (CLIENT_ID,))
    
    test_action = cursor.fetchone()
    if test_action and perf_data:
        action_date, action_type, target_text, campaign_name, winner_src, new_camp = test_action
        
        print(f"\nTesting with most recent action:")
        print(f"  Date: {action_date}")
        print(f"  Type: {action_type}")
        print(f"  Target: {target_text[:50]}")
        
        # Calculate windows
        upload_days = int(avg_gap) if 'avg_gap' in locals() else 7
        action_date_only = action_date.date() if hasattr(action_date, 'date') else action_date
        before_end = action_date_only
        before_start = action_date_only - timedelta(days=upload_days - 1)
        after_start = action_date_only + timedelta(days=1)
        after_end = action_date_only + timedelta(days=upload_days)
        
        print(f"\nComparison Windows (upload_days={upload_days}):")
        print(f"  Before: {before_start} to {before_end} ({upload_days} days)")
        print(f"  After:  {after_start} to {after_end} ({upload_days} days)")
        
        # Check data availability
        cursor.execute("""
            SELECT COUNT(*), MIN(start_date), MAX(start_date)
            FROM target_stats
            WHERE client_id = %s
            AND LOWER(target_text) = LOWER(%s)
            AND start_date >= %s AND start_date <= %s
        """, (CLIENT_ID, target_text, before_start, before_end))
        
        before_avail = cursor.fetchone()
        
        cursor.execute("""
            SELECT COUNT(*), MIN(start_date), MAX(start_date)
            FROM target_stats
            WHERE client_id = %s
            AND LOWER(target_text) = LOWER(%s)
            AND start_date >= %s AND start_date <= %s
        """, (CLIENT_ID, target_text, after_start, after_end))
        
        after_avail = cursor.fetchone()
        
        print(f"\nData Availability:")
        print(f"  Before: {before_avail[0]} rows ({before_avail[1]} to {before_avail[2]})")
        print(f"  After:  {after_avail[0]} rows ({after_avail[1]} to {after_avail[2]})")
        
        if after_avail[0] < upload_days * 0.5:
            print(f"\n  ⚠️  Insufficient after-period data ({after_avail[0]} < {upload_days * 0.5})")
            print(f"      Impact analyzer will mark as 'insufficient_data'")
    
    print("\n\n" + "=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)
    
    if harvest_actions:
        has_metadata = sum(1 for row in harvest_actions if row[3] is not None)
        if has_metadata == len(harvest_actions):
            print("\n✅ SUCCESS - All harvest actions have winner source metadata")
            print("   The fix is working correctly!")
        elif has_metadata > 0:
            print(f"\n⚠️  PARTIAL - {has_metadata}/{len(harvest_actions)} harvests have metadata")
            print("   Some actions may be from old optimizer runs")
        else:
            print("\n❌ ISSUE - No harvest actions have winner source metadata")
            print("   The optimizer may still be using old code")
            print("   Try restarting Streamlit and running optimizer again")
    
    print(f"\n✓ Schema: New columns available")
    print(f"✓ Logic: Dynamic {int(avg_gap) if 'avg_gap' in locals() else '?'}-day comparison windows")
    print(f"✓ Data: {len(perf_data) if perf_data else 0} weeks of performance data available")
    print("\n" + "=" * 80)

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    cursor.close()
    conn.close()
