"""
Account Settings Module

Provides user settings and account management interface.
Two-tabbed main panel:
1. User Settings - Personal details, change password
2. Create Ad Account - Ad account creation form

Styling follows brand guidelines (BRAND_GUIDELINES.md)
"""
import streamlit as st
from auth.service import AuthService


def run_account_settings():
    """Main entry point for Account Settings module."""
    
    # Page header with icon
    icon_color = "#9A9AAA"  # Slate Grey
    settings_icon = f'<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="{icon_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 10px;"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>'
    
    st.markdown(f'<h1 style="margin-bottom: 2rem; font-size: 2.2rem; font-weight: 800; text-transform: uppercase; letter-spacing: -0.02em; color: #E9EAF0;">{settings_icon}ACCOUNT SETTINGS</h1>', unsafe_allow_html=True)
    
    # Tab navigation styling
    st.markdown("""
    <style>
    /* Premium Tab Buttons */
    div[data-testid="stHorizontalBlock"] div.stButton > button {
        background: rgba(154, 154, 170, 0.05) !important;
        border: 1px solid rgba(154, 154, 170, 0.15) !important;
        color: #9A9AAA !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
        padding: 8px 16px !important;
    }
    div[data-testid="stHorizontalBlock"] div.stButton > button:hover {
        background: rgba(154, 154, 170, 0.1) !important;
        border-color: rgba(91, 86, 112, 0.3) !important;
        color: #E9EAF0 !important;
    }
    /* Active Tab Styling */
    div[data-testid="stHorizontalBlock"] div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #5B5670 0%, #464156 100%) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: #E9EAF0 !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize active tab
    if 'active_settings_tab' not in st.session_state:
        st.session_state['active_settings_tab'] = "User Settings"
    
    # Tab buttons
    col1, col2, col_spacer = st.columns([1, 1, 2])
    with col1:
        is_active = st.session_state['active_settings_tab'] == "User Settings"
        if st.button("👤 USER SETTINGS", key="btn_user_settings", use_container_width=True, type="primary" if is_active else "secondary"):
            st.session_state['active_settings_tab'] = "User Settings"
            st.rerun()
    with col2:
        is_active = st.session_state['active_settings_tab'] == "Ad Accounts"
        if st.button("🏢 AD ACCOUNTS", key="btn_ad_accounts", use_container_width=True, type="primary" if is_active else "secondary"):
            st.session_state['active_settings_tab'] = "Ad Accounts"
            st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Render active tab
    if st.session_state['active_settings_tab'] == "User Settings":
        _render_user_settings()
    else:
        _render_ad_accounts()


def _render_user_settings():
    """Render the User Settings tab - Profile, email, password change."""
    auth = AuthService()
    user = auth.get_current_user()
    user_email = auth.get_user_email()
    
    # Card container style
    card_style = """
        background: rgba(91, 86, 112, 0.08);
        border: 1px solid rgba(91, 86, 112, 0.15);
        border-radius: 16px;
        padding: 2rem;
        margin-bottom: 1.5rem;
    """
    
    # Get existing user metadata
    user_metadata = {}
    if user:
        user_metadata = getattr(user, 'user_metadata', {}) or {}
    
    # Profile Information (Read-only)
    st.markdown(f"""
        <div style="{card_style}">
            <h3 style="color: #E9EAF0; font-size: 1.1rem; font-weight: 600; margin: 0 0 1rem 0; letter-spacing: 0.5px;">
                Account Information
            </h3>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
            <div style="margin-bottom: 1rem;">
                <label style="color: #9A9AAA; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px;">Email Address</label>
                <p style="color: #E9EAF0; font-size: 1rem; margin: 0.25rem 0 0 0; font-weight: 500;">{user_email or 'Not available'}</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        user_id = getattr(user, 'id', 'N/A') if user else 'N/A'
        user_id_display = str(user_id)[:12] if user_id != 'N/A' else 'N/A'
        st.markdown(f"""
            <div style="margin-bottom: 1rem;">
                <label style="color: #9A9AAA; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px;">User ID</label>
                <p style="color: #9A9AAA; font-size: 0.85rem; margin: 0.25rem 0 0 0; font-family: monospace;">{user_id_display}...</p>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Editable Profile Section
    st.markdown(f"""
        <div style="{card_style}">
            <h3 style="color: #E9EAF0; font-size: 1.1rem; font-weight: 600; margin: 0 0 0.5rem 0; letter-spacing: 0.5px;">
                Edit Profile
            </h3>
            <p style="color: #9A9AAA; font-size: 0.85rem; margin: 0 0 1rem 0;">Update your personal information</p>
        </div>
    """, unsafe_allow_html=True)
    
    with st.form("edit_profile_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            full_name = st.text_input(
                "Full Name",
                value=user_metadata.get('full_name', ''),
                placeholder="John Doe",
                key="profile_name"
            )
            company = st.text_input(
                "Company / Organization",
                value=user_metadata.get('company', ''),
                placeholder="Acme Corp",
                key="profile_company"
            )
        
        with col2:
            phone = st.text_input(
                "Phone Number",
                value=user_metadata.get('phone', ''),
                placeholder="+1 234 567 8900",
                key="profile_phone"
            )
            role = st.text_input(
                "Job Title / Role",
                value=user_metadata.get('role', ''),
                placeholder="PPC Manager",
                key="profile_role"
            )
        
        submitted = st.form_submit_button("Save Profile", type="primary", use_container_width=True)
        
        if submitted:
            # Update user metadata in Supabase
            update_data = {
                'full_name': full_name,
                'phone': phone,
                'company': company,
                'role': role
            }
            result = auth.update_user_metadata(update_data)
            if result.get("success"):
                st.success("✅ Profile updated successfully!")
                st.rerun()
            else:
                st.error(result.get("error", "Failed to update profile"))
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Change Password Section
    st.markdown(f"""
        <div style="{card_style}">
            <h3 style="color: #E9EAF0; font-size: 1.1rem; font-weight: 600; margin: 0 0 1rem 0; letter-spacing: 0.5px;">
                Change Password
            </h3>
        </div>
    """, unsafe_allow_html=True)
    
    with st.form("change_password_form", clear_on_submit=True):
        new_password = st.text_input(
            "New Password",
            type="password",
            placeholder="Minimum 8 characters",
            key="settings_new_pwd"
        )
        confirm_password = st.text_input(
            "Confirm New Password",
            type="password",
            placeholder="Confirm your new password",
            key="settings_confirm_pwd"
        )
        
        submitted = st.form_submit_button("Update Password", type="primary", use_container_width=True)
        
        if submitted:
            if not new_password or not confirm_password:
                st.error("Please fill in both fields")
            elif new_password != confirm_password:
                st.error("Passwords do not match")
            elif len(new_password) < 8:
                st.error("Password must be at least 8 characters")
            else:
                result = auth.update_password(new_password)
                if result["success"]:
                    st.success("✅ Password updated successfully!")
                else:
                    st.error(result.get("error", "Failed to update password"))
    
    # Action Management Section
    st.markdown(f"""
        <div style="{card_style}">
            <h3 style="color: #E9EAF0; font-size: 1.1rem; font-weight: 600; margin: 0 0 0.5rem 0; letter-spacing: 0.5px;">
                Action Management
            </h3>
            <p style="color: #9A9AAA; font-size: 0.85rem; margin: 0 0 1rem 0;">Manage your optimization action history</p>
        </div>
    """, unsafe_allow_html=True)
    
    client_id = st.session_state.get('active_account_id')
    
    if client_id:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("""
                <p style="color: #9A9AAA; font-size: 0.9rem; margin-top: 8px;">
                    Clear all optimization actions logged today for the current account.
                    This cannot be undone.
                </p>
            """, unsafe_allow_html=True)
        with col2:
            if st.button("🗑️ Clear Today's Actions", type="secondary", use_container_width=True, key="clear_todays_actions"):
                from ui.action_confirmation import clear_todays_actions
                deleted = clear_todays_actions(client_id)
                if deleted > 0:
                    st.success(f"✅ Cleared {deleted} actions from today.")
                else:
                    st.info("No actions found for today.")
    else:
        st.caption("Select an account from the sidebar to manage actions.")


def _render_ad_accounts():
    """Render the Ad Accounts tab - List and create accounts."""
    db = st.session_state.get('db_manager')
    
    if not db:
        st.error("Database not initialized")
        return
    
    # Get all accounts
    accounts = db.get_all_accounts()
    
    # Card container style
    card_style = """
        background: rgba(91, 86, 112, 0.08);
        border: 1px solid rgba(91, 86, 112, 0.15);
        border-radius: 16px;
        padding: 2rem;
        margin-bottom: 1.5rem;
    """
    
    # Existing Accounts Section
    st.markdown(f"""
        <div style="{card_style}">
            <h3 style="color: #E9EAF0; font-size: 1.1rem; font-weight: 600; margin: 0 0 1rem 0; letter-spacing: 0.5px;">
                Your Ad Accounts ({len(accounts)})
            </h3>
        </div>
    """, unsafe_allow_html=True)
    
    if accounts:
        for acc_id, acc_name, acc_type in accounts:
            is_active = st.session_state.get('active_account_id') == acc_id
            status_badge = '<span style="background: #2A8EC9; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.7rem; margin-left: 8px;">ACTIVE</span>' if is_active else ''
            
            st.markdown(f"""
                <div style="background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(91, 86, 112, 0.1); border-radius: 8px; padding: 1rem; margin-bottom: 0.75rem; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="color: #E9EAF0; font-weight: 600;">{acc_name}</span>{status_badge}
                        <br>
                        <span style="color: #9A9AAA; font-size: 0.8rem;">{acc_type.upper()} • <code style="background: rgba(0,0,0,0.2); padding: 2px 4px; border-radius: 3px;">{acc_id}</code></span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No ad accounts yet. Create one below.")
    
    # Create New Account Section
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"""
        <div style="{card_style}">
            <h3 style="color: #E9EAF0; font-size: 1.1rem; font-weight: 600; margin: 0 0 1rem 0; letter-spacing: 0.5px;">
                ➕ Create New Ad Account
            </h3>
        </div>
    """, unsafe_allow_html=True)
    
    with st.form("create_account_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            account_name = st.text_input(
                "Account Name",
                placeholder="MyBrand Premium or Acme Corp",
                key="new_acc_name"
            )
        
        with col2:
            account_type = st.selectbox(
                "Account Type",
                ["brand", "client", "marketplace", "test"],
                key="new_acc_type",
                help="Choose the type that best describes this account"
            )
        
        # Optional metadata
        with st.expander("Additional Info (Optional)"):
            meta_col1, meta_col2 = st.columns(2)
            with meta_col1:
                marketplace = st.text_input("Marketplace", placeholder="Amazon US")
            with meta_col2:
                currency = st.selectbox("Currency", ["USD", "AED", "SAR", "GBP", "EUR", "INR"])
            notes = st.text_area("Notes", placeholder="Additional notes about this account")
        
        submitted = st.form_submit_button("Create Account", type="primary", use_container_width=True)
        
        if submitted:
            if not account_name:
                st.error("Please enter an Account Name")
            else:
                # Auto-generate ID from name
                account_id = account_name.lower().replace(' ', '_').replace('-', '_')
                account_id = ''.join(c for c in account_id if c.isalnum() or c == '_')
                
                metadata = {
                    "marketplace": marketplace if 'marketplace' in dir() else "",
                    "currency": currency if 'currency' in dir() else "USD",
                    "notes": notes if 'notes' in dir() else ""
                }
                
                success = db.create_account(account_id, account_name, account_type, metadata)
                
                if success:
                    st.success(f"✅ Account '{account_name}' created successfully!")
                    st.caption(f"Account ID: `{account_id}`")
                    
                    # Set as active account
                    st.session_state['active_account_id'] = account_id
                    st.session_state['active_account_name'] = account_name
                    
                    # Clear cached data for new account
                    if 'unified_data' in st.session_state:
                        st.session_state.unified_data = {
                            'search_term_report': None,
                            'advertised_product_report': None,
                            'bulk_id_mapping': None,
                            'category_mapping': None,
                            'enriched_data': None,
                            'upload_status': {
                                'search_term_report': False,
                                'advertised_product_report': False,
                                'bulk_id_mapping': False,
                                'category_mapping': False
                            },
                            'upload_timestamps': {}
                        }
                    
                    st.rerun()
                else:
                    st.error("❌ Account already exists. Try a different name.")
