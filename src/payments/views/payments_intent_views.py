import stripe
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from payments.models.payments_models import Payment
from users.models.user_models import User
from rest_framework import status
from rest_framework.renderers import JSONRenderer
from django.db import connection
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
    renderer_classes = [JSONRenderer]

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
        
    
class PaymentHistoryView(APIView):
    """
    API endpoint to retrieve payment history for a specific user using raw SQL.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        Retrieves all payments for the authenticated user.

        Returns:
            - JSON response containing payment details.
        """
        user_id = request.user.id
        payments = self.get_payments_for_user(user_id)

        if not payments:
            return Response({"message": "No payments found for this user."}, status=status.HTTP_404_NOT_FOUND)
        
        formatted_payments = []
        for payment in payments:
            formatted_payments.append({
                'id': payment[0],
                'amount': payment[1],
                'status': payment[2],
                'created_at': payment[3].isoformat() if payment[3] else None,
                'stripe_payment_intent_id': payment[4],
                'payment_method_id': payment[5],
                'transaction_fee': payment[6],
                'cancellation_fee': payment[7],
                'expert_username': payment[8],
                'customer_username': payment[9],
            })
        return Response(formatted_payments, status=status.HTTP_200_OK)
    
    @staticmethod
    def get_payments_for_user(user_id):
        """
        Retrieves payments for a specific user using raw SQL.

        Args:
            user_id (int): The ID of the user to retrieve payments for.

        Returns:
            list: List of payments for the user.
        """
        with connection.cursor() as cursor:
            query = """
            SELECT p.id, p.amount, p.status, p.created_at, p.stripe_payment_intent_id, p.payment_method_id,
                p.transaction_fee, p.cancellation_fee, e.username AS expert_username, c.username AS customer_username
            FROM payments_payment p 
            JOIN users c ON p.customer_id = c.id
            JOIN users e ON p.expert_id = e.id
            WHERE p.customer_id = %s;
            """
            cursor.execute(query, [str(user_id)])
            results = cursor.fetchall()
        return results


class TransactionHistoryView(APIView):
    """
    API endpoint to retrieve or create financial transactions for a user using raw SQL.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        Retrieves all transactions for the authenticated user.

        Returns:
            - JSON response containing transaction details.
        """
        user_id = request.user.id
        print(f"Authenticated user ID: {user_id}")
        transactions = self.get_transactions_for_user(user_id)

        if not transactions:
            return Response({"message": "No transactions found for this user."}, status=status.HTTP_404_NOT_FOUND)
        
        formatted_transactions = []
        for transaction in transactions:
            formatted_transactions.append({
                'id': transaction[0],
                'amount': transaction[1],
                'status': transaction[2],
                'type': transaction[3],
                'created_at': transaction[4].isoformat() if transaction[4] else None,
                'payment_id': transaction[5],
                'user_id': transaction[6],
            })
        return Response(formatted_transactions, status=status.HTTP_200_OK)
    

    def post(self, request, *args, **kwargs):
        """
        Creates a new transaction for the authenticated user.

        Returns:
            - JSON response with the created transaction details.
        """
        user_id = request.user.id
        payment_id = request.data.get("payment_id")
        transaction_type = request.data.get("type")
        status_ = request.data.get("status")
        amount = request.data.get("amount")

        if not payment_id or not transaction_type or not status or not amount:
            return Response({"message": "Missing required fields."}, status=status.HTTP_400_BAD_REQUEST)
        
        transaction_id = self.create_transaction(user_id, payment_id, transaction_type, status_, amount)

        return Response({
            'id': transaction_id,
            'user_id_id': user_id,
            'payment_id': payment_id,
            'type': transaction_type,
            'status': status_,
            'amount': amount,
        }, status=status.HTTP_201_CREATED)
    
    @staticmethod
    def get_transactions_for_user(user_id):
        """
        Retrieves transactions for a specific user using raw SQL.

        Args:
            user_id (int): The ID of the user to retrieve transactions for.

        Returns:
            list: List of transactions for the user.
        """
        with connection.cursor() as cursor:
            query = """
            SELECT t.id, t.amount, t.status, t.type, t.created_at, t.payment_id, t.user_id_id AS user_id
            FROM payments_transaction t
            WHERE t.user_id_id = %s;
            """
            cursor.execute(query, [str(user_id)])
            results = cursor.fetchall()
        return results
    
    @staticmethod
    def create_transaction(user_id_id, payment_id, transaction_type, status_, amount):
        """
        Creates a new transaction using raw SQL.

        Args:
            user_id (int): The ID of the user initiating the transaction.
            payment_id (int): The associated payment ID.
            transaction_type (str): The type of transaction ('charge' or 'withdrawal').
            status (str): The status of the transaction ('completed', 'cancel', 'pending', etc.).
            amount (float): The amount of money for the transaction.

        Returns:
            str: The ID of the created transaction.
        """
        with connection.cursor() as cursor:
            query = """
            INSERT INTO payments_transaction (user_id_id, payment_id, type, status, amount, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, [user_id_id, payment_id, transaction_type, status_, amount])
            transaction_id = cursor.lastrowid
        return transaction_id
    

class BillingHistoryView(APIView):
    """
    API endpoint to retrieve or create financial billings for a user using raw SQL.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        Retrieves all billings for the authenticated user.

        Returns:
            - JSON response containing billing details.
        """
        user_id = request.user.id
        print(f"Authenticated user ID: {user_id}")
        billings = self.get_billing_for_user(user_id)

        if not billings:
            return Response({"message": "No billings found for this user."}, status=status.HTTP_404_NOT_FOUND)
        
        formatted_billings = []
        for billing in billings:
            formatted_billings.append({
                'id': billing[0],
                'total_earnings': billing[1],
                'balance': billing[2],
                'total_hours': billing[3],
                'date': billing[4].isoformat() if billing[4] else None,
                'transaction_status': billing[5],
                'user_id': billing[6],
            })
        return Response(formatted_billings, status=status.HTTP_200_OK)
    

    def post(self, request, *args, **kwargs):
        """
        Creates a new billing for the authenticated user.

        Returns:
            - JSON response with the created billing details.
        """
        user_id = request.user.id
        total_earnings = request.data.get("total_earnings")
        balance = request.data.get("balance")
        amount = request.data.get("amount")
        total_hours = request.data.get("total_hours")
        date = request.data.get("date")
        transaction_status = request.data.get("transaction_status")

        if not total_earnings or not balance or not amount or not total_hours or not date:
            return Response({"message": "Missing required fields."}, status=status.HTTP_400_BAD_REQUEST)
        
        billing_id = self.create_billing(user_id, total_earnings, balance, amount, total_hours, date, transaction_status)

        return Response({
            'id': billing_id,
            'user_id_id': user_id,
            'total_earnings': total_earnings,
            'balance': balance,
            'amount': amount,
            'total_hours': total_hours,
            'date': date,
            'transaction_status': transaction_status,
        }, status=status.HTTP_201_CREATED)
    
    @staticmethod
    def get_billing_for_user(user_id):
        """
        Retrieves billings for a specific user using raw SQL.

        Args:
            user_id (int): The ID of the user to retrieve billings for.

        Returns:
            list: List of billings for the user.
        """
        with connection.cursor() as cursor:
            query = """
            SELECT b.id, b.total_earnings, b.balance, b.total_hours, b.date, b.transaction_status_id AS transaction_status, b.user_id_id AS user_id
            FROM payments_billing b
            WHERE b.user_id_id = %s;
            """
            cursor.execute(query, [str(user_id)])
            results = cursor.fetchall()
        return results
    
    @staticmethod
    def create_billing(user_id, total_earnings, balance, amount, total_hours, date, transaction_status):
        """
        Creates a new transaction using raw SQL.

        Args:
            user_id (UUID): The ID of the user associated with the billing.
            total_earnings (Decimal): The total earnings for the user.
            balance (Decimal): The current balance of the user.
            amount (Decimal): The amount to be paid out or owed.
            total_hours (Decimal): Total hours worked, if applicable.
            date (datetime): The date when the billing entry is created.
            transaction_status (UUID): The ID of the related transaction status.

        Returns:
            str: The ID of the created billing.
        """
        with connection.cursor() as cursor:
            query = """
            INSERT INTO payments_billing (user_id_id, total_earnings, balance, amount, total_hours, date, transaction_status_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, [user_id, total_earnings, balance, amount, total_hours, date, transaction_status])
            billing_id = cursor.lastrowid
        return billing_id
    