from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from payments.models.payments_models import Payment

User = get_user_model()

class PaymentModelTest(TestCase):
    def setUp(self):
        """Set up test users and a payment instance."""
        self.customer = User.objects.create_user(username="customer", password="testpass")
        self.expert = User.objects.create_user(username="expert", password="testpass")

    def test_create_payment(self):
        """Test if a payment instance is created correctly."""
        payment = Payment.objects.create(
            customer=self.customer,
            expert=self.expert,
            stripe_payment_intent_id="pi_123456789",
            payment_method_id="pm_987654321",
            amount=100.00,
        )
        self.assertEqual(payment.customer, self.customer)
        self.assertEqual(payment.expert, self.expert)
        self.assertEqual(payment.amount, 100.00)
        self.assertEqual(payment.status, "authorized")
        self.assertEqual(payment.cancellation_fee, 0.0)

    def test_status_choices(self):
        """Test that status only accepts valid choices."""
        payment = Payment.objects.create(
            customer=self.customer,
            expert=self.expert,
            stripe_payment_intent_id="pi_123456789",
            amount=50.00,
        )
        valid_statuses = [
            "authorized", "captured", "partially_captured",
            "canceled", "refunded", "partially_refunded", "failed"
        ]
        for status in valid_statuses:
            payment.status = status
            payment.save()
            self.assertEqual(payment.status, status)

    def test_invalid_status_choice(self):
        """Test that an invalid status raises an error."""
        payment = Payment(
            customer=self.customer,
            expert=self.expert,
            stripe_payment_intent_id="pi_126",
            amount=Decimal("25.00"),
            status="not_a_valid_status"
        )
        with self.assertRaises(Exception):
            payment.full_clean()

    def test_payment_str(self):
        """Test the string representation of a payment."""
        payment = Payment.objects.create(
            customer=self.customer,
            expert=self.expert,
            stripe_payment_intent_id="pi_123456789",
            amount=75.00,
        )
        expected_str = f"{self.customer} → {self.expert} | 75.00 | authorized"
        self.assertEqual(str(payment), expected_str)
    
    def test_unique_stripe_payment_intent_id(self):
        """Test that duplicate Stripe PaymentIntent IDs are not allowed."""
        Payment.objects.create(
            customer=self.customer,
            expert=self.expert,
            stripe_payment_intent_id="pi_125",
            amount=Decimal("75.00")
        )
        with self.assertRaises(Exception):
            Payment.objects.create(
                customer=self.customer,
                expert=self.expert,
                stripe_payment_intent_id="pi_125",
                amount=Decimal("75.00")
                )