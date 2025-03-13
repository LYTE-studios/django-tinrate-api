from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from django.urls import reverse
from payments.models.payments_models import Payment
from unittest.mock import patch
import stripe

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
        print(response.content)
        print(response.data)
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
