from src.agents.decision import DecisionEngine
from src.models.schemas import ClassificationResult, PaymentRecord

def test_guardrail_max_retries():
    engine = DecisionEngine()
    record = PaymentRecord(payment_id="123", amount=1000, status="failed", retry_count=4, created_at=0)
    classification = ClassificationResult(root_cause="insufficient_funds", confidence_score=0.9, reasoning="")
    decision = engine.decide_action(classification, record)
    assert decision.action == "escalate_to_human"

def test_guardrail_risky_card():
    engine = DecisionEngine()
    record = PaymentRecord(payment_id="123", amount=1000, status="failed", retry_count=0, created_at=0)
    classification = ClassificationResult(root_cause="risky_card", confidence_score=0.9, reasoning="")
    decision = engine.decide_action(classification, record)
    assert decision.action == "escalate_to_human"

def test_guardrail_low_confidence():
    engine = DecisionEngine()
    record = PaymentRecord(payment_id="123", amount=1000, status="failed", retry_count=0, created_at=0)
    classification = ClassificationResult(root_cause="insufficient_funds", confidence_score=0.6, reasoning="Not sure")
    decision = engine.decide_action(classification, record)
    assert decision.action == "escalate_to_human"
