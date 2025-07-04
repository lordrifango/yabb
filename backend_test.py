#!/usr/bin/env python3
import requests
import json
import time
import re
import statistics
from datetime import datetime

# Get the backend URL from the frontend .env file
with open('/app/frontend/.env', 'r') as f:
    env_content = f.read()
    backend_url_match = re.search(r'REACT_APP_BACKEND_URL=(.+)', env_content)
    if backend_url_match:
        BACKEND_URL = backend_url_match.group(1).strip()
    else:
        raise ValueError("Could not find REACT_APP_BACKEND_URL in frontend/.env")

print(f"Using backend URL: {BACKEND_URL}")

# Test data
valid_phone = "6505551234"
valid_country_code = "+1"
invalid_code_short = "12345"  # Not 6 digits
invalid_code_letters = "12345a"  # Contains letters
valid_code = "123456"  # Any 6 digits should work

# Profile test data
valid_profile_data = {
    "first_name": "Jean",
    "last_name": "Dupont",
    "date_of_birth": "1990-01-01",
    "gender": "male",
    "city": "Paris",
    "country": "France",
    "occupation": "Engineer",
    "language": "fr",
    "currency": "FCFA"
}

update_profile_data = {
    "first_name": "Jean-Pierre",
    "city": "Lyon",
    "occupation": "Senior Engineer"
}

def test_send_code_endpoint():
    """Test the /api/auth/send-code endpoint"""
    print("\n=== Testing POST /api/auth/send-code ===")
    
    # Test with valid phone and country code
    url = f"{BACKEND_URL}/api/auth/send-code"
    payload = {
        "phone": valid_phone,
        "country_code": valid_country_code
    }
    
    print(f"Sending request to {url} with payload: {payload}")
    response = requests.post(url, json=payload)
    
    print(f"Response status code: {response.status_code}")
    print(f"Response body: {response.text}")
    
    # Validate response
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    
    data = response.json()
    assert data["success"] == True, "Expected success to be True"
    assert "session_id" in data, "Expected session_id in response"
    assert data["session_id"] is not None, "Expected session_id to not be None"
    
    # Return session_id for use in other tests
    return data["session_id"]

def test_verify_code_endpoint(session_id):
    """Test the /api/auth/verify-code endpoint"""
    print("\n=== Testing POST /api/auth/verify-code ===")
    url = f"{BACKEND_URL}/api/auth/verify-code"
    
    # Test with invalid code format (too short)
    print("\nTesting with invalid code (too short):")
    payload = {
        "phone": valid_phone,
        "country_code": valid_country_code,
        "code": invalid_code_short
    }
    
    print(f"Sending request to {url} with payload: {payload}")
    response = requests.post(url, json=payload)
    
    print(f"Response status code: {response.status_code}")
    print(f"Response body: {response.text}")
    
    # Validate response for invalid code
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    data = response.json()
    assert data["success"] == False, "Expected success to be False for invalid code format"
    
    # Test with invalid code format (contains letters)
    print("\nTesting with invalid code (contains letters):")
    payload["code"] = invalid_code_letters
    
    print(f"Sending request to {url} with payload: {payload}")
    response = requests.post(url, json=payload)
    
    print(f"Response status code: {response.status_code}")
    print(f"Response body: {response.text}")
    
    # Validate response for invalid code
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    data = response.json()
    assert data["success"] == False, "Expected success to be False for invalid code format"
    
    # Test with valid code format
    print("\nTesting with valid code format:")
    payload["code"] = valid_code
    
    print(f"Sending request to {url} with payload: {payload}")
    response = requests.post(url, json=payload)
    
    print(f"Response status code: {response.status_code}")
    print(f"Response body: {response.text}")
    
    # Validate response for valid code
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    data = response.json()
    assert data["success"] == True, "Expected success to be True for valid code format"
    assert "session_id" in data, "Expected session_id in response"
    
    # Return verified session_id
    return data["session_id"]

def test_check_session_endpoint(session_id):
    """Test the /api/auth/check-session/{session_id} endpoint"""
    print("\n=== Testing GET /api/auth/check-session/{session_id} ===")
    
    # Test with valid session_id
    print("\nTesting with valid session_id:")
    url = f"{BACKEND_URL}/api/auth/check-session/{session_id}"
    
    print(f"Sending request to {url}")
    response = requests.get(url)
    
    print(f"Response status code: {response.status_code}")
    print(f"Response body: {response.text}")
    
    # Validate response for valid session
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    data = response.json()
    assert data["valid"] == True, "Expected valid to be True for valid session"
    assert "phone" in data, "Expected phone in response"
    assert "country_code" in data, "Expected country_code in response"
    
    # Test with invalid session_id
    print("\nTesting with invalid session_id:")
    invalid_session_id = "invalid-session-id"
    url = f"{BACKEND_URL}/api/auth/check-session/{invalid_session_id}"
    
    print(f"Sending request to {url}")
    response = requests.get(url)
    
    print(f"Response status code: {response.status_code}")
    print(f"Response body: {response.text}")
    
    # Validate response for invalid session
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    data = response.json()
    assert data["valid"] == False, "Expected valid to be False for invalid session"

def create_and_verify_session(phone, country_code):
    """Helper function to create and verify a session"""
    # Create session
    response = requests.post(
        f"{BACKEND_URL}/api/auth/send-code", 
        json={"phone": phone, "country_code": country_code}
    )
    session_id = response.json()["session_id"]
    
    # Verify session
    requests.post(
        f"{BACKEND_URL}/api/auth/verify-code", 
        json={"phone": phone, "country_code": country_code, "code": "123456"}
    )
    
    return session_id

def test_profile_create_endpoint(session_id):
    """Test the /api/profile/create endpoint"""
    print("\n=== Testing POST /api/profile/create ===")
    
    # Test with valid session_id and profile data
    print("\nTesting with valid session_id and profile data:")
    url = f"{BACKEND_URL}/api/profile/create?session_id={session_id}"
    
    print(f"Sending request to {url} with payload: {valid_profile_data}")
    response = requests.post(url, json=valid_profile_data)
    
    print(f"Response status code: {response.status_code}")
    print(f"Response body: {response.text}")
    
    # Validate response
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    
    data = response.json()
    assert data["success"] == True, "Expected success to be True"
    assert "profile" in data, "Expected profile in response"
    assert data["profile"] is not None, "Expected profile to not be None"
    assert data["profile"]["first_name"] == valid_profile_data["first_name"], "First name doesn't match"
    assert data["profile"]["last_name"] == valid_profile_data["last_name"], "Last name doesn't match"
    
    # Test creating duplicate profile (should fail)
    print("\nTesting duplicate profile creation (should fail):")
    response = requests.post(url, json=valid_profile_data)
    
    print(f"Response status code: {response.status_code}")
    print(f"Response body: {response.text}")
    
    # Validate response for duplicate profile
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    data = response.json()
    assert data["success"] == False, "Expected success to be False for duplicate profile"
    assert "Un profil existe déjà" in data["message"], "Expected duplicate profile error message"
    
    # Test with invalid session_id
    print("\nTesting with invalid session_id:")
    invalid_session_id = "invalid-session-id"
    url = f"{BACKEND_URL}/api/profile/create?session_id={invalid_session_id}"
    
    print(f"Sending request to {url} with payload: {valid_profile_data}")
    response = requests.post(url, json=valid_profile_data)
    
    print(f"Response status code: {response.status_code}")
    print(f"Response body: {response.text}")
    
    # Validate response for invalid session
    assert response.status_code == 401, f"Expected status code 401, got {response.status_code}"
    
    # Test with missing required fields
    print("\nTesting with missing required fields:")
    url = f"{BACKEND_URL}/api/profile/create?session_id={session_id}"
    invalid_profile_data = {
        # Missing first_name and last_name
        "city": "Paris",
        "country": "France"
    }
    
    print(f"Sending request to {url} with payload: {invalid_profile_data}")
    response = requests.post(url, json=invalid_profile_data)
    
    print(f"Response status code: {response.status_code}")
    print(f"Response body: {response.text}")
    
    # Validate response for missing required fields
    assert response.status_code == 422, f"Expected status code 422, got {response.status_code}"
    
    return True

def test_profile_get_endpoint(session_id):
    """Test the /api/profile/{session_id} GET endpoint"""
    print("\n=== Testing GET /api/profile/{session_id} ===")
    
    # Test with valid session_id
    print("\nTesting with valid session_id:")
    url = f"{BACKEND_URL}/api/profile/{session_id}"
    
    print(f"Sending request to {url}")
    response = requests.get(url)
    
    print(f"Response status code: {response.status_code}")
    print(f"Response body: {response.text}")
    
    # Validate response
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    
    data = response.json()
    assert data["success"] == True, "Expected success to be True"
    assert "profile" in data, "Expected profile in response"
    assert data["profile"] is not None, "Expected profile to not be None"
    assert data["profile"]["first_name"] == valid_profile_data["first_name"], "First name doesn't match"
    assert data["profile"]["last_name"] == valid_profile_data["last_name"], "Last name doesn't match"
    
    # Test with invalid session_id
    print("\nTesting with invalid session_id:")
    invalid_session_id = "invalid-session-id"
    url = f"{BACKEND_URL}/api/profile/{invalid_session_id}"
    
    print(f"Sending request to {url}")
    response = requests.get(url)
    
    print(f"Response status code: {response.status_code}")
    print(f"Response body: {response.text}")
    
    # Validate response for invalid session
    assert response.status_code == 401, f"Expected status code 401, got {response.status_code}"
    
    # Test with non-existent profile (create a new session without profile)
    print("\nTesting with session that has no profile:")
    # Create a new session
    new_phone = "6505557777"
    new_session_id = create_and_verify_session(new_phone, valid_country_code)
    
    url = f"{BACKEND_URL}/api/profile/{new_session_id}"
    
    print(f"Sending request to {url}")
    response = requests.get(url)
    
    print(f"Response status code: {response.status_code}")
    print(f"Response body: {response.text}")
    
    # Validate response for non-existent profile
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    data = response.json()
    assert data["success"] == False, "Expected success to be False for non-existent profile"
    assert "Profil non trouvé" in data["message"], "Expected profile not found message"
    
    return True

def test_profile_update_endpoint(session_id):
    """Test the /api/profile/{session_id} PUT endpoint"""
    print("\n=== Testing PUT /api/profile/{session_id} ===")
    
    # Test with valid session_id and update data
    print("\nTesting with valid session_id and update data:")
    url = f"{BACKEND_URL}/api/profile/{session_id}"
    
    print(f"Sending request to {url} with payload: {update_profile_data}")
    response = requests.put(url, json=update_profile_data)
    
    print(f"Response status code: {response.status_code}")
    print(f"Response body: {response.text}")
    
    # Validate response
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    
    data = response.json()
    assert data["success"] == True, "Expected success to be True"
    assert "profile" in data, "Expected profile in response"
    assert data["profile"] is not None, "Expected profile to not be None"
    assert data["profile"]["first_name"] == update_profile_data["first_name"], "Updated first name doesn't match"
    assert data["profile"]["city"] == update_profile_data["city"], "Updated city doesn't match"
    assert data["profile"]["occupation"] == update_profile_data["occupation"], "Updated occupation doesn't match"
    # Fields not in update_profile_data should remain unchanged
    assert data["profile"]["last_name"] == valid_profile_data["last_name"], "Last name should remain unchanged"
    
    # Test with invalid session_id
    print("\nTesting with invalid session_id:")
    invalid_session_id = "invalid-session-id"
    url = f"{BACKEND_URL}/api/profile/{invalid_session_id}"
    
    print(f"Sending request to {url} with payload: {update_profile_data}")
    response = requests.put(url, json=update_profile_data)
    
    print(f"Response status code: {response.status_code}")
    print(f"Response body: {response.text}")
    
    # Validate response for invalid session
    assert response.status_code == 401, f"Expected status code 401, got {response.status_code}"
    
    # Test with non-existent profile (create a new session without profile)
    print("\nTesting with session that has no profile:")
    # Create a new session
    new_phone = "6505558888"
    new_session_id = create_and_verify_session(new_phone, valid_country_code)
    
    url = f"{BACKEND_URL}/api/profile/{new_session_id}"
    
    print(f"Sending request to {url} with payload: {update_profile_data}")
    response = requests.put(url, json=update_profile_data)
    
    print(f"Response status code: {response.status_code}")
    print(f"Response body: {response.text}")
    
    # Validate response for non-existent profile
    assert response.status_code == 404, f"Expected status code 404, got {response.status_code}"
    
    return True

def run_all_tests():
    """Run all tests in sequence"""
    try:
        print(f"Starting backend API tests at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Test MongoDB connectivity
        test_mongodb_connectivity()
        
        # Test authentication endpoints
        print("\n=== Testing Authentication Endpoints ===")
        # Test send code endpoint
        session_id = test_send_code_endpoint()
        print(f"Generated session_id: {session_id}")
        
        # Test verify code endpoint
        verified_session_id = test_verify_code_endpoint(session_id)
        print(f"Verified session_id: {verified_session_id}")
        
        # Test check session endpoint
        test_check_session_endpoint(verified_session_id)
        
        # Test profile endpoints
        print("\n=== Testing Profile Endpoints ===")
        # Test profile creation
        test_profile_create_endpoint(verified_session_id)
        
        # Test profile retrieval
        test_profile_get_endpoint(verified_session_id)
        
        # Test profile update
        test_profile_update_endpoint(verified_session_id)
        
        # Run performance tests
        print("\n=== Running Performance Tests ===")
        performance_test_results = run_performance_tests()
        
        print("\n=== All tests completed successfully! ===")
        return True
    except AssertionError as e:
        print(f"\n❌ Test failed: {str(e)}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        return False

def test_mongodb_connectivity():
    """Test MongoDB connectivity by checking if sessions are stored properly"""
    print("\n=== Testing MongoDB Connectivity ===")
    
    # First, create a new session
    url = f"{BACKEND_URL}/api/auth/send-code"
    payload = {
        "phone": "6505559999",
        "country_code": "+1"
    }
    
    print(f"Creating a new session via {url}")
    response = requests.post(url, json=payload)
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    
    data = response.json()
    session_id = data["session_id"]
    
    # Verify the session by checking it exists
    url = f"{BACKEND_URL}/api/auth/check-session/{session_id}"
    print(f"Verifying session exists in MongoDB via {url}")
    
    # Wait a moment to ensure data is stored
    time.sleep(0.5)
    
    response = requests.get(url)
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    
    # The session should exist but not be verified yet
    data = response.json()
    assert "valid" in data, "Expected 'valid' field in response"
    assert data["valid"] == False, "Expected session to be invalid (not verified yet)"
    
    # Now verify the session
    url = f"{BACKEND_URL}/api/auth/verify-code"
    payload = {
        "phone": "6505559999",
        "country_code": "+1",
        "code": "123456"
    }
    
    print(f"Verifying the session via {url}")
    response = requests.post(url, json=payload)
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    
    # Check that the session is now verified
    url = f"{BACKEND_URL}/api/auth/check-session/{session_id}"
    print(f"Checking that session is now verified via {url}")
    
    response = requests.get(url)
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    
    data = response.json()
    assert data["valid"] == True, "Expected session to be valid (verified)"
    
    print("MongoDB connectivity test passed - sessions are being stored and updated correctly")

def run_performance_tests(num_iterations=5):
    """Run performance tests on all endpoints"""
    send_code_times = []
    verify_code_times = []
    check_session_times = []
    profile_create_times = []
    profile_get_times = []
    profile_update_times = []
    
    for i in range(num_iterations):
        print(f"\nPerformance test iteration {i+1}/{num_iterations}")
        
        # Test send-code performance
        start_time = time.time()
        response = requests.post(
            f"{BACKEND_URL}/api/auth/send-code", 
            json={"phone": f"650555{i}234", "country_code": "+1"}
        )
        end_time = time.time()
        send_code_times.append((end_time - start_time) * 1000)  # Convert to ms
        
        session_id = response.json()["session_id"]
        
        # Test verify-code performance
        start_time = time.time()
        response = requests.post(
            f"{BACKEND_URL}/api/auth/verify-code", 
            json={"phone": f"650555{i}234", "country_code": "+1", "code": "123456"}
        )
        end_time = time.time()
        verify_code_times.append((end_time - start_time) * 1000)  # Convert to ms
        
        # Test check-session performance
        start_time = time.time()
        response = requests.get(f"{BACKEND_URL}/api/auth/check-session/{session_id}")
        end_time = time.time()
        check_session_times.append((end_time - start_time) * 1000)  # Convert to ms
        
        # Test profile-create performance
        start_time = time.time()
        profile_data = {
            "first_name": f"User{i}",
            "last_name": f"Test{i}",
            "date_of_birth": "1990-01-01",
            "gender": "male",
            "city": "Paris",
            "country": "France"
        }
        response = requests.post(f"{BACKEND_URL}/api/profile/create?session_id={session_id}", json=profile_data)
        end_time = time.time()
        profile_create_times.append((end_time - start_time) * 1000)  # Convert to ms
        
        # Test profile-get performance
        start_time = time.time()
        response = requests.get(f"{BACKEND_URL}/api/profile/{session_id}")
        end_time = time.time()
        profile_get_times.append((end_time - start_time) * 1000)  # Convert to ms
        
        # Test profile-update performance
        start_time = time.time()
        update_data = {
            "city": f"NewCity{i}",
            "occupation": f"Occupation{i}"
        }
        response = requests.put(f"{BACKEND_URL}/api/profile/{session_id}", json=update_data)
        end_time = time.time()
        profile_update_times.append((end_time - start_time) * 1000)  # Convert to ms
    
    # Calculate and print statistics
    print("\nPerformance Test Results (in milliseconds):")
    print(f"  send-code:      avg={statistics.mean(send_code_times):.2f}ms, min={min(send_code_times):.2f}ms, max={max(send_code_times):.2f}ms")
    print(f"  verify-code:    avg={statistics.mean(verify_code_times):.2f}ms, min={min(verify_code_times):.2f}ms, max={max(verify_code_times):.2f}ms")
    print(f"  check-session:  avg={statistics.mean(check_session_times):.2f}ms, min={min(check_session_times):.2f}ms, max={max(check_session_times):.2f}ms")
    print(f"  profile-create: avg={statistics.mean(profile_create_times):.2f}ms, min={min(profile_create_times):.2f}ms, max={max(profile_create_times):.2f}ms")
    print(f"  profile-get:    avg={statistics.mean(profile_get_times):.2f}ms, min={min(profile_get_times):.2f}ms, max={max(profile_get_times):.2f}ms")
    print(f"  profile-update: avg={statistics.mean(profile_update_times):.2f}ms, min={min(profile_update_times):.2f}ms, max={max(profile_update_times):.2f}ms")
    
    return {
        "send_code": {
            "avg": statistics.mean(send_code_times),
            "min": min(send_code_times),
            "max": max(send_code_times)
        },
        "verify_code": {
            "avg": statistics.mean(verify_code_times),
            "min": min(verify_code_times),
            "max": max(verify_code_times)
        },
        "check_session": {
            "avg": statistics.mean(check_session_times),
            "min": min(check_session_times),
            "max": max(check_session_times)
        },
        "profile_create": {
            "avg": statistics.mean(profile_create_times),
            "min": min(profile_create_times),
            "max": max(profile_create_times)
        },
        "profile_get": {
            "avg": statistics.mean(profile_get_times),
            "min": min(profile_get_times),
            "max": max(profile_get_times)
        },
        "profile_update": {
            "avg": statistics.mean(profile_update_times),
            "min": min(profile_update_times),
            "max": max(profile_update_times)
        }
    }

if __name__ == "__main__":
    run_all_tests()