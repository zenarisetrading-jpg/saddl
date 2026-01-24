
import sys
import os
from pathlib import Path

# Add project root to path
# We assume we are in saddle/desktop/dev_resources/scripts
# We need to add saddle/desktop to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from core.auth.service import AuthService
from core.db_manager import get_db_manager

def update_admin_email():
    print("Connecting to database...")
    auth_service = AuthService()
    
    # We need to interact with the DB directly or use list_users
    # AuthService uses self._get_connection()
    
    try:
        with auth_service._get_connection() as conn:
            cur = conn.cursor()
            
            print("Listing all users:")
            cur.execute("SELECT id, email, role, status FROM users")
            users = cur.fetchall()
            for u in users:
                print(f" - {u}")
                
            old_email = "admin@saddle.io"
            new_email = "admin@saddl.io"
            
            # Check for old email
            cur.execute("SELECT id FROM users WHERE email = %s", (old_email,))
            row = cur.fetchone()
            
            if row:
                user_id = row[0]
                print(f"\nFound user with old email {old_email} (ID: {user_id})")
                
                # Check if new email already exists (to avoid unique constraint violation)
                cur.execute("SELECT id FROM users WHERE email = %s", (new_email,))
                existing_new = cur.fetchone()
                
                if existing_new:
                    print(f"WARNING: User with new email {new_email} ALREADY EXISTS (ID: {existing_new[0]}).")
                    print("Cannot update old user to new email because it would conflict.")
                    # Maybe delete the old one? Or the new one?
                    # For now, just report it.
                else:
                    print(f"Updating email from {old_email} to {new_email}...")
                    cur.execute("UPDATE users SET email = %s WHERE id = %s", (new_email, user_id))
                    print("Update successful!")
            else:
                print(f"\nUser {old_email} NOT FOUND.")
                
                # Check if maybe it's already updated?
                cur.execute("SELECT id FROM users WHERE email = %s", (new_email,))
                if cur.fetchone():
                    print(f"User {new_email} ALREADY EXISTS. It seems the update was already done?")
                else:
                    print(f"Neither {old_email} nor {new_email} exist.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    update_admin_email()
