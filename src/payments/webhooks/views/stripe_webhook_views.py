import stripe
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework import status
from django.conf import settings
import stripe.webhook
from payments.models.payments_models import Payment
from payments.celery.tasks import handle_stripe_event

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY

class StripeWebhookView(APIView):
    """
    Handles Stripe webhook events.

    This view listens for events from Stripe and processes payment status updates.
    It ensures that payments are updated in the system accordingly.
    """
    @csrf_exempt
    def post(self, request, *args, **kwargs):
        """
        Handles incoming Stripe webhook events.

        Args:
            request (HttpRequest): The incoming request from Stripe.

        Returns:
            JsonResponse: A response indicating success or failure.
        """
        payload = request.body
        sig_header = request.headers.get("Stripe-Signature")

        try:
            #verify Stripe signature
            event = stripe.webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError as e:
            logger.error("Invalid payload received from Stripe: {e}")
            return JsonResponse({"error": "Invalid payload"}, status=status.HTTP_400_BAD_REQUEST)
        except stripe.error.SignatureVerificationError as e:
            logger.error("Stripe webhook signature verification failed: {e}")
            return JsonResponse({"error": "Invalid signature"}, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"Recevied Stripe webhook: {event['type']}")
        
        handle_stripe_event.delay(event)

        return JsonResponse({"message": "Webhook received"}, status=status.HTTP_200_OK)
