from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Payment(models.Model):
    """
    Represents a payment transaction in the system.

    Attributes:
        customer (User): The customer making the payment.
        expert (User): The expert receiving the payment.
        stripe_payment_intent_id (str): The unique Stripe PaymentIntent ID.
        payment_method_id (str): The unique Stripe PaymentMethod ID (card details stored securely by Stripe).
        amount (Decimal): The total amount held.
        status (str): The current status of the payment (Authorized, Captured, Canceled, Refunded).
        cancellation_fee (Decimal): The percentage of the charge if the customer cancels late.
        created_at (datetime): The timestamp when the payment was created.
    """
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="payments_made")
    expert = models.ForeignKey(User, on_delete=models.CASCADE, related_name="payments_received")
    stripe_payment_intent_id = models.CharField(max_length=255, unique=True)
    payment_method_id = models.CharField(max_length=255, null=True, blank=True) 
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=50,
        choices=[
            ("authorized", "Authorized"), #payment blocked, not captured yet
            ("captured", "Captured"), #payment fully charged
            ("partially_captured", "Partially Captured"), #partial charge applied
            ("canceled", "Canceled"), #payment released, no charge
            ("refunded", "Refunded"), #after charge, full refund
            ("partially_refunded", " Partially Refunded"), #after charge, partial refund
        ],
        default="authorized"
    )
    cancellation_fee = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.0,
        help_text="Percentage of the charge kept if the customer cancels late."
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer} → {self.expert} | {self.amount} | {self.status}"