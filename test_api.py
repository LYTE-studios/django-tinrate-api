#!/usr/bin/env python3
"""
Simple test script to verify the TinRate API is working correctly.
Run this after starting the Django server to test basic functionality.
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000/v1"

def test_health_check():
    """Test the health check endpoint."""
    print("🔍 Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/health/")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data['status']}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_config_endpoint():
    """Test the config endpoint."""
    print("🔍 Testing config endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/config/")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Config endpoint passed: {data['success']}")
            return True
        else:
            print(f"❌ Config endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Config endpoint error: {e}")
        return False

def test_user_registration():
    """Test user registration."""
    print("🔍 Testing user registration...")
    try:
        user_data = {
            "email": "test@example.com",
            "password": "testpassword123",
            "firstName": "Test",
            "lastName": "User",
            "country": "US"
        }
        
        response = requests.post(f"{BASE_URL}/auth/register/", json=user_data)
        if response.status_code == 201:
            data = response.json()
            print(f"✅ User registration passed: {data['success']}")
            return True, data
        else:
            print(f"❌ User registration failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False, None
    except Exception as e:
        print(f"❌ User registration error: {e}")
        return False, None

def test_experts_list():
    """Test experts listing (public endpoint)."""
    print("🔍 Testing experts listing...")
    try:
        response = requests.get(f"{BASE_URL}/experts/")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Experts listing passed: {data['success']}")
            print(f"   Found {len(data['data']['experts'])} experts")
            return True
        else:
            print(f"❌ Experts listing failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Experts listing error: {e}")
        return False

def test_featured_experts():
    """Test featured experts endpoint."""
    print("🔍 Testing featured experts...")
    try:
        response = requests.get(f"{BASE_URL}/experts/featured/")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Featured experts passed: {data['success']}")
            print(f"   Found {len(data['data']['experts'])} featured experts")
            return True
        else:
            print(f"❌ Featured experts failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Featured experts error: {e}")
        return False

def test_search():
    """Test search endpoint."""
    print("🔍 Testing search...")
    try:
        response = requests.get(f"{BASE_URL}/search/?q=design")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Search passed: {data['success']}")
            print(f"   Found {data['data']['totalResults']} results")
            return True
        else:
            print(f"❌ Search failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Search error: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Starting TinRate API Tests")
    print("=" * 50)
    
    tests = [
        test_health_check,
        test_config_endpoint,
        test_experts_list,
        test_featured_experts,
        test_search,
        test_user_registration,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test == test_user_registration:
                result, _ = test()
            else:
                result = test()
            
            if result:
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
        
        print()  # Add spacing between tests
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The API is working correctly.")
        sys.exit(0)
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()