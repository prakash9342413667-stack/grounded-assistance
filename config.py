import os
from dotenv import load_dotenv

load_dotenv()

MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
FALLBACK_MODEL = os.getenv("GEMINI_FALLBACK_MODEL", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Gemini 3.8 Flash Standard paid-tier text rates (USD per 1 million tokens)
# These are configurable estimates, not billing data. Recheck Google's pricing page.
INPUT_USD_PER_MILLION = float(os.getenv("INPUT_USD_PER_MILLION", "0.75"))
OUTPUT_USD_PER_MILLION = float(os.getenv("OUTPUT_USD_PER_MILLION", "3.75"))