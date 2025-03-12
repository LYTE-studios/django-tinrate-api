from rest_framework import serializers
from models.payments_models import Payment

class CancelPaymentSerializer(serializers.Serializer):
    """
    Serializer to handle the cancellation of a payment.

    This serializer validates the data for canceling a payment.
    It ensures that the provided PaymentIntent ID exists and handles the cancellation process.

    Attributes:
        payment_intent_id (str): The Stripe PaymentIntent ID associated with the payment to be canceled.
    """
    payment_intent_id = serializers.CharField()

    def validate_payment_intent_id(self, value):
        """
        Validates the provided PaymentIntent ID to ensure it exists in the system and is eligible for cancellation.

        Args:
            value (str): The Stripe PaymentIntent ID to validate.

        Returns:
            str: The validated PaymentIntent ID if it exists and can be canceled.

        Raises:
            ValidationError: If the payment with the given PaymentIntent ID does not exist, is already canceled,
                             refunded, or not eligible for cancellation (i.e., not in 'authorized' or 'partially_captured' status).
        """
        try:
            payment = Payment.objects.get(stripe_payment_intent_id=value)
        except Payment.DoesNotExist:
            raise serializers.ValidationError("Payment not found.")
        
        if payment.status == "canceled":
            raise serializers.ValidationError("Payment has already been canceled.")
        if payment.status == "refunded":
            raise serializers.ValidationError("Refunded payments cannot be canceled.")
        if payment.status not in ["authorized", "partially_captured"]:
            raise serializers.ValidationError("Only authorized or partially captured payments can be canceled.")
        
        return value