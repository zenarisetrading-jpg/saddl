"""
Database Seeding Module
=======================
Handles initialization of default data (e.g., admin user) for fresh deployments.
This is critical for Streamlit Cloud where the SQLite DB is ephemeral.
"""

import os
from core.auth.service import AuthService
from core.auth.models import Role

DEFAULT_ADMIN_EMAIL = "admin@saddle.io"
DEFAULT_ADMIN_PASSWORD = "admin123"

def seed_initial_data():
    """
    Check if users exist. If not, create default admin.
    """
    print("SEED: Checking for existing users...")
    
    auth_service = AuthService()
    
    # We need to peek into the DB directly or use list_users (if org_id known)
    # Since we might not have an org yet, let's use a direct check via the service's connection
    # or just try to create the user and catch "already exists".
    
    # Check if ANY user exists (to avoid re-seeding if we have data)
    try:
        with auth_service._get_connection() as conn:
            cur = conn.cursor()
            # Check if default admin explicitly exists
            ph = auth_service.db_manager.placeholder
            cur.execute(f"SELECT id FROM users WHERE email = {ph}", (DEFAULT_ADMIN_EMAIL,))
            admin_check = cur.fetchone()
            
            if admin_check:
                print(f"SEED: Default admin ({DEFAULT_ADMIN_EMAIL}) exists. Skipping seed.")
                return

            print("SEED: Default admin not found. Creating...")
            
            # Create Default Organization ID (e.g., 'primary')
            default_org_id = "primary-org"
            
            # Create Admin
            success = auth_service.create_user_manual(
                email=DEFAULT_ADMIN_EMAIL,
                password=DEFAULT_ADMIN_PASSWORD,
                role=Role.ADMIN,
                org_id=default_org_id
            )
            
            if success:
                print(f"SEED: Successfully created default admin: {DEFAULT_ADMIN_EMAIL}")
                print(f"SEED: Password: {DEFAULT_ADMIN_PASSWORD}")
            else:
                print("SEED: Failed to create default admin.")
            
    except Exception as e:
        import traceback
        print(f"SEED ERROR: {e}")
        traceback.print_exc()
