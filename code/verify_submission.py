import pandas as pd
from pathlib import Path
import sys

def verify():
    output_file = Path("support_tickets/output.csv")
    if not output_file.exists():
        print("❌ Error: output.csv not found.")
        return

    df = pd.read_csv(output_file)
    print(f"Checking {len(df)} rows in {output_file}...")

    # 1. Required Columns
    expected_cols = ["issue", "subject", "company", "status", "product_area", "response", "justification", "request_type"]
    missing = [c for c in expected_cols if c not in df.columns]
    if missing:
        print(f"❌ Error: Missing columns: {missing}")
    else:
        print("✅ Column structure is correct.")

    # 2. Status Validation
    valid_status = ["replied", "escalated"]
    invalid_status = df[~df['status'].isin(valid_status)]
    if not invalid_status.empty:
        print(f"❌ Error: Invalid status values found in rows: {invalid_status.index.tolist()}")
    else:
        print("✅ All status values are valid (replied/escalated).")

    # 3. Product Area Taxonomy (Partial check)
    if 'product_area' in df.columns:
        null_areas = df[df['product_area'].isna()]
        if not null_areas.empty:
            print(f"❌ Error: Missing product_area in rows: {null_areas.index.tolist()}")
        else:
            print("✅ No missing product_area fields.")

    # 4. Response lengths
    if 'response' in df.columns:
        empty_responses = df[df['response'].isna() | (df['response'].str.strip() == "")]
        if not empty_responses.empty:
            print(f"❌ Error: Empty responses in rows: {empty_responses.index.tolist()}")
        else:
            print("✅ All tickets have a response string.")

    print("\n--- FINAL VERIFICATION SUMMARY ---")
    if missing or not invalid_status.empty or not null_areas.empty or not empty_responses.empty:
        print("❌ SUBMISSION HAS ERRORS. Do not submit yet.")
    else:
        print("✨ SUBMISSION LOOKS PERFECT. Ready for HackerRank!")

if __name__ == "__main__":
    verify()
