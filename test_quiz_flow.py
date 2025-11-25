"""
Quiz Flow Test for Tutor Agent

Tests the complete learning interaction loop:
1. Start a session
2. Generate practice questions (RAG-based)
3. Submit an answer
4. Check progress

Run with: python test_quiz_flow.py
Requires the server to be running: uvicorn backend.api.main:app --port 8000
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


def test_quiz_flow():
    """Test the complete quiz/practice flow."""
    
    # 1. Start Session
    print_section("1. Starting Session")
    session_payload = {
        "student_id": "quiz_student_01",
        "student_name": "Quiz Tester",
        "language": "en",
        "difficulty": "intermediate",
        "topic": "Photosynthesis"
    }
    print(f"Request: {json.dumps(session_payload, indent=2)}")
    
    session_res = requests.post(
        f"{BASE_URL}/session/start", 
        json=session_payload,
        timeout=60
    )
    
    if session_res.status_code != 200:
        print(f"❌ Failed to start session: {session_res.status_code}")
        print(session_res.text)
        return False
    
    session_data = session_res.json()
    session_id = session_data.get("session_id")
    # Get the actual student_id from database (UUID)
    db_student_id = session_data.get("student_profile", {}).get("student_id", "quiz_student_01")
    print(f"✅ Session started: {session_id}")
    print(f"DB Student ID: {db_student_id}")
    print(f"Welcome: {session_data.get('welcome_message')[:100]}...")
    
    # 2. Chat to request practice questions (this stores them in session)
    print_section("2. Requesting Practice Questions via Chat")
    chat_payload = {
        "session_id": session_id,
        "student_id": db_student_id,  # Use DB student ID
        "message": "Give me some practice questions about photosynthesis",
        "topic": "Photosynthesis"
    }
    print(f"Request: {json.dumps(chat_payload, indent=2)}")
    print("\nWaiting for questions to be generated...")
    
    chat_res = requests.post(
        f"{BASE_URL}/chat",
        json=chat_payload,
        timeout=120
    )
    
    if chat_res.status_code != 200:
        print(f"❌ Failed to generate questions: {chat_res.status_code}")
        print(chat_res.text)
        return False
    
    chat_data = chat_res.json()
    print(f"✅ Response received")
    print(f"Intent: {chat_data.get('intent_detected')}")
    print(f"Handler: {chat_data.get('handler_used')}")
    
    questions = chat_data.get("questions", [])
    if questions:
        print(f"\n📝 Generated {len(questions)} questions:")
        for i, q in enumerate(questions[:3]):  # Show first 3
            print(f"  Q{i+1}: {q.get('question', 'N/A')[:80]}...")
    else:
        print("⚠️ No questions in response (may be in response text)")
        print(f"Response preview: {chat_data.get('response', '')[:300]}...")
    
    # 3. Submit an Answer
    print_section("3. Submitting Answer")
    
    # If we have questions, try to answer the first one
    if questions:
        answer_payload = {
            "session_id": session_id,
            "student_id": db_student_id,  # Use DB student ID
            "question_index": 0,
            "student_answer": "Plants use sunlight, water, and carbon dioxide to produce glucose and oxygen"
        }
        print(f"Request: {json.dumps(answer_payload, indent=2)}")
        
        answer_res = requests.post(
            f"{BASE_URL}/answer/check",
            json=answer_payload,
            timeout=60
        )
        
        if answer_res.status_code == 200:
            answer_data = answer_res.json()
            print(f"✅ Answer checked:")
            print(f"   Correct: {answer_data.get('is_correct')}")
            print(f"   Score: {answer_data.get('score')}")
            print(f"   Feedback: {answer_data.get('feedback', '')[:200]}...")
        else:
            print(f"⚠️ Answer check failed: {answer_res.status_code}")
            print(answer_res.text)
    else:
        print("⏭️ Skipping answer check (no questions available)")
    
    # 4. Check Progress (use db_student_id which is the learner UUID)
    print_section("4. Checking Progress")
    progress_res = requests.get(
        f"{BASE_URL}/progress/{db_student_id}",  # Use db_student_id (learner UUID)
        timeout=60
    )
    
    if progress_res.status_code == 200:
        progress_data = progress_res.json()
        print(f"✅ Progress retrieved:")
        print(f"Summary: {progress_data.get('summary', '')[:300]}...")
        print(f"Statistics: {json.dumps(progress_data.get('statistics', {}), indent=2)}")
    else:
        print(f"⚠️ Progress check failed: {progress_res.status_code}")
    
    # 5. Check Active Sessions
    print_section("5. Active Sessions")
    sessions_res = requests.get(f"{BASE_URL}/sessions/active", timeout=10)
    if sessions_res.status_code == 200:
        sessions = sessions_res.json()
        print(f"Active sessions: {sessions.get('count')}")
        for s in sessions.get('sessions', []):
            print(f"  - {s.get('session_id')[:8]}... : {s.get('student_id')} ({s.get('interactions')} interactions)")
    
    # 6. End Session
    print_section("6. Ending Session")
    end_res = requests.delete(f"{BASE_URL}/session/{session_id}", timeout=10)
    if end_res.status_code == 200:
        end_data = end_res.json()
        print(f"✅ Session ended: {end_data.get('interactions')} interactions recorded")
    else:
        print(f"⚠️ End session failed: {end_res.status_code}")
    
    return True


def test_direct_practice_generate():
    """Test the direct practice/generate endpoint."""
    print_section("BONUS: Direct Practice Generate Endpoint")
    
    payload = {
        "topic": "Photosynthesis",
        "difficulty": "intermediate",
        "count": 3,
        "language": "en",
        "student_id": "direct_test_01"
    }
    print(f"Request: {json.dumps(payload, indent=2)}")
    print("\nGenerating questions directly...")
    
    res = requests.post(
        f"{BASE_URL}/practice/generate",
        json=payload,
        timeout=120
    )
    
    if res.status_code == 200:
        data = res.json()
        print(f"✅ Generated {data.get('count')} questions for {data.get('topic')}")
        questions = data.get('questions', [])
        for i, q in enumerate(questions[:3]):
            print(f"\n  Q{i+1} ({q.get('type', 'unknown')}):")
            print(f"    {q.get('question', 'N/A')[:100]}...")
            if q.get('options'):
                for opt in q.get('options', [])[:2]:
                    print(f"      - {opt}")
    else:
        print(f"❌ Failed: {res.status_code}")
        print(res.text[:500])


def main():
    print("\n" + "=" * 60)
    print("  TUTOR AGENT - QUIZ FLOW TEST")
    print("  Testing: Complete Learning Interaction Loop")
    print("=" * 60)
    
    try:
        # First test health
        health = requests.get(f"{BASE_URL}/health", timeout=60)
        if health.status_code != 200:
            print("❌ Server not ready. Please start the server first.")
            return
        print("✅ Server is healthy")
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        print("Please start the server: uvicorn backend.api.main:app --port 8000")
        return
    
    # Run main test
    success = test_quiz_flow()
    
    # Run bonus test
    test_direct_practice_generate()
    
    # Summary
    print_section("TEST COMPLETE")
    if success:
        print("🎉 Quiz flow test completed successfully!")
    else:
        print("⚠️ Some tests may have failed. Check output above.")


if __name__ == "__main__":
    main()
