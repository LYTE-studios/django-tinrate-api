from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from authentication.serializers.auth_serializers import RegisterSerializer, LoginSerializer
from authentication.services.tokens_services import TokenService

class RegisterView(APIView):
    """
    View for registering a new user and generating authentication tokens.

    This view handles the user registration process by accepting the user data,
    validating it using the provided serializer, saving the user, and generating 
    JWT authentication tokens for the newly created user.

    Attributes:
        serializer_class (): The serializer used to validate and save the user data.

    Methods:
        post(self, request, *args, **kwargs): Handles POST requests to register a new user and return authentication tokens.

    Responses:
        201 Created: The user's account is successfully created, and authentication tokens are returned in the response.

    """
    serializer_class = RegisterSerializer
    
    def post(self, request, *args, **kwargs):
        """
        Handles POST requests to register a new user and generate JWT tokens.

        This method:
            - Validates the input data using the `RegisterSerializer`.
            - Saves the user data and creates the new user.
            - Generates authentication tokens (access and refresh tokens) for the user using the `generate_jwt_token` from `TokenService`.
            - Returns the access and refresh tokens in the response.

        Args:
            self (RegisterView): The instance of the UserRegistrationView class.
            request (Request): The HTTP request object containing user data to be registered.

        Returns:
            Response: A response containing the access and refresh tokens for the newly created user.
        """
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token = TokenService.generate_jwt_token(user)
            return Response( {"access": token["access"], "refresh": token["refresh"]},
            status=status.HTTP_201_CREATED,)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class LoginView(APIView):
    """
    View for user login and JWT token generation.

    This view handles user authentication by accepting a username and password,
    validating them using the `LoginSerializer`, and generating JWT authentication
    tokens (access & refresh) upon successful login.

    Methods:
        post(self, request, *args, **kwargs):
            Handles POST requests for user login and returns authentication tokens.
    """
    def post(self, request, *args, **kwargs):
        """
        Handles POST requests for user login.

        This method:
            - Validates the input credentials using `LoginSerializer`.
            - If valid, generates authentication tokens.
            - Returns the tokens in the response.

        Args:
            request (Request): The HTTP request object containing login credentials.

        Returns:
            Response: A response containing access and refresh tokens if successful,
                      or an error message if authentication fails.
        """
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]
 
            token = TokenService.generate_jwt_token(user)

            return Response(
                {
                    "user": user.id,
                    "message": "Login successful!",
                    "access": token["access"],  # Access token
                    "refresh": token["refresh"],  # Refresh token
                },
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)