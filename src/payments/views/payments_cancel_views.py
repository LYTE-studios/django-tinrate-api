import stripe
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from payments.models.payments_models import Payment
from users.models.user_models import User
from rest_framework import status
from payments.serializers.payments_cancel_serializers import CancelPaymentSerializer


class ChargeCancellationFeeView(APIView):
    """
    View for applying a cancellation fee if applicable when an appointment is canceled.

    This view checks the cancellation policy of the expert, verifies the time frame,
    and applies the cancellation fee accordingly.

    Methods:
        post(request):
            - Handles POST requests to apply cancellation fees based on the expert's policy.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Handles the cancellation process and applies cancellation fee if applicable.

        Args:
            request (Request): The HTTP request object containing the `payment_intent_id`, 
                                `expert_id`, and cancellation details.

        Returns:
            Response: A response with success or failure message regarding the cancellation.
        """
        serializer = CancelPaymentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        payment_intent_id = serializer.validated_data['payment_intent_id']
        percentage = serializer.validated_data.get('percentage') 

        try:
            payment = Payment.objects.get(stripe_payment_intent_id=payment_intent_id)
        except Payment.DoesNotExist:
            return Response({"error": "Payment not found."}, status=status.HTTP_404_NOT_FOUND)
        
        
        #check if the expert has set a cancellation fee 
        expert = getattr(payment, "expert", None)
        if expert.is_expert and not expert.allow_cancellation_fee:
                return Response({"message": "Expert does not charge cancellation fee."}, status=status.HTTP_200_OK)
            
        if expert.allow_cancellation_fee and percentage is None:
            return Response({"error": "Cancellation percentage is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            percentage = float(percentage)
            if not (0 < percentage <= 100):
                return Response({"error": "Percentage must be between 1 and 100."}, status=status.HTTP_400_BAD_REQUEST)
        except (TypeError, ValueError):
            return Response({"error": "Invalid percentage value."}, status=status.HTTP_400_BAD_REQUEST)

        amount_to_charge = float(payment.amount) * (float(percentage) / 100)
        if amount_to_charge <= 0:
            return Response({"error": "No cancellation fee charged."}, status=status.HTTP_200_OK)

        try:
            stripe.PaymentIntent.capture(payment_intent_id, amount_to_charge=int(amount_to_charge * 100))
            payment.status = "partially_captured"
            payment.cancellation_fee = percentage
            payment.save()
            return Response({"message": f"Captured {percentage:.0f}% cancellation fee."})
        
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
        
            