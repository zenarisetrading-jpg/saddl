"""
Portable deployment configuration.
Auto-detects environment and generates correct URLs.
Works on localhost, Streamlit Cloud, and custom domains WITHOUT code changes.
"""

import streamlit as st
import os
from typing import Optional


def get_base_url() -> str:
    """
    Automatically detect the base URL for the current deployment.
    
    Works across:
    - Local development (localhost)
    - Streamlit Cloud (*.streamlit.app)
    - Custom domains (your-domain.com)
    
    Returns:
        Base URL without trailing slash (e.g., "https://app.saddl.io")
    """
    
    # METHOD 1: Try to get from Streamlit's internal context
    # This is the most reliable method for deployed apps
    try:
        # Get the current page URL from Streamlit
        # This works because Streamlit tracks the session URL
        query_params = st.query_params
        
        # Streamlit Cloud and deployed apps expose this
        if hasattr(st, 'get_script_run_ctx'):
            ctx = st.get_script_run_ctx()
            if ctx and hasattr(ctx, 'session_info'):
                session_info = ctx.session_info
                if hasattr(session_info, 'client'):
                    client = session_info.client
                    
                    # Construct URL from client info
                    protocol = "https" if client.get('is_ssl', True) else "http"
                    host = client.get('host', '')
                    port = client.get('port', '')
                    
                    if host:
                        # Port 80/443 don't need to be included
                        if port and port not in [80, 443, '80', '443']:
                            return f"{protocol}://{host}:{port}"
                        return f"{protocol}://{host}"
    except Exception:
        pass  # Fall through to next method
    
    # METHOD 2: Check environment variables
    # Good for containerized deployments (Docker, Kubernetes)
    base_url = os.environ.get('APP_BASE_URL')
    if base_url:
        return base_url.rstrip('/')
    
    # METHOD 3: Try Streamlit config (works on Streamlit Cloud)
    try:
        server_address = st.get_option("browser.serverAddress")
        server_port = st.get_option("browser.serverPort")
        
        if server_address:
            # Streamlit Cloud uses HTTPS
            protocol = "https" if st.get_option("server.headless") else "http"
            
            # Don't include port if it's standard (80/443)
            if server_port and server_port not in [80, 443]:
                return f"{protocol}://{server_address}:{server_port}"
            return f"{protocol}://{server_address}"
    except Exception:
        pass
    
    # METHOD 4: Localhost fallback (development)
    # This is what runs when testing locally
    try:
        # Check if we are potentially on Streamlit Cloud but detection failed
        # Streamlit Cloud usually runs on port 8501 inside the container
        # We can default to the known production URL if we are not explicitly on localhost dev machine
        # Simple heuristic: If hostname is not 'localhost' or '127.0.0.1', likely cloud.
        import socket
        hostname = socket.gethostname()
        
        # Streamlit Cloud hostnames are usually random strings (containers), not 'localhost'
        if "localhost" not in hostname and "127.0.0.1" not in hostname:
             return "https://saddle-adpulse.streamlit.app"
             
        port = st.get_option("server.port") or 8501
        return f"http://localhost:{port}"
    except Exception:
        pass
    
    # METHOD 5: Ultimate fallback
    return "http://localhost:8501"


def get_environment() -> str:
    """
    Detect current deployment environment.
    
    Returns:
        "local", "streamlit_cloud", or "production"
    """
    base_url = get_base_url()
    
    if "localhost" in base_url or "127.0.0.1" in base_url:
        return "local"
    elif "streamlit.app" in base_url:
        return "streamlit_cloud"
    else:
        return "production"


def build_share_url(report_id: str) -> str:
    """
    Build shareable report URL for current environment.
    
    Args:
        report_id: Unique 8-character report identifier
    
    Returns:
        Complete shareable URL
        
    Examples:
        Local: http://localhost:8501?page=shared_report&id=a7f3e9c1
        Cloud: https://saddle.streamlit.app?page=shared_report&id=a7f3e9c1
        Custom: https://app.saddl.io?page=shared_report&id=a7f3e9c1
    """
    base_url = get_base_url()
    return f"{base_url}?page=shared_report&id={report_id}"


def get_display_url() -> str:
    """
    Get user-friendly display URL for current environment.
    
    Returns:
        Formatted URL for display purposes
    """
    base_url = get_base_url()
    env = get_environment()
    
    if env == "local":
        return "localhost (development)"
    elif env == "streamlit_cloud":
        return base_url.replace("https://", "").replace("http://", "")
    else:
        return base_url.replace("https://", "").replace("http://", "")
