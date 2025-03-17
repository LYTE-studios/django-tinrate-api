from celery import shared_task
from django.conf import settings
from payments.models.payments_models import Payment
import stripe
import logging

logger = logging.getLogger(__name__)
logger.info(f"Database settings: {settings.DATABASES['default']}")

@shared_task
def handle_stripe_event(event):
    """
    Processes Stripe webhook events asynchronously.

    Args:
        event (dict): The Stripe event payload received from the webhook.
    """
    logger.info(f"Received event in Celery: {event}")
    event_type = event.get("type")
    logger.info(f"Event type: {event_type}")

    data = event.get("data", {}).get("object", {})

    if not event_type or not data:
        logger.error("Invalid event structure received from Stripe.")
        return "Invalid event structure."
    
    logger.info(f"Looking for payment with intent ID: {data.get('id')}")


    try:
        # Fetch the payment record based on the PaymentIntent ID
        payment = Payment.objects.get(stripe_payment_intent_id=data.get('id'))
    except Payment.DoesNotExist:
        return f"Payment with intent ID {data.get('id')} not found."
    
    logger.info(f"Processing event {event_type} for payment {payment.id}")
    
    #mapping Stripe events to model choices
    status_mapping = {
        "payment_intent.authorized":"authorized",
        "payment_intent.succeeded": "captured",
        "payment_intent.payment_failed": "failed",
        "payment_intent.canceled" : "canceled",
        "charge.refunded" : "refunded",
        "charge.partially_refunded" : "partially_refunded",
        "charge.captured" : "captured",
        "charge.partially_captured": "partially_captured",
    }

    new_status = status_mapping.get(event_type)
    if new_status:
        
        
        payment.status = new_status
        payment.save()
        logger.info(f"Updated payment {payment.id} status to {new_status}.")
        return f"Processed Stripe event {event_type} for payment {payment.id}."
    else:
        logger.warning(f"Unhandled Stripe event type: {event_type}.")
        return f"Unhandled Stripe event type: {event_type}."

   
