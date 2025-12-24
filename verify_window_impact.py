import pandas as pd
from core.postgres_manager import PostgresManager
import json

def calculate_impact_locally(pm, client_id, w):
    w_minus_1 = w - 1
    w_int = w
    w2_minus_1 = 2 * w - 1
    
    query = f"""
        WITH date_range AS (
            SELECT 
                MAX(start_date) as latest_date,
                MAX(start_date) - INTERVAL '{w_minus_1} days' as after_start,
                MAX(start_date) - INTERVAL '{w_int} days' as before_end,
                MAX(start_date) - INTERVAL '{w2_minus_1} days' as before_start
            FROM target_stats 
            WHERE client_id = '{client_id}'
        ),
        before_stats AS (
            SELECT 
                LOWER(target_text) as target_lower, LOWER(campaign_name) as campaign_lower,
                SUM(spend) as spend, SUM(sales) as sales
            FROM target_stats t CROSS JOIN date_range dr
            WHERE t.client_id = '{client_id}' AND t.start_date >= dr.before_start AND t.start_date <= dr.before_end
            GROUP BY 1, 2
        ),
        after_stats AS (
            SELECT 
                LOWER(target_text) as target_lower, LOWER(campaign_name) as campaign_lower,
                SUM(spend) as spend, SUM(sales) as sales
            FROM target_stats t CROSS JOIN date_range dr
            WHERE t.client_id = '{client_id}' AND t.start_date >= dr.after_start AND t.start_date <= dr.latest_date
            GROUP BY 1, 2
        ),
        before_campaign AS (
            SELECT LOWER(campaign_name) as campaign_lower, SUM(spend) as spend, SUM(sales) as sales
            FROM target_stats t CROSS JOIN date_range dr
            WHERE t.client_id = '{client_id}' AND t.start_date >= dr.before_start AND t.start_date <= dr.before_end
            GROUP BY 1
        ),
        after_campaign AS (
            SELECT LOWER(campaign_name) as campaign_lower, SUM(spend) as spend, SUM(sales) as sales
            FROM target_stats t CROSS JOIN date_range dr
            WHERE t.client_id = '{client_id}' AND t.start_date >= dr.after_start AND t.start_date <= dr.latest_date
            GROUP BY 1
        )
        SELECT 
            a.action_date, a.action_type, a.target_text, a.campaign_name, a.ad_group_name,
            COALESCE(bs.spend, bc.spend, 0) as before_spend,
            COALESCE(bs.sales, bc.sales, 0) as before_sales,
            COALESCE(afs.spend, ac.spend, 0) as observed_after_spend,
            COALESCE(afs.sales, ac.sales, 0) as observed_after_sales
        FROM actions_log a CROSS JOIN date_range dr
        LEFT JOIN before_stats bs ON LOWER(a.target_text) = bs.target_lower AND LOWER(a.campaign_name) = bs.campaign_lower
        LEFT JOIN after_stats afs ON LOWER(a.target_text) = afs.target_lower AND LOWER(a.campaign_name) = afs.campaign_lower
        LEFT JOIN before_campaign bc ON LOWER(a.campaign_name) = bc.campaign_lower
        LEFT JOIN after_campaign ac ON LOWER(a.campaign_name) = ac.campaign_lower
        WHERE a.client_id = '{client_id}' AND DATE(a.action_date) < dr.after_start
    """
    
    with pm._get_connection() as conn:
        df = pd.read_sql(query, conn)
        
    if df.empty: return {"revenue_impact": 0, "roas_change": 0}

    # Simplified incremental revenue impact
    # Impact = before_spend * (after_roas - before_roas)
    df['r_before'] = df['before_sales'] / df['before_spend']
    df['r_after'] = df['observed_after_sales'] / df['observed_after_spend']
    df.loc[df['before_spend'] == 0, 'r_before'] = 0
    df.loc[df['observed_after_spend'] == 0, 'r_after'] = 0
    
    df['impact'] = df['before_spend'] * (df['r_after'] - df['r_before'])
    
    # Aggregate
    tot_before_sales = df['before_sales'].sum()
    tot_before_spend = df['before_spend'].sum()
    tot_after_sales = df['observed_after_sales'].sum()
    tot_after_spend = df['observed_after_spend'].sum()
    
    r_before_agg = tot_before_sales / tot_before_spend if tot_before_spend > 0 else 0
    r_after_agg = tot_after_sales / tot_after_spend if tot_after_spend > 0 else 0
    roas_lift = ((r_after_agg - r_before_agg) / r_before_agg * 100) if r_before_agg > 0 else 0
    
    return {
        "revenue_impact": df['impact'].sum(),
        "roas_change": roas_lift,
        "actions": len(df)
    }

def test_windows():
    db_url = 'postgresql://postgres.wuakeiwxkjvhsnmkzywz:Zen%40rise%40123%21@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres'
    pm = PostgresManager(db_url)
    client_id = 'demo_account_2'
    
    results = {}
    for w in [7, 30]:
        res = calculate_impact_locally(pm, client_id, w)
        results[w] = res
        print(f"\n{w}D Result:")
        print(f"  Actions: {res['actions']}")
        print(f"  ROAS Change: {res['roas_change']:.1f}%")
        print(f"  Revenue Impact: ${res['revenue_impact']:,.2f}")

    s7 = results[7]
    s30 = results[30]
    print(f"\nDelta Summary (7D -> 30D):")
    print(f"  Incremental Revenue Shift: ${s30['revenue_impact'] - s7['revenue_impact']:,.2f}")

if __name__ == "__main__":
    test_windows()
