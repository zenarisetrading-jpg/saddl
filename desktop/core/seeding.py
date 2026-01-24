"""
Database Seeding Module
=======================
Handles initialization of default data (e.g., admin user) for fresh deployments.
This is critical for Streamlit Cloud where the SQLite DB is ephemeral.
"""

import os
import uuid
from core.auth.service import AuthService
from core.auth.models import Role

DEFAULT_ADMIN_EMAIL = "admin@saddl.io"
DEFAULT_ADMIN_PASSWORD = "admin123"

def seed_initial_data():
    """
    Check if users exist. If not, create default admin.
    """
    print("SEED: Starting initialization...")
    
    auth_service = AuthService()

    # Determine default org details
    # Deterministic UUID for primary org
    default_org_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, "saddle.io"))
    default_org_name = "Primary Organization"
    
    # 1. Ensure Default Organization Exists (Always run this to backfill)
    try:
        with auth_service._get_connection() as conn:
            cur = conn.cursor()
            ph = auth_service.db_manager.placeholder
            # UPSERT Organization
            cur.execute(f"""
                INSERT INTO organizations (id, name, type) VALUES ({ph}, {ph}, 'SELLER')
                ON CONFLICT (id) DO NOTHING
            """, (default_org_id, default_org_name))
            print(f"SEED: Verified Organization {default_org_id}")
    except Exception as org_err:
        print(f"SEED WARNING: Failed to seed organization: {org_err}")
        # We continue because the critical part is the user creation, 
        # and maybe the table doesn't exist yet in some weird state, 
        # but we want to try the user check/create anyway.

    
    # 2. Check if admin exists (Read-only)
    admin_exists = False
    try:
        with auth_service._get_connection() as conn:
            cur = conn.cursor()
            ph = auth_service.db_manager.placeholder
            cur.execute(f"SELECT id FROM users WHERE email = {ph}", (DEFAULT_ADMIN_EMAIL,))
            if cur.fetchone():
                admin_exists = True
    except Exception as e:
        print(f"SEED CHECK ERROR: {e}")
        return f"Error checking DB: {e}"

    if admin_exists:
        msg = f"SEED: Default admin ({DEFAULT_ADMIN_EMAIL}) exists. skipping user creation."
        print(msg)
        return msg

    print("SEED: Default admin not found. Creating...")
    
    # 3. Create Admin (Write)
    try:
        success = auth_service.create_user_manual(
            email=DEFAULT_ADMIN_EMAIL,
            password=DEFAULT_ADMIN_PASSWORD,
            role=Role.ADMIN,
            org_id=default_org_id
        )
        
        if success:
            msg = f"SEED: Successfully created default admin: {DEFAULT_ADMIN_EMAIL}"
            print(msg)
            return msg
        else:
            msg = "SEED: Failed to create default admin (Internal Error)."
            print(msg)
            return msg
            
    except Exception as e:
        msg = f"SEED ERROR during creation: {e}"
        print(msg)
        return msg
