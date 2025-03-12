from rest_framework import serializers
from models.payments_models import Payment

class ReleasePaymentSerializer(serializers.Serializer):
    """
    Serializer to handle the release of a blocked payment (unauthorized).

    This serializer validates the data for releasing a payment, which essentially undoes the authorization process.

    Attributes:
        payment_intent_id (str): The Stripe PaymentIntent ID associated with the payment to be released.
    """
    payment_intent_id = serializers.CharField()

    def validate_payment_intent_id(self, value):
        """
        Validates if the provided PaymentIntent ID exists and is in an authorized or canceled state.

        Args:
            value (str): The Stripe PaymentIntent ID to validate.

        Returns:
            str: The validated PaymentIntent ID if it exists.

        Raises:
            ValidationError: If the payment with the given PaymentIntent ID does not exist, or is not in authorized or canceled state.
        """
        try:
            payment = Payment.objects.get(stripe_payment_intent_id=value)
        except Payment.DoesNotExist:
            raise serializers.ValidationError("Payment not found.")
        
        if payment.status == "released":
            raise serializers.ValidationError("Payment has already been released.")
        if payment.status not in ["authorized", "canceled"]:
            raise serializers.ValidationError("Payment cannot be released because it is in an invalid state.")
        return value