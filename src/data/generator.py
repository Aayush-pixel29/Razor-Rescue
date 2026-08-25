import random
import uuid
from typing import List, Dict, Any

def generate_synthetic_batch(num_records: int = 50) -> List[Dict[str, Any]]:
    records = []
    
    failure_scenarios = [
        {
            "code": "BAD_REQUEST_ERROR",
            "desc": "Customer entered OTP twice but bank session expired during verification.",
            "reason": "payment_failed"
        },
        {
            "code": "GATEWAY_ERROR",
            "desc": "Payment failed after issuer response timed out; customer balance appears sufficient.",
            "reason": "payment_failed"
        },
        {
            "code": "BAD_REQUEST_ERROR",
            "desc": "Transaction blocked by issuer risk system after unusual velocity and device change.",
            "reason": "payment_failed"
        },
        {
            "code": "BAD_REQUEST_ERROR",
            "desc": "Card returned expiry mismatch after migration.",
            "reason": "payment_failed"
        },
        {
            "code": "GATEWAY_ERROR",
            "desc": "Insufficient funds detected during authorization hold.",
            "reason": "payment_failed"
        }
    ]
    
    for _ in range(num_records):
        scenario = random.choice(failure_scenarios)
        records.append({
            "payment_id": f"pay_{uuid.uuid4().hex[:10]}",
            "amount": random.randint(100, 5000) * 100, # INR in paise
            "currency": "INR",
            "status": "failed",
            "error_code": scenario["code"],
            "error_reason": scenario["reason"],
            "error_description": scenario["desc"],
            "customer_id": f"cust_{random.randint(10000, 99999)}",
            "contact": f"+9198765{random.randint(10000, 99999)}",
            "email": "customer@example.com",
            "retry_count": random.choice([0, 0, 1, 2, 4]), # Include max retries
            "card_network": random.choice(["Visa", "MasterCard", "RuPay"]),
            "created_at": int(1707433011 - random.randint(0, 100000))
        })
        
    return records
