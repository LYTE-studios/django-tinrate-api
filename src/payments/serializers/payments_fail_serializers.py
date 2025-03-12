from rest_framework import serializers
from payments.models.payments_models import Payment

class FailedPaymentSerializer(serializers.ModelSerializer):
    """
    Serializer for failed payments.

    Attributes:
        id (UUID): The unique ID of the failed payment.
        amount (Decimal): The amount of the failed transaction.
        status (str): The status of the payment (should be 'failed').
        created_at (datetime): The timestamp of when the payment attempt was made.
    """
    class Meta:
        model: Payment
        fields = ["id", "amount", "status", "created_at"]

    def validate_status(self, value):
        """
        Ensures that only failed payments are serialized.

        Args:
            value (str): The payment status.

        Returns:
            str: The validated status.

        Raises:
            serializers.ValidationError: If the status is not 'failed'.
        """
        if value != "failed":
            raise serializers.ValidationError("Only failed payments can be retrieved.")
        return value