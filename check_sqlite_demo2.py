"""
Check local SQLite database for demo_Account_2 actions
"""
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

db_path = '/Users/zayaanyousuf/Documents/Amazon PPC/saddle/saddle/data/ppc_live.db'

print("=" * 80)
print("IMPACT ANALYSIS - demo_Account_2 (LOCAL SQLite)")
print("=" * 80)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    CLIENT_ID = 'demo_Account_2'
    
    # 1. Check ALL actions for this account
    print(f"\n1. ALL ACTIONS FOR {CLIENT_ID}")
    print("-" * 80)
    
    cursor.execute("""
        SELECT 
            MIN(action_date) as earliest,
            MAX(action_date) as latest,
            COUNT(*) as total,
            COUNT(DISTINCT batch_id) as batches,
            SUM(CASE WHEN action_type = 'HARVEST' THEN 1 ELSE 0 END) as harvests,
            SUM(CASE WHEN action_type = 'NEGATIVE' THEN 1 ELSE 0 END) as negatives,
            SUM(CASE WHEN action_type = 'BID_CHANGE' THEN 1 ELSE 0 END) as bid_changes
        FROM actions_log
        WHERE client_id = ?
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
        print(f"\n❌ No actions found for {CLIENT_ID} in local database")
        cursor.close()
        conn.close()
        exit(0)
    
    # 2. Check batches with new metadata
    print(f"\n\n2. OPTIMIZATION BATCHES")
    print("-" * 80)
    
    cursor.execute("""
        SELECT 
            batch_id,
            DATE(MIN(action_date)) as batch_date,
            COUNT(*) as actions,
            SUM(CASE WHEN action_type = 'HARVEST' THEN 1 ELSE 0 END) as harvests,
            SUM(CASE WHEN winner_source_campaign IS NOT NULL THEN 1 ELSE 0 END) as with_winner,
            SUM(CASE WHEN new_campaign_name IS NOT NULL THEN 1 ELSE 0 END) as with_new_camp
        FROM actions_log
        WHERE client_id = ?
        GROUP BY batch_id
        ORDER BY MIN(action_date) DESC
    """, (CLIENT_ID,))
    
    print(f"\n{'Batch ID':<10} {'Date':<12} {'Actions':>8} {'Harvests':>9} {'W/Winner':>10} {'W/NewCamp':>11}")
    print("-" * 80)
    batches = cursor.fetchall()
    for row in batches:
        batch_id, batch_date, actions, harvests, with_winner, with_new_camp = row
        print(f"{batch_id:<10} {str(batch_date):<12} {actions:>8} {harvests:>9} {with_winner:>10} {with_new_camp:>11}")
    
    # 3. Harvest actions detail
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
        WHERE client_id = ?
        AND action_type = 'HARVEST'
        ORDER BY action_date DESC
        LIMIT 10
    """, (CLIENT_ID,))
    
    harvest_actions = cursor.fetchall()
    if harvest_actions:
        print(f"\nFound {len(harvest_actions)} harvest actions:\n")
        for i, row in enumerate(harvest_actions, 1):
            action_date, target, campaign, winner, new_camp, before_mt, after_mt, reason = row
            print(f"#{i} {action_date}")
            print(f"   Term: {target[:60]}")
            print(f"   Campaign: {campaign or 'NULL'}")
            print(f"   ✓ Winner Source: {winner or 'NULL'}")
            print(f"   ✓ New Campaign: {new_camp or 'NULL'}")
            print(f"   ✓ Match Type: {before_mt or 'NULL'} → {after_mt or 'NULL'}")
            print(f"   Reason: {reason}")
            print("-" * 80)
        
        # Check metadata
        has_metadata = sum(1 for row in harvest_actions if row[3] is not None)
        print(f"\n{'✅' if has_metadata == len(harvest_actions) else '⚠️'} {has_metadata}/{len(harvest_actions)} harvest actions have winner source metadata")
    else:
        print("\nNo harvest actions found")
    
    # 4. Check negative actions for preventative detection
    print(f"\n\n4. NEGATIVE ACTIONS (Preventative Check)")
    print("-" * 80)
    
    cursor.execute("""
        SELECT 
            action_date,
            target_text,
            campaign_name,
            reason
        FROM actions_log
        WHERE client_id = ?
        AND action_type = 'NEGATIVE'
        ORDER BY action_date DESC
        LIMIT 5
    """, (CLIENT_ID,))
    
    neg_actions = cursor.fetchall()
    if neg_actions:
        print(f"\nSample negative actions (to check if preventative):\n")
        for i, row in enumerate(neg_actions, 1):
            action_date, target, campaign, reason = row
            print(f"#{i} {action_date}")
            print(f"   Term: {target[:60]}")
            print(f"   Campaign: {campaign}")
            print(f"   Reason: {reason}")
            
            # Check if there's before_spend for this target
            cursor.execute("""
                SELECT SUM(spend) 
                FROM target_stats
                WHERE client_id = ?
                AND LOWER(target_text) = LOWER(?)
                AND start_date < ?
            """, (CLIENT_ID, target, action_date))
            
            before_spend = cursor.fetchone()[0] or 0
            if before_spend == 0:
                print(f"   ⚠️  PREVENTATIVE (before_spend = $0)")
            else:
                print(f"   ✓ Creditable (before_spend = ${before_spend:.2f})")
            print("-" * 80)
    
    # 5. Available performance data
    print(f"\n\n5. PERFORMANCE DATA")
    print("-" * 80)
    
    cursor.execute("""
        SELECT 
            start_date,
            COUNT(*) as rows,
            SUM(spend) as spend,
            SUM(sales) as sales
        FROM target_stats
        WHERE client_id = ?
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
        from datetime import datetime
        dates_dt = [datetime.strptime(d, '%Y-%m-%d').date() if isinstance(d, str) else d for d in dates_list]
        if len(dates_dt) >= 2:
            gaps = [(dates_dt[i] - dates_dt[i+1]).days for i in range(len(dates_dt)-1)]
            avg_gap = sum(gaps) / len(gaps) if gaps else 0
            print(f"\nDate gaps: {gaps}")
            print(f"Average: {avg_gap:.1f} days")
            print(f"✓ Comparison windows: {int(avg_gap)} days")
    
    print("\n\n" + "=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)
    
    print(f"\n✓ Actions logged: {total:,} actions across {batches} optimization runs")
    
    if harvest_actions:
        has_metadata = sum(1 for row in harvest_actions if row[3] is not None)
        if has_metadata == len(harvest_actions):
            print(f"✅ ALL {len(harvest_actions)} harvest actions have winner source metadata!")
            print("   The fix is working correctly!")
        elif has_metadata > 0:
            print(f"⚠️  Only {has_metadata}/{len(harvest_actions)} harvests have metadata")
            print("   The optimizer was recently updated - older actions don't have it")
        else:
            print(f"❌ NO harvest actions have winner source metadata")
            print("   The new code may not be active yet")
    
    if perf_data:
        print(f"✓ Performance data: {len(dates_list)} weeks available")
        if 'avg_gap' in locals():
            print(f"✓ Upload frequency: ~{avg_gap:.1f} days → {int(avg_gap)}-day comparison windows")
    
    print("\n" + "=" * 80)

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    cursor.close()
    conn.close()
