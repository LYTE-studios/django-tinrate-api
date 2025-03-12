import stripe
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from payments.models.payments_models import Payment
from payments.serializers.payments_refund_serializers import RefundPaymentSerializer
from users.models.user_models import User
from rest_framework import status


class RefundPaymentView(APIView):
    """
    View for processing full and partial refunds.

    This view handles both full and partial refunds for payments made via Stripe.
    It accepts a `payment_intent_id` (required) and a `refund_amount` (optional).
    If no `refund_amount` is provided, a full refund will be processed.
    If a `refund_amount` is provided, a partial refund will be processed.

    Methods:
        post(self, request, *args, **kwargs):
            Handles POST requests to process full or partial refunds.
    """
    def post(self, request, *args, **kwargs):
        """
        Handles POST requests to process full or partial refunds.

        This method:
            - Accepts a `payment_intent_id` (required) and an optional `refund_amount`.
            - Processes a full refund if no `refund_amount` is specified.
            - Processes a partial refund if a `refund_amount` is provided.
            - Updates the payment status to "refunded" in the database after the refund is processed.
            - Returns a success message along with the refund ID if successful.

        Args:
            request (Request): The HTTP request object containing the `payment_intent_id` and optional `refund_amount`.

        Returns:
            Response: A response containing a success message with the refund ID or an error message if the refund fails.
        """
        serializer = RefundPaymentSerializer(data=request.data)
        
        if serializer.is_valid():
            payment_intent_id = serializer.validated_data["payment_intent_id"]
            refund_amount = serializer.validated_data("refund_amount")

        #ensure payment_intent_id is provided
        if not payment_intent_id:
            return Response({"error": "Payment Intent ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        #retrieve the payment object from the database
        try:
            payment = Payment.objects.get(stripe_payment_intent_id = payment_intent_id)
        except Payment.DoesNotExist:
            return Response({"error": "Payment not found."}, status=status.HTTP_404_NOT_FOUND)
        
        #process refund 
        try:
            if refund_amount:
                #if refund_amount is provided, process a partial refund
                refund = stripe.Refund.create(
                    payment_intent=payment_intent_id,
                    amount=int(refund_amount * 100)
                )
                payment.status = "partially_refunded"
            else:
                #if not refund_amount is provided, process a full refund
                refund = stripe.Refund.create(payment_intent=payment_intent_id)
                payment.status = "refunded"

            payment.save()
            return Response({"message": "Refund processed successfully.", "refund_id": refund.id})
        
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
        