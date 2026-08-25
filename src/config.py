import os
from dotenv import load_dotenv

load_dotenv()

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
    raise ValueError("Razorpay credentials missing in environment variables.")

if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
    print("WARNING: GEMINI_API_KEY is not set correctly. The LLM Classifier will not work until this is configured.")

DB_PATH = "audit.db"
