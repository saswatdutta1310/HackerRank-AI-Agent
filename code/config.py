import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Project Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SUPPORT_TICKETS_DIR = BASE_DIR / "support_tickets"

INPUT_CSV = SUPPORT_TICKETS_DIR / "support_tickets.csv"
OUTPUT_CSV = SUPPORT_TICKETS_DIR / "output.csv"
SAMPLE_CSV = SUPPORT_TICKETS_DIR / "sample_support_tickets.csv"

# Domains
COMPANIES = ["HackerRank", "Claude", "Visa"]

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Settings
SEED = 42

# Retrieval settings
CHUNK_SIZE = 400
CHUNK_OVERLAP = 50
TOP_K = 3
BM25_THRESHOLD = 0.5  # Min score to consider a document relevant

# Models
GEMINI_MODELS = [
    "gemini-flash-latest",
    "gemini-2.0-flash",
    "gemini-flash-lite-latest",
    "gemini-pro-latest"
]
CLAUDE_MODEL = "claude-3-5-haiku-20241022"
