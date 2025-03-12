from rest_framework import serializers
from models.payments_models import Payment

class RefundPaymentSerializer(serializers.Serializer):
    """
    Serializer to handle the refund process for a payment.

    This serializer validates the data for processing a full or partial refund.
    It checks if the provided refund amount is valid, ensures the `payment_intent_id` exists,
    and ensures the refund amount does not exceed the total payment amount.

    Attributes:
        payment_intent_id (str): The Stripe PaymentIntent ID to refund.
        amount (Decimal): The amount to refund, which can be partial or full.
    """
    payment_intent_id = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)

    def validate(self, data):
        """
        Custom validation to ensure the refund amount is valid.
        
        Args:
            data (dict): The data being validated before initiating the refund.

        Returns:
            dict: The validated data or raises a validation error.

        Raises:
            ValidationError: If the refund amount is less than or equal to zero.
        """
        if data["amount"] <= 0:
            raise serializers.ValidationError("Refund amount must be greater than 0.")
        return data
    
    def validate_payment_intent_id(self, value):
        """
        Validates if the provided payment intent ID exists in the system.

        This method checks the database to ensure the provided `payment_intent_id` corresponds to an existing payment.

        Args:
            value (str): The Stripe PaymentIntent ID to validate.

        Returns:
            str: The validated PaymentIntent ID if it exists.

        Raises:
            ValidationError: If the payment with the given PaymentIntent ID does not exist.
        """
        try:
            payment = Payment.objects.get(stripe_payment_intent_id=value)
        except Payment.DoesNotExist:
            raise serializers.ValidationError("Payment not found.")
        
        
        if payment.status == "refunded":
            raise serializers.ValidationError("Payment has already been refunded.")
        if payment.status not in ["authorized", "captured"]:
            raise serializers.ValidationError("Only authorized and captured payments can be refunded.")
        return value

    def validate_refund_amount(self, value):
        """
        Validates the refund amount against the total payment amount.

        This method ensures the refund amount does not exceed the total payment amount 
        stored in the database.

        Args:
            value (Decimal): The refund amount.

        Returns:
            Decimal: The validated refund amount if it is valid.

        Raises:
            ValidationError: If the refund amount is greater than the total payment amount.
        """
        payment_intent_id = self.initial_data.get("payment_intent_id")
        payment = Payment.objects.get(stripe_payment_intent_id=payment_intent_id)
        
        if value and value > payment.amount:
            raise serializers.ValidationError("Refund amount cannot exceed the total payment amount.")
        return value
