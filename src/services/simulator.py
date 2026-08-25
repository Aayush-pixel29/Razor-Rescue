import random
from src.models.schemas import PaymentRecord

class PaymentSimulator:
    """
    Simulates the real-world outcome of payment recovery actions based on ground truth.
    This replaces random success with mathematically sound probability environments.
    """
    
    @staticmethod
    def simulate_immediate_retry(ground_truth_cause: str, record: PaymentRecord) -> tuple[bool, int, str, bool]:
        """Returns (success, amount_recovered, status_message, is_bad_retry)"""
        
        if ground_truth_cause == "risky_card":
            # Retrying a risky card is terrible and gets blocked by the bank
            return False, 0, "Failed - Bank blocked risky retry", True
            
        elif ground_truth_cause == "insufficient_funds":
            # Immediate retry on insufficient funds almost always fails (they didn't get paid in 2 seconds)
            if random.random() < 0.05:
                return True, record.amount, "Success - Funds available", False
            return False, 0, "Failed - Still insufficient funds", True
            
        elif ground_truth_cause in ["bank_timeout", "network_error"]:
            # High success rate for transient network errors
            if random.random() < 0.75:
                return True, record.amount, "Success - Network recovered", False
            return False, 0, "Failed - Network still down", False
            
        elif ground_truth_cause == "card_expired":
            # Retrying an expired card always fails
            return False, 0, "Failed - Card expired", True
            
        elif ground_truth_cause == "otp_failed":
            # Retrying without user interaction fails
            return False, 0, "Failed - Missing user authentication", True
            
        else:
            return False, 0, "Failed - Unknown reason", False
