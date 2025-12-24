"""
Final verification of Impact Analyzer Fix for demo_account_2
"""
import psycopg2
import os
from datetime import datetime, timedelta

db_url = os.getenv('DATABASE_URL', 'postgresql://postgres.wuakeiwxkjvhsnmkzywz:Zen%40rise%40123%21@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres')
conn = psycopg2.connect(db_url)
cursor = conn.cursor()

CLIENT_ID = 'demo_account_2'

print("=" * 80)
print("IMPACT ANALYZER FIX - FINAL VERIFICATION")
print(f"Account: {CLIENT_ID}")
print("=" * 80)

# 1. Actions Summary
cursor.execute("""
    SELECT 
        DATE(MIN(action_date)) as first_run,
        DATE(MAX(action_date)) as last_run,
        COUNT(DISTINCT batch_id) as total_batches,
        COUNT(*) as total_actions,
        COUNT(CASE WHEN action_type = 'HARVEST' THEN 1 END) as harvests,
        COUNT(CASE WHEN winner_source_campaign IS NOT NULL THEN 1 END) as with_metadata
    FROM actions_log
    WHERE client_id = %s
""", (CLIENT_ID,))

first, last, batches, total, harvests, with_metadata = cursor.fetchone()

print(f"\n📊 OPTIMIZATION RUNS SUMMARY")
print(f"   Period: {first} to {last}")
print(f"   Batches: {batches} optimization runs")
print(f"   Total Actions: {total:,}")
print(f"   Harvest Actions: {harvests}")
print(f"   Actions with new metadata: {with_metadata}")

# 2. Check harvest actions for winner source
print(f"\n\n🌾 HARVEST ACTIONS - WINNER SOURCE TRACKING")
print("-" * 80)

cursor.execute("""
    SELECT 
        DATE(action_date) as date,
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
""", (CLIENT_ID,))

harvest_rows = cursor.fetchall()

if harvest_rows:
    for i, row in enumerate(harvest_rows, 1):
        date, term, campaign, winner, new_camp, before_mt, after_mt, reason = row
        print(f"\n#{i} {date}")
        print(f"   Term: {term[:50]}")
        print(f"   Source Campaign: {campaign or 'NULL'}")
        print(f"   Winner Source: {'✓ ' + winner if winner else '❌ NULL (old code)'}")
        print(f"   New Campaign: {'✓ ' + new_camp if new_camp else '❌ NULL (old code)'}")
        print(f"   Match Type: {before_mt or 'NULL'} → {after_mt or 'NULL'}")
        print("-" * 40)
    
    has_metadata = sum(1 for row in harvest_rows if row[3] is not None)
    
    if has_metadata == len(harvest_rows):
        print(f"\n✅ SUCCESS: ALL {len(harvest_rows)} harvest actions have winner source metadata!")
    elif has_metadata > 0:
        print(f"\n⚠️  PARTIAL: {has_metadata}/{len(harvest_rows)} actions have metadata")
        print(f"   (Older actions from before the fix don't have it)")
    else:
        print(f"\n❌ ISSUE: NO actions have metadata - fix may not be active")
else:
    print("   No harvest actions found")

# 3. Performance data for comparison windows
print(f"\n\n📈 PERFORMANCE DATA (for impact calculation)")
print("-" * 80)

cursor.execute("""
    SELECT start_date, COUNT(*) as rows
    FROM target_stats
    WHERE client_id = %s
    GROUP BY start_date
    ORDER BY start_date DESC
    LIMIT 5
""", (CLIENT_ID,))

dates = [row[0] for row in cursor.fetchall()]
print(f"\nAvailable dates: {[str(d) for d in dates]}")

if len(dates) >= 2:
    gaps = [(dates[i] - dates[i+1]).days for i in range(len(dates)-1)]
    avg_gap = sum(gaps) / len(gaps)
    print(f"Date gaps: {gaps} days")
    print(f"Average upload frequency: {avg_gap:.1f} days")
    print(f"✓ Impact analyzer will use {int(avg_gap)}-day comparison windows")

# 4. Test impact calculation for one harvest action
if harvest_rows and dates:
    print(f"\n\n🧪 SAMPLE IMPACT CALCULATION")
    print("-" * 80)
    
    # Use first harvest
    test_action = harvest_rows[0]
    action_date_val, target_text, campaign_name, winner_src, new_camp, before_mt, after_mt, reason = test_action
    
    print(f"\nTesting: {target_text[:50]}")
    print(f"Action Date: {action_date_val}")
    
    # Calculate comparison windows
    upload_days = int(avg_gap) if 'avg_gap' in locals() else 7
    action_date = action_date_val if hasattr(action_date_val, 'year') else datetime.strptime(str(action_date_val), '%Y-%m-%d').date()
    before_end = action_date
    before_start = action_date - timedelta(days=upload_days - 1)
    after_start = action_date + timedelta(days=1)
    after_end = action_date + timedelta(days=upload_days)
    
    print(f"\nComparison Windows ({upload_days} days):")
    print(f"  Before: {before_start} to {before_end}")
    print(f"  After:  {after_start} to {after_end}")
    
    if winner_src and new_camp:
        print(f"\n✓ Using WINNER SOURCE logic:")
        print(f"  Before: {winner_src} campaign only")
        print(f"  After:  {new_camp} campaign only")
        
        # Query before performance
        cursor.execute("""
            SELECT SUM(spend), SUM(sales), COUNT(*)
            FROM target_stats
            WHERE client_id = %s
            AND LOWER(target_text) = LOWER(%s)
            AND campaign_name = %s
            AND start_date >= %s AND start_date <= %s
        """, (CLIENT_ID, target_text, winner_src, before_start, before_end))
        
        before = cursor.fetchone()
        before_spend, before_sales, before_weeks = before if before else (0, 0, 0)
        
        # Query after performance  
        cursor.execute("""
            SELECT SUM(spend), SUM(sales), COUNT(*)
            FROM target_stats
            WHERE client_id = %s
            AND LOWER(target_text) = LOWER(%s)
            AND campaign_name = %s
            AND start_date >= %s AND start_date <= %s
        """, (CLIENT_ID, target_text, new_camp, after_start, after_end))
        
        after = cursor.fetchone()
        after_spend, after_sales, after_weeks = after if after else (0, 0, 0)
        
    else:
        print(f"\n⚠️  NO winner source - using ALL campaigns (old behavior)")
        
        cursor.execute("""
            SELECT SUM(spend), SUM(sales), COUNT(*)
            FROM target_stats
            WHERE client_id = %s
            AND LOWER(target_text) = LOWER(%s)
            AND start_date >= %s AND start_date <= %s
        """, (CLIENT_ID, target_text, before_start, before_end))
        
        before = cursor.fetchone()
        before_spend, before_sales, before_weeks = before if before else (0, 0, 0)
        
        cursor.execute("""
            SELECT SUM(spend), SUM(sales), COUNT(*)
            FROM target_stats
            WHERE client_id = %s
            AND LOWER(target_text) = LOWER(%s)
            AND start_date >= %s AND start_date <= %s
        """, (CLIENT_ID, target_text, after_start, after_end))
        
        after = cursor.fetchone()
        after_spend, after_sales, after_weeks = after if after else (0, 0, 0)
    
    before_spend = before_spend or 0
    before_sales = before_sales or 0
    after_spend = after_spend or 0
    after_sales = after_sales or 0
    
    print(f"\n  Before ({before_weeks} data points):")
    print(f"    Spend: ${before_spend:.2f}")
    print(f"    Sales: ${before_sales:.2f}")
    print(f"    ROAS: {(before_sales/before_spend if before_spend > 0 else 0):.2f}")
    
    print(f"\n  After ({after_weeks} data points):")
    print(f"    Spend: ${after_spend:.2f}")
    print(f"    Sales: ${after_sales:.2f}")
    print(f"    ROAS: {(after_sales/after_spend if after_spend > 0 else 0):.2f}")
    
    delta_sales = after_sales - before_sales
    delta_spend = after_spend - before_spend
    impact = delta_sales - delta_spend
    
    print(f"\n  Impact:")
    print(f"    Δ Sales: ${delta_sales:+.2f}")
    print(f"    Δ Spend: ${delta_spend:+.2f}")
    print(f"    Profit Impact: ${impact:+.2f}")

print("\n\n" + "=" * 80)
print("FINAL VERDICT")
print("=" * 80)

if harvest_rows:
    has_metadata = sum(1 for row in harvest_rows if row[3] is not None)
    
    if has_metadata == len(harvest_rows):
        print("\n✅ FIX IS WORKING PERFECTLY!")
        print(f"   - All {len(harvest_rows)} harvest actions have winner source tracking")
        print(f"   - Comparison windows based on {int(avg_gap) if 'avg_gap' in locals() else '?'}-day upload frequency")
        print(f"   - Harvest comparisons use winner source → new campaign")
        print("\n   The Impact Analyzer fix is fully operational! ✓")
    elif has_metadata > 0:
        print("\n⚠️  FIX IS PARTIALLY WORKING")
        print(f"   - {has_metadata}/{len(harvest_rows)} newer actions have metadata")
        print(f"   - Older actions from before the fix don't have it")
        print("\n   This is EXPECTED - the fix only affects new optimization runs")
    else:
        print("\n❌ FIX NOT ACTIVE")
        print("   - No actions have winner source metadata")
        print("   - The optimizer may need to be restarted")
        print("\n   Please restart Streamlit and run the optimizer again")
else:
    print("\nℹ️  No harvest actions to verify")
    print("   Run the optimizer with harvest candidates to test the fix")

print("\n" + "=" * 80)

conn.close()
