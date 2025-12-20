#!/usr/bin/env python3
"""Manually recalculate and update health score with 30-day filter"""

import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

db_path = Path("data/ppc_test.db")
conn = sqlite3.connect(str(db_path))

print("\n" + "=" * 70)
print("MANUAL HEALTH SCORE UPDATE (30-Day Filter)")
print("=" * 70)

# Get client ID
cursor = conn.cursor()
cursor.execute("SELECT DISTINCT client_id FROM target_stats LIMIT 1")
client_id = cursor.fetchone()[0]
print(f"\nClient ID: {client_id}")

# Get data with 30-day filter
df = pd.read_sql_query("""
    SELECT 
        start_date,
        spend,
        sales,
        orders,
        clicks,
        target_text
    FROM target_stats
    WHERE client_id = ?
""", conn, params=[client_id])

# Apply 30-day filter
df['start_date'] = pd.to_datetime(df['start_date'])
max_date = df['start_date'].max()
cutoff_date = max_date - timedelta(days=30)
df_30d = df[df['start_date'] >= cutoff_date].copy()

print(f"\nDate Range:")
print(f"  Latest: {max_date.strftime('%Y-%m-%d')}")
print(f"  Cutoff: {cutoff_date.strftime('%Y-%m-%d')}")
print(f"  Rows in 30 days: {len(df_30d):,}")

# Calculate health metrics
total_spend = df_30d['spend'].sum()
total_sales = df_30d['sales'].sum()
total_orders = df_30d['orders'].sum()
total_clicks = df_30d['clicks'].sum()

# Efficiency at target level
target_agg = df_30d.groupby('target_text').agg({'spend': 'sum', 'orders': 'sum'}).reset_index()
converting_spend = target_agg[target_agg['orders'] > 0]['spend'].sum()

current_roas = total_sales / total_spend if total_spend > 0 else 0
efficiency_rate = (converting_spend / total_spend * 100) if total_spend > 0 else 0
wasted_spend = total_spend - converting_spend
waste_ratio = 100 - efficiency_rate
cvr = (total_orders / total_clicks * 100) if total_clicks > 0 else 0

# Score calculations
roas_score = min(100, current_roas / 4.0 * 100)
efficiency_score = efficiency_rate
cvr_score = min(100, cvr / 5.0 * 100)
health_score = (roas_score * 0.4 + efficiency_score * 0.4 + cvr_score * 0.2)

print(f"\nCalculated Metrics:")
print(f"  Total Spend: AED {total_spend:,.2f}")
print(f"  Total Sales: AED {total_sales:,.2f}")
print(f"  Orders: {total_orders:,.0f}")
print(f"  Clicks: {total_clicks:,.0f}")
print(f"  ROAS: {current_roas:.2f}x")
print(f"  Efficiency Rate: {efficiency_rate:.1f}%")
print(f"  CVR: {cvr:.2f}%")

print(f"\nComponent Scores:")
print(f"  ROAS Score: {roas_score:.1f}/100")
print(f"  Efficiency Score: {efficiency_score:.1f}/100")
print(f"  CVR Score: {cvr_score:.1f}/100")
print(f"\n  🎯 HEALTH SCORE: {health_score:.1f}/100")

# Update database
cursor.execute("""
    INSERT OR REPLACE INTO account_health_metrics
    (client_id, health_score, roas_score, waste_score, cvr_score,
     efficiency_rate, waste_ratio, wasted_spend, current_roas, current_acos, cvr,
     total_spend, total_sales, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
""", (
    client_id,
    health_score,
    roas_score,
    efficiency_score,  # maps to waste_score column
    cvr_score,
    efficiency_rate,
    waste_ratio,
    wasted_spend,
    current_roas,
    (total_spend / total_sales * 100) if total_sales > 0 else 0,
    cvr,
    total_spend,
    total_sales
))

conn.commit()

# Verify
cursor.execute("SELECT health_score FROM account_health_metrics WHERE client_id = ?", (client_id,))
result = cursor.fetchone()

print(f"\n✅ Database Updated!")
print(f"   Stored Health Score: {result[0]:.1f}/100")

conn.close()

print("=" * 70)
print("\nRefresh your Home page to see the updated score!\n")
