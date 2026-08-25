import razorpay
from typing import Dict, Optional
from src.config import RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET

class RazorpayService:
    def __init__(self):
        self.client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

    def create_payment_link(self, amount: int, currency: str, description: str, customer: Dict[str, str]) -> Optional[str]:
        """Creates a payment link using Razorpay APIs."""
        try:
            payload = {
                "amount": amount,
                "currency": currency,
                "accept_partial": False,
                "description": description,
                "customer": customer,
                "notify": {
                    "sms": True,
                    "email": True
                },
                "reminder_enable": False,
                "notes": {
                    "reason": "payment_recovery"
                }
            }
            link_response = self.client.payment_link.create(payload)
            return link_response.get("short_url")
        except Exception as e:
            print(f"Error creating payment link: {e}")
            return None

    def capture_payment(self, payment_id: str, amount: int) -> bool:
        """Capture an authorized payment."""
        try:
            self.client.payment.capture(payment_id, amount)
            return True
        except Exception as e:
            print(f"Error capturing payment: {e}")
            return False
