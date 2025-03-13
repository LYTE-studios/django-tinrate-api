import stripe
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from payments.models.payments_models import Payment
from users.models.user_models import User
from rest_framework import status
from payments.serializers.payments_capture_serializers import CapturePaymentSerializer


stripe.api_key = settings.STRIPE_SECRET_KEY

class CapturePaymentView(APIView):
    """
    API endpoint to capture (finalize) a held PaymentIntent.

    Methods:
        post(request):
            - Captures the full payment after the appointment.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Captures a Stripe PaymentIntent.

        Request:
            - payment_intent_id (str): The ID of the PaymentIntent.

        Returns:
            - JSON response confirming capture or error message.
        """
        serializer = CapturePaymentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        payment_intent_id = serializer.validated_data['payment_intent_id']

        if not payment_intent_id:
            return Response({"error": "Payment Intent ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            stripe.PaymentIntent.capture(payment_intent_id)
            payment = Payment.objects.get(stripe_payment_intent_id = payment_intent_id)
            payment.status = "captured"
            payment.save()
            return Response({"message":"Payment captured successfuly."})
        except stripe.error.CardError as e:
            return Response({"error": "Card error:" + str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except stripe.error.RateLimitError as e:
            return Response({"error": "Rate limit exceeded. Please try again later."}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        except stripe.error.InvalidRequestError as e:
            return Response({"error": "Invalid request:" + str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except stripe.error.AuthenticationError as e:
            return Response({"error": "Authentication error:" + str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        except stripe.error.StripeError as e:
            return Response({"error": "Stripe API error:" + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({"error": "An unexpected error occured" + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
       