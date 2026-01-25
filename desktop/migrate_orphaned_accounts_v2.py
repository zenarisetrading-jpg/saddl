#!/usr/bin/env python3
"""
Orphaned Accounts Migration Script v2
======================================
Migrates accounts without organization_id to the Primary Organization.
Works with both SQLite (accounts table) and Postgres (amazon_accounts table).

Usage:
    python migrate_orphaned_accounts_v2.py [--dry-run]
"""

import os
import sys
from pathlib import Path

# Add desktop to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / '.env')
    load_dotenv(Path(__file__).parent.parent / '.env')
except ImportError:
    pass

from core.db_manager import get_db_manager
import uuid


def get_table_schema(db, conn, table_name):
    """Get column names for a table."""
    cur = conn.cursor()

    if hasattr(db, 'db_url'):  # Postgres
        cur.execute(f"""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = '{table_name}'
            ORDER BY ordinal_position
        """)
        return [row[0] for row in cur.fetchall()]
    else:  # SQLite
        cur.execute(f"PRAGMA table_info({table_name})")
        return [row[1] for row in cur.fetchall()]


def table_exists(db, conn, table_name):
    """Check if a table exists."""
    cur = conn.cursor()

    if hasattr(db, 'db_url'):  # Postgres
        cur.execute(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = '{table_name}'
            )
        """)
        return cur.fetchone()[0]
    else:  # SQLite
        cur.execute(f"""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='{table_name}'
        """)
        return bool(cur.fetchone())


def migrate_orphaned_accounts(dry_run=False):
    """Migrate all accounts without organization_id to Primary Organization."""

    print("=" * 70)
    print("ORPHANED ACCOUNTS MIGRATION v2")
    if dry_run:
        print("DRY RUN MODE - No changes will be made")
    print("=" * 70)

    db = get_db_manager(test_mode=False)
    is_postgres = hasattr(db, 'db_url')

    print(f"\nDatabase Type: {'Postgres' if is_postgres else 'SQLite'}")

    # Step 1: Determine which table exists
    print("\n[1/5] Detecting account table...")

    with db._get_connection() as conn:
        # Check for both possible table names
        has_accounts = table_exists(db, conn, 'accounts')
        has_amazon_accounts = table_exists(db, conn, 'amazon_accounts')

        if has_amazon_accounts:
            table_name = 'amazon_accounts'
            print(f"   ✓ Found: amazon_accounts (Postgres schema)")
        elif has_accounts:
            table_name = 'accounts'
            print(f"   ✓ Found: accounts (SQLite schema)")
        else:
            print("   ✗ No account table found!")
            print("      Expected 'accounts' or 'amazon_accounts'")
            return False

        # Get schema
        columns = get_table_schema(db, conn, table_name)
        print(f"   ✓ Table columns: {', '.join(columns)}")

        # Determine ID column and name column
        if 'id' in columns:
            id_col = 'id'
        elif 'account_id' in columns:
            id_col = 'account_id'
        else:
            print("   ✗ No ID column found (expected 'id' or 'account_id')")
            return False

        if 'display_name' in columns:
            name_col = 'display_name'
            extra_col = 'marketplace' if 'marketplace' in columns else None
        elif 'account_name' in columns:
            name_col = 'account_name'
            extra_col = 'account_type' if 'account_type' in columns else None
        else:
            print("   ✗ No name column found")
            return False

    # Step 2: Find Primary Organization
    print("\n[2/5] Finding Primary Organization...")

    primary_org_id = None

    with db._get_connection() as conn:
        cur = conn.cursor()

        if table_exists(db, conn, 'organizations'):
            cur.execute("SELECT id FROM organizations LIMIT 1")
            row = cur.fetchone()
            if row:
                primary_org_id = row[0]
                print(f"   ✓ Found existing organization: {primary_org_id}")

        if not primary_org_id:
            # Use deterministic UUID
            primary_org_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, "saddle.io"))
            print(f"   ✓ Using deterministic Primary Org ID: {primary_org_id}")

    # Step 3: Find orphaned accounts
    print("\n[3/5] Finding orphaned accounts...")

    orphaned_accounts = []

    with db._get_connection() as conn:
        cur = conn.cursor()

        has_org_col = 'organization_id' in columns

        if has_org_col:
            # Query with columns we detected
            select_cols = f"{id_col}, {name_col}"
            if extra_col:
                select_cols += f", {extra_col}"

            cur.execute(f"""
                SELECT {select_cols}
                FROM {table_name}
                WHERE organization_id IS NULL OR organization_id = ''
            """)
            orphaned_accounts = cur.fetchall()
        else:
            print("   ℹ organization_id column doesn't exist - all accounts are orphaned")
            select_cols = f"{id_col}, {name_col}"
            if extra_col:
                select_cols += f", {extra_col}"

            cur.execute(f"SELECT {select_cols} FROM {table_name}")
            orphaned_accounts = cur.fetchall()

    if not orphaned_accounts:
        print("   ✓ No orphaned accounts found!")
        return True

    print(f"   ✓ Found {len(orphaned_accounts)} orphaned account(s):")
    for acc in orphaned_accounts:
        display = f"{acc[1]}"
        if len(acc) > 2 and acc[2]:
            display += f" ({acc[2]})"
        print(f"      - {display}")

    # Step 4: Add organization_id column if needed
    if not has_org_col:
        print("\n[4/5] Adding organization_id column...")

        if dry_run:
            print("   [DRY RUN] Would add organization_id column")
        else:
            with db._get_connection() as conn:
                cur = conn.cursor()

                if is_postgres:
                    cur.execute(f"""
                        ALTER TABLE {table_name}
                        ADD COLUMN organization_id TEXT
                    """)
                else:
                    cur.execute(f"""
                        ALTER TABLE {table_name}
                        ADD COLUMN organization_id TEXT
                    """)
                print("   ✓ Added organization_id column")
    else:
        print("\n[4/5] Schema check...")
        print("   ✓ organization_id column already exists")

    # Step 5: Migrate accounts
    print("\n[5/5] Migrating accounts to Primary Organization...")

    if dry_run:
        print(f"   [DRY RUN] Would migrate {len(orphaned_accounts)} account(s)")
        for acc in orphaned_accounts:
            print(f"      - {acc[1]} → {primary_org_id}")
    else:
        migrated_count = 0

        with db._get_connection() as conn:
            cur = conn.cursor()
            ph = db.placeholder

            for account in orphaned_accounts:
                account_id_value = account[0]
                account_name_value = account[1]

                cur.execute(f"""
                    UPDATE {table_name}
                    SET organization_id = {ph}
                    WHERE {id_col} = {ph}
                """, (primary_org_id, account_id_value))

                migrated_count += 1
                print(f"   ✓ Migrated: {account_name_value}")

        print("\n" + "=" * 70)
        print(f"SUCCESS! Migrated {migrated_count} account(s) to Primary Organization")
        print("=" * 70)
        print(f"\nPrimary Organization ID: {primary_org_id}")
        print(f"Table: {table_name}")
        print("\nYou can now view all accounts in Settings > Ad Accounts")

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
