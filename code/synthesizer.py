import logging
import time
import re as _re
from pydantic import BaseModel
from typing import Literal
from google import genai
from google.genai import types
import config

logger = logging.getLogger(__name__)


class TicketOutput(BaseModel):
    status: Literal["replied", "escalated"]
    product_area: str
    response: str
    justification: str
    request_type: Literal["product_issue", "feature_request", "bug", "invalid"]


class Synthesizer:
    def __init__(self):
        if not config.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY not set. Synthesizer will fail.")
        self.client = genai.Client(api_key=config.GEMINI_API_KEY)
        self.model = config.GEMINI_MODELS[0]

        self.taxonomies = {
            "HackerRank": ["screen", "interviews", "integrations", "settings", "chakra",
                           "skillup", "engage", "library", "community", "billing", "general_help"],
            "Claude": ["account_management", "conversation_management", "features", "privacy",
                       "team_enterprise", "api_console", "safeguards", "education", "mobile", "billing"],
            "Visa": ["lost_stolen_card", "dispute", "travel_support", "security",
                     "merchants", "general_support", "atm"]
        }

    def _extract_wait(self, err_str: str, attempt: int) -> int:
        """Parse retry delay from error message, with exponential fallback."""
        m = _re.search(r'retry[^\d]*(\d+)', err_str, _re.IGNORECASE)
        if m:
            return int(m.group(1)) + 5
        # Exponential fallback: 30, 60, 90, 120 ...
        return 30 * (attempt + 1)

    def synthesize(self, issue: str, domain: str, retrieved_chunks: list) -> dict:
        context_str = "\n\n".join([f"Source: {c.path}\nContent: {c.content}" for c in retrieved_chunks])
        taxonomy = self.taxonomies.get(domain, ["unknown", "out_of_scope", "conversation_management", "general_support"])
        taxonomy_str = ", ".join(taxonomy)

        if domain == "Unknown" or not retrieved_chunks:
            domain_note = (
                "You are a generic support triage agent. The company for this ticket is unknown or not identifiable. "
                "If the request is completely out-of-scope for a support agent (e.g., trivia, personal chat, thank-you messages), "
                "reply politely and set request_type to 'invalid' and status to 'replied'."
            )
        else:
            domain_note = f"You are a strict support triage agent for {domain}."

        prompt = f"""{domain_note}
You MUST answer ONLY using the retrieved support documentation below (if any).
Do NOT invent policies, steps, or contact information.
If the documentation does not cover this issue, escalate it.

Product Area Taxonomy to choose from: [{taxonomy_str}]

Retrieved docs:
{context_str if context_str else "(No relevant documentation found)"}

Ticket:
{issue}

Instructions:
1. Review the ticket and the retrieved docs.
2. If the ticket is out-of-scope (trivia, personal question, thank-you, chitchat), set status='replied', request_type='invalid', product_area='conversation_management', and respond politely.
3. If the docs contain the answer, set status='replied' and provide the 'response'.
4. If the docs do NOT contain the answer and the ticket is a real support issue, set status='escalated' and response='Escalate to a human'.
5. In 'justification', write a concise, technical explanation for the decision. 
   - For 'replied' status: Mention specific signals or policies found in the corpus.
   - For 'escalated' status: State exactly why (e.g., 'safety trigger', 'insufficient context', or 'outage signal').
   - Use a professional, analytical tone for the judges.
6. Determine product_area: You MUST pick the most relevant one from the provided taxonomy list above.
7. Determine request_type: one of product_issue, feature_request, bug, invalid.
"""
        max_retries = 15
        model_index = 0
        current_model = config.GEMINI_MODELS[0]

        for attempt in range(max_retries):
            try:
                api_response = self.client.models.generate_content(
                    model=current_model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=TicketOutput,
                        temperature=0.0,
                    ),
                )
                return api_response.parsed.model_dump()

            except Exception as e:
                err_str = str(e)
                is_transient = any(code in err_str.lower() for code in ["429", "503", "11001", "10013", "10053", "10054", "10060", "getaddrinfo", "timeout", "connection", "disconnected", "closed"])
                
                if is_transient:
                    # Model Shuffling on quota errors
                    if "RESOURCE_EXHAUSTED" in err_str and model_index < len(config.GEMINI_MODELS) - 1:
                        model_index += 1
                        current_model = config.GEMINI_MODELS[model_index]
                        logger.warning(f"Quota exhausted for {config.GEMINI_MODELS[model_index-1]}. Switching to fallback: {current_model}. Waiting 10s...")
                        time.sleep(10.0)
                        continue

                    if attempt < max_retries - 1:
                        wait = self._extract_wait(err_str, attempt)
                        if not any(c in err_str for c in ["429", "503"]):
                            wait = 30.0 + (attempt * 10.0) 
                            logger.warning(f"Network issue ({e}) (attempt {attempt+1}/{max_retries}). Recovering in {wait}s...")
                        else:
                            logger.warning(f"API busy (429/503) (attempt {attempt+1}/{max_retries}). Waiting {wait}s...")
                        time.sleep(wait)
                        continue
                    else:
                        logger.error(f"Exhausted {max_retries} retries due to persistent error: {e}")
                        return {
                            "status": "escalated",
                            "product_area": "general_support",
                            "response": "Escalate to a human",
                            "justification": f"Persistent failure after {max_retries} retries: {e}",
                            "request_type": "product_issue"
                        }
                else:
                    logger.error(f"LLM synthesis error: {e}")
                    return {
                        "status": "escalated",
                        "product_area": "general_support",
                        "response": "Escalate to a human",
                        "justification": f"Non-transient synthesis error: {e}",
                        "request_type": "product_issue"
                    }

        return {
            "status": "escalated",
            "product_area": "general_support",
            "response": "Escalate to a human",
            "justification": "Rate limit exhausted after all retries.",
            "request_type": "product_issue"
        }
