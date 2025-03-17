import uuid
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
    transaction_fee = models.DecimalField(max_digits=5, decimal_places=2)
    status = models.CharField(
        max_length=50,
        choices=[
            ("authorized", "Authorized"), #payment blocked, not captured yet
            ("captured", "Captured"), #payment fully charged
            ("partially_captured", "Partially Captured"), #partial charge applied
            ("canceled", "Canceled"), #payment released, no charge
            ("refunded", "Refunded"), #after charge, full refund
            ("partially_refunded", " Partially Refunded"), #after charge, partial refund
            ("failed", " Failed"), #payment attempt failed
        ],
        default="authorized"
    )
    cancellation_fee = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.0,
        help_text="Percentage of the charge kept if the customer cancels late."
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer} → {self.expert} | {self.amount:.2f} | {self.status}"
    

class Transaction(models.Model):
    """
    Represents a financial transaction, which can be a charge or withdrawal.

    Attributes:
        user_id (User): The user initiating the transaction.
        payment (Payment): A reference to the payment associated with this transaction.
        type (str): The type of transaction (charge or withdrawal).
        status (str): The status of the transaction (completed, canceled, pending).
        amount (Decimal): The amount of money involved in the transaction.
        created_at (datetime): The timestamp when the transaction occurred.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.OneToOneField(User, on_delete=models.CASCADE, related_name="transactions")
    payment = models.ForeignKey("Payment", on_delete=models.SET_NULL, null=True, related_name="payments")
    type = models.CharField(max_length=50, choices=[("charge", "Charge"), ("withdrawal", "Withdrawal")])
    status = models.CharField(max_length=50, choices=[
                                                ("completed", "Completed"),
                                                ("cancel", "Cancel"), 
                                                ("withdrawal", "Withdrawal"),
                                                ("pending", "Pending")])
    amount = models.DecimalField(max_digits=5, decimal_places=2)
    created_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Transaction {self.id} | {self.amount:.2f}"
    
class Billing(models.Model):
    """
    Represents the billing details for a user, including earnings and balance.

    Attributes:
        user_id (User): The user associated with the billing details.
        total_earnings (Decimal): Total amount earned by the user.
        balance (Decimal): Current balance of the user.
        amount (Decimal): Amount owed or to be paid out.
        total_hours (Decimal): Total hours worked, if applicable.
        date (datetime): The date the billing entry was created.
        transaction_status (Transaction): The transaction associated with the billing.
    
    Methods:
        __str__: Returns a string representation of the billing entry.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.OneToOneField(User, on_delete=models.CASCADE, related_name="billing")
    total_earnings = models.DecimalField(max_digits=5, decimal_places=2)
    balance = models.DecimalField(max_digits=5, decimal_places=2)
    amount = models.DecimalField(max_digits=5, decimal_places=2)
    total_hours = models.DecimalField(max_digits=5, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)
    transaction_status = models.ForeignKey("Transaction", on_delete=models.SET_NULL, null=True, related_name="billing_status")

    def __str__(self):
        return f"Billing for {self.user_id.username} | Total Earnings: {self.total_earnings}"