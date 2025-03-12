from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
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
            "client_secret": "secret_123"
        }

        data = {"amount": 50.00, "expert_id": self.expert.id, "customer_id":self.customer.id}
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



