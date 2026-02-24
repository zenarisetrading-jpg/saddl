import urllib.parse
import uuid
import streamlit as st

def generate_amazon_oauth_url(client_id: str | None = None, force_new_state: bool = False) -> str:
    """
    Generates the Amazon LWA OAuth consent URL.
    Creates a unique client_id (state) to track this connection request.
    """
    # Existing-account path: use the provided client_id as OAuth state.
    # Callback persists this value as client_settings.client_id.
    if client_id:
        state = str(client_id)
    else:
        # Onboarding/new-account path keeps previous behavior.
        if force_new_state or 'amazon_oauth_state' not in st.session_state:
            st.session_state['amazon_oauth_state'] = f"sc-{uuid.uuid4().hex[:12]}"
        state = st.session_state['amazon_oauth_state']
    
    # Construct the SP-API OAuth URL
    # Replace with your actual LWA App Client ID from the Amazon Developer Console
    client_id = "amzn1.application-oa2-client.01f9593238f1407788692c0bde4500b5" 
    
    params = {
        "application_id": client_id,
        "redirect_uri": "https://wuakeiwxkjvhsnmkzywz.supabase.co/functions/v1/amazon-oauth-callback",
        "version": "beta",
        "state": state
    }
    
    base_url = "https://sellercentral.amazon.ae/apps/authorize/consent"
    return f"{base_url}?{urllib.parse.urlencode(params)}"
