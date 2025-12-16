"""
Shared UI Components

Reusable UI elements to ensure consistent styling across modules.
"""

import streamlit as st

def metric_card(label: str, value: str, delta: str = None, color: str = None, border_color: str = "#333", subtitle: str = None):
    """
    Render a styled metric card using HTML.
    
    Args:
        label: The label text (e.g. "Spend")
        value: The value text (e.g. "AED 1,234")
        delta: Optional percentage change (e.g. "+12%")
        color: Text color for the value (default white)
        border_color: Border color for the card (default dark grey)
        subtitle: Optional subtitle text below the value
    """
    delta_html = ""
    if delta:
        delta_val = delta.strip().replace('%', '').replace('+', '')
        try:
            is_positive = float(delta_val) > 0
            text_color = "#4ade80" if is_positive else "#f87171"  # Green / Red
            arrow = "↑" if is_positive else "↓"
            delta_html = f'<span style="color: {text_color}; font-size: 14px; margin-left: 8px;">{arrow} {delta}</span>'
        except:
            delta_html = f'<span style="color: #888; font-size: 14px; margin-left: 8px;">{delta}</span>'

    subtitle_html = ""
    if subtitle:
        subtitle_html = f'<p style="color: #888; font-size: 11px; margin: 4px 0 0 0;">{subtitle}</p>'

    label_color = "var(--text-color)"
    if not color:
        color = "var(--text-color)"
    
    # Use custom border color if provided
    border_style = f"border: 1px solid {border_color};" if border_color else "border: 1px solid var(--border-color);"
    
    # Build HTML as single line to avoid Streamlit rendering issues
    html = f'<div style="background-color: var(--card-bg); padding: 15px; border-radius: 8px; {border_style} margin-bottom: 10px; height: 100%;"><p style="color: {label_color}; opacity: 0.7; font-size: 12px; margin: 0 0 5px 0;">{label}</p><div style="display: flex; align-items: baseline;"><p style="color: {color}; font-size: 20px; font-weight: bold; margin: 0;">{value}</p>{delta_html}</div>{subtitle_html}</div>'
    st.markdown(html, unsafe_allow_html=True)
