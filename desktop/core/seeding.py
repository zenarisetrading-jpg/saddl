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
            cur.execute("SELECT COUNT(*) FROM users")
            count = cur.fetchone()[0]
            
            if count > 0:
                print(f"SEED: Found {count} users. Skipping seed.")
                return

            print("SEED: No users found. Creating default admin...")
            
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
        print(f"SEED: Error during seeding: {e}")
