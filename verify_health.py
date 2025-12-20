#!/usr/bin/env python3
"""Verify health score calculation for last 30 days"""

import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

db_path = Path("data/ppc_test.db")
conn = sqlite3.connect(str(db_path))

# Get the data
df = pd.read_sql_query("""
    SELECT 
        start_date,
        spend,
        sales,
        orders,
        clicks
    FROM target_stats
    WHERE client_id = (SELECT DISTINCT client_id FROM target_stats LIMIT 1)
    ORDER BY start_date DESC
""", conn)

print("\n" + "=" * 70)
print("HEALTH SCORE VERIFICATION (30-DAY vs ALL DATA)")
print("=" * 70)

# Convert dates
df['start_date'] = pd.to_datetime(df['start_date'])

# Date range info
print(f"\nData Date Range:")
print(f"  Earliest: {df['start_date'].min().strftime('%Y-%m-%d')}")
print(f"  Latest:   {df['start_date'].max().strftime('%Y-%m-%d')}")
print(f"  Total weeks: {df['start_date'].nunique()}")

# Filter to last 30 days
max_date = df['start_date'].max()
cutoff_date = max_date - timedelta(days=30)
df_30d = df[df['start_date'] >= cutoff_date].copy()

print(f"\n30-Day Filter Applied:")
print(f"  Cutoff Date: {cutoff_date.strftime('%Y-%m-%d')}")
print(f"  Weeks included: {df_30d['start_date'].nunique()}")

# Calculate for both periods
def calc_health(data, label):
    total_spend = data['spend'].sum()
    total_sales = data['sales'].sum()
    total_orders = data['orders'].sum()
    total_clicks = data['clicks'].sum()
    
    # Get individual rows for efficiency calc
    rows = pd.read_sql_query(f"""
        SELECT spend, orders
        FROM target_stats
        WHERE client_id = (SELECT DISTINCT client_id FROM target_stats LIMIT 1)
        {'AND start_date >= ?' if '30-Day' in label else ''}
    """, conn, params=[cutoff_date.strftime('%Y-%m-%d')] if '30-Day' in label else None)
    
    converting_spend = rows[rows['orders'] > 0]['spend'].sum()
    
    current_roas = total_sales / total_spend if total_spend > 0 else 0
    efficiency_rate = (converting_spend / total_spend * 100) if total_spend > 0 else 0
    cvr = (total_orders / total_clicks * 100) if total_clicks > 0 else 0
    
    # Score calculations (matching optimizer logic)
    roas_score = min(100, current_roas / 4.0 * 100)
    efficiency_score = efficiency_rate
    cvr_score = min(100, cvr / 5.0 * 100)
    health_score = (roas_score * 0.4 + efficiency_score * 0.4 + cvr_score * 0.2)
    
    print(f"\n{label}:")
    print(f"  Spend: AED {total_spend:,.0f}")
    print(f"  Sales: AED {total_sales:,.0f}")
    print(f"  Orders: {total_orders:,.0f}")
    print(f"  Clicks: {total_clicks:,.0f}")
    print(f"  ROAS: {current_roas:.2f}x")
    print(f"  Efficiency Rate: {efficiency_rate:.1f}%")
    print(f"  CVR: {cvr:.2f}%")
    print(f"  ---")
    print(f"  ROAS Score: {roas_score:.1f}/100")
    print(f"  Efficiency Score: {efficiency_score:.1f}/100")
    print(f"  CVR Score: {cvr_score:.1f}/100")
    print(f"  ===")
    print(f"  HEALTH SCORE: {health_score:.1f}/100")

calc_health(df, "ALL DATA")
calc_health(df_30d, "30-Day Period")

# Check what's in database
cursor = conn.cursor()
cursor.execute("SELECT health_score FROM account_health_metrics ORDER BY id DESC LIMIT 1")
result = cursor.fetchone()
if result:
    print(f"\nStored in Database: {result[0]:.1f}/100")
else:
    print(f"\nNo health score found in database")

print("=" * 70)
print("\n✅ To update: Re-run the optimizer with the new 30-day logic\n")

conn.close()
