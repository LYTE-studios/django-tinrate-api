from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from authentication.serializers.auth_serializers import RegisterSerializer
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
    

