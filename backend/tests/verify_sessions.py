import requests
import uuid
import json

BASE_URL = "http://localhost:8000/api/sessions"

def test_create_session():
    print("Testing Create Session...")
    response = requests.post(BASE_URL, json={"metadata": {"test": "data"}})
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Session created: {data['session_id']}")
        return data['session_id']
    else:
        print(f"❌ Failed to create session: {response.text}")
        return None

def test_get_session(session_id):
    print(f"Testing Get Session {session_id}...")
    response = requests.get(f"{BASE_URL}/{session_id}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Session retrieved: {data}")
        assert data['metadata'] == {"test": "data"}
    else:
        print(f"❌ Failed to get session: {response.text}")

def test_update_session(session_id):
    print(f"Testing Update Session {session_id}...")
    response = requests.patch(f"{BASE_URL}/{session_id}", json={"metadata": {"updated": "true"}})
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Session updated: {data}")
        assert data['metadata'] == {"updated": "true"}
    else:
        print(f"❌ Failed to update session: {response.text}")

if __name__ == "__main__":
    session_id = test_create_session()
    if session_id:
        test_get_session(session_id)
        test_update_session(session_id)
