import pytest
from src.agents.decision import DecisionEngine
from src.models.schemas import ClassificationResult, PaymentRecord

def test_hard_stop_risky_card_overrides_confidence():
    engine = DecisionEngine()
    classification = ClassificationResult(root_cause="risky_card", confidence_score=0.80, reasoning="Medium confidence risk")
    record = PaymentRecord(payment_id="123", amount=100, currency="INR", status="failed", retry_count=0)
    
    decision = engine.decide_action(classification, record)
    assert decision.action == "escalate_to_human" # Must not be send_payment_link

def test_hard_stop_max_retries_overrides_confidence():
    engine = DecisionEngine()
    classification = ClassificationResult(root_cause="network_error", confidence_score=0.99, reasoning="Definite network timeout")
    record = PaymentRecord(payment_id="123", amount=100, currency="INR", status="failed", retry_count=4)
    
    decision = engine.decide_action(classification, record)
    assert decision.action == "escalate_to_human" # Must not be retry_immediately

def test_medium_confidence_downgrades_to_link():
    engine = DecisionEngine()
    classification = ClassificationResult(root_cause="network_error", confidence_score=0.75, reasoning="Looks like network timeout")
    record = PaymentRecord(payment_id="123", amount=100, currency="INR", status="failed", retry_count=0)
    
    decision = engine.decide_action(classification, record)
    assert decision.action == "send_payment_link" # Downgraded from immediate_retry due to <0.85 conf
