#!/usr/bin/env python3
"""
Orphaned Accounts Migration Script
===================================
Migrates all amazon_accounts without organization_id to the Primary Organization.

Usage:
    python migrate_orphaned_accounts.py
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

def migrate_orphaned_accounts():
    """Migrate all accounts without organization_id to Primary Organization."""

    print("=" * 60)
    print("ORPHANED ACCOUNTS MIGRATION")
    print("=" * 60)

    db = get_db_manager(test_mode=False)

    # Determine primary organization ID
    print("\n[1/4] Finding Primary Organization...")

    primary_org_id = None

    try:
        with db._get_connection() as conn:
            cur = conn.cursor()

            # Check if organizations table exists
            if hasattr(db, 'db_url'):  # PostgresManager
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_name = 'organizations'
                    )
                """)
            else:  # SQLite
                cur.execute("""
                    SELECT name FROM sqlite_master
                    WHERE type='table' AND name='organizations'
                """)

            has_orgs_table = bool(cur.fetchone())

            if has_orgs_table:
                # Try to find existing primary org
                cur.execute("SELECT id FROM organizations LIMIT 1")
                row = cur.fetchone()
                if row:
                    primary_org_id = row[0]
                    print(f"   ✓ Found existing organization: {primary_org_id}")

            if not primary_org_id:
                # Use deterministic UUID for "saddle.io" primary org
                primary_org_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, "saddle.io"))
                print(f"   ✓ Using Primary Org ID: {primary_org_id}")

    except Exception as e:
        print(f"   ⚠ Warning: {e}")
        # Fallback to deterministic UUID
        primary_org_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, "saddle.io"))
        print(f"   ✓ Using Primary Org ID: {primary_org_id}")

    # Find orphaned accounts
    print("\n[2/4] Finding orphaned accounts...")

    orphaned_accounts = []

    try:
        with db._get_connection() as conn:
            cur = conn.cursor()

            # Check if organization_id column exists
            if hasattr(db, 'db_url'):  # Postgres
                cur.execute("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name='amazon_accounts' AND column_name='organization_id'
                """)
            else:  # SQLite
                cur.execute("PRAGMA table_info(amazon_accounts)")
                columns = [row[1] for row in cur.fetchall()]
                has_org_col = 'organization_id' in columns

            if hasattr(db, 'db_url'):
                has_org_col = bool(cur.fetchone())

            if has_org_col:
                # Find accounts with NULL organization_id
                cur.execute("""
                    SELECT id, account_id, account_name
                    FROM amazon_accounts
                    WHERE organization_id IS NULL
                """)
                orphaned_accounts = cur.fetchall()
            else:
                # Column doesn't exist yet - all accounts are orphaned
                cur.execute("""
                    SELECT id, account_id, account_name
                    FROM amazon_accounts
                """)
                orphaned_accounts = cur.fetchall()
                print("   ℹ organization_id column doesn't exist - will migrate all accounts")

    except Exception as e:
        print(f"   ✗ Error finding orphaned accounts: {e}")
        return False

    if not orphaned_accounts:
        print("   ✓ No orphaned accounts found!")
        return True

    print(f"   ✓ Found {len(orphaned_accounts)} orphaned accounts:")
    for acc in orphaned_accounts:
        print(f"      - {acc[2]} ({acc[1]})")

    # Add organization_id column if it doesn't exist
    print("\n[3/4] Ensuring schema has organization_id column...")

    try:
        with db._get_connection() as conn:
            cur = conn.cursor()

            if not has_org_col:
                if hasattr(db, 'db_url'):  # Postgres
                    cur.execute("""
                        ALTER TABLE amazon_accounts
                        ADD COLUMN organization_id TEXT
                    """)
                else:  # SQLite
                    cur.execute("""
                        ALTER TABLE amazon_accounts
                        ADD COLUMN organization_id TEXT
                    """)
                print("   ✓ Added organization_id column")
            else:
                print("   ✓ Column already exists")

    except Exception as e:
        print(f"   ✗ Error adding column: {e}")
        return False

    # Migrate accounts
    print("\n[4/4] Migrating accounts to Primary Organization...")

    migrated_count = 0

    try:
        with db._get_connection() as conn:
            cur = conn.cursor()

            ph = db.placeholder

            for account in orphaned_accounts:
                account_id = account[0]
                account_name = account[2]

                cur.execute(f"""
                    UPDATE amazon_accounts
                    SET organization_id = {ph}
                    WHERE id = {ph}
                """, (primary_org_id, account_id))

                migrated_count += 1
                print(f"   ✓ Migrated: {account_name}")

    except Exception as e:
        print(f"   ✗ Error migrating accounts: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "=" * 60)
    print(f"SUCCESS! Migrated {migrated_count} accounts to Primary Organization")
    print("=" * 60)
    print(f"\nPrimary Organization ID: {primary_org_id}")
    print("\nYou can now view all accounts in Settings > Ad Accounts")

    return True


if __name__ == "__main__":
    try:
        success = migrate_orphaned_accounts()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nMigration cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
