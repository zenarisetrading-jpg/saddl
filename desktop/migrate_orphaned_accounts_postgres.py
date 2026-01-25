#!/usr/bin/env python3
"""
Orphaned Accounts Migration Script - POSTGRES ONLY
===================================================
Migrates accounts in POSTGRES database without organization_id to Primary Organization.

IMPORTANT: This script connects to your production Postgres database.
           Make sure DATABASE_URL is set in your environment or .env file.

Usage:
    # Set DATABASE_URL first
    export DATABASE_URL="postgresql://user:pass@host:port/dbname"

    # Or create .env file with:
    # DATABASE_URL=postgresql://user:pass@host:port/dbname

    # Test first with dry-run
    python migrate_orphaned_accounts_postgres.py --dry-run

    # Then run for real
    python migrate_orphaned_accounts_postgres.py
"""

import os
import sys
from pathlib import Path

# Add desktop to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables from root folder first
try:
    from dotenv import load_dotenv
    # Try root folder first (/saddle/.env)
    load_dotenv(Path(__file__).parent.parent / '.env')
    # Then desktop folder (/saddle/desktop/.env)
    load_dotenv(Path(__file__).parent / '.env')
except ImportError:
    pass

import uuid


def get_postgres_connection():
    """Get direct Postgres connection."""
    db_url = os.getenv("DATABASE_URL")

    if not db_url:
        print("=" * 70)
        print("ERROR: DATABASE_URL not found!")
        print("=" * 70)
        print("\nPlease set your DATABASE_URL environment variable:")
        print("\nOption 1: Export in terminal")
        print('  export DATABASE_URL="postgresql://user:pass@host:port/dbname"')
        print("\nOption 2: Create .env file")
        print('  echo "DATABASE_URL=postgresql://user:pass@host:port/dbname" > .env')
        print("\nOption 3: Get from Streamlit Cloud")
        print("  - Go to your Streamlit Cloud app settings")
        print("  - Copy the DATABASE_URL from secrets")
        print("=" * 70)
        sys.exit(1)

    try:
        import psycopg2
        from psycopg2 import pool
    except ImportError:
        print("ERROR: psycopg2 not installed!")
        print("Install it with: pip install psycopg2-binary")
        sys.exit(1)

    return psycopg2.connect(db_url)


def get_table_schema(conn, table_name):
    """Get column names for a table."""
    cur = conn.cursor()
    cur.execute(f"""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = '{table_name}'
        ORDER BY ordinal_position
    """)
    return [row[0] for row in cur.fetchall()]


def table_exists(conn, table_name):
    """Check if a table exists."""
    cur = conn.cursor()
    cur.execute(f"""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_name = '{table_name}'
        )
    """)
    return cur.fetchone()[0]


def migrate_orphaned_accounts(dry_run=False):
    """Migrate all accounts without organization_id to Primary Organization."""

    print("=" * 70)
    print("ORPHANED ACCOUNTS MIGRATION - POSTGRES")
    if dry_run:
        print("DRY RUN MODE - No changes will be made")
    print("=" * 70)

    # Connect to Postgres
    print("\n[1/6] Connecting to Postgres...")

    try:
        conn = get_postgres_connection()
        print("   ✓ Connected to Postgres")
    except Exception as e:
        print(f"   ✗ Connection failed: {e}")
        return False

    # Step 2: Determine which table exists
    print("\n[2/6] Detecting account table...")

    try:
        # Check for both possible table names
        has_accounts = table_exists(conn, 'accounts')
        has_amazon_accounts = table_exists(conn, 'amazon_accounts')

        if has_amazon_accounts:
            table_name = 'amazon_accounts'
            print(f"   ✓ Found: amazon_accounts")
        elif has_accounts:
            table_name = 'accounts'
            print(f"   ✓ Found: accounts")
        else:
            print("   ✗ No account table found!")
            print("      Expected 'accounts' or 'amazon_accounts'")
            conn.close()
            return False

        # Get schema
        columns = get_table_schema(conn, table_name)
        print(f"   ✓ Columns: {', '.join(columns)}")

        # Determine column names
        if 'id' in columns:
            id_col = 'id'
        elif 'account_id' in columns:
            id_col = 'account_id'
        else:
            print("   ✗ No ID column found")
            conn.close()
            return False

        if 'display_name' in columns:
            name_col = 'display_name'
            extra_col = 'marketplace' if 'marketplace' in columns else None
        elif 'account_name' in columns:
            name_col = 'account_name'
            extra_col = 'account_type' if 'account_type' in columns else None
        else:
            print("   ✗ No name column found")
            conn.close()
            return False

        has_org_col = 'organization_id' in columns

    except Exception as e:
        print(f"   ✗ Error: {e}")
        conn.close()
        return False

    # Step 3: Find Primary Organization
    print("\n[3/6] Finding Primary Organization...")

    primary_org_id = None

    try:
        cur = conn.cursor()

        if table_exists(conn, 'organizations'):
            cur.execute("SELECT id FROM organizations LIMIT 1")
            row = cur.fetchone()
            if row:
                primary_org_id = str(row[0])
                print(f"   ✓ Found organization: {primary_org_id}")

        if not primary_org_id:
            # Use deterministic UUID
            primary_org_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, "saddle.io"))
            print(f"   ✓ Using Primary Org ID: {primary_org_id}")

    except Exception as e:
        print(f"   ✗ Error: {e}")
        conn.close()
        return False

    # Step 4: Find orphaned accounts
    print("\n[4/6] Finding orphaned accounts...")

    orphaned_accounts = []

    try:
        cur = conn.cursor()

        select_cols = f"{id_col}, {name_col}"
        if extra_col:
            select_cols += f", {extra_col}"

        if has_org_col:
            cur.execute(f"""
                SELECT {select_cols}
                FROM {table_name}
                WHERE organization_id IS NULL OR organization_id = ''
            """)
            orphaned_accounts = cur.fetchall()
        else:
            print("   ℹ organization_id column doesn't exist - all accounts are orphaned")
            cur.execute(f"SELECT {select_cols} FROM {table_name}")
            orphaned_accounts = cur.fetchall()

    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        conn.close()
        return False

    if not orphaned_accounts:
        print("   ✓ No orphaned accounts found!")
        conn.close()
        return True

    print(f"   ✓ Found {len(orphaned_accounts)} orphaned account(s):")
    for acc in orphaned_accounts:
        display = f"{acc[1]}"
        if len(acc) > 2 and acc[2]:
            display += f" ({acc[2]})"
        print(f"      - {display}")

    # Step 5: Add organization_id column if needed
    if not has_org_col:
        print("\n[5/6] Adding organization_id column...")

        if dry_run:
            print("   [DRY RUN] Would add organization_id column")
        else:
            try:
                cur = conn.cursor()
                cur.execute(f"""
                    ALTER TABLE {table_name}
                    ADD COLUMN organization_id TEXT
                """)
                conn.commit()
                print("   ✓ Added organization_id column")
            except Exception as e:
                print(f"   ✗ Error: {e}")
                conn.rollback()
                conn.close()
                return False
    else:
        print("\n[5/6] Schema check...")
        print("   ✓ organization_id column exists")

    # Step 6: Migrate accounts
    print("\n[6/6] Migrating accounts...")

    if dry_run:
        print(f"   [DRY RUN] Would migrate {len(orphaned_accounts)} account(s) to:")
        print(f"   Organization ID: {primary_org_id}")
        for acc in orphaned_accounts:
            print(f"      - {acc[1]}")
    else:
        migrated_count = 0

        try:
            cur = conn.cursor()

            for account in orphaned_accounts:
                account_id_value = account[0]
                account_name_value = account[1]

                cur.execute(f"""
                    UPDATE {table_name}
                    SET organization_id = %s
                    WHERE {id_col} = %s
                """, (primary_org_id, account_id_value))

                migrated_count += 1
                print(f"   ✓ Migrated: {account_name_value}")

            conn.commit()

            print("\n" + "=" * 70)
            print(f"SUCCESS! Migrated {migrated_count} account(s)")
            print("=" * 70)
            print(f"\nOrganization ID: {primary_org_id}")
            print(f"Table: {table_name}")
            print("\nRefresh your app - accounts should now appear in Settings > Ad Accounts")

        except Exception as e:
            print(f"   ✗ Error: {e}")
            import traceback
            traceback.print_exc()
            conn.rollback()
            conn.close()
            return False

    conn.close()
    return True


if __name__ == "__main__":
    try:
        dry_run = '--dry-run' in sys.argv
        success = migrate_orphaned_accounts(dry_run=dry_run)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nMigration cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
