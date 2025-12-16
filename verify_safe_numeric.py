
import pandas as pd
import numpy as np

def safe_numeric(series: pd.Series) -> pd.Series:
    """Convert series to numeric, handling currency symbols and errors."""
    s_cleaned = series.astype(str).str.replace(r'[^0-9.-]', '', regex=True)
    print("\n[DEBUG] Cleaned strings sample:")
    print(s_cleaned.head(10))
    return pd.to_numeric(
        s_cleaned, 
        errors='coerce'
    ).fillna(0.0)

# Test Cases
data = {
    'mixed': [
        "AED 100.50", 
        "1,234.56", 
        "0.65", 
        0.75, 
        "SAR 50", 
        "text", 
        "", 
        None,
        "10.00 AED"
    ]
}
df = pd.DataFrame(data)

print("Original Data:")
print(df['mixed'])

df['cleaned'] = safe_numeric(df['mixed'])

print("\nFinal Data:")
print(df['cleaned'])

print("\nSums:")
print(f"Total: {df['cleaned'].sum()}")
