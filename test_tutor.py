"""
Smoke Test for Tutor Agent API

This script tests the basic functionality of the Tutor Agent endpoints:
1. Health check
2. Start a session
3. Chat with the tutor
4. Generate practice questions
5. Get progress

Run with: python test_tutor.py
Requires the server to be running: uvicorn backend.api.main:app --reload --port 8000
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000/api/tutor"


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_health():
    """Test the health endpoint."""
    print_section("1. Health Check")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_start_session():
    """Test starting a new tutoring session."""
    print_section("2. Start Session")
    payload = {
        "student_id": "test_student_001",
        "student_name": "Test Student",
        "topic": "Photosynthesis",
        "language": "en",
        "difficulty": "beginner"
    }
    try:
        print(f"Request: {json.dumps(payload, indent=2)}")
        response = requests.post(f"{BASE_URL}/session/start", json=payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        return response.status_code == 200, data.get("session_id")
    except Exception as e:
        print(f"Error: {e}")
        return False, None


def test_chat(session_id: str):
    """Test chatting with the tutor."""
    print_section("3. Chat with Tutor")
    payload = {
        "session_id": session_id,
        "student_id": "test_student_001",
        "message": "What is photosynthesis? Explain it simply.",
        "topic": "Photosynthesis"
    }
    try:
        print(f"Request: {json.dumps(payload, indent=2)}")
        print("\nWaiting for response (this may take a moment)...")
        response = requests.post(f"{BASE_URL}/chat", json=payload, timeout=60)
        print(f"Status Code: {response.status_code}")
        data = response.json()
        # Truncate response if too long for display
        if len(data.get("response", "")) > 500:
            display_data = data.copy()
            display_data["response"] = data["response"][:500] + "...[truncated]"
        else:
            display_data = data
        print(f"Response: {json.dumps(display_data, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_practice_questions():
    """Test generating practice questions."""
    print_section("4. Generate Practice Questions")
    payload = {
        "topic": "Photosynthesis",
        "difficulty": "beginner",
        "count": 3,
        "language": "en",
        "student_id": "test_student_001"
    }
    try:
        print(f"Request: {json.dumps(payload, indent=2)}")
        print("\nWaiting for questions to be generated...")
        response = requests.post(f"{BASE_URL}/practice/generate", json=payload, timeout=60)
        print(f"Status Code: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_progress(student_id: str):
    """Test getting student progress."""
    print_section("5. Get Student Progress")
    try:
        response = requests.get(f"{BASE_URL}/progress/{student_id}", timeout=30)
        print(f"Status Code: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_active_sessions():
    """Test getting active sessions list."""
    print_section("6. Active Sessions")
    try:
        response = requests.get(f"{BASE_URL}/sessions/active", timeout=10)
        print(f"Status Code: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_end_session(session_id: str):
    """Test ending a session."""
    print_section("7. End Session")
    try:
        response = requests.delete(f"{BASE_URL}/session/{session_id}", timeout=10)
        print(f"Status Code: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


def main():
    """Run all smoke tests."""
    print("\n" + "=" * 60)
    print("  TUTOR AGENT SMOKE TEST")
    print("  Testing: http://localhost:8000/api/tutor")
    print("=" * 60)
    
    results = {
        "health": False,
        "start_session": False,
        "chat": False,
        "practice": False,
        "progress": False,
        "active_sessions": False,
        "end_session": False
    }
    
    # Run tests
    results["health"] = test_health()
    
    if results["health"]:
        success, session_id = test_start_session()
        results["start_session"] = success
        
        if success and session_id:
            results["chat"] = test_chat(session_id)
            time.sleep(1)  # Brief pause between tests
            
            results["practice"] = test_practice_questions()
            time.sleep(1)
            
            results["progress"] = test_progress("test_student_001")
            
            results["active_sessions"] = test_active_sessions()
            
            results["end_session"] = test_end_session(session_id)
    
    # Summary
    print_section("TEST SUMMARY")
    total_passed = sum(results.values())
    total_tests = len(results)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {test_name}: {status}")
    
    print(f"\n  Total: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("\n  🎉 All tests passed! Tutor Agent is working correctly.")
    else:
        print("\n  ⚠️ Some tests failed. Check the errors above.")
    
    return total_passed == total_tests


if __name__ == "__main__":
    main()
