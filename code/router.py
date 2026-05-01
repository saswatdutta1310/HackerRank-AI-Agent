import config
import logging

logger = logging.getLogger(__name__)

def infer_domain(company_field: str, issue_text: str) -> str:
    """Infers the product domain based on the company field and issue text."""
    if not isinstance(company_field, str):
        company_field = str(company_field) if company_field else "None"
        
    company_field_lower = company_field.strip().lower()
    
    if company_field_lower != "none" and company_field_lower != "nan":
        # Check against known companies
        if company_field_lower == "hackerrank":
            return "HackerRank"
        elif company_field_lower == "claude":
            return "Claude"
        elif company_field_lower == "visa":
            return "Visa"
            
    # If None or unrecognized, try keyword inference
    if not isinstance(issue_text, str):
        return "Unknown"
        
    issue_lower = issue_text.lower()
    
    hr_terms = ["hackerrank", "assessment", "test ", "candidate", "recruiter", " screen", "interview", "coding challenge", "skillup", "plagiarism"]
    claude_terms = ["claude", "anthropic", "workspace", "artifact", "api key", "haiku", "sonnet", "opus", "prompt"]
    visa_terms = ["visa", "card", "cardholder", "transaction", "atm", "chargeback", "issuer", "bank", "travel cheque", "credit", "debit", "merchant"]
    
    hr_count = sum(1 for t in hr_terms if t in issue_lower)
    cl_count = sum(1 for t in claude_terms if t in issue_lower)
    visa_count = sum(1 for t in visa_terms if t in issue_lower)
    
    max_count = max(hr_count, cl_count, visa_count)
    if max_count == 0:
        return "Unknown"
        
    if hr_count == max_count:
        return "HackerRank"
    elif cl_count == max_count:
        return "Claude"
    else:
        return "Visa"
