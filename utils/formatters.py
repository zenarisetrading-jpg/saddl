"""
Output Formatting Utilities

Functions for creating Excel files, CSVs, and other output formats.
"""

import pandas as pd
from io import BytesIO
from typing import Dict, Union

def dataframe_to_excel(df: pd.DataFrame, sheet_name: str = "Sheet1") -> bytes:
    """
    Convert DataFrame to Excel bytes.
    
    Args:
        df: DataFrame to convert
        sheet_name: Name for the Excel sheet
        
    Returns:
        Excel file as bytes
    """
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    return output.getvalue()

def dict_to_excel(data_dict: Dict[str, pd.DataFrame], filename_prefix: str = "data") -> bytes:
    """
    Convert dictionary of DataFrames to multi-sheet Excel.
    
    Args:
        data_dict: Dictionary where keys are sheet names, values are DataFrames
        filename_prefix: Prefix for filename (not used in bytes output)
        
    Returns:
        Excel file as bytes
    """
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for sheet_name, df in data_dict.items():
            if not df.empty:
                # Truncate sheet name to 31 chars (Excel limit)
                safe_name = sheet_name[:31]
                df.to_excel(writer, sheet_name=safe_name, index=False)
    
    return output.getvalue()

def format_currency(value: float, currency: str = "AED") -> str:
    """
    Format number as currency.
    
    Args:
        value: Numeric value
        currency: Currency code
        
    Returns:
        Formatted string like "AED 1,234.56"
    """
    return f"{currency} {value:,.2f}"

def format_percentage(value: float, decimals: int = 2) -> str:
    """
    Format number as percentage.
    
    Args:
        value: Numeric value (e.g., 0.1234 or 12.34)
        decimals: Number of decimal places
        
    Returns:
        Formatted string like "12.34%"
    """
    # Handle both decimal (0.1234) and percentage (12.34) formats
    if value < 1:
        value = value * 100
    
    return f"{value:.{decimals}f}%"

def format_large_number(value: float) -> str:
    """
    Format large numbers with K/M suffixes.
    
    Args:
        value: Numeric value
        
    Returns:
        Formatted string like "1.2K" or "3.4M"
    """
    if value >= 1_000_000:
        return f"{value/1_000_000:.1f}M"
    elif value >= 1_000:
        return f"{value/1_000:.1f}K"
    else:
        return f"{value:.0f}"

def create_amazon_bulk_file(df: pd.DataFrame, entity_type: str = "keyword") -> pd.DataFrame:
    """
    Format DataFrame for Amazon bulk upload.
    
    Args:
        df: DataFrame with data
        entity_type: Type of entity (keyword, negative, campaign, etc.)
        
    Returns:
        Formatted DataFrame ready for Amazon upload
    """
    # Define column order based on entity type
    if entity_type == "negative_keyword":
        required_cols = [
            "Product", "Entity", "Operation", "Campaign ID", "Ad Group ID",
            "Campaign Name", "Ad Group Name", "Keyword Text", "Match Type"
        ]
    elif entity_type == "keyword":
        required_cols = [
            "Product", "Entity", "Operation", "Campaign ID", "Ad Group ID",
            "Campaign Name", "Ad Group Name", "Bid", "Keyword Text", "Match Type"
        ]
    else:
        # Generic format
        required_cols = list(df.columns)
    
    # Create output DataFrame with required columns
    output = pd.DataFrame()
    
    for col in required_cols:
        if col in df.columns:
            output[col] = df[col]
        else:
            output[col] = ""
    
    return output

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe file system use.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    import re
    
    # Remove invalid characters
    safe = re.sub(r'[<>:"/\\|?*]', '', filename)
    
    # Replace spaces with underscores
    safe = safe.replace(' ', '_')
    
    # Limit length
    if len(safe) > 200:
        safe = safe[:200]
    
    return safe

# Alias for backward compatibility / clarity
to_excel_download = dataframe_to_excel
