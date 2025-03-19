from rest_framework_simplejwt.tokens import RefreshToken

class TokenService:
    @staticmethod
    def generate_jwt_token(user):
        """Generate access and refresh tokens for user"""
        refresh = RefreshToken.for_user(user)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }

