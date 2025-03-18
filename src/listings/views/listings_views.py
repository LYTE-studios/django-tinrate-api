from django.http import JsonResponse, HttpResponse
from django.views import View
from rest_framework import status
from django.db import connection
import json

class ListingView(View):
    def get(self, request):
        user_id = request.GET.get('user_id')
        if not user_id:
            return JsonResponse({"error": "user_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT listings.id, listings.title, listings.description, listings.amount, listings.availability,
                    listings.created_at, role.name AS role_name, company.name AS company_name, experience.name AS experience_name
                FROM listings
                JOIN role ON listings.role_id = role.id
                LEFT JOIN company ON listings.company_id = company.id
                JOIN experience ON listings.experience_id = experience.id
                WHERE listings.user_id = %s
            """, [user_id])
            rows = cursor.fetchall()

            if not rows:
                return JsonResponse({"message": "No listings found for this user."}, status=status.HTTP_404_NOT_FOUND)
            
            listings = []
            for row in rows:
                listing = {
                    'id': row[0],
                    'title': row[1],
                    'description': row[2],
                    'amount': str(row[3]),
                    'availability': row[4].strftime('%Y-%m-%d %H:%M:%S'),
                    'created_at': row[5].strftime('%Y-%m-%d %H:%M:%S'),
                    'role': row[6],
                    'company': row[7] if row[7] else None,
                    'experience': row[8],
                }
                listings.append(listing)
            return JsonResponse({"listings": listings})