import logging
from langdetect import detect, LangDetectException
import re

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )

def detect_language(text: str) -> str:
    """Detects the language of the given text. Returns 'en' as fallback."""
    if not text or not text.strip():
        return 'en'
    
    # Common English words/patterns to prevent false positives for short strings
    english_hints = r"\b(the|is|i|to|and|not|working|help|have|my|how|do|am|me|this|that|can)\b"
    if re.search(english_hints, text.lower()):
        return 'en'

    try:
        lang = detect(text)
        return lang
    except LangDetectException:
        return 'en'

def clean_text(text: str) -> str:
    """Basic sanitization of input text."""
    if not isinstance(text, str):
        return ""
    # Remove multiple spaces/newlines
    text = re.sub(r'\s+', ' ', text)
    return text.strip()
