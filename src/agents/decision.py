from src.models.schemas import ClassificationResult, DecisionResult, PaymentRecord

class DecisionEngine:
    def __init__(self):
        self.max_retries = 3

    def decide_action(self, classification: ClassificationResult, record: PaymentRecord) -> DecisionResult:
        
        # --- HARD SAFETY STOPS (Must execute before any confidence checks) ---
        
        # Bounded Rule 1: No auto-retries on risky cards (Fraud prevention)
        if classification.root_cause == "risky_card":
            return DecisionResult(
                action="escalate_to_human",
                reason="Transactions flagged for risk must never be automatically recovered.",
                requires_api_call=False
            )
            
        # Bounded Rule 2: Max retries cap (Prevent infinite loops and high costs)
        if record.retry_count >= self.max_retries:
            return DecisionResult(
                action="escalate_to_human",
                reason=f"Exceeded max retries cap of {self.max_retries}.",
                requires_api_call=False
            )

        # --- CONFIDENCE CALIBRATION ---
        
        # Bounded Rule 3: Low Confidence Escalate
        if classification.confidence_score < 0.70:
            return DecisionResult(
                action="escalate_to_human",
                reason=f"LLM confidence ({classification.confidence_score}) is below the safe threshold of 0.70. Escalating.",
                requires_api_call=False
            )
            
        # Bounded Rule 4: Medium Confidence Safe Manual Recovery
        if 0.70 <= classification.confidence_score < 0.85:
            # Restricted Action: Even if it thinks it knows the cause, don't auto-retry. Send a link instead so the user verifies.
            return DecisionResult(
                action="send_payment_link",
                reason=f"LLM confidence ({classification.confidence_score}) is in the restricted tier (0.70-0.85). Defaulting to safe manual link.",
                requires_api_call=True
            )

        # --- BUSINESS LOGIC (High Confidence > 0.85) ---
        
        if classification.root_cause == "insufficient_funds":
            return DecisionResult(
                action="retry_delayed",
                reason="Insufficient funds. Schedule retry for 24h later.",
                requires_api_call=False
            )
        elif classification.root_cause in ["bank_timeout", "network_error"]:
            return DecisionResult(
                action="retry_immediately",
                reason="Network or bank timeouts are transient. Retry immediately.",
                requires_api_call=True
            )
        elif classification.root_cause == "otp_failed":
            return DecisionResult(
                action="send_payment_link",
                reason="OTP failed, customer needs to manually re-authenticate. Sending payment link.",
                requires_api_call=True
            )
        elif classification.root_cause == "card_expired":
            return DecisionResult(
                action="send_payment_link",
                reason="Card expired. Send link so they can use a new payment method.",
                requires_api_call=True
            )
        else:
            return DecisionResult(
                action="escalate_to_human",
                reason="Unknown failure cause. Escalating.",
                requires_api_call=False
            )
