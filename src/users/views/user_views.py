from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from users.models.user_models import User
from users.serializers.user_serializer import UserSerializer

class UserView(APIView):
    """
    API view for retrieving, updating, and deleting the basic user information.

    Methods:
        get: Retrieves the basic user info.
        put: Updates the user's basic info.
        delete: Deletes the user's account.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Retrieves the basic information of the currently authenticated user.
        """
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data)
    
    def put(self, request):
        """
        Updates the basic user information.
        """
        user = request.user
        serializer = UserSerializer(user, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.validate_name_fields(request.data)
            serializer.update_user(user, serializer.validated_data)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request):
        """
        Deletes the currently authenticated user's account.
        """
        user = request.user
        serializer = UserSerializer()
        response = serializer.delete_user(user)
        return Response(response, status=status.HTTP_204_NO_CONTENT)