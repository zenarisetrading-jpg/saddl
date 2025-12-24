"""
Test script for Negatives Bulk Export Validation Rules.
"""

import pandas as pd
import sys
import os

sys.path.append(os.getcwd())

from features.bulk_export import validate_negatives_bulk, EXPORT_COLUMNS

def test_validation_rules():
    print("=== Testing Negatives Bulk Validation ===\n")
    
    # Create a mock dataframe with intentional violations
    data = {
        "Product": ["Sponsored Products"] * 6,
        "Entity": ["Negative Keyword", "Negative Keyword", "Negative Product Targeting", "Negative Keyword", "Negative Keyword", "Negative Keyword"],
        "Operation": ["Create"] * 6,
        "Campaign Id": ["c1", "c1", "", "c4", "c5", "c5"],  # Row 3 missing ID
        "Ad Group Id": ["a1", "a1", "a3", "a4", "a5", "a5"],
        "Campaign Name": ["Camp A", "Camp A", "Camp C", "Camp D", "Camp E", "Camp E"],
        "Ad Group Name": ["AG 1", "AG 1", "AG 3", "AG 4", "AG 5", "AG 5"],
        "Bid": ["", "1.50", "", "", "", ""],  # Row 2 has bid (R3 violation)
        "Ad Group Default Bid": [""] * 6,
        "Keyword Text": ["kw1", "kw1", "should be blank", "kw4", "kw5", "kw5"],  # Row 3 R1 violation, Row 5/6 duplicate (R6)
        "Match Type": ["negativeExact", "wrong", "", "negativeExact", "negativeExact", "negativeExact"],  # Row 2 R2 violation
        "Product Targeting Expression": ["should be blank", "", "asin=\"B001\"", "", "", ""],  # Row 1 R1 violation
        "Keyword Id": ["KW1", "KW2", "KW3_shouldnt_exist", "KW4", "KW5", "KW5"],  # Row 3 R1/R5 violation
        "Product Targeting Id": ["", "", "PT3", "", "", ""],
        "State": ["enabled"] * 6
    }
    
    df = pd.DataFrame(data)
    
    print("Input DataFrame:")
    print(df[["Entity", "Campaign Id", "Keyword Text", "Product Targeting Expression", "Match Type", "Keyword Id", "Product Targeting Id", "Bid"]].to_string())
    print("\n")
    
    # Run validation
    validated_df, issues = validate_negatives_bulk(df)
    
    print(f"Found {len(issues)} validation issues:\n")
    for issue in issues:
        # Handle both old format ('rule') and new format ('code')
        rule = issue.get('rule') or issue.get('code', 'UNKNOWN')
        row = issue.get('row', -1)
        msg = issue.get('msg') or issue.get('message', '')
        print(f"  [{rule}] Row {row}: {msg}")
    
    print("\n\nValidated DataFrame:")
    print(validated_df[["Entity", "Campaign Id", "Keyword Text", "Product Targeting Expression", "Match Type", "Keyword Id", "Product Targeting Id", "Bid"]].to_string())
    
    # Assertions - handle both 'rule' and 'code' keys
    def get_rule(issue):
        return issue.get('rule') or issue.get('code', '')
    
    assert any(get_rule(i) == "R1" for i in issues), "R1 not detected"
    assert any(get_rule(i) == "R2" for i in issues), "R2 not detected"
    assert any(get_rule(i) == "R3" for i in issues), "R3 not detected"
    assert any(get_rule(i) == "R4" or get_rule(i) == "GEN005" for i in issues), "R4/GEN005 not detected"
    assert any(get_rule(i) == "R6" for i in issues), "R6 not detected"
    
    print("\n✅ ALL VALIDATION RULES TESTED SUCCESSFULLY")

if __name__ == "__main__":
    test_validation_rules()
