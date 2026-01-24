"""
Login Screen
============
Minimal login interface wiring.
PRD Reference: ORG_USERS_ROLES_PRD.md §12

Note: This is a UI shell. Integration with auth middleware happens in the main app flow.

Views:
- login: Main login form
- forgot_password: Password reset request
- accept_invite: Invitation acceptance (Phase 2)
"""

import streamlit as st
from core.auth.middleware import AuthError


def _check_for_invitation_token() -> bool:
    """
    Check if URL contains an invitation token.
    If so, route to the accept_invite page.

    Returns:
        True if token found and routing to accept_invite, False otherwise
    """
    try:
        params = st.query_params
        token = params.get("token")

        if token:
            # Route to invitation acceptance
            st.session_state['auth_view'] = 'accept_invite'
            return True
    except Exception:
        pass

    return False



def render_forgot_password():
    """Renders the forgot password form."""
    
    # 1. Logo
    # 1. Logo
    from ui.theme import ThemeManager
    # Login page force uses 'dark' or 'light'? Usually dark background implies dark logo or light logo against dark bg.
    # login page has dark styling (rgba(255,255,255,0.02) bg). So we want the default logo (which is usually for dark mode).
    # Checking previous code: filename was hardcoded "saddle_logo.png" (default).
    logo_data = ThemeManager.get_cached_logo('dark')
    
    if logo_data:
        st.markdown(
            f"""
            <div style="text-align: center; margin-bottom: 0.5rem;">
                <img src="data:image/png;base64,{logo_data}" style="width: 320px; max-width: 80%; opacity: 1.0;"> 
            </div>
            """, 
            unsafe_allow_html=True
        )

    # 2. Header
    st.markdown('<h1 class="login-title">Reset Password</h1>', unsafe_allow_html=True)
    st.markdown('<div class="login-subtitle">Enter your email to receive reset instructions</div>', unsafe_allow_html=True)

    # 3. Form
    with st.form("forgot_form"):
        email = st.text_input("Email", placeholder="user@example.com")
        
        submitted = st.form_submit_button("Send Instructions", type="primary")
        
        if submitted:
            if not email:
                st.error("Please enter your email address")
            else:
                from core.auth.service import AuthService
                service = AuthService()
                if service.request_password_reset(email):
                    st.success("Instructions sent! Check your email for a temporary password.")
                else:
                    st.error("Unable to process request.")

    # 4. Back Link
    if st.button("← Back to Log In", type="secondary", use_container_width=True):
        st.session_state['auth_view'] = 'login'
        st.rerun()

def render_login():
    """Renders the login flow (Dispatcher)."""

    # State Management
    if 'auth_view' not in st.session_state:
        st.session_state['auth_view'] = 'login'

    # Check for invitation token in URL (Phase 2)
    # This must happen before CSS to allow accept_invite to apply its own styles
    _check_for_invitation_token()

    # Route to accept_invite if that's the current view
    if st.session_state['auth_view'] == 'accept_invite':
        from ui.auth.accept_invite import render_accept_invite
        render_accept_invite()
        return

    # Global CSS for Auth Screens
    st.markdown("""
        <style>
        /* Widened container for better desktop experience */
        .block-container { max-width: 600px; padding-top: 2rem; padding-bottom: 5rem; }

        /* Ensure image is perfectly centered */
        img { display: block; margin-left: auto; margin-right: auto; }

        h1.login-title { font-family: 'Inter', sans-serif; font-weight: 700; font-size: 2.2rem; text-align: center; margin-top: 0; margin-bottom: 0.5rem; color: white; }
        div.login-subtitle { text-align: center; color: #94a3b8; margin-bottom: 2.5rem; font-size: 1rem; }
        div[data-testid="stForm"] { border: 1px solid rgba(255, 255, 255, 0.1); background-color: rgba(255, 255, 255, 0.02); padding: 3rem; border-radius: 16px; }
        button[kind="primary"] { width: 100%; background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%) !important; border: none; color: white !important; font-weight: 600; padding: 0.75rem 0; font-size: 1rem; }
        button[kind="primary"]:hover { box-shadow: 0 4px 12px rgba(14, 165, 233, 0.4); transform: translateY(-1px); }
        /* Link Button Styling */
        button[kind="secondary"] { border: none !important; background: transparent !important; color: #94a3b8 !important; }
        button[kind="secondary"]:hover { color: white !important; }
        #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
        </style>
    """, unsafe_allow_html=True)

    if st.session_state['auth_view'] == 'forgot_password':
        render_forgot_password()
        return

    # --- LOGIN VIEW ---
    
    # 1. Logo
    # 1. Logo
    from ui.theme import ThemeManager
    logo_data = ThemeManager.get_cached_logo('dark')
    
    if logo_data:
        st.markdown(
            f"""
            <div style="text-align: center; margin-bottom: 0.5rem;">
                <img src="data:image/png;base64,{logo_data}" style="width: 320px; max-width: 80%; opacity: 1.0;"> 
            </div>
            """, 
            unsafe_allow_html=True
        )
    else:
        st.title("SADDLE")

    # 2. Header
    st.markdown('<h1 class="login-title">Welcome Back</h1>', unsafe_allow_html=True)
    st.markdown('<div class="login-subtitle">Sign in to your account</div>', unsafe_allow_html=True)
    
    # 3. Form
    with st.form("login_form"):
        email = st.text_input("Email", placeholder="user@example.com")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        
        submitted = st.form_submit_button("Log In", type="primary")
        
        if submitted:
            if not email or not password:
                st.error("Please enter email and password")
            else:
                from core.auth.service import AuthService
                auth = AuthService()
                
                result = auth.sign_in(email, password)
                if result["success"]:
                    st.success(f"Welcome back!")
                    st.rerun()
                else:
                    st.error(result.get("error", "Login failed"))

    # 4. Footer / Forgot Pwd
    col1, col2 = st.columns([1, 1])
    with col1: pass
    with col2: pass
        
    if st.button("Forgot Password?", type="secondary", use_container_width=True):
        st.session_state['auth_view'] = 'forgot_password'
        st.rerun()

    st.markdown("""
        </div>
        
        <!-- DEBUG: DB Connection Info -->
        <div style="text-align: center; margin-top: 2rem; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 15px;">
            <p style="font-size: 0.7rem; color: #475569; margin: 0;">
                System Status
            </p>
    """, unsafe_allow_html=True)

    # Check DB Type
    try:
        from core.db_manager import get_db_manager
        db = get_db_manager()
        db_type = db.__class__.__name__
        is_postgres = "Postgres" in db_type
        
        status_color = "#10b981" if is_postgres else "#f59e0b"
        status_text = "🟢 Connected (Postgres)" if is_postgres else "🟠 Local Storage (SQLite)"
        
        st.markdown(f"""
            <div style="text-align: center; font-size: 0.75rem; color: {status_color}; font-weight: 600; margin-top: 4px;">
                {status_text}
            </div>
            <div style="text-align: center; font-size: 0.65rem; color: #475569; margin-top: 4px; font-family: monospace;">
                v1.2 • {db_type}
            </div>
        """, unsafe_allow_html=True)

        if st.checkbox("Show Debug Tools"):
             if st.button("Repair Admin Account"):
                 try:
                     from core.seeding import seed_initial_data, DEFAULT_ADMIN_EMAIL, DEFAULT_ADMIN_PASSWORD
                     from core.auth.service import AuthService

                     st.info("Step 1: Dropping existing users table if schema is incorrect...")
                     auth = AuthService()

                     # Drop and recreate users table to fix schema issues
                     with auth._get_connection() as conn:
                         cur = conn.cursor()

                         # Check if we're using Postgres
                         if hasattr(auth.db_manager, 'connection_pool'):
                             st.info("Detected Postgres - dropping and recreating tables with UUID schema...")
                             cur.execute("DROP TABLE IF EXISTS user_account_overrides CASCADE")
                             cur.execute("DROP TABLE IF EXISTS users CASCADE")

                             # Recreate with correct schema
                             cur.execute("""
                                 CREATE TABLE users (
                                     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                                     organization_id TEXT NOT NULL,
                                     email TEXT NOT NULL UNIQUE,
                                     password_hash TEXT NOT NULL,
                                     role TEXT NOT NULL,
                                     billable BOOLEAN DEFAULT TRUE,
                                     status TEXT DEFAULT 'ACTIVE',
                                     must_reset_password BOOLEAN DEFAULT FALSE,
                                     password_updated_at TIMESTAMP,
                                     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                     updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                                 )
                             """)

                             cur.execute("""
                                 CREATE TABLE user_account_overrides (
                                     id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                                     user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                                     amazon_account_id TEXT NOT NULL,
                                     role TEXT NOT NULL,
                                     created_by TEXT,
                                     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                     UNIQUE(user_id, amazon_account_id)
                                 )
                             """)
                             st.success("Tables recreated with UUID schema")
                         else:
                             st.info("Using SQLite - schema should be correct already")

                     # Run seeding
                     st.info("Step 2: Creating default admin user...")
                     seed_initial_data()
                     st.success(f"Seeding complete! Try logging in as {DEFAULT_ADMIN_EMAIL} / {DEFAULT_ADMIN_PASSWORD}")

                     # Double check existence
                     with auth._get_connection() as conn:
                         cur = conn.cursor()
                         cur.execute(f"SELECT email, role FROM users WHERE email = '{DEFAULT_ADMIN_EMAIL}'")
                         row = cur.fetchone()
                         if row:
                             st.success(f"✅ User verified in DB: {row[0]} ({row[1]})")
                         else:
                             st.error("Still not found in DB after seeding!")

                 except Exception as e:
                     st.error(f"Repair failed: {e}")
                     import traceback
                     st.code(traceback.format_exc())

    except Exception as e:
         st.markdown(f"""
            <div style="text-align: center; font-size: 0.75rem; color: #ef4444; margin-top: 4px;">
                🔴 System Error: {str(e)[:50]}...
            </div>
        """, unsafe_allow_html=True)
