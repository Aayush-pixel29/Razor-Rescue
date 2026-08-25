import json
import random
from datetime import datetime, timedelta

def generate_synthetic_batch(num_records: int = 50):
    reasons = [
        ("BAD_REQUEST_ERROR", "payment_failed", "The payment was failed due to incorrect OTP"),
        ("GATEWAY_ERROR", "payment_failed", "Bank timeout occurred"),
        ("BAD_REQUEST_ERROR", "payment_failed", "Insufficient balance in the account"),
        ("BAD_REQUEST_ERROR", "payment_failed", "Card has expired"),
        ("RISK_ERROR", "payment_failed", "Transaction flagged by risk rules"),
        ("GATEWAY_ERROR", "payment_failed", "Network error while connecting to bank")
    ]
    
    records = []
    for i in range(num_records):
        error = random.choice(reasons)
        record = {
            "payment_id": f"pay_fake_{random.randint(100000, 999999)}",
            "amount": random.randint(100, 5000) * 100, # paise
            "currency": "INR",
            "status": "failed",
            "error_code": error[0],
            "error_reason": error[1],
            "error_description": error[2],
            "customer_id": f"cust_{random.randint(10000, 99999)}",
            "contact": "+919876543210",
            "email": f"customer{i}@example.com",
            "retry_count": random.choice([0, 0, 0, 1, 2, 3, 4]), # Some will exceed max retries
            "card_network": random.choice(["Visa", "MasterCard", "RuPay"]),
            "created_at": int((datetime.now() - timedelta(days=random.randint(0, 5))).timestamp())
        }
        records.append(record)
        
    return records

if __name__ == "__main__":
    records = generate_synthetic_batch(50)
    with open("data_batch.json", "w") as f:
        json.dump(records, f, indent=2)
    print(f"Generated {len(records)} records in data_batch.json")
