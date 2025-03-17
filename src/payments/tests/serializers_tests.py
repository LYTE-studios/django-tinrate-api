from datetime import datetime
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from rest_framework.exceptions import ValidationError, NotFound
from django.urls import reverse
from payments.models.payments_models import Payment
from payments.serializers.payments_cancel_serializers import CancelPaymentSerializer
from payments.serializers.payments_capture_serializers import CapturePaymentSerializer
from payments.serializers.payments_fail_serializers import FailedPaymentSerializer
from payments.serializers.payments_refund_serializers import RefundPaymentSerializer
from payments.serializers.payments_release_serializers import ReleasePaymentSerializer
from unittest.mock import patch
import stripe
import uuid

User = get_user_model()

class PaymentSerializerTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.customer = User.objects.create_user(username="customer", password="testpass")
        self.expert = User.objects.create_user(username="expert", password="testpass")
        self.client.force_authenticate(user=self.customer)
        self.url = reverse("intent_payment")

    @patch("stripe.PaymentIntent.create")
    def test_valid_data_creates_payment(self, mock_create_intent):
        """Test that valid data creates a Payment object."""
        mock_create_intent.return_value = {
            "id": "pi_123",
            "client_secret": "secret_123",
        }
        data = {"amount":50.00, "expert_id": int(self.expert.id)}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        payment = Payment.objects.get(id=response.data["id"])
        self.assertEqual(payment.amount, 50.00)
        self.assertEqual(payment.customer, self.customer)
        self.assertEqual(payment.expert, self.expert)
        self.assertEqual(payment.status, "authorized")

    def test_invalid_amount(self):
        """Test creating payment with invalid amount."""
        data =  {"amount":0, "expert_id": int(self.expert.id)}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Amount must be greater than 0.", response.data["non_field_errors"])

    def test_invalid_expert_id(self):
        """Test creating payment with invalid expert_id."""
        data = {"amount":100.00, "expert_id": 5555}
        response = self.client.post(self.url, data, format="json")
        error_message = "Expert not found."
        found_error = any(error == error_message for error in response.data)
        
        self.assertTrue(found_error, "Expected error message for expert_id not found.")

    def test_missing_expert_id(self):
        """test creating payment with missing expert_id."""
        data = {"amount":100.00}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("This field is required.", response.data["expert_id"])

    def test_missing_amount(self):
        """Test creating payment without an amount set."""
        data = {"expert_id":  int(self.expert.id)}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("This field is required.", response.data["amount"])


class CancelPaymentSerializerTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.customer = User.objects.create_user(username="customer", password="testpass")
        self.expert = User.objects.create_user(username="expert", password="testpass")
        self.client.force_authenticate(user=self.customer)
        self.url = reverse("intent_payment")

        """Set up test data for various payment statuses."""
        self.payment_authorized = Payment.objects.create(
            stripe_payment_intent_id="pi_123",
            status="authorized",
            amount=50.00,
            customer=self.customer,
            expert=self.expert,
        )
        self.payment_partially_captured = Payment.objects.create(
            stripe_payment_intent_id="pi_124",
            status="partially_captured",
            amount=50.00,
            customer=self.customer,
            expert=self.expert,
        )
        self.payment_canceled = Payment.objects.create(
            stripe_payment_intent_id="pi_125",
            status="canceled",
            amount=50.00,
            customer=self.customer,
            expert=self.expert,
        )
        self.payment_refunded = Payment.objects.create(
            stripe_payment_intent_id="pi_126",
            status="refunded",
            amount=50.00,
            customer=self.customer,
            expert=self.expert,
        )
        self.payment_failed = Payment.objects.create(
            stripe_payment_intent_id="pi_127",
            status="failed",
            amount=50.00,
            customer=self.customer,
            expert=self.expert,
        )

    def test_valid_payment_intent_id_authorized(self):
        """Test that an authorized payment can be validated successfully."""
        serializer=CancelPaymentSerializer(data={"payment_intent_id":"pi_123"})
        self.assertTrue(serializer.is_valid())

    def test_valid_payment_intent_id_partially_captured(self):
        """Test that a partially captured payment can be validated successfully."""
        serializer = CancelPaymentSerializer(data={"payment_intent_id":"pi_124"})
        self.assertTrue(serializer.is_valid())

    def test_invalid_payment_intent_id_not_found(self):
        """Test that a non-existent PaymentIntent ID raises a validation error."""
        serializer = CancelPaymentSerializer(data={"payment_intent_id":"pi_non_existent"})
        with self.assertRaises(ValidationError) as context:
            serializer.is_valid(raise_exception=True)
        self.assertIn("Payment not found.", str(context.exception))

    def test_invalid_payment_intent_id_canceled(self):
        """Test that a canceled payment cannot be validated."""
        serializer = CancelPaymentSerializer(data={"payment_intent_id":"pi_125"})
        with self.assertRaises(ValidationError) as context:
            serializer.is_valid(raise_exception=True)
        self.assertIn("Payment has already been canceled.", str(context.exception))

    def test_invalid_payment_intent_id_refunded(self):
        """Test that a refunded payment cannot be validated."""
        serializer = CancelPaymentSerializer(data={"payment_intent_id":"pi_126"})
        with self.assertRaises(ValidationError) as context:
            serializer.is_valid(raise_exception=True)
        self.assertIn("Refunded payments cannot be canceled.", str(context.exception))

    def test_invalid_payment_intent_id_other_status(self):
        """Test that a payment with an invalid status cannot be validated."""
        serializer = CancelPaymentSerializer(data={"payment_intent_id":"pi_127"})
        with self.assertRaises(ValidationError) as context:
            serializer.is_valid(raise_exception=True)
        self.assertIn("Only authorized or partially captured payments can be canceled.", str(context.exception))

    def test_optional_percentage_field(self):
        """Test that the percentage field is optional and correclty validated."""
        serializer = CancelPaymentSerializer(data={"payment_intent_id": "pi_123",
            "percentage": 20.5})
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["percentage"], 20.5)


class CapturePaymentSerializerTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.customer = User.objects.create_user(username="customer", password="testpass")
        self.expert = User.objects.create_user(username="expert", password="testpass")
        self.client.force_authenticate(user=self.customer)
        self.url = reverse("intent_payment")

        """Set up test data for various payment statuses."""
        self.payment_authorized = Payment.objects.create(
            stripe_payment_intent_id="pi_123",
            status="authorized",
            amount=50.00,
            customer=self.customer,
            expert=self.expert,
        )
        self.payment_captured = Payment.objects.create(
            stripe_payment_intent_id="pi_124",
            status="captured",
            amount=50.00,
            customer=self.customer,
            expert=self.expert,
        )
        self.payment_refunded = Payment.objects.create(
            stripe_payment_intent_id="pi_126",
            status="refunded",
            amount=50.00,
            customer=self.customer,
            expert=self.expert,
        )
        self.payment_failed = Payment.objects.create(
            stripe_payment_intent_id="pi_127",
            status="failed",
            amount=50.00,
            customer=self.customer,
            expert=self.expert,
        )

    def test_valid_payment_intent_id_authorized(self):
        """Test that an authorized payment intent ID passes validation."""
        serializer = CapturePaymentSerializer(data={"payment_intent_id":"pi_123"})
        self.assertTrue(serializer.is_valid())

    def test_invalid_payment_intent_id_not_found(self):
        """Test that a non-existent payment intent ID raises a validation error."""
        serializer = CapturePaymentSerializer(data={"payment_intent_id":"pi_non_existent"})
        with self.assertRaises(ValidationError) as context:
            serializer.is_valid(raise_exception=True)
        self.assertIn("Payment with this PaymentIntent ID does not exist.", str(context.exception))

    def test_invalid_payment_intent_id_captured(self):
        """Test that an already captured payment intent ID raises a validation error."""
        serializer = CapturePaymentSerializer(data={"payment_intent_id":"pi_124"})
        with self.assertRaises(ValidationError) as context:
            serializer.is_valid(raise_exception=True)
        self.assertIn("Payment has already been captured.", str(context.exception))

    def test_invalid_payment_intent_id_refunded(self):
        """Test that a refunded payment intent ID raises a validation error."""
        serializer = CapturePaymentSerializer(data={"payment_intent_id":"pi_126"})
        with self.assertRaises(ValidationError) as context:
            serializer.is_valid(raise_exception=True)
        self.assertIn("Refunded payments cannot be captured.", str(context.exception))
    
    def test_invalid_payment_intent_id_wrong_status(self):
        """Test that a payment intent ID with a non-authorized status raises a validation error."""
        serializer = CapturePaymentSerializer(data={"payment_intent_id":"pi_127"})
        with self.assertRaises(ValidationError) as context:
            serializer.is_valid(raise_exception=True)
        self.assertIn("Payment is not in authorized state.", str(context.exception))


class FailedPaymentSerializerTest(TestCase):
    def setUp(self):
        self.valid_data={
            "id":uuid.uuid4(),
            "amount":Decimal("49.99"),
            "status":"failed",
            "created_at":datetime.now()
        }
        self.invalid_data_status={
            "id":uuid.uuid4(),
            "amount":Decimal("49.99"),
            "status":"captured",
            "created_at":datetime.now()
        }
        self.missing_fields_data={
            "id":uuid.uuid4(),
            "status":"failed",
            "created_at":datetime.now()
        }

    def test_valid_failed_payments(self):
        """Test that the serializer is valid when given correct data."""
        serializer = FailedPaymentSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_invalid_status(self):
        """Test that the seriallizer raises a validation error for non-failed status."""
        serializer = FailedPaymentSerializer(data=self.invalid_data_status)
        self.assertFalse(serializer.is_valid())
        self.assertIn("status", serializer.errors)
        self.assertEqual(serializer.errors["status"][0], "Only failed payments can be retrieved.")

    def test_missing_required_fields(self):
        """Test that the serializer fails when required fields are missing."""
        serializer = FailedPaymentSerializer(data=self.missing_fields_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("amount", serializer.errors)


class RefundPaymentSerializerTest(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(username="customer", password="testpass")
        self.expert = User.objects.create_user(username="expert", password="testpass")
        self.payment_intent_id = uuid.uuid4()
        self.payment = Payment.objects.create(
            stripe_payment_intent_id=str(self.payment_intent_id),
            status="authorized",
            amount=100.00,
            customer=self.customer,
            expert=self.expert,
        )
        self.valid_data={
            "payment_intent_id":str(self.payment_intent_id),
            "refund_amount":Decimal("50.00")
        }
        self.invalid_data_amount={
            "payment_intent_id":str(self.payment_intent_id),
            "refund_amount":Decimal("-10.00")
        }
        self.excessive_refund_amount={
            "payment_intent_id":str(self.payment_intent_id),
            "refund_amount":Decimal("150.00")
        }
        self.invalid_payment_intent={
            "payment_intent_id":"invalid_intent_id",
            "refund_amount":Decimal("50.00")
        }

    def test_valid_refund_payment(self):
        """Test that the serializer is valid whe given correct data."""
        serializer = RefundPaymentSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_invalid_refund_amount(self):
        """
        Test that the serializer raises a validation error when the refund amount
        is less than or equal to 0.
        """
        serializer = RefundPaymentSerializer(data=self.invalid_data_amount)
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)
        self.assertEqual(serializer.errors["non_field_errors"][0], "Refund amount must be greater than 0.")

    def test_excessive_refund_amount(self):
        """
        Test that the serializer raises a vaidation error if the refund amount
        exceeds the total payment amount.
        """
        serializer = RefundPaymentSerializer(data=self.excessive_refund_amount)
        self.assertFalse(serializer.is_valid())
        self.assertIn("refund_amount", serializer.errors)
        self.assertEqual(serializer.errors["refund_amount"][0], "Refund amount cannot exceed the total payment amount.")

    def test_invalid_payment_intent_id(self):
        """Test that the serializer raises a validation error when the payment intent ID does not exist."""
        serializer = RefundPaymentSerializer(data=self.invalid_payment_intent)
        with self.assertRaises(NotFound):
            serializer.is_valid(raise_exception=True)

    def test_already_refunded_payment(self):
        """Test that the serializer raises a validation error when the payment has already been refunded."""
        self.payment.status = "refunded"
        self.payment.save()
        serializer = RefundPaymentSerializer(data=self.valid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("payment_intent_id", serializer.errors)
        self.assertEqual(serializer.errors["payment_intent_id"][0], "Payment has already been refunded.")

    def test_invalid_payment_status(self):
        """
        Test that the serializer raises a validation error if the payment status is 
        not authorized or captured.
        """
        self.payment.status = "failed"
        self.payment.save()
        serializer = RefundPaymentSerializer(data=self.valid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("payment_intent_id", serializer.errors)
        self.assertEqual(serializer.errors["payment_intent_id"][0], "Only authorized and captured payments can be refunded.")


class ReleasePaymentSerializerTest(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(username="customer", password="testpass")
        self.expert = User.objects.create_user(username="expert", password="testpass")
        self.payment_authorized = Payment.objects.create(
        stripe_payment_intent_id=str(uuid.uuid4()),
        amount=Decimal("49.99"),
        status="authorized",
        created_at=datetime.now(),
        customer=self.customer,
        expert=self.expert,
        )
        self.payment_canceled = Payment.objects.create(
        stripe_payment_intent_id=str(uuid.uuid4()),
        amount=Decimal("49.99"),
        status="canceled",
        created_at=datetime.now(),
        customer=self.customer,
        expert=self.expert,
        )
        self.payment_captured = Payment.objects.create(
        stripe_payment_intent_id=str(uuid.uuid4()),
        amount=Decimal("49.99"),
        status="captured",
        created_at=datetime.now(),
        customer=self.customer,
        expert=self.expert,
        )
        self.valid_data={"payment_intent_id": str(self.payment_authorized.stripe_payment_intent_id)}
        self.invalid_data_not_found={"payment_intent_id": "non_existent_id"}
        self.invalid_data_released={"payment_intent_id": str(self.payment_canceled.stripe_payment_intent_id)}
        self.invalid_data={"payment_intent_id": str(self.payment_captured.stripe_payment_intent_id)}

    def test_valid_release_payment(self):
        """Test that the serializer is valid when  given correct data."""
        serializer = ReleasePaymentSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_invalid_payment_intent_id_not_found(self):
        """Test that the serializer raises a validation error when the payment intent ID does not exist."""
        serializer = ReleasePaymentSerializer(data=self.invalid_data_not_found)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors['payment_intent_id'][0], "Payment not found.")

    def test_invalid_payment_intent_id_already_released(self):
        """Test that the serializer raises a validation error when the payment has already been released."""
        serializer = ReleasePaymentSerializer(data=self.invalid_data_released)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors['payment_intent_id'][0], "Payment has already been released.")

    def test_invalid_payment_intent_id_invalid_status(self):
        """Test that the serializer raises a validation error when the payment is in an invalid state for release."""
        serializer = ReleasePaymentSerializer(data=self.invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors['payment_intent_id'][0], "Payment cannot be released because it is in an invalid state.")
