from pydantic import BaseModel, Field
from typing import Optional, Literal

class PaymentRecord(BaseModel):
    """Represents a failed payment record in the system."""
    payment_id: str
    amount: int  # in paise (e.g., 10000 = ₹100.00)
    currency: str = "INR"
    status: str
    error_code: Optional[str] = None
    error_description: Optional[str] = None
    error_reason: Optional[str] = None
    customer_id: Optional[str] = None
    contact: Optional[str] = None
    email: Optional[str] = None
    retry_count: int = 0
    card_network: Optional[str] = None
    created_at: int

class ClassificationResult(BaseModel):
    """Output from the LLM Classifier Agent."""
    root_cause: Literal[
        "insufficient_funds", 
        "bank_timeout", 
        "otp_failed", 
        "card_expired", 
        "risky_card", 
        "network_error",
        "unknown"
    ]
    confidence_score: float = Field(ge=0.0, le=1.0)
    reasoning: str

class DecisionResult(BaseModel):
    """Output from the deterministic Decision Engine."""
    action: Literal[
        "retry_immediately",
        "retry_delayed",
        "send_payment_link",
        "escalate_to_human",
        "do_not_retry"
    ]
    reason: str
    requires_api_call: bool
