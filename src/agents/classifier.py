import json
import google.generativeai as genai
from typing import Dict, Any
from src.config import GEMINI_API_KEY
from src.models.schemas import ClassificationResult

if GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here":
    genai.configure(api_key=GEMINI_API_KEY)
    
class PaymentClassifierAgent:
    def __init__(self):
        # We use Gemini 1.5 Pro or Flash to process the payload
        self.model = genai.GenerativeModel('gemini-1.5-pro-latest')

    def classify_failure(self, payment_record: Dict[str, Any]) -> ClassificationResult:
        if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
            return self._fallback_classification(payment_record)

        prompt = f"""
        You are an expert AI classifying failed payment records.
        Analyze this payment failure and determine the root cause.
        
        Payment Record:
        {json.dumps(payment_record, indent=2)}
        
        Valid root causes:
        - insufficient_funds
        - bank_timeout
        - otp_failed
        - card_expired
        - risky_card
        - network_error
        - unknown
        
        Output MUST be valid JSON matching this schema exactly:
        {{
            "root_cause": "...",
            "confidence_score": 0.95,
            "reasoning": "Explanation of why this root cause was chosen based on the error_description"
        }}
        """
        
        try:
            # We enforce JSON output structure directly from the model
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    response_mime_type="application/json",
                )
            )
            result_dict = json.loads(response.text)
            return ClassificationResult(**result_dict)
        except Exception as e:
            print(f"LLM Classification failed: {e}")
            return self._fallback_classification(payment_record)

    def _fallback_classification(self, record: Dict[str, Any]) -> ClassificationResult:
        """A rule-based fallback if the LLM API fails or isn't configured."""
        desc = record.get("error_description", "").lower()
        cause = "unknown"
        if "otp" in desc: cause = "otp_failed"
        elif "timeout" in desc: cause = "bank_timeout"
        elif "balance" in desc or "insufficient" in desc: cause = "insufficient_funds"
        elif "expired" in desc: cause = "card_expired"
        elif "risk" in desc: cause = "risky_card"
        elif "network" in desc: cause = "network_error"
        
        return ClassificationResult(
            root_cause=cause,
            confidence_score=0.8,
            reasoning="Fallback pattern matching based on error description."
        )
