import time
import json
import sqlite3
import argparse
import random
from datetime import datetime
from src.data.generator import generate_synthetic_batch
from src.agents.classifier import PaymentClassifierAgent
from src.agents.decision import DecisionEngine
from src.services.simulator import PaymentSimulator
from src.models.schemas import PaymentRecord

DB_PATH = "evaluation.db"

def setup_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS eval_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payment_id TEXT NOT NULL,
                strategy TEXT NOT NULL,
                ground_truth_cause TEXT NOT NULL,
                status TEXT NOT NULL,
                amount_recovered INTEGER DEFAULT 0,
                is_bad_retry BOOLEAN DEFAULT 0,
                llm_classification TEXT,
                guardrail_action TEXT
            )
        ''')
        conn.execute('DELETE FROM eval_log')
        conn.commit()

def log_eval(payment_id, strategy, ground_truth, status, amount, bad_retry, llm=None, guardrail=None):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            INSERT INTO eval_log (payment_id, strategy, ground_truth_cause, status, amount_recovered, is_bad_retry, llm_classification, guardrail_action)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (payment_id, strategy, ground_truth, status, amount, bad_retry, json.dumps(llm) if llm else None, json.dumps(guardrail) if guardrail else None))
        conn.commit()

def determine_truth(record):
    desc = record["error_description"].lower()
    if "otp" in desc: return "otp_failed"
    elif "timeout" in desc: return "bank_timeout"
    elif "balance" in desc or "insufficient" in desc: return "insufficient_funds"
    elif "expired" in desc or "migration" in desc: return "card_expired"
    elif "risk" in desc or "velocity" in desc: return "risky_card"
    return "network_error"

def main():
    parser = argparse.ArgumentParser(description="Razor-Rescue Evaluation Harness")
    parser.add_argument("--records", type=int, default=1000, help="Number of records to simulate")
    parser.add_argument("--fast", action="store_true", help="Bypass LLM network call for speed")
    args = parser.parse_args()
    
    # Deterministic seed for reproducible evaluation
    random.seed(42)
    
    print(f"[START] Running Razor-Rescue Evaluation Harness on {args.records} records")
    setup_db()
    
    print("\n[1] Generating synthetic payments with ground truths (Seed: 42)...")
    raw_records = generate_synthetic_batch(args.records)
    
    classifier = PaymentClassifierAgent()
    decision_engine = DecisionEngine()
    
    if args.fast:
        classifier_fn = classifier._fallback_classification
    else:
        classifier_fn = classifier.classify_failure

    print("\n[2] Running Strategy A: Blind Retry Baseline")
    for record in raw_records:
        truth = determine_truth(record)
        pr = PaymentRecord(**record)
        
        success, amount, msg, is_bad = PaymentSimulator.simulate_immediate_retry(truth, pr)
        status = "recovered" if success else "failed"
        log_eval(pr.payment_id, "Baseline", truth, status, amount, is_bad)
        
    print("\n[3] Running Strategy B: Razor-Rescue (AI + Guardrails)")
    for i, raw_record in enumerate(raw_records):
        truth = determine_truth(raw_record)
        pr = PaymentRecord(**raw_record)
        
        classification = classifier_fn(raw_record)
        decision = decision_engine.decide_action(classification, pr)
        
        status = "ignored"
        amount = 0
        is_bad = False
        
        if decision.action == "send_payment_link":
            success, amount, msg, is_bad = PaymentSimulator.simulate_payment_link(truth, pr)
            status = "recovered" if success else "link_abandoned"
        elif decision.action == "retry_immediately":
            success, amount, msg, is_bad = PaymentSimulator.simulate_immediate_retry(truth, pr)
            status = "recovered" if success else "failed"
        elif decision.action == "retry_delayed":
            success, amount, msg, is_bad = PaymentSimulator.simulate_delayed_retry(truth, pr)
            status = "recovered" if success else "failed_after_24h"
        elif decision.action == "escalate_to_human":
            status = "escalated"
            
        log_eval(pr.payment_id, "Razor-Rescue", truth, status, amount, is_bad, classification.model_dump(), decision.model_dump())
        
        if not args.fast:
            time.sleep(4)
            
        if (i+1) % 100 == 0:
            print(f"  Processed {i+1}/{args.records} records...")

    print("\n[DONE] Evaluation complete! Run 'streamlit run dashboard.py' to see the comparison.")

if __name__ == "__main__":
    main()
