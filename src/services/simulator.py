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
            return False, 0, "Failed - Bank blocked risky retry", True
            
        elif ground_truth_cause == "insufficient_funds":
            # Immediate retry on insufficient funds almost always fails (they didn't get paid in 2 seconds)
            if random.random() < 0.05:
                return True, record.amount, "Success - Funds available", False
            return False, 0, "Failed - Still insufficient funds", True
            
        elif ground_truth_cause in ["bank_timeout", "network_error"]:
            if random.random() < 0.75:
                return True, record.amount, "Success - Network recovered", False
            return False, 0, "Failed - Network still down", False
            
        elif ground_truth_cause in ["card_expired", "otp_failed"]:
            return False, 0, f"Failed - {ground_truth_cause}", True
            
        else:
            return False, 0, "Failed - Unknown reason", False

    @staticmethod
    def simulate_payment_link(ground_truth_cause: str, record: PaymentRecord) -> tuple[bool, int, str, bool]:
        """Simulates customer converting on a payment link."""
        if ground_truth_cause == "risky_card":
            return False, 0, "Failed - Customer ignored link", False
            
        # ~40% of legitimate customers pay when sent a link for an expired card or OTP failure
        if random.random() < 0.40:
            return True, record.amount, "Success - Customer paid via link", False
            
        return False, 0, "Failed - Link abandoned", False

    @staticmethod
    def simulate_delayed_retry(ground_truth_cause: str, record: PaymentRecord) -> tuple[bool, int, str, bool]:
        """Simulates a +24h delayed retry (e.g., waiting for funds to clear)."""
        if ground_truth_cause == "risky_card":
            return False, 0, "Failed - Bank blocked delayed retry", True
            
        elif ground_truth_cause == "insufficient_funds":
            # Giving the customer 24h to deposit money significantly increases success rate
            if random.random() < 0.60:
                return True, record.amount, "Success - Funds available after 24h", False
            return False, 0, "Failed - Still insufficient funds after 24h", False
            
        elif ground_truth_cause in ["bank_timeout", "network_error"]:
            if random.random() < 0.90:
                return True, record.amount, "Success - Network recovered after 24h", False
            return False, 0, "Failed - Network still down", False
            
        return False, 0, "Failed - Issue persists", False
