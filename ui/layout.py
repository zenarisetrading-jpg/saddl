"""
UI Layout Components

Page setup, sidebar navigation, and home page.
"""

import streamlit as st

from ui.theme import ThemeManager

def setup_page():
    """Setup page CSS and styling."""
    # Apply dynamic theme CSS
    ThemeManager.apply_css()

def render_sidebar(navigate_to):
    """
    Render sidebar navigation.
    
    Args:
        navigate_to: Function to navigate between modules
        
    Returns:
        Selected module name
    """
    # Account selector FIRST (auto-hides if only 1 account)
    from ui.account_manager import render_account_selector
    render_account_selector()
    
    st.sidebar.markdown("## **S2C LaunchPad**")
    
    # Theme Toggle
    ThemeManager.render_toggle()
    
    st.sidebar.markdown("*PPC Intelligence Suite*")
    
    if st.sidebar.button("Home", use_container_width=True):
        navigate_to('home')
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("##### SYSTEM")
    
    # Data Hub - central upload
    if st.sidebar.button("Data Upload", use_container_width=True):
        navigate_to('data_hub')
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("##### ANALYZE")
    
    # Core features
    if st.sidebar.button("Optimizer", use_container_width=True):
        navigate_to('optimizer')
    
    if st.sidebar.button("ASIN Shield", use_container_width=True):
        navigate_to('asin_mapper')
    
    if st.sidebar.button("Clusters", use_container_width=True):
        navigate_to('ai_insights')
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("##### ACTIONS")
    
    if st.sidebar.button("Launchpad", use_container_width=True):
        navigate_to('creator')
    
    st.sidebar.markdown("---")
    
    if st.sidebar.button("Help", use_container_width=True):
        navigate_to('readme')
    
    return st.session_state.get('current_module', 'home')

def render_home():
    """Render the S2C Ads OS Dashboard."""
    
    # Hero Section
    st.markdown("""
    <div style="text-align: center; padding: 40px 0; background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border-radius: 12px; margin-bottom: 30px;">
        <h1 style="font-size: 3rem; margin-bottom: 10px; background: linear-gradient(90deg, #6366f1, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">S2C Ads Operating System</h1>
        <p style="font-size: 1.2rem; color: #94a3b8;">Intelligent PPC Management for Amazon & Noon</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Active Context Badge
    if 'db_manager' in st.session_state and st.session_state['db_manager']:
        db_mode = "TEST (ppc_test.db)" if st.session_state.get('test_mode') else "LIVE (ppc_live.db)"
        st.caption(f"🟢 System Active | Database: {db_mode}")
        
        # Show active account (if multi-account mode)
        if not st.session_state.get('single_account_mode', False):
            active_account = st.session_state.get('active_account_name', 'No account selected')
            st.caption(f"📊 Active Account: **{active_account}**")
    else:
        st.caption("🔴 System Idle | Database Not Connected")

    st.divider()
    
    # Workflow Cards (Ingest -> Analyze -> Optimize -> Execute)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("### 1. Ingest")
        st.info("**Data Hub**")
        st.caption("Upload Search Term Reports, Bulk Files, and Business Reports.")
        if st.button("📂 Go to Data Hub", use_container_width=True):
            st.session_state['current_module'] = 'data_hub'
            st.rerun()

    with col2:
        st.markdown("### 2. Analyze")
        st.info("**Impact Analyzer**")
        st.caption("View wasted spend, missed sales, and ROI opportunities.")
        if st.button("📉 View Impact", use_container_width=True):
            st.session_state['current_module'] = 'impact'
            st.rerun()

    with col3:
        st.markdown("### 3. Optimize")
        st.info("**Optimization Hub**")
        st.caption("Review and approve Bids, Negatives, and Harvests.")
        if st.button("⚡ Run Optimizer", use_container_width=True):
            st.session_state['current_module'] = 'optimizer'
            st.rerun()
            
    with col4:
        st.markdown("### 4. Execute")
        st.info("**Launcher**")
        st.caption("Launch optimized campaigns and push changes to Amazon.")
        if st.button("🚀 Launch Campaigns", use_container_width=True):
            st.session_state['current_module'] = 'creator'
            st.rerun()

    st.divider()
    
    # AI Teaser & Quick Actions
    c_ai, c_docs = st.columns([2, 1])
    
    with c_ai:
        st.markdown("""
        ### 🧠 AI Strategist is Ready
        Your data is automatically analyzed by the AI. Open the chat bubble in the bottom right 
        to ask questions like:
        - *"Where am I wasting the most money?"*
        - *"Draft a strategy to launch SKU X"*
        """)
        
    with c_docs:
        st.markdown("### 📚 Resources")
        if st.button("📖 Documentation", use_container_width=True):
            st.session_state['current_module'] = 'readme'
            st.rerun()
        st.markdown("[Report a Bug](mailto:support@s2c.com)")
    

