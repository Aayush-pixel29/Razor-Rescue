import json
import random
import time
from src.data.generator import generate_synthetic_batch
from src.agents.classifier import PaymentClassifierAgent
from src.agents.decision import DecisionEngine
from src.services.razorpay_client import RazorpayService
from src.db.audit import AuditLogger
from src.models.schemas import PaymentRecord

def main():
    print("[START] Starting Razor-Rescue: AI Revenue Recovery Agent")
    
    logger = AuditLogger()
    classifier = PaymentClassifierAgent()
    decision_engine = DecisionEngine()
    rzp_client = RazorpayService()
    
    print("\n[1] Ingesting failed payment batch...")
    raw_records = generate_synthetic_batch(75) # Increased batch size
    print(f"Loaded {len(raw_records)} failed payments.")
    
    print("\n[2] Processing batch via Agentic Workflow...")
    
    for i, raw_record in enumerate(raw_records):
        try:
            record = PaymentRecord(**raw_record)
            classification = classifier.classify_failure(raw_record)
            decision = decision_engine.decide_action(classification, record)
            
            execution_outcome = {}
            amount_recovered = 0
            status = "escalated"
            
            if decision.action == "send_payment_link" and decision.requires_api_call:
                customer_data = {
                    "name": f"Customer {record.customer_id}",
                    "email": record.email,
                    "contact": record.contact
                }
                link = rzp_client.create_payment_link(
                    amount=record.amount,
                    currency=record.currency,
                    description=f"Retry payment for {record.payment_id}",
                    customer=customer_data
                )
                if link:
                    execution_outcome["payment_link"] = link
                    # Use simulator to determine if customer actually paid it later
                    # (Avoids claiming fake immediate revenue for a link)
                    from src.services.simulator import PaymentSimulator
                    from evaluate import determine_truth
                    truth = determine_truth(raw_record)
                    success, amount, msg, is_bad = PaymentSimulator.simulate_payment_link(truth, record)
                    
                    if success:
                        execution_outcome["status"] = "Link sent -> Customer Paid"
                        status = "recovered"
                        amount_recovered = amount
                    else:
                        execution_outcome["status"] = "Link sent -> Customer Abandoned"
                        status = "failed"
                else:
                    execution_outcome["status"] = "Failed to generate link"
                    status = "failed"
                    
            elif decision.action == "retry_immediately":
                from src.services.simulator import PaymentSimulator
                from evaluate import determine_truth
                truth = determine_truth(raw_record)
                success, amount, msg, is_bad = PaymentSimulator.simulate_immediate_retry(truth, record)
                if success:
                    execution_outcome["status"] = "Immediate Retry -> Success"
                    status = "recovered"
                    amount_recovered = amount
                else:
                    execution_outcome["status"] = "Immediate Retry -> Failed"
                    status = "failed"
                
            elif decision.action == "retry_delayed":
                from src.services.simulator import PaymentSimulator
                from evaluate import determine_truth
                truth = determine_truth(raw_record)
                success, amount, msg, is_bad = PaymentSimulator.simulate_delayed_retry(truth, record)
                if success:
                    execution_outcome["status"] = "Scheduled 24h -> Success"
                    status = "recovered"
                    amount_recovered = amount
                else:
                    execution_outcome["status"] = "Scheduled 24h -> Failed"
                    status = "failed"
                
            elif decision.action == "escalate_to_human":
                execution_outcome["status"] = "Escalated to human review"
                status = "escalated"
                
            else:
                execution_outcome["status"] = "Ignored/Do not retry"
                status = "ignored"

            # Step D: Log Full Audit Trail
            logger.log_record(
                payment_id=record.payment_id,
                input_data=raw_record,
                classification=classification.model_dump(),
                decision=decision.model_dump(),
                execution_outcome=execution_outcome,
                amount_recovered=amount_recovered,
                status=status
            )
            
            # Rate limiting for Gemini Free Tier (15 Requests Per Minute)
            # 4 seconds per record = 15 records per minute
            time.sleep(4)
            
        except Exception as e:
            # Graceful failure handling
            print(f"Error processing record {raw_record.get('payment_id', 'unknown')}: {e}")
            logger.log_record(
                payment_id=raw_record.get('payment_id', 'unknown_id'),
                input_data=raw_record,
                classification={"error": str(e)},
                decision={"action": "error", "reason": "Failed during processing"},
                execution_outcome={"status": "Runtime Exception"},
                amount_recovered=0,
                status="error"
            )
        
        if (i+1) % 10 == 0:
            print(f"Processed {i+1}/{len(raw_records)} records...")
            
    print("\n[3] Generating Audit Report...")
    metrics = logger.get_summary_metrics()
    print("=" * 50)
    print("[REPORT] REVENUE RECOVERY REPORT")
    print("=" * 50)
    print(f"Total Records Processed: {metrics['total_processed']}")
    print(f"Confirmed Recoveries:    {metrics['recovered_count']}")
    print(f"Recovery Rate:           {metrics['recovery_rate_percent']:.2f}%")
    print(f"Total INR Recovered:     INR {metrics['total_amount_recovered_inr']:,.2f}")
    print(f"Exceptions/Escalated:    {metrics['escalations_and_exceptions']}")
    print("=" * 50)
    print("Audit log successfully saved to audit.db - this proves explainability.")

if __name__ == "__main__":
    main()
