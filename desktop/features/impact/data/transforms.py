"""
Data Transforms - DataFrame transformations for impact calculations.
"""

import numpy as np
import pandas as pd


def ensure_impact_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure required columns for impact calculation exist in the dataframe.
    This handles cache compatibility when columns were calculated in postgres_manager
    but old cached data doesn't have them.

    Returns a copy of the dataframe with all required columns.
    """
    df = df.copy()
    MIN_CLICKS_FOR_RELIABLE = 5

    # If market_tag already exists, return as-is
    if 'market_tag' in df.columns and 'expected_trend_pct' in df.columns:
        return df

    # Calculate counterfactual metrics
    df['spc_before'] = df['before_sales'] / df['before_clicks'].replace(0, np.nan)
    df['cpc_before'] = df['before_spend'] / df['before_clicks'].replace(0, np.nan)
    df['expected_clicks'] = df['observed_after_spend'] / df['cpc_before']
    df['expected_sales'] = df['expected_clicks'] * df['spc_before']

    df['expected_trend_pct'] = ((df['expected_sales'] - df['before_sales']) / df['before_sales'] * 100).fillna(0)
    df['actual_change_pct'] = ((df['observed_after_sales'] - df['before_sales']) / df['before_sales'] * 100).fillna(0)
    df['decision_value_pct'] = df['actual_change_pct'] - df['expected_trend_pct']
    df['decision_impact'] = df['observed_after_sales'] - df['expected_sales']

    # Apply low-sample guardrail
    low_sample_mask = df['before_clicks'] < MIN_CLICKS_FOR_RELIABLE
    df.loc[low_sample_mask, 'decision_impact'] = 0
    df.loc[low_sample_mask, 'decision_value_pct'] = 0

    # Assign market_tag
    conditions = [
        (df['expected_trend_pct'] >= 0) & (df['decision_value_pct'] >= 0),
        (df['expected_trend_pct'] < 0) & (df['decision_value_pct'] >= 0),
        (df['expected_trend_pct'] >= 0) & (df['decision_value_pct'] < 0),
        (df['expected_trend_pct'] < 0) & (df['decision_value_pct'] < 0),
    ]
    choices = ['Offensive Win', 'Defensive Win', 'Gap', 'Market Drag']
    df['market_tag'] = np.select(conditions, choices, default='Unknown')

    return df
