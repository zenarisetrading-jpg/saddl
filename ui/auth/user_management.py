"""
User Management UI
==================
Screen for managing users, roles, and invites.
PRD Reference: ORG_USERS_ROLES_PRD.md §11, §13

Features:
- List users
- Invite user (with billing warning)
- Role assignment
"""

import streamlit as st
from core.auth.permissions import Role, PERMISSION_MATRIX, get_billable_default
from core.auth.middleware import require_permission

# Example price (could come from config/DB)
SEAT_PRICE = 49.00

def render_user_management():
    st.header("User Management")

    # V2 Backend Wiring
    from core.auth.service import AuthService
    auth = AuthService()
    current_user = auth.get_current_user()
    
    # 1. User List (Real Data)
    st.subheader("Team Members")
    
    if current_user:
        users = auth.list_users(current_user.organization_id)
        if not users:
             st.info("No users found (except you?)")
             
        for user in users:
            col1, col2, col3 = st.columns([3, 2, 2])
            with col1:
                st.write(user["email"])
                if user["id"] == current_user.id:
                    st.caption("(You)")
            with col2:
                st.code(user["role"])
            with col3:
                st.caption(user["status"])
                # Admin Reset Action
                # Only show if:
                # 1. Current user is Admin/Owner (Actually middleware handles page access, but logic here too)
                # 2. Target != Self
                if user["id"] != current_user.id:
                    # Unique key needed for button inside loop
                    if st.button("Reset Pwd", key=f"reset_{user['id']}", help="Force reset user password"):
                        res = auth.admin_reset_password(current_user, str(user["id"]))
                        if res.success:
                            st.warning(f"⚠️ Temp Password for {user['email']}: {res.reason}")
                            st.info("User will be forced to change this on next login.")
                        else:
                            st.error(res.reason)
    else:
        st.error("Session error.")
            
    st.divider()
    
    # 2. Invite User
    st.subheader("Invite New User")
    
    with st.form("invite_user_form"):
        new_email = st.text_input("Email Address")
        new_role_str = st.selectbox(
            "Role", 
            options=[r.value for r in Role], 
            index=2 # Default to OPERATOR
        )
        
        # Billing Warning Logic (Soft Enforcement)
        is_billable = get_billable_default(new_role_str)
        if is_billable:
            st.warning(
                f"⚠️ Adding this user will add ${SEAT_PRICE}/month to your bill "
                "(pro-rated for the rest of this billing cycle)."
            )
        else:
            st.info("ℹ️ This role is non-billable (free).")
            
        submitted = st.form_submit_button("Create User")
        
        if submitted:
            if not new_email:
                st.error("Email required")
            else:
                if current_user:
                    res = auth.create_user_invite(new_email, Role(new_role_str), current_user.organization_id)
                    if res["success"]:
                        st.success(f"User created: {new_email}")
                        st.info(f"🔑 Temporary Password: **{res.get('temp_password', 'Welcome123!')}**")
                        st.balloons()
                    else:
                        st.error(f"Failed: {res.get('error')}")
                else:
                     st.error("You must be logged in.")
