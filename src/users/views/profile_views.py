from django.http import HttpResponse, JsonResponse
from django.db import connection
from django.views import View
from rest_framework import status
from collections import namedtuple
from users.models.user_models import User
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

ProfileUserData = namedtuple('ProfileUserData', ['id', 'role', 'company', 'total_meetings', 'rating'])

@method_decorator(csrf_exempt, name="dispatch")
class UserProfileView(View):
    def get(self, request):
        print("GET request received!")
        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_profile';")
            table_exists = cursor.fetchone()
            print(f"Table exists: {table_exists is not None}")

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    up.id,
                    r.name AS role,
                    c.name AS company,
                    up.total_meetings,
                    up.rating
                FROM
                    user_profile up
                LEFT JOIN user_role r ON up.role_id = r.id
                LEFT JOIN user_company c ON up.company_id = c.id
            """)
            rows = cursor.fetchall()
            print(f"Rows fetched: {rows}")
        if not rows:
            return HttpResponse("No data found.")
        users = [ProfileUserData(*row) for row in rows]
        result_str = ""
        for user in users:
            result_str += f"ID: {user.id}, Role: {user.role}, Company: {user.company}, Total Meetings: {user.total_meetings}, Rating: {user.rating}"
        print(result_str)
        return HttpResponse(f"Results printed: {result_str}")
            
    @csrf_exempt      
    def post(self, request):
        print("POST request received!")
        user_id = request.POST.get('id')
        role_name = request.POST.get('role')
        company_name = request.POST.get('company')
        total_meetings = request.POST.get('total_meetings')
        rating = request.POST.get('rating')

        if user_id and role_name and company_name and total_meetings and rating:

            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM user_profile")
                count = cursor.fetchone()[0]
                print(f"Records in user_profile: {count}")

            with connection.cursor() as cursor:
                cursor.execute("SELECT id FROM user_role WHERE name= %s", [role_name])
                role_id = cursor.fetchone()
                print(f"Role id: {role_id}")

            with connection.cursor() as cursor:
                cursor.execute("SELECT id FROM user_company WHERE name= %s", [company_name])
                company_id = cursor.fetchone()

            if role_id and company_id:
                role_id= role_id[0]
                company_id= company_id[0]

                cursor.execute("""
                    INSERT INTO user_profile(user_id_id, role_id, company_id, total_meetings, rating)
                    VALUES (%s, %s, %s, %s, %s)
                    """, [user_id, role_id, company_id, total_meetings, rating])

                connection.commit()
         
            
            print(f"Inserted: ID={user_id}, Role={role_name}, Company={company_name}, Total meetings={total_meetings}, Rating={rating}")
            return JsonResponse({
                "message": "User profile created",
                "user_id": user_id,
                "role": role_name,
                "company": company_name,
                "total_meetings": total_meetings,
                "rating":rating
            })
        return JsonResponse({"error": "All fields are required"}, status=status.HTTP_400_BAD_REQUEST)

           
@method_decorator(csrf_exempt, name="dispatch")         
class ExperienceView(View):
    def get(self, request):
        print("GET request received!")

        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_experience';")
            table_exists = cursor.fetchone()
            print(f"Table exists: {table_exists is not None}")

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, name, weight
                FROM user_experience
            """)
            rows = cursor.fetchall()
            print(f"Rows fetched: {rows}")
        
        if not rows:
            return HttpResponse("No data found.")
        
        result_str = ""
        for row in rows:
            result_str += f"ID: {row[0]}, Name: {row[1]}, Weight: {row[2]}\n"
        
        return HttpResponse(f"Results printed: {result_str}")
    
    def post(self, request):
        print("POST request received!")

        name = request.POST.get('name')
        weight = request.POST.get('weight')

        with connection.cursor() as cursor:
            if name and weight:
                cursor.execute("""
                    INSERT INTO user_experience (name, weight)
                    VALUES (%s, %s)
                """)
                connection.commit()
            print(f"Inserted: Name: {name}, Weight: {weight}")
            return JsonResponse({
                "message": "Experience created",
                "name": name,
                "weight": weight,
            })
        return JsonResponse({"error": "All fields are required"}, status=status.HTTP_400_BAD_REQUEST)
            
@method_decorator(csrf_exempt, name="dispatch")  
class RoleView(View):
    def get(self, request):
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM user_role")
            rows = cursor.fetchall()
            if not rows:
                return JsonResponse({"message":"No roles found"}, status=status.HTTP_400_BAD_REQUEST)
            roles = [{'id': row[0], 'name': row[1]} for row in rows]
            return JsonResponse({'roles': roles})
        
    def post(self, request):
        role_name = request.POST.get('name')
        if role_name:
            with connection.cursor() as cursor:
                cursor.execute("INSERT INTO user_role (name) VALUES (%s)", [role_name])
                return JsonResponse({"message": "Role created", "role": role_name})
        return JsonResponse({"error": "Role name is required"}, status=status.HTTP_400_BAD_REQUEST)
    
@method_decorator(csrf_exempt, name="dispatch") 
class CompanyView(View):
    def get(self, request):
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM user_company")
            rows = cursor.fetchall()
            if not rows:
                return JsonResponse({"message":"No companies found"}, status=status.HTTP_400_BAD_REQUEST)
            companies = [{"id": row[0], "name": row[1], "description": row[2]} for row in rows]
            return JsonResponse({"companies": companies})
    
    def post(self, request):
        company_name = request.POST.get("name")
        description = request.POST.get("description")
        if company_name:
            with connection.cursor() as cursor:
                cursor.execute("INSERT INTO user_company (name, description) VALUES (%s, %s)", [company_name, description])
                return JsonResponse({"message": "Company created", "company": company_name})
        return JsonResponse({"error": "Company name is required"}, status=status.HTTP_400_BAD_REQUEST)
