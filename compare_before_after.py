"""
Calculate BEFORE vs AFTER impact scores for specific harvest actions
Shows exactly how the fix changed the numbers
"""
import psycopg2
import os
from datetime import datetime, timedelta

db_url = os.getenv('DATABASE_URL', 'postgresql://postgres.wuakeiwxkjvhsnmkzywz:Zen%40rise%40123%21@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres')
conn = psycopg2.connect(db_url)
cursor = conn.cursor()

CLIENT_ID = 'demo_account_2'

print("=" * 80)
print("BEFORE vs AFTER: Impact Calculation Comparison")
print("=" * 80)

# Get a harvest action with full metadata
cursor.execute("""
    SELECT 
        action_date,
        target_text,
        campaign_name,
        winner_source_campaign,
        new_campaign_name,
        before_match_type,
        after_match_type
    FROM actions_log
    WHERE client_id = %s
    AND action_type = 'HARVEST'
    AND winner_source_campaign IS NOT NULL
    ORDER BY action_date DESC
    LIMIT 1
""", (CLIENT_ID,))

action = cursor.fetchone()
if not action:
    print("No harvest actions with metadata found")
    exit(0)

action_date, target_text, campaign_name, winner_src, new_camp, before_mt, after_mt = action

print(f"\nTest Action:")
print(f"  Search Term: {target_text}")
print(f"  Action Date: {action_date}")
print(f"  Winner Source: {winner_src}")
print(f"  New Campaign: {new_camp}")
print(f"  Match Type: {before_mt} → {after_mt}")

# Calculate comparison windows (7-day upload frequency)
upload_days = 7
action_dt = action_date.date() if hasattr(action_date, 'date') else action_date
before_end = action_dt
before_start = action_dt - timedelta(days=upload_days - 1)
after_start = action_dt + timedelta(days=1)
after_end = action_dt + timedelta(days=upload_days)

print(f"\nComparison Windows ({upload_days} days):")
print(f"  Before: {before_start} to {before_end}")
print(f"  After:  {after_start} to {after_end}")

# ============================================================================
# OLD METHOD: Compare ALL campaigns
# ============================================================================
print("\n" + "=" * 80)
print("❌ OLD METHOD (Before Fix): All Campaigns")
print("=" * 80)

cursor.execute("""
    SELECT 
        campaign_name,
        SUM(spend) as spend,
        SUM(sales) as sales,
        COUNT(*) as weeks
    FROM target_stats
    WHERE client_id = %s
    AND LOWER(target_text) = LOWER(%s)
    AND start_date >= %s AND start_date <= %s
    GROUP BY campaign_name
    ORDER BY spend DESC
""", (CLIENT_ID, target_text, before_start, before_end))

before_campaigns = cursor.fetchall()
old_before_spend_total = 0
old_before_sales_total = 0

print(f"\nBefore Period - ALL campaigns with '{target_text[:40]}':")
for camp, spend, sales, weeks in before_campaigns:
    print(f"  {camp[:50]:50s} ${spend:8.2f}  ${sales:8.2f}")
    old_before_spend_total += spend or 0
    old_before_sales_total += sales or 0

print(f"  {'TOTAL (all campaigns)':50s} ${old_before_spend_total:8.2f}  ${old_before_sales_total:8.2f}")

cursor.execute("""
    SELECT 
        campaign_name,
        SUM(spend) as spend,
        SUM(sales) as sales
    FROM target_stats
    WHERE client_id = %s
    AND LOWER(target_text) = LOWER(%s)
    AND start_date >= %s AND start_date <= %s
    GROUP BY campaign_name
""", (CLIENT_ID, target_text, after_start, after_end))

after_campaigns = cursor.fetchall()
old_after_spend_total = 0
old_after_sales_total = 0

print(f"\nAfter Period - ALL campaigns with '{target_text[:40]}':")
for camp, spend, sales in after_campaigns:
    print(f"  {camp[:50]:50s} ${spend:8.2f}  ${sales:8.2f}")
    old_after_spend_total += spend or 0
    old_after_sales_total += sales or 0

print(f"  {'TOTAL (all campaigns)':50s} ${old_after_spend_total:8.2f}  ${old_after_sales_total:8.2f}")

old_delta_sales = old_after_sales_total - old_before_sales_total
old_delta_spend = old_after_spend_total - old_before_spend_total
old_impact = old_delta_sales - old_delta_spend

print(f"\n❌ OLD IMPACT CALCULATION:")
print(f"  Δ Sales: ${old_delta_sales:+.2f}")
print(f"  Δ Spend: ${old_delta_spend:+.2f}")
print(f"  Profit Impact: ${old_impact:+.2f}")

# ============================================================================
# NEW METHOD: Winner source only
# ============================================================================
print("\n" + "=" * 80)
print("✅ NEW METHOD (After Fix): Winner Source Only")
print("=" * 80)

cursor.execute("""
    SELECT SUM(spend), SUM(sales), COUNT(*)
    FROM target_stats
    WHERE client_id = %s
    AND LOWER(target_text) = LOWER(%s)
    AND campaign_name = %s
    AND start_date >= %s AND start_date <= %s
""", (CLIENT_ID, target_text, winner_src, before_start, before_end))

before_data = cursor.fetchone()
new_before_spend = before_data[0] or 0
new_before_sales = before_data[1] or 0
before_weeks = before_data[2]

print(f"\nBefore Period - WINNER campaign only:")
print(f"  {winner_src[:50]:50s} ${new_before_spend:8.2f}  ${new_before_sales:8.2f}")

cursor.execute("""
    SELECT SUM(spend), SUM(sales), COUNT(*)
    FROM target_stats
    WHERE client_id = %s
    AND LOWER(target_text) = LOWER(%s)
    AND campaign_name = %s
    AND start_date >= %s AND start_date <= %s
""", (CLIENT_ID, target_text, new_camp, after_start, after_end))

after_data = cursor.fetchone()
new_after_spend = after_data[0] or 0
new_after_sales = after_data[1] or 0
after_weeks = after_data[2]

print(f"\nAfter Period - NEW harvest campaign:")
print(f"  {new_camp[:50]:50s} ${new_after_spend:8.2f}  ${new_after_sales:8.2f}")

new_delta_sales = new_after_sales - new_before_sales
new_delta_spend = new_after_spend - new_before_spend
new_impact = new_delta_sales - new_delta_spend

print(f"\n✅ NEW IMPACT CALCULATION:")
print(f"  Δ Sales: ${new_delta_sales:+.2f}")
print(f"  Δ Spend: ${new_delta_spend:+.2f}")
print(f"  Profit Impact: ${new_impact:+.2f}")

# ============================================================================
# COMPARISON
# ============================================================================
print("\n" + "=" * 80)
print("📊 COMPARISON: What Changed")
print("=" * 80)

diff_sales = new_delta_sales - old_delta_sales
diff_spend = new_delta_spend - old_delta_spend
diff_impact = new_impact - old_impact

print(f"\n{'Metric':<20} {'Old Method':>15} {'New Method':>15} {'Difference':>15}")
print("-" * 70)
print(f"{'Before Spend':<20} ${old_before_spend_total:>14,.2f} ${new_before_spend:>14,.2f} ${(new_before_spend - old_before_spend_total):>14,+.2f}")
print(f"{'Before Sales':<20} ${old_before_sales_total:>14,.2f} ${new_before_sales:>14,.2f} ${(new_before_sales - old_before_sales_total):>14,+.2f}")
print(f"{'After Spend':<20} ${old_after_spend_total:>14,.2f} ${new_after_spend:>14,.2f} ${(new_after_spend - old_after_spend_total):>14,+.2f}")
print(f"{'After Sales':<20} ${old_after_sales_total:>14,.2f} ${new_after_sales:>14,.2f} ${(new_after_sales - old_after_sales_total):>14,+.2f}")
print("-" * 70)
print(f"{'Δ Sales':<20} ${old_delta_sales:>14,+.2f} ${new_delta_sales:>14,+.2f} ${diff_sales:>14,+.2f}")
print(f"{'Δ Spend':<20} ${old_delta_spend:>14,+.2f} ${new_delta_spend:>14,+.2f} ${diff_spend:>14,+.2f}")
print(f"{'PROFIT IMPACT':<20} ${old_impact:>14,+.2f} ${new_impact:>14,+.2f} ${diff_impact:>14,+.2f}")

if abs(diff_impact) > 1:
    pct_change = (diff_impact / abs(old_impact) * 100) if old_impact != 0 else float('inf')
    print(f"\n{'Impact changed by':<20} {pct_change:>14,.1f}%")
    
    if diff_impact > 0:
        print(f"\n✅ NEW method shows BETTER impact (${diff_impact:+.2f} more profit)")
    else:
        print(f"\n⚠️  NEW method shows WORSE impact (${diff_impact:+.2f} less profit)")
    print("   This is more ACCURATE because it only compares the winner campaign")
else:
    print("\n✓ Impact is similar in both methods for this action")

print("\n" + "=" * 80)

conn.close()
