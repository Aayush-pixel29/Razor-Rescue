from src.models.schemas import ClassificationResult, DecisionResult, PaymentRecord

class DecisionEngine:
    def __init__(self):
        self.max_retries = 3

    def decide_action(self, classification: ClassificationResult, record: PaymentRecord) -> DecisionResult:
        # Bounded Rule 1: No auto-retries on risky cards (Fraud prevention)
        if classification.root_cause == "risky_card":
            return DecisionResult(
                action="escalate_to_human",
                reason="Transactions flagged for risk must never be automatically retried.",
                requires_api_call=False
            )
            
        # Bounded Rule 2: Max retries cap (Prevent infinite loops and high costs)
        if record.retry_count >= self.max_retries:
            return DecisionResult(
                action="escalate_to_human",
                reason=f"Exceeded max retries cap of {self.max_retries}.",
                requires_api_call=False
            )

        # Main Business Logic Mapping based on Root Cause
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
                action="do_not_retry",
                reason="Unknown failure cause. Do not waste retries.",
                requires_api_call=False
            )
