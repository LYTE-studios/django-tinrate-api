from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from django.urls import reverse
from payments.models.payments_models import Payment
from unittest.mock import patch
import stripe

User = get_user_model()


class CreatePaymentIntentViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.customer = User.objects.create_user(username="customer", password="testpass")
        self.expert = User.objects.create_user(username="expert", password="testpass")
        self.client.force_authenticate(user=self.customer)
        self.url = reverse("intent_payment")

    @patch("stripe.PaymentIntent.create")
    def test_create_payment_intent_success(self, mock_create_intent):
        """Test successful creation of a PaymentIntent."""
        mock_create_intent.return_value = {
            "id": "pi_123",
            "client_secret": "secret_123",
        }

        data = {"amount": 50.00, "expert_id": int(self.expert.id), "customer_id":self.customer.id}
        response = self.client.post(self.url, data, format="json")
        print(response.content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("payment_intent", response.data)
        self.assertIn("client_secret", response.data)
        #check if payment was created in the database
        self.assertTrue(Payment.objects.filter(stripe_payment_intent_id="pi_123").exists())

        payment = Payment.objects.get(stripe_payment_intent_id=response.data["payment_intent"])
        self.assertEqual(payment.customer, self.customer)
        self.assertEqual(payment.expert, self.expert)
        self.assertEqual(payment.amount, data["amount"])
        self.assertEqual(payment.status, "authorized")

    def test_create_payment_intent_missing_fields(self):
        """Test failure when required fields are missing."""
        data={}
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("amount", response.data)
        self.assertIn("expert_id", response.data)

    def test_create_payment_intent_invalid_expert(self):
        """Test failure when the expert does not exist."""
        data={"amount": 50.00, "expert_id": 5555}
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "Expert not found")

    @patch("stripe.PaymentIntent.create")
    def test_payment_intent_rate_limit(self, mock_create_intent):
        """Test failure when Stripe's rate limit is exceeded."""
        mock_create_intent.side_effect = stripe.error.RateLimitError("Too many requests")

        data={"amount":50.00, "expert_id": int(self.expert.id)}
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertEqual(response.data["error"], "Rate limit exceeded. Please try again later.")

    @patch("stripe.PaymentIntent.create")
    def test_create_payment_intent_invalid_request(self, mock_create_intent):
        """Test failure when Stripe raises an InvalidRequestError."""
        mock_create_intent.side_effect = stripe.error.InvalidRequestError("Invalid request", param="currency")

        data={"amount":50.00, "expert_id": int(self.expert.id)}
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid request", response.data["error"])


    @patch("stripe.PaymentIntent.create")
    def test_create_payment_intent_authentication_error(self, mock_create_intent):
        """Test failure when Stripe authentication fails."""
        mock_create_intent.side_effect = stripe.error.AuthenticationError("Invalid API key")

        data={"amount": 50.00, "expert_id": int(self.expert.id)}
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("Authentication error", response.data["error"])

    @patch("stripe.PaymentIntent.create")
    def test_create_payment_intent_generic_stripe_error(self, mock_create_intent):
        """Test failure when Stripe raises a generic error."""
        mock_create_intent.side_effect = stripe.error.StripeError("Stripe is down")

        data={"amount": 50.00, "expert_id": int(self.expert.id)}
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("Stripe API error", response.data["error"])

    @patch("stripe.PaymentIntent.create")
    @patch("payments.models.payments_models.Payment.objects.create")
    def test_create_payment_intent_db_error(self, mock_create_payment, mock_create_intent):
        """Test failure whe  the payment record cannot be saved in the database."""
        mock_create_intent.return_value={
            "id": "pi_123",
            "client_secret": "secret_123",
        }
        mock_create_payment.side_effect = Exception("Database error")

        data={"amount": 50.00, "expert_id": int(self.expert.id)}
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("Error saving payment information", response.data["error"])

        
class ChargeCancellationFeeViewTest(APITestCase):
    def setUp(self):
        self.customer = User.objects.create_user(username="customer", password="password123")
        self.expert = User.objects.create_user(username="expert", password="password123", is_expert=True, 
                                               allow_cancellation_fee=True)
        
        self.payment = Payment.objects.create(
            customer=self.customer,
            expert=self.expert,
            stripe_payment_intent_id="pi_123",
            amount=100.00,
            status="authorized",
        )
        self.url = reverse("cancel_payment")

    @patch("stripe.PaymentIntent.capture")
    def test_successful_cancellation_fee(self, mock_capture):
        """Test successful cancellation fee charge."""
        mock_capture.return_value={"id":"pi_123"}
        
        self.client.force_authenticate(user=self.customer)
        data={
            "payment_intent_id": "pi_123",
            "percentage":20,
        }

        percentage = 20
        response = self.client.post(self.url, data)
        self.payment.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.payment.status, "partially_captured")
        self.assertEqual(self.payment.cancellation_fee, 20)
        self.assertEqual(f"Captured {percentage}% cancellation fee.", response.json()["message"])

    def test_expert_does_not_charge_fee(self):
        """Test when expert does not charge cancellation fee."""
        self.expert.allow_cancellation_fee = False
        self.expert.save()

        self.client.force_authenticate(user=self.customer)
        data={
            "payment_intent_id":"pi_123",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Expert does not charge cancellation fee.", response.json()["message"])

    
    def test_missing_payment_intent_id(self):
        """Test request without payment_intent_id."""
        self.client.force_authenticate(user=self.customer)
        data = {
            "percentage": 20,
        }
        response = self.client.post(self.url, data)
        self.assertIn("payment_intent_id", response.data)
        self.assertIn("This field is required.", str(response.data["payment_intent_id"]))

    def test_missing_percentage_when_expert_allows_fee(self):
        """Test missing percentage when expert allows fees."""
        self.client.force_authenticate(user=self.customer)
        data = {
            "payment_intent_id":"pi_123",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Cancellation percentage is required.", response.json()["error"])     

    def test_invalid_payment_id(self):
        """Test invalid payment_intent_id (Payment not found).""" 
        self.client.force_authenticate(user=self.customer)
        data={
            "payment_intent_id": "pi_invalid",
            "percentage":20,
        }  
        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("'Payment not found.", str(response.data["payment_intent_id"]))

    @patch("stripe.PaymentIntent.capture", side_effect=stripe.error.CardError("Card declined", param="card",
                                                                              code="card_declined"))
    def test_stripe_card_error(self, mock_capture):
        """Test Stripe card error during cancellation fee charge."""
        self.client.force_authenticate(user=self.customer)
        data={
            "payment_intent_id":"pi_123",
            "percentage": 20,
        }
        response= self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Card error:", response.json()["error"])

