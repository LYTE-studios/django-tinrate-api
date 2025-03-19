import uuid
from django.http import JsonResponse, HttpResponse
from django.views import View
from django.utils.timezone import now
from rest_framework import status
from django.db import connection
import json
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

@method_decorator(csrf_exempt, name="dispatch")
class ListingView(View):
    def get(self, request):
        user_id = request.GET.get('user_id')
        if not user_id:
            return JsonResponse({"error": "user_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT listings.id, listings.title, listings.description, listings.amount, listings.availability,
                    listings.created_at, user_role.name AS role_name, user_company.name AS company_name, user_experience.name AS experience_name
                FROM listings
                JOIN user_role ON listings.role_id = user_role.id
                LEFT JOIN user_company ON listings.company_id = user_company.id
                JOIN user_experience ON listings.experience_id = user_experience.id
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
                    'user_role': row[6],
                    'user_company': row[7] if row[7] else None,
                    'user_experience': row[8],
                }
                listings.append(listing)
            return JsonResponse({"listings": listings})
        
    def post(self, request):
        try:
            data = json.loads(request.body)

            required_fields = ['user_id', 'role_id', 'title', 'amount', 'experience_id']
            for field in required_fields:
                if field not in data or not data[field]:
                    return JsonResponse({"error": f"{field} is required"}, status=status.HTTP_400_BAD_REQUEST)
                
            listing_id = str(uuid.uuid4())
            availability = data.get('availability', now().strftime('%Y-%m-%d %H:%M:%S'))
            company_id = data.get('company_id')
            description = data.get('description', '')

            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO listings (id, user_id, role_id, company_id, title, description, amount, experience_id,
                            availability, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, [listing_id, data['user_id'], data['role_id'], company_id, data['title'], description,
                      data['amount'], data['experience_id'], availability, now()])
                
            return JsonResponse({"message": 'Listing created successfully', "listing_id": listing_id}, status=status.HTTP_201_CREATED)
        
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)