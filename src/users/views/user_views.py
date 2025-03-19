from django.http import HttpResponse, JsonResponse
from django.db import connection
from django.views import View
from rest_framework import status
from collections import namedtuple
from users.models.user_models import User

UserData = namedtuple('UserData', ['id', 'username', 'email'])

class UserView(View):
    def get(self, request):
        print("GET request received!")
        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
            table_exists = cursor.fetchone()
            print(f"Table exists: {table_exists is not None}")

        with connection.cursor() as cursor:
            cursor.execute("SELECT id, username, email FROM users")
            rows = cursor.fetchall()
            if not rows:
                return HttpResponse("No data found.")
            users = [UserData(*row) for row in rows]
            result_str = ""
            for user in users:
                result_str += f"ID: {user.id}, Username: {user.username}, Email: {user.email}"
            print(result_str)
            return HttpResponse(f"Results printed: {result_str}")
            
    def post(self, request):
        print("Post request received!")
        username = request.POST.get("username")
        email = request.POST.get("email")
        if username and email:
            user = User(username=username, email=email)
            user.save()
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO users (username, email) VALUES (%s, %s)", [username, email]
                )
                connection.commit()
            print(f"Inserted: {username}, {email}")
            return JsonResponse({"message": "User created!", "username":username, "email":email})
        return JsonResponse({"error": "Username and email are required"}, status=status.HTTP_400_BAD_REQUEST)