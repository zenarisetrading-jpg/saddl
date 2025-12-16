import streamlit as st

class ThemeManager:
    """Manages dynamic theme switching (Dark/Light) via CSS injection."""
    
    @staticmethod
    def init_theme():
        """Initialize theme state if not present."""
        if 'theme_mode' not in st.session_state:
            st.session_state.theme_mode = 'dark' # Default

    @staticmethod
    def render_toggle():
        """Render the toggle in sidebar and apply styles."""
        ThemeManager.init_theme()
        
        # Toggle Switch
        is_dark = st.sidebar.toggle('🌙 Dark Mode', value=(st.session_state.theme_mode == 'dark'))
        
        # Update State
        new_mode = 'dark' if is_dark else 'light'
        if new_mode != st.session_state.theme_mode:
            st.session_state.theme_mode = new_mode
            st.rerun() # Rerun to apply changes instantly
            
        # Apply CSS
        ThemeManager.apply_css()
        
    @staticmethod
    def apply_css():
        """Inject CSS based on current mode."""
        ThemeManager.init_theme() # Ensure state exists
        mode = st.session_state.theme_mode
        
        if mode == 'dark':
            bg_color = "#111827"
            sec_bg = "#1f2937"
            text_color = "#f3f4f6"
            border_color = "#374151"
            card_bg = "#1f2937"
        else:
            bg_color = "#ffffff"
            sec_bg = "#f3f4f6"
            text_color = "#111827"
            border_color = "#e5e7eb"
            card_bg = "#ffffff"

        css = f"""
        <style>
            :root {{
                --bg-color: {bg_color};
                --secondary-bg: {sec_bg};
                --text-color: {text_color};
                --border-color: {border_color};
                --card-bg: {card_bg};
            }}
            
            /* Main App Background */
            .stApp {{
                background-color: var(--bg-color);
                color: var(--text-color);
            }}
            
            /* Sidebar Background */
            [data-testid="stSidebar"] {{
                background-color: var(--secondary-bg);
            }}
            
            /* Text Colors - Targeted Fixes */
            h1, h2, h3, h4, h5, h6, .stMarkdown p, .stMarkdown li, .stText {{
                color: var(--text-color);
            }}

            /* Sidebar Specific Text Fix */
            [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label, [data-testid="stSidebar"] .stMarkdown {{
                color: var(--text-color) !important;
            }}

            /* Metric Values Fix */
            [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {{
                color: var(--text-color) !important;
            }}
            
            /* Inputs / Selectboxes */
            .stSelectbox div[data-baseweb="select"] > div {{
                background-color: var(--secondary-bg);
                color: var(--text-color);
                border-color: var(--border-color);
            }}
            
            /* Streamlit Metrics (Built-in) */
            div[data-testid="metric-container"] {{
                background-color: var(--card-bg);
                border: 1px solid var(--border-color);
                padding: 10px;
                border-radius: 8px;
            }}
        </style>
        """
        st.markdown(css, unsafe_allow_html=True)

    @staticmethod
    def get_chart_template():
        """Return the Plotly template name."""
        return 'plotly_dark' if st.session_state.get('theme_mode', 'dark') == 'dark' else 'plotly_white'
