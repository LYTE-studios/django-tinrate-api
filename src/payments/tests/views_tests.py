import json
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

class CapturePaymentViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.customer = User.objects.create_user(username="customer", password="password123")
        self.expert = User.objects.create_user(username="expert", password="password123", is_expert=True, 
                                               allow_cancellation_fee=True)
        self.client.force_authenticate(user=self.customer)

        self.payment = Payment.objects.create(
            customer=self.customer,
            expert=self.expert,
            stripe_payment_intent_id="pi_123",
            amount=100.00,
            status="authorized",
        )
        self.valid_payload = {"payment_intent_id" : "pi_123"}
        self.invalid_payload = {"payment_intent_id" : "invalid_id"}
        self.url = reverse("capture_payment")

    @patch("stripe.PaymentIntent.capture")
    def test_successful_payment_capture(self, mock_capture):
        """Test capturing a payment successfully."""
        response = self.client.post(self.url, self.valid_payload, format="json")

        self.payment.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["message"], "Payment captured successfuly.")
        self.assertEqual(self.payment.status, "captured")
        
    def test_missing_payment_intent_id(self):
        """Test request without payment_intent_id."""
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("payment_intent_id", response.json())

    @patch("stripe.PaymentIntent.capture", side_effect=stripe.error.InvalidRequestError("Invalid request",
                                                                                        param="payment_intent_id"))
    def test_invalid_payment_intent(self, mock_capture):
        """Test capturing payment with an invalid PaymentIntent ID."""
        response = self.client.post(self.url, self.invalid_payload, format="json")
        print(response.content)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Payment with this PaymentIntent ID does not exist.", str(response.data["payment_intent_id"]))

    @patch("stripe.PaymentIntent.capture", side_effect=stripe.error.CardError("Card declined",
                                                                             param="card",
                                                                             code="card_declined"))
    def test_card_error(self, mock_capture):
        """Test capturing payment when Stripe raises a CardError."""
        response = self.client.post(self.url, self.valid_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Card error", response.json()["error"])

    @patch("stripe.PaymentIntent.capture", side_effect=stripe.error.RateLimitError("Too many requests"))
    def test_rate_limit_error(self, mock_capture):
        """Test capturing payment when Stripe rate limit is exceeded."""
        response = self.client.post(self.url, self.valid_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn("Rate limit exceeded. Please try again later.", response.json()["error"])
        
    @patch("stripe.PaymentIntent.capture", side_effect=stripe.error.AuthenticationError("Invalid API key"))
    def test_authentication_error(self, mock_capture):
        """Test capturing payment when there's an authentication issue with Stripe."""
        response = self.client.post(self.url, self.valid_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("Authentication error", response.json()["error"])

    @patch("stripe.PaymentIntent.capture", side_effect=Exception("Unexpected error"))
    def test_unexpected_error(self, mock_capture):
        """Test capturing payment when an unkown error occurs."""
        response = self.client.post(self.url, self.valid_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("An unexpected error occured", response.json()["error"])
           

class FailPaymentsViewTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.customer = User.objects.create_user(username="customer", password="password123")
        self.expert = User.objects.create_user(username="expert", password="password123", is_expert=True, 
                                               allow_cancellation_fee=True)
        self.client.force_authenticate(user=self.customer)

        self.payment1 = Payment.objects.create(
            customer=self.customer,
            expert=self.expert,
            stripe_payment_intent_id="pi_123",
            amount=100.00,
            status="failed",
        )
        self.payment2 = Payment.objects.create(
            customer=self.customer,
            expert=self.expert,
            stripe_payment_intent_id="pi_124",
            amount=100.00,
            status="failed",
        )
        self.url = reverse("fail_payment")

    def test_get_failed_payments(self):
        """Test to retrieve a list of faile payments for the authenticated user."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(int(response.data[0]["id"]), self.payment1.id)
        self.assertEqual(int(response.data[1]["id"]), self.payment2.id)

    def test_get_failed_payments_no_results(self):
        """test if no failed payments are found."""
        other_user = get_user_model().objects.create_user(username="otheruser", password="password123")
        self.client.force_authenticate(user=other_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data,[])
    
    def test_get_failed_payments_unauthenticated(self):
        """Test if an unauthenticated user gets a 401 Unauthorized response."""
        self.client.logout()
        response = self.client.get(self.url)
        print(response.content)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_failed_payments_with_error(self):
        """Test handling internal errors (e.g., database errors)."""
        with self.assertRaises(Exception):
            with self.client.force_authenticate(user=self.user):
                self.client.get(self.url)

class RefundPaymentViewTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.customer = User.objects.create_user(username="customer", password="password123")
        self.expert = User.objects.create_user(username="expert", password="password123", is_expert=True, 
                                               allow_cancellation_fee=True)
        self.client.force_authenticate(user=self.customer)

        self.payment = Payment.objects.create(
            customer=self.customer,
            expert=self.expert,
            stripe_payment_intent_id="pi_123",
            amount=100.00,
            status="authorized",
        )
        self.url = reverse("refund_payment")
    
    def test_missing_payment_intent_id(self):
        """Test refund request with mising payment_intent_id."""
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("payment_intent_id", response.data)
        self.assertEqual(response.data["payment_intent_id"], ["This field is required."])

    def test_payment_not_found(self):
        """Test refund request when payment does not exist."""
        response = self.client.post(self.url, {"payment_intent_id":"nonexistent_id"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("Payment not found.", response.json()["detail"])

    def test_payment_already_refunded(self):
        """Test refund request when payment has already been refunded."""
        self.payment.status = "refunded"
        self.payment.save()
        response = self.client.post(self.url, {"payment_intent_id": self.payment.stripe_payment_intent_id})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Payment has already been refunded.", str(response.data["payment_intent_id"]))

    @patch("stripe.Refund.create")
    def test_invalid_refund_amount(self, mock_refund_create):
        """Test refund request with invalid refund amount."""
        mock_refund_create.return_value = {"id": "refund_123", "status":"failed"}
        response = self.client.post(self.url, {
            "payment_intent_id":self.payment.stripe_payment_intent_id,
            "refund_amount":-10.00,
        })
        print(response.content)
        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Refund amount must be greater than 0.", response.json()["non_field_errors"])
        mock_refund_create.assert_not_called()

    @patch("stripe.Refund.create")
    def test_successful_full_refund(self, mock_refund_create):
        """Test a successful full refund."""
        mock_refund_create.return_value = {"id": "refund_123", "status":"captured"}
        response = self.client.post(self.url, {"payment_intent_id": self.payment.stripe_payment_intent_id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Refund processed successfully.", response.json()["message"])
        self.assertEqual(response.json()["refund_id"], "refund_123")

    @patch("stripe.Refund.create")
    def test_successful_partial_refund(self, mock_refund_create):
        """Test a successful partial refund."""
        mock_refund_create.return_value = {"id": "refund_123", "status": "succeeded"}
        response = self.client.post(self.url, {"payment_intent_id": self.payment.stripe_payment_intent_id, "refund_amount": 50.0})
        self.payment.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Refund processed successfully.", response.json()["message"])
        self.assertEqual(response.json()["refund_id"], "refund_123")
        self.assertEqual(self.payment.status, "partially_refunded")


class ReleasePaymentViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.customer = User.objects.create_user(username="customer", password="password123")
        self.expert = User.objects.create_user(username="expert", password="password123", is_expert=True, 
                                               allow_cancellation_fee=False)
        self.client.force_authenticate(user=self.customer)

        self.payment = Payment.objects.create(
            customer=self.customer,
            expert=self.expert,
            stripe_payment_intent_id="pi_123",
            amount=100.00,
            status="authorized",
        )
        self.valid_payload = {"payment_intent_id" : "pi_123"}
        self.invalid_payload = {"payment_intent_id" : "invalid_id"}
        self.missing = {}
        self.url = reverse("release_payment")

    @patch("stripe.PaymentIntent.cancel")
    def test_successful_payment_release(self, mock_stripe_cancel):
        """Test successful cancellation of a held PaymentIntent."""
        mock_stripe_cancel.return_value = {"status":"canceled"}
        response = self.client.post(self.url, self.valid_payload)
        self.payment.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.payment.status, "canceled")
        self.assertEqual(response.data["message"], "Payment released, no charge applied.")

    def test_missing_payment_intent_id(self):
        """Test error when payment_intent_id is missing."""
        response = self.client.post(self.url, self.invalid_payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("payment_intent_id", response.data) 
        self.assertEqual(response.data["payment_intent_id"][0].code, "invalid")  

    def test_invalid_payment_intent_id(self):
        """Test error when payment_intent_id does not exist."""
        response = self.client.post(self.url, self.invalid_payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error_detail = response.data["payment_intent_id"][0]
        self.assertEqual(str(error_detail), "Payment not found.")

    @patch("stripe.PaymentIntent.cancel", side_effect=Exception("Stripe API error"))
    def test_stripe_api_failure(self, mock_stripe_cancel):
        """Test Stripe API error handling."""
        response = self.client.post(self.url, self.valid_payload)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("error", response.data)
    

class StripeWebhookViewTest(APITestCase):
    def setUp(self):
        self.customer = User.objects.create_user(username="customer", password="password123")
        self.expert = User.objects.create_user(username="expert", password="password123", is_expert=True, 
                                               allow_cancellation_fee=False)
        self.client.force_authenticate(user=self.customer)
        self.payment_intent_id = 'pi_123'
        self.payment = Payment.objects.create(
            customer=self.customer,
            expert=self.expert,
            stripe_payment_intent_id=self.payment_intent_id,
            amount=100.00,
            status="authorized",
        )
        self.url = reverse("stripe_webhook")

    @patch('stripe.Webhook.construct_event')
    @patch("payments.tasks.handle_stripe_event.delay")
    def test_handle_payment_intent_succeeded_event(self, mock_stripe_event, mock_construct_event, mock_handle_stripe_event):
        """
        Test that when a 'payment_intent.succeeded' event is received, the payment 
        status is updated to 'captured'.
        """
        mock_stripe_event.return_value = {
            'type':'payment_intent.succeeded',
            'data': {
                'object': {
                    'id': self.payment_intent_id,
                    'amount_received': 100,
                    'status': 'succeeded',
                }
            }
        }
        mock_construct_event.return_value = mock_stripe_event
        response = self.client.post(self.url, 
                                json.dumps(mock_stripe_event),
                                content_type='application/json', 
                                HTTP_STRIPE_SIGNATURE="test_signature")
        print(response.content)
        print(response.json())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_handle_stripe_event.assert_called_with(mock_stripe_event)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, 'captured')