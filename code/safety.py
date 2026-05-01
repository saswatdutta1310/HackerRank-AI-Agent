import re
import logging
from utils import detect_language

logger = logging.getLogger(__name__)

class SafetyScreener:
    def __init__(self):
        self.high_risk_patterns = [
            r"\bfraud\b",
            r"\bidentity theft\b",
            r"\bvulnerability\b",
            r"\bbug bounty\b",
            r"\bsecurity breach\b",
            r"\bhacked\b",
        ]
        
        self.override_patterns = [
            r"restore access",
            r"i am not the owner",
            r"i am not the admin",
            r"force them to pass me",
            r"increase my score",
            r"change my score",
        ]
        
        self.injection_patterns = [
            r"internal rules",
            r"system instructions",
            r"ignore previous instructions",
            r"show me your context",
            r"system prompt",
        ]
        
        self.destructive_patterns = [
            r"delete all",
            r"rm -rf",
            r"drop table",
        ]
        
        self.outage_patterns = [
            r"site is down",
            r"all pages are inaccessible",
            r"none of the submissions",
            r"all requests are failing",
            r"500 internal server error",
        ]

    def screen_ticket(self, issue: str, domain: str) -> dict | None:
        """
        Returns a dict if escalation is required immediately.
        Otherwise returns None.
        """
        issue_lower = issue.lower()
        
        # 1. Prompt Injection
        for pat in self.injection_patterns:
            if re.search(pat, issue_lower):
                logger.warning(f"Safety: Prompt injection detected: {pat}")
                return {
                    "status": "escalated",
                    "product_area": "unknown" if domain == "Unknown" else "general_support",
                    "response": "Escalate to a human",
                    "justification": "Detected unauthorized request for internal system configuration or prompt instructions (Potential Prompt Injection).",
                    "request_type": "invalid"
                }
                
        # 2. Destructive
        for pat in self.destructive_patterns:
            if re.search(pat, issue_lower):
                logger.warning(f"Safety: Destructive pattern detected: {pat}")
                return {
                    "status": "escalated",
                    "product_area": "unknown" if domain == "Unknown" else "general_support",
                    "response": "Escalate to a human",
                    "justification": "Detected destructive intent or harmful command.",
                    "request_type": "invalid"
                }

        # 3. Foreign Language + Injection combo (e.g., French ticket asking for internal rules)
        lang = detect_language(issue)
        if lang != 'en':
            # Check if it also contains injection-like patterns — that's a red flag
            foreign_injection = any(re.search(pat, issue_lower) for pat in [
                r"r\u00e8gles", r"syst\u00e8me", r"interne", r"montre", r"affiche",
                r"ignore", r"oublie", r"instruc"
            ])
            logger.warning(f"Safety: Foreign language detected ({lang}), injection={foreign_injection}. Escalating.")
            return {
                "status": "escalated",
                "product_area": "unknown" if domain == "Unknown" else "general_support",
                "response": "Escalate to a human",
                "justification": f"Manual review required: Primary ticket content is in '{lang}'. Non-English requests are routed to specialized support teams for accurate processing.",
                "request_type": "invalid" if foreign_injection else "product_issue"
            }

        # 4. Outage
        for pat in self.outage_patterns:
            if re.search(pat, issue_lower):
                logger.warning(f"Safety: Platform outage detected: {pat}")
                return {
                    "status": "escalated",
                    "product_area": "unknown" if domain == "Unknown" else "general_support",
                    "response": "Escalate to a human",
                    "justification": "Detected signals of a platform-wide outage. Escalating immediately.",
                    "request_type": "bug"
                }

        # 5. High Risk
        for pat in self.high_risk_patterns:
            if re.search(pat, issue_lower):
                logger.warning(f"Safety: High risk keyword detected: {pat}")
                return {
                    "status": "escalated",
                    "product_area": "unknown" if domain == "Unknown" else "general_support",
                    "response": "Escalate to a human",
                    "justification": f"High-risk security or fraud keyword detected: {pat}",
                    "request_type": "product_issue"
                }
                
        # 6. Unauthorized Action Overrides
        for pat in self.override_patterns:
            if re.search(pat, issue_lower):
                logger.warning(f"Safety: Unauthorized override detected: {pat}")
                return {
                    "status": "escalated", 
                    "product_area": "unknown" if domain == "Unknown" else "general_support",
                    "response": "Escalate to a human",
                    "justification": "User is requesting an action that requires elevated privileges or is against standard policy.",
                    "request_type": "invalid"
                }
                
        # 7. Vague / Unknown — only escalate if truly unresolvable (very short AND no keyword signal)
        if domain == "Unknown" and len(issue.split()) < 5:
            logger.warning("Safety: Vague issue with unknown domain.")
            return {
                "status": "escalated",
                "product_area": "unknown",
                "response": "Escalate to a human",
                "justification": "Insufficient context to identify user intent or company domain. Requires manual clarifying outreach.",
                "request_type": "product_issue"
            }
            
        return None
