import logging
import random
import config
from router import infer_domain
from safety import SafetyScreener
from retriever import Retriever
from synthesizer import Synthesizer
from utils import clean_text

logger = logging.getLogger(__name__)

class TriageAgent:
    def __init__(self):
        random.seed(config.SEED)
        self.screener = SafetyScreener()
        self.retriever = Retriever()
        self.retriever.load_corpus()
        self.synthesizer = Synthesizer()
        
    def process_ticket(self, issue: str, subject: str, company: str) -> dict:
        issue_clean = clean_text(issue)
        company_clean = clean_text(company)
        
        # 1. Router
        domain = infer_domain(company_clean, issue_clean)
        
        # 2. Safety Screener
        escalation = self.screener.screen_ticket(issue_clean, domain)
        if escalation:
            return escalation
            
        # 3. Retriever — skip for Unknown domain (no corpus to search)
        chunks = []
        if domain != "Unknown":
            chunks = self.retriever.retrieve(issue_clean, domain)
            if not chunks:
                logger.info("No relevant chunks found. Escalating.")
                return {
                    "status": "escalated",
                    "product_area": "general_support",
                    "response": "Escalate to a human",
                    "justification": "No relevant documentation found in corpus for this issue.",
                    "request_type": "product_issue"
                }
            
        # 4. Synthesizer — handles both corpus-grounded and Unknown domain tickets
        result = self.synthesizer.synthesize(issue_clean, domain, chunks)
        return result
