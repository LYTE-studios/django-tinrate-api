import stripe
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from payments.models.payments_models import Payment
from users.models.user_models import User
from rest_framework import status
from payments.serializers.payments_intent_serializers import PaymentSerializer

stripe.api_key = settings.STRIPE_SECRET_KEY

class CreatePaymentIntentView(APIView):
    """
    API endpoint to create a Stripe PaymentIntent (Authorization Only).

    Methods:
        post(request):
            - Creates a PaymentIntent with manual capture.
            - Holds the amount until confirmation.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """
        Handles the creation of a PaymentIntent.

        Request:
            - amount (float): The amount to be authorized.
            - expert_id (int): The ID of the expert being booked.

        Returns:
            - JSON response containing PaymentIntent details.
        """
        serializer = PaymentSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Extract validated data
        payment = serializer.save()
        amount = serializer.validated_data["amount"]
        expert_id = serializer.validated_data["expert_id"]

        if not amount or not expert_id:
            return Response({"error": "Amount and expert_id are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            expert = User.objects.get(id=expert_id)
        except User.DoesNotExist:
            return Response({"error": "Expert not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            # Create a PaymentIntent (Authorization only)
            intent = stripe.PaymentIntent.create(
                amount=int(float(amount) * 100),
                currency="eur",
                payment_method_types=["card"],
                capture_method="manual",  # Holds the payment, do not capture yet
                metadata={"expert_id": expert_id}
            )
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
            return Response({"error": "An unexpected error occurred: " + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            # Store the payment in the database
            intent_id = intent.get("id") if isinstance(intent, dict) else intent.id
            client_secret = intent.get("client_secret") if isinstance(intent, dict) else intent.client_secret

            Payment.objects.create(
                customer=request.user,
                expert=expert,
                stripe_payment_intent_id=intent_id,
                amount=amount,
                status="authorized"
            )

            # Return the PaymentIntent details
            return Response({"payment_intent": intent_id, "client_secret": client_secret}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": "Error saving payment information: " + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
