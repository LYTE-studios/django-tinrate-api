import uuid
from django.http import HttpResponse, JsonResponse
from django.db import connection
from django.views import View
from rest_framework import status
from collections import namedtuple
from users.models.user_models import User
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json

@method_decorator(csrf_exempt, name="dispatch")
class SettingsView(View):
    def get(self, request):
        user_id = request.GET.get('user_id')
        print(f"Received user_id: {user_id}")
        if not user_id:
            return JsonResponse({"error": "user_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, profile, account_security, notification_pref, payment_settings, support_help
                FROM user_settings
                WHERE user_id = %s
            """, [user_id])
            row = cursor.fetchone()

            if not row:
                return JsonResponse({"message": "No settings found for this user."}, status=status.HTTP_404_NOT_FOUND)
            
            settings = {
                'id': row[0],
                'profile': json.loads(row[1]) if row[1] else None,
                'account_security': json.loads(row[2]) if row[2] else None,
                'notification_pref': json.loads(row[3]) if row[3] else None,
                'payment_settings': json.loads(row[4]) if row[4] else None,
                'support_help': json.loads(row[5]) if row[5] else None,
            }
            return JsonResponse({"settings": settings})
        
    def post(self, request):
        user_id = request.POST.get("user_id")
        profile = request.POST.get("profile")
        account_security = request.POST.get("account_security")
        notification_pref = request.POST.get("notification_pref")
        payment_settings = request.POST.get("payment_settings")
        support_help = request.POST.get("support_help")

        if not user_id:
            return JsonResponse({"error": "user_id is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO user_settings (id, user_id, profile, account_security, notification_pref, payment_settings, support_help)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, [uuid.uuid4(), user_id, profile, account_security, notification_pref, payment_settings, support_help])
            return JsonResponse({"message": "Settings created"})
            