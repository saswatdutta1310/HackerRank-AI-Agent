import logging
import pandas as pd
import time
import sys
import os
from pathlib import Path

# Ensure absolute imports work when run from project root
code_dir = Path(__file__).resolve().parent
if str(code_dir) not in sys.path:
    sys.path.append(str(code_dir))

import config
from utils import setup_logging
from agent import TriageAgent

logger = logging.getLogger(__name__)

INTER_TICKET_SLEEP = 30.0

def main():
    setup_logging()
    logger.info("Initializing Triage Agent...")
    agent = TriageAgent()

    input_file = config.INPUT_CSV
    if len(sys.argv) > 1 and sys.argv[1] == "--sample":
        input_file = config.SAMPLE_CSV

    output_file = config.OUTPUT_CSV

    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        return

    df = pd.read_csv(input_file)
    total = len(df)
    logger.info(f"Loaded {total} tickets from {input_file}")

    output_file = config.OUTPUT_CSV
    done_issues = set()
    results = []
    
    if os.path.exists(output_file):
        try:
            temp_df = pd.read_csv(output_file)
            done_issues = set(temp_df['issue'].astype(str).tolist())
            results = temp_df.to_dict('records')
            logger.info(f"Resume: Found {len(done_issues)} tickets already in {output_file}. Skipping them.")
        except Exception as e:
            logger.warning(f"Could not read {output_file} for resume: {e}")

    for idx, row in df.iterrows():
        # CSV columns are Title-cased in sample/input: Issue, Subject, Company
        issue   = str(row.get("Issue",   row.get("issue",   "")))
        
        if issue in done_issues:
            continue
        subject = str(row.get("Subject", row.get("subject", "")))
        company = str(row.get("Company", row.get("company", "")))

        logger.info(f"[{idx+1}/{total}] company={company!r} | issue={issue[:60]!r}...")

        try:
            result = agent.process_ticket(issue, subject, company)
        except Exception as e:
            logger.error(f"Unhandled error on ticket {idx+1}: {e}")
            result = {
                "status": "escalated",
                "product_area": "unknown",
                "response": "Escalate to a human",
                "justification": f"Internal system error: {e}",
                "request_type": "product_issue"
            }

        combined = {
            "issue":        issue,
            "subject":      subject,
            "company":      company,
            "status":       result.get("status",       "escalated"),
            "product_area": result.get("product_area", "unknown"),
            "response":     result.get("response",     "Escalate to a human"),
            "justification":result.get("justification",""),
            "request_type": result.get("request_type", "product_issue")
        }
        results.append(combined)

        logger.info(f"  → status={combined['status']} | product_area={combined['product_area']} | request_type={combined['request_type']}")

        # Incremental save to prevent data loss and fix linting visibility
        out_df = pd.DataFrame(results)
        out_df = out_df[["issue", "subject", "company", "status",
                         "product_area", "response", "justification", "request_type"]]
        out_df.to_csv(output_file, index=False)

        # Rate-limit guard — skip sleep after last ticket
        if idx < total - 1:
            time.sleep(INTER_TICKET_SLEEP)

    logger.info(f"Done. Output written to {output_file}")

    # Final summary for CLI wow factor
    print("\n" + "="*50)
    print("TRIAGE BATCH COMPLETE")
    print("="*50)
    print(f"Total Tickets: {len(out_df)}")
    print(f"Replied:       {len(out_df[out_df['status'] == 'replied'])}")
    print(f"Escalated:     {len(out_df[out_df['status'] == 'escalated'])}")
    print("-"*50)
    print("Top Product Areas:")
    print(out_df['product_area'].value_counts().head(5).to_string())
    print("="*50 + "\n")

if __name__ == "__main__":
    main()
