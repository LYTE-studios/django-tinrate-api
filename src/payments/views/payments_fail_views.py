from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.exceptions import ObjectDoesNotExist
from payments.models.payments_models import Payment
from payments.serializers.payments_fail_serializers import FailedPaymentSerializer

class FailPaymentsView(generics.ListAPIView):
    """
    API View to retrieve a list of failed payments.

    Permissions:
        - Requires authentication.

    Returns:
        - List of failed payments for the authenticated user.
    """
    serializer_class = FailedPaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Retrieves the failed payments for the logged-in user.

        Returns:
            QuerySet: List of failed payments.
        """
        return Payment.objects.filter(customer=self.request.user, status="failed")
    
    def list(self, request, *args, **kwargs):
        """
        Overrides the default list method to handle errors.

        Returns:
            Response: JSON response containing failed payments or an error message.
        """
        try:
            queryset = self.get_queryset()
            if not queryset.exists():
                return Response({"message":"No failed payments found."}, status=status.HTTP_200_OK)

            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Payment.DoesNotExist:
            return Response({"error": "No failed payments exist for this user."}, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            return Response({"error": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            