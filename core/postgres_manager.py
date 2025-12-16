"""
PostgreSQL Database Manager for Supabase Integration.

Implements the same interface as DatabaseManager but uses psycopg2 and PostgreSQL syntax.
Handles 'ON CONFLICT' for upserts instead of 'INSERT OR REPLACE'.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
from typing import Optional, List, Dict, Any, Union
from datetime import date, datetime, timedelta
from contextlib import contextmanager
import pandas as pd
import uuid

class PostgresManager:
    """
    PostgreSQL persistence for Supabase / Cloud Postgres.
    """
    
    def __init__(self, db_url: str):
        """
        Initialize Postgres manager.
        
        Args:
            db_url: Postgres connection string (postgres://user:pass@host:port/db)
        """
        self.db_url = db_url
        self._init_schema()
    
    @contextmanager
    def _get_connection(self):
        """Context manager for safe database connections."""
        conn = psycopg2.connect(self.db_url, cursor_factory=RealDictCursor)
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _init_schema(self):
        """Create tables if they don't exist."""
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                # Weekly Stats Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS weekly_stats (
                        id SERIAL PRIMARY KEY,
                        client_id TEXT NOT NULL,
                        start_date DATE NOT NULL,
                        end_date DATE NOT NULL,
                        spend DOUBLE PRECISION DEFAULT 0,
                        sales DOUBLE PRECISION DEFAULT 0,
                        roas DOUBLE PRECISION DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(client_id, start_date)
                    )
                """)
                
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_weekly_stats_client_date ON weekly_stats(client_id, start_date)")
                
                # Target Stats Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS target_stats (
                        id SERIAL PRIMARY KEY,
                        client_id TEXT NOT NULL,
                        start_date DATE NOT NULL,
                        campaign_name TEXT NOT NULL,
                        ad_group_name TEXT NOT NULL,
                        target_text TEXT NOT NULL,
                        match_type TEXT,
                        spend DOUBLE PRECISION DEFAULT 0,
                        sales DOUBLE PRECISION DEFAULT 0,
                        clicks INTEGER DEFAULT 0,
                        impressions INTEGER DEFAULT 0,
                        orders INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(client_id, start_date, campaign_name, ad_group_name, target_text)
                    )
                """)
                
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_target_stats_lookup ON target_stats(client_id, start_date, campaign_name)")
                
                # Actions Log Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS actions_log (
                        id SERIAL PRIMARY KEY,
                        action_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        client_id TEXT NOT NULL,
                        batch_id TEXT NOT NULL,
                        entity_name TEXT,
                        action_type TEXT NOT NULL,
                        old_value TEXT,
                        new_value TEXT,
                        reason TEXT,
                        campaign_name TEXT,
                        ad_group_name TEXT,
                        target_text TEXT,
                        match_type TEXT,
                        UNIQUE(client_id, action_date, target_text, action_type, campaign_name)
                    )
                """)
                
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_actions_log_batch ON actions_log(batch_id, action_date)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_actions_log_client ON actions_log(client_id, action_date)")
                
                # Category Mappings
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS category_mappings (
                        client_id TEXT NOT NULL,
                        sku TEXT NOT NULL,
                        category TEXT,
                        sub_category TEXT,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (client_id, sku)
                    )
                """)
                
                # Advertised Product Cache
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS advertised_product_cache (
                        client_id TEXT NOT NULL,
                        campaign_name TEXT,
                        ad_group_name TEXT,
                        sku TEXT,
                        asin TEXT,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(client_id, campaign_name, ad_group_name, sku)
                    )
                """)
                
                # Bulk Mappings
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS bulk_mappings (
                        client_id TEXT NOT NULL,
                        campaign_name TEXT,
                        campaign_id TEXT,
                        ad_group_name TEXT,
                        ad_group_id TEXT,
                        keyword_text TEXT,
                        keyword_id TEXT,
                        targeting_expression TEXT,
                        targeting_id TEXT,
                        sku TEXT,
                        match_type TEXT,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(client_id, campaign_name, ad_group_name, keyword_text, targeting_expression)
                    )
                """)
                
                # Accounts
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS accounts (
                        account_id TEXT PRIMARY KEY,
                        account_name TEXT NOT NULL,
                        account_type TEXT DEFAULT 'brand',
                        metadata TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

    def save_weekly_stats(self, client_id: str, start_date: date, end_date: date, spend: float, sales: float, roas: Optional[float] = None) -> int:
        if roas is None:
            roas = sales / spend if spend > 0 else 0.0
        
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO weekly_stats (client_id, start_date, end_date, spend, sales, roas, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (client_id, start_date) DO UPDATE SET
                        end_date = EXCLUDED.end_date,
                        spend = EXCLUDED.spend,
                        sales = EXCLUDED.sales,
                        roas = EXCLUDED.roas,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING id
                """, (client_id, start_date, end_date, spend, sales, roas))
                result = cursor.fetchone()
                return result['id'] if result else 0

    def save_target_stats_batch(self, df: pd.DataFrame, client_id: str, start_date: Union[date, str] = None) -> int:
        if df is None or df.empty:
            return 0
        
        # NOTE: Reusing the same logic from DB Manager for dataframe processing
        # Identifying columns
        target_col = None
        for col in ['Customer Search Term', 'Targeting', 'Keyword Text']:
            if col in df.columns:
                target_col = col
                break
        
        if target_col is None:
            return 0
            
        required = ['Campaign Name', 'Ad Group Name']
        if not all(col in df.columns for col in required):
            return 0
            
        # Standard aggregation maps
        agg_cols = {}
        if 'Spend' in df.columns: agg_cols['Spend'] = 'sum'
        if 'Sales' in df.columns: agg_cols['Sales'] = 'sum'
        if 'Clicks' in df.columns: agg_cols['Clicks'] = 'sum'
        if 'Impressions' in df.columns: agg_cols['Impressions'] = 'sum'
        if 'Orders' in df.columns: agg_cols['Orders'] = 'sum'
        if 'Match Type' in df.columns: agg_cols['Match Type'] = 'first'
        
        if not agg_cols:
            return 0
        
        df_copy = df.copy()
        
        # Date Logic
        date_col = None
        for col in ['Date', 'Start Date', 'Report Date', 'date', 'start_date']:
            if col in df_copy.columns:
                date_col = col
                break
        
        if date_col:
            if df_copy[date_col].dtype == object and df_copy[date_col].astype(str).str.contains(' - ').any():
                 df_copy[date_col] = df_copy[date_col].astype(str).str.split(' - ').str[0]
            
            df_copy['_date'] = pd.to_datetime(df_copy[date_col], errors='coerce')
            df_copy['_week_start'] = df_copy['_date'].dt.to_period('W-MON').dt.start_time.dt.date
            weeks = df_copy['_week_start'].dropna().unique()
        else:
            if start_date is None:
                start_date = datetime.now().date()
            elif isinstance(start_date, str):
                try:
                    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                except:
                    start_date = datetime.now().date()
            
            days_since_monday = start_date.weekday()
            week_start_monday = start_date - timedelta(days=days_since_monday)
            df_copy['_week_start'] = week_start_monday
            weeks = [week_start_monday]
        
        df_copy['_camp_norm'] = df_copy['Campaign Name'].astype(str).str.lower().str.strip()
        df_copy['_ag_norm'] = df_copy['Ad Group Name'].astype(str).str.lower().str.strip()
        df_copy['_target_norm'] = df_copy[target_col].astype(str).str.lower().str.strip()
        
        total_saved = 0
        
        for week_start in weeks:
            if pd.isna(week_start): continue
            
            week_data = df_copy[df_copy['_week_start'] == week_start]
            if week_data.empty: continue
            
            grouped = week_data.groupby(['_camp_norm', '_ag_norm', '_target_norm']).agg(agg_cols).reset_index()
            
            week_start_str = week_start.isoformat() if isinstance(week_start, date) else str(week_start)[:10]
            
            # Prepare data for bulk insert
            records = []
            for _, row in grouped.iterrows():
                match_type_norm = str(row.get('Match Type', '')).lower().strip()
                records.append((
                    client_id,
                    week_start_str,
                    row['_camp_norm'],
                    row['_ag_norm'],
                    row['_target_norm'],
                    match_type_norm,
                    float(row.get('Spend', 0) or 0),
                    float(row.get('Sales', 0) or 0),
                    int(row.get('Orders', 0) or 0),
                    int(row.get('Clicks', 0) or 0),
                    int(row.get('Impressions', 0) or 0)
                ))
            
            if records:
                with self._get_connection() as conn:
                    with conn.cursor() as cursor:
                        execute_values(cursor, """
                            INSERT INTO target_stats 
                            (client_id, start_date, campaign_name, ad_group_name, target_text, match_type, spend, sales, orders, clicks, impressions, updated_at)
                            VALUES %s
                            ON CONFLICT (client_id, start_date, campaign_name, ad_group_name, target_text) DO UPDATE SET
                                spend = EXCLUDED.spend,
                                sales = EXCLUDED.sales,
                                orders = EXCLUDED.orders,
                                clicks = EXCLUDED.clicks,
                                impressions = EXCLUDED.impressions,
                                updated_at = CURRENT_TIMESTAMP
                        """, records)
                        
                total_saved += len(records)
                
        return total_saved

    def get_all_weekly_stats(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM weekly_stats ORDER BY start_date DESC")
                return cursor.fetchall()
    
    def get_stats_by_client(self, client_id: str) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM weekly_stats WHERE client_id = %s ORDER BY start_date DESC", (client_id,))
                return cursor.fetchall()

    def get_target_stats_by_account(self, account_id: str, limit: int = 50000) -> pd.DataFrame:
        with self._get_connection() as conn:
            query = "SELECT * FROM target_stats WHERE client_id = %s ORDER BY start_date DESC LIMIT %s"
            return pd.read_sql_query(query, conn, params=(account_id, limit))

    def get_target_stats_df(self, client_id: str = 'default_client') -> pd.DataFrame:
        with self._get_connection() as conn:
            query = """
                SELECT 
                    start_date as "Date",
                    campaign_name as "Campaign Name",
                    ad_group_name as "Ad Group Name",
                    target_text as "Targeting",
                    match_type as "Match Type",
                    spend as "Spend",
                    sales as "Sales",
                    orders as "Orders",
                    clicks as "Clicks",
                    impressions as "Impressions"
                FROM target_stats 
                WHERE client_id = %s 
                ORDER BY start_date DESC
            """
            df = pd.read_sql(query, conn, params=(client_id,))
            if not df.empty and 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'])
            return df
            
    def get_stats_by_date_range(self, start_date: date, end_date: date, client_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                if client_id:
                    cursor.execute("""
                        SELECT * FROM weekly_stats 
                        WHERE start_date >= %s AND start_date <= %s AND client_id = %s
                        ORDER BY start_date DESC
                    """, (start_date, end_date, client_id))
                else:
                    cursor.execute("""
                        SELECT * FROM weekly_stats 
                        WHERE start_date >= %s AND start_date <= %s
                        ORDER BY start_date DESC
                    """, (start_date, end_date))
                
                return cursor.fetchall()
    
    def get_unique_clients(self) -> List[str]:
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT DISTINCT client_id FROM weekly_stats ORDER BY client_id")
                return [row['client_id'] for row in cursor.fetchall()]

    def delete_stats_by_client(self, client_id: str) -> int:
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM weekly_stats WHERE client_id = %s", (client_id,))
                rows = cursor.rowcount
                cursor.execute("DELETE FROM target_stats WHERE client_id = %s", (client_id,))
                rows += cursor.rowcount
                cursor.execute("DELETE FROM actions_log WHERE client_id = %s", (client_id,))
                rows += cursor.rowcount
                return rows

    def clear_all_stats(self) -> int:
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM weekly_stats")
                return cursor.rowcount

    def get_connection_status(self) -> tuple[str, str]:
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
            return "Connected (Postgres)", "green"
        except Exception as e:
            return f"Error: {str(e)}", "red"

    def get_stats_summary(self) -> Dict[str, Any]:
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_records,
                        COUNT(DISTINCT client_id) as unique_clients,
                        MIN(start_date) as earliest_date,
                        MAX(start_date) as latest_date,
                        SUM(spend) as total_spend,
                        SUM(sales) as total_sales
                    FROM weekly_stats
                """)
                return dict(cursor.fetchone())

    def save_category_mapping(self, df: pd.DataFrame, client_id: str):
        if df is None or df.empty: return 0
        
        sku_col = df.columns[0]
        cat_col = next((c for c in df.columns if 'category' in c.lower() and 'sub' not in c.lower()), None)
        sub_col = next((c for c in df.columns if 'sub' in c.lower()), None)
        
        data = []
        for _, row in df.iterrows():
            data.append((
                client_id,
                str(row[sku_col]),
                str(row[cat_col]) if cat_col and pd.notna(row[cat_col]) else None,
                str(row[sub_col]) if sub_col and pd.notna(row[sub_col]) else None
            ))
            
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                execute_values(cursor, """
                    INSERT INTO category_mappings (client_id, sku, category, sub_category, updated_at)
                    VALUES %s
                    ON CONFLICT (client_id, sku) DO UPDATE SET
                        category = EXCLUDED.category,
                        sub_category = EXCLUDED.sub_category,
                        updated_at = CURRENT_TIMESTAMP
                """, data)
        return len(data)

    def get_category_mappings(self, client_id: str) -> pd.DataFrame:
        with self._get_connection() as conn:
            return pd.read_sql("SELECT sku as SKU, category as Category, sub_category as 'Sub-Category' FROM category_mappings WHERE client_id = %s", conn, params=(client_id,))

    def save_advertised_product_map(self, df: pd.DataFrame, client_id: str):
        if df is None or df.empty: return 0
        
        required = ['Campaign Name', 'Ad Group Name']
        if not all(c in df.columns for c in required): return 0
        
        sku_col = 'SKU' if 'SKU' in df.columns else None
        asin_col = 'ASIN' if 'ASIN' in df.columns else None
        
        data = []
        for _, row in df.iterrows():
            data.append((
                client_id,
                row['Campaign Name'],
                row['Ad Group Name'],
                str(row[sku_col]) if sku_col and pd.notna(row[sku_col]) else None,
                str(row[asin_col]) if asin_col and pd.notna(row[asin_col]) else None
            ))
            
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                execute_values(cursor, """
                    INSERT INTO advertised_product_cache 
                    (client_id, campaign_name, ad_group_name, sku, asin, updated_at)
                    VALUES %s
                    ON CONFLICT (client_id, campaign_name, ad_group_name, sku) DO UPDATE SET
                        asin = EXCLUDED.asin,
                        updated_at = CURRENT_TIMESTAMP
                """, data)
        return len(data)

    def get_advertised_product_map(self, client_id: str) -> pd.DataFrame:
        with self._get_connection() as conn:
            return pd.read_sql("SELECT campaign_name as 'Campaign Name', ad_group_name as 'Ad Group Name', sku as SKU, asin as ASIN FROM advertised_product_cache WHERE client_id = %s", conn, params=(client_id,))

    def save_bulk_mapping(self, df: pd.DataFrame, client_id: str):
        if df is None or df.empty: return 0
        
        sku_col = next((c for c in df.columns if c.lower() in ['sku', 'msku', 'vendor sku', 'vendor_sku']), None)
        cid_col = 'CampaignId' if 'CampaignId' in df.columns else None
        aid_col = 'AdGroupId' if 'AdGroupId' in df.columns else None
        kwid_col = 'KeywordId' if 'KeywordId' in df.columns else None
        tid_col = 'TargetingId' if 'TargetingId' in df.columns else None
        
        kw_text_col = next((c for c in df.columns if c.lower() in ['keyword text', 'customer search term']), None)
        tgt_expr_col = next((c for c in df.columns if c.lower() in ['product targeting expression', 'targetingexpression']), None)
        mt_col = 'Match Type' if 'Match Type' in df.columns else None
        
        data = []
        for _, row in df.iterrows():
            if 'Campaign Name' not in row: continue
            
            data.append((
                client_id,
                str(row['Campaign Name']),
                str(row[cid_col]) if cid_col and pd.notna(row.get(cid_col)) else None,
                str(row.get('Ad Group Name')) if 'Ad Group Name' in df.columns and pd.notna(row.get('Ad Group Name')) else None,
                str(row[aid_col]) if aid_col and pd.notna(row.get(aid_col)) else None,
                str(row[kw_text_col]) if kw_text_col and pd.notna(row.get(kw_text_col)) else None,
                str(row[kwid_col]) if kwid_col and pd.notna(row.get(kwid_col)) else None,
                str(row[tgt_expr_col]) if tgt_expr_col and pd.notna(row.get(tgt_expr_col)) else None,
                str(row[tid_col]) if tid_col and pd.notna(row.get(tid_col)) else None,
                str(row[sku_col]) if sku_col and pd.notna(row.get(sku_col)) else None,
                str(row[mt_col]) if mt_col and pd.notna(row.get(mt_col)) else None
            ))
            
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                execute_values(cursor, """
                    INSERT INTO bulk_mappings 
                    (client_id, campaign_name, campaign_id, ad_group_name, ad_group_id, 
                        keyword_text, keyword_id, targeting_expression, targeting_id, sku, match_type, updated_at)
                    VALUES %s
                    ON CONFLICT (client_id, campaign_name, ad_group_name, keyword_text, targeting_expression) DO UPDATE SET
                        campaign_id = EXCLUDED.campaign_id,
                        ad_group_id = EXCLUDED.ad_group_id,
                        keyword_id = EXCLUDED.keyword_id,
                        targeting_id = EXCLUDED.targeting_id,
                        sku = EXCLUDED.sku,
                        match_type = EXCLUDED.match_type,
                        updated_at = CURRENT_TIMESTAMP
                """, data)
        return len(data)

    def get_bulk_mapping(self, client_id: str) -> pd.DataFrame:
        with self._get_connection() as conn:
            return pd.read_sql("""
                SELECT 
                    campaign_name as "Campaign Name", 
                    campaign_id as "CampaignId", 
                    ad_group_name as "Ad Group Name", 
                    ad_group_id as "AdGroupId",
                    keyword_text as "Customer Search Term",
                    keyword_id as "KeywordId",
                    targeting_expression as "Product Targeting Expression",
                    targeting_id as "TargetingId",
                    sku as "SKU",
                    match_type as "Match Type"
                FROM bulk_mappings 
                WHERE client_id = %s
            """, conn, params=(client_id,))

    def log_action_batch(self, actions: List[Dict[str, Any]], client_id: str, batch_id: Optional[str] = None, action_date: Optional[str] = None) -> int:
        if not actions: return 0
        if batch_id is None: batch_id = str(uuid.uuid4())[:8]
        if action_date:
            date_str = str(action_date)[:10] if action_date else datetime.now().isoformat()
        else:
            date_str = datetime.now().isoformat()
            
        data = []
        for action in actions:
            data.append((
                date_str,
                client_id,
                batch_id,
                action.get('entity_name', ''),
                action.get('action_type', 'UNKNOWN'),
                str(action.get('old_value', '')),
                str(action.get('new_value', '')),
                action.get('reason', ''),
                action.get('campaign_name', ''),
                action.get('ad_group_name', ''),
                action.get('target_text', ''),
                action.get('match_type', '')
            ))
            
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                execute_values(cursor, """
                    INSERT INTO actions_log 
                    (action_date, client_id, batch_id, entity_name, action_type, old_value, new_value, 
                        reason, campaign_name, ad_group_name, target_text, match_type)
                    VALUES %s
                    ON CONFLICT (client_id, action_date, target_text, action_type, campaign_name) DO NOTHING
                """, data)
        return len(actions)

    def create_account(self, account_id: str, account_name: str, account_type: str = 'brand', metadata: dict = None) -> bool:
        import json
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    metadata_json = json.dumps(metadata) if metadata else '{}'
                    cursor.execute("""
                        INSERT INTO accounts (account_id, account_name, account_type, metadata)
                        VALUES (%s, %s, %s, %s)
                    """, (account_id, account_name, account_type, metadata_json))
                    return True
        except psycopg2.IntegrityError:
            return False

    def get_all_accounts(self) -> List[tuple]:
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT account_id, account_name, account_type FROM accounts ORDER BY account_name")
                return [(row['account_id'], row['account_name'], row['account_type']) for row in cursor.fetchall()]

    def get_account(self, account_id: str) -> Optional[Dict[str, Any]]:
        import json
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM accounts WHERE account_id = %s", (account_id,))
                row = cursor.fetchone()
                if row:
                    result = dict(row)
                    if result.get('metadata'):
                        try:
                            result['metadata'] = json.loads(result['metadata'])
                        except:
                            result['metadata'] = {}
                    return result
                return None

