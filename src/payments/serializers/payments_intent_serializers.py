from rest_framework import serializers
from payments.models.payments_models import Payment
from django.contrib.auth import get_user_model


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
    expert_id = serializers.IntegerField()  
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)  
    class Meta:
        model = Payment
        fields = ['id','expert_id', 'amount', 'status', 'cancellation_fee']
        
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
    
    def create(self, validated_data):

        user = self.context['request'].user

        try:
            expert = get_user_model().objects.get(id=validated_data['expert_id'])
        except get_user_model().DoesNotExist:
            raise serializers.ValidationError("Expert not found.")
        
        payment = Payment.objects.create(
            customer=user,
            expert=expert,
            stripe_payment_intent_id='',
            amount=validated_data['amount'],
            status='authorized',
        )
        return payment