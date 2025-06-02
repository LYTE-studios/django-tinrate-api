#!/usr/bin/env python3
"""
Test script to verify that registration works with nullable fields.
"""
import requests
import json

# Test data with minimal required fields (only email and password)
test_data = {
    "email": "test@example.com",
    "password": "TestPassword123!"
}

# Test data with all fields
test_data_complete = {
    "email": "test2@example.com", 
    "password": "TestPassword123!",
    "firstName": "John",
    "lastName": "Doe",
    "country": "US"
}

def test_registration(data, description):
    """Test registration with given data."""
    print(f"\n=== {description} ===")
    print(f"Request data: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(
            "http://localhost:8000/api/auth/register/",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 201:
            print("✅ Registration successful!")
        else:
            print("❌ Registration failed!")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure Django server is running on localhost:8000")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("Testing TinRate API Registration with Nullable Fields")
    print("=" * 50)
    
    # Test with minimal fields
    test_registration(test_data, "Registration with minimal fields (email + password only)")
    
    # Test with complete fields
    test_registration(test_data_complete, "Registration with all fields")