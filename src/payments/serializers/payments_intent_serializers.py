from rest_framework import serializers
from models.payments_models import Payment

class PaymentSerializer(serializers.ModelSerializer):
    """
    Serializer for Payment model to handle creation, validation, and response formatting.

    Attributes:
        customer (User): The customer making the payment.
        expert (User): The expert receiving the payment.
        stripe_payment_intent_id (str): The unique Stripe PaymentIntent ID.
        payment_method_id (str): The Stripe PaymentMethod ID (card details).
        amount (Decimal): The total amount of the payment.
        status (str): The current payment status (authorized, captured, canceled, refunded).
        cancellation_fee (Decimal): The fee applied if the customer cancels late.
        created_at (datetime): Timestamp when the payment was created.
    """
    class Meta:
        model = Payment
        fields = ['customer', 'expert', 'stripe_payment_intent_id', 'payment_method_id',
                   'amount', 'status', 'cancellation_fee', 'created_at']
        
    def validate(self, data):
        """
        Custom validation logic for the payment.

        Args:
            data (dict): The data being validated before creating the payment.

        Returns:
            dict: The validated data or raises a validation error.
        """
        if data["amount"] <= 0:
            raise serializers.ValidationError("Amount must be greater than 0.")
        return data