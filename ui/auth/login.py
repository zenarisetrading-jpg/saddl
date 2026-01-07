"""
Login Screen
============
Minimal login interface wiring.
PRD Reference: ORG_USERS_ROLES_PRD.md §12

Note: This is a UI shell. Integration with auth middleware happens in the main app flow.
"""

import streamlit as st
from core.auth.middleware import AuthError

def render_login():
    """Renders the login form."""
    st.title("Sign In")
    
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        
        submitted = st.form_submit_button("Login")
        
        if submitted:
            if not email or not password:
                st.error("Please enter email and password")
                return
            
            # V2 Logic
            from core.auth.service import AuthService
            auth = AuthService()
            
            result = auth.sign_in(email, password)
            if result["success"]:
                st.success(f"Welcome back, {result['user'].email}!")
                st.rerun() # Reloads app, now authenticated
            else:
                st.error(result.get("error", "Login failed"))
