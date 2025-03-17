import stripe
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from payments.models.payments_models import Payment
from users.models.user_models import User
from rest_framework import status
from .payments_cancel_views import ChargeCancellationFeeView
from payments.serializers.payments_release_serializers import ReleasePaymentSerializer


class ReleasePaymentView(APIView):
    """
    API endpoint to release a held PaymentIntent if the expert cancels.

    Methods:
        post(request):
            - Cancels the PaymentIntent so the user is not charged.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Cancels a held PaymentIntent.

        Request:
            - payment_intent_id (str): The ID of the PaymentIntent.

        Returns:
            - JSON response confirming cancellation.
        """
        serializer = ReleasePaymentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        payment_intent_id = serializer.validated_data["payment_intent_id"]

        
        try:
            payment = Payment.objects.get(stripe_payment_intent_id=payment_intent_id)
        except Payment.DoesNotExist:
            return Response({"error": "Payment not found."}, status=status.HTTP_404_NOT_FOUND)

        expert = payment.expert

        if expert.allow_cancellation_fee:
            charge_cancel_view = ChargeCancellationFeeView.as_view()
            return charge_cancel_view(request._request)
        
        try:
            stripe.PaymentIntent.cancel(payment_intent_id)
            payment.status = "canceled"
            payment.save()
            return Response({"message": "Payment released, no charge applied."}, status=status.HTTP_200_OK)


        except stripe.error.CardError as e:
            return Response({"error": "Card error: " + str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except stripe.error.RateLimitError as e:
            return Response({"error": "Rate limit exceeded. Please try again later."}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        except stripe.error.InvalidRequestError as e:
            return Response({"error": "Invalid request: " + str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except stripe.error.AuthenticationError as e:
            return Response({"error": "Authentication error: " + str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        except stripe.error.StripeError as e:
            return Response({"error": "Stripe API error: " + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({"error": "An unexpected error occurred" + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
            
    
        