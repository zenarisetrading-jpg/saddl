#!/usr/bin/env python3
"""
Run Migration 006: Add end_date and customer_search_term to target_stats

Usage:
    cd desktop
    python dev_resources/scripts/run_migration_006.py
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(project_root.parent / '.env')

from core.postgres_manager import PostgresManager

def run_migration():
    """Execute migration 006 to fix target_stats schema."""

    print("=" * 60)
    print("Migration 006: target_stats Schema Update")
    print("=" * 60)

    # Get database URL from environment
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("❌ ERROR: DATABASE_URL not set in environment")
        print("   Make sure .env file exists with DATABASE_URL=postgres://...")
        return False

    db = PostgresManager(db_url)

    try:
        with db._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
    except Exception as e:
        print(f"❌ ERROR: Could not connect to database: {e}")
        print("   Check DATABASE_URL in .env file")
        return False

    print("✓ Connected to database")

    # Execute migration steps
    migration_steps = [
        # Step 1: Add columns
        ("Add end_date column",
         "ALTER TABLE target_stats ADD COLUMN IF NOT EXISTS end_date DATE"),

        ("Add customer_search_term column",
         "ALTER TABLE target_stats ADD COLUMN IF NOT EXISTS customer_search_term TEXT"),

        # Step 2: Backfill data
        ("Backfill end_date",
         "UPDATE target_stats SET end_date = start_date + INTERVAL '6 days' WHERE end_date IS NULL"),

        ("Backfill customer_search_term",
         "UPDATE target_stats SET customer_search_term = target_text WHERE customer_search_term IS NULL"),

        # Step 3: Drop old constraints (these may fail if constraint doesn't exist - that's OK)
        ("Drop old constraint (variant 1)",
         "ALTER TABLE target_stats DROP CONSTRAINT IF EXISTS target_stats_client_id_start_date_campaign_name_ad_group_na_key"),

        ("Drop old constraint (variant 2)",
         "ALTER TABLE target_stats DROP CONSTRAINT IF EXISTS target_stats_unique_key"),

        ("Drop old constraint (variant 3)",
         "ALTER TABLE target_stats DROP CONSTRAINT IF EXISTS unique_target_stats"),

        # Step 4: Add new constraint
        ("Add new unique constraint",
         """ALTER TABLE target_stats
            ADD CONSTRAINT target_stats_unique_composite
            UNIQUE (client_id, start_date, campaign_name, ad_group_name, target_text, customer_search_term, match_type)"""),

        # Step 5: Create indexes
        ("Create date range index",
         "CREATE INDEX IF NOT EXISTS idx_target_stats_date_range ON target_stats(client_id, start_date, end_date)"),

        ("Create customer_search_term index",
         "CREATE INDEX IF NOT EXISTS idx_target_stats_cst ON target_stats(client_id, customer_search_term)"),
    ]

    success_count = 0
    error_count = 0

    for step_name, sql in migration_steps:
        try:
            with db._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql)
            print(f"  ✓ {step_name}")
            success_count += 1
        except Exception as e:
            error_msg = str(e)
            # Some errors are expected (constraint already exists, etc.)
            if "already exists" in error_msg:
                print(f"  ⊘ {step_name} (already done)")
                success_count += 1
            else:
                print(f"  ✗ {step_name}: {error_msg}")
                error_count += 1

    print()
    print("-" * 60)

    # Verify the schema
    print("\nVerifying schema...")
    try:
        with db._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_name = 'target_stats'
                    ORDER BY ordinal_position
                """)
                columns = cursor.fetchall()

                print("\ntarget_stats columns:")
                has_end_date = False
                has_cst = False
                for col_name, col_type in columns:
                    marker = ""
                    if col_name == "end_date":
                        has_end_date = True
                        marker = " ← NEW"
                    elif col_name == "customer_search_term":
                        has_cst = True
                        marker = " ← NEW"
                    print(f"    {col_name}: {col_type}{marker}")

                print()
                if has_end_date and has_cst:
                    print("✅ Migration successful! Both columns exist.")
                    return True
                else:
                    missing = []
                    if not has_end_date:
                        missing.append("end_date")
                    if not has_cst:
                        missing.append("customer_search_term")
                    print(f"❌ Migration incomplete. Missing: {', '.join(missing)}")
                    return False

    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False


if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
