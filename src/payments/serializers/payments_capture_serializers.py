from rest_framework import serializers
from models.payments_models import Payment

class CapturePaymentSerializer(serializers.Serializer):
    """
    Serializer to handle capturing a payment once it is authorized.

    Attributes:
        payment_intent_id (str): The Stripe PaymentIntent ID to capture.
    """
    payment_intent_id = serializers.CharField()

    def validate_payment_intent_id(self, value):
        """
        Custom validation to check if the provided PaymentIntent ID exists in the database
        and if the payment can be captured.

        Args:
            value (str): The PaymentIntent ID to validate.

        Returns:
            str: The validated PaymentIntent ID if it exists and is eligible for capture.

        Raises:
            ValidationError: If the PaymentIntent ID does not exist, has already been captured,
                             is refunded, or is not in an authorized state.
        """
        try:
            payment = Payment.objects.get(stripe_payment_intent_id = value)
        except Payment.DoesNotExist:
            raise serializers.ValidationError("Payment with this PaymentIntent ID does not exist.")
        
        if payment.status == "captured":
            raise serializers.ValidationError("Payment has already been captured.")
        if payment.status == "refunded":
            raise serializers.ValidationError("Refunded payments cannot be captured.")
        if payment.status != "authorized":
            raise serializers.ValidationError("Payment is not in authorized state.")
        return value