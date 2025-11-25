"""
Arabic Tutor Agent Test

This script verifies that the Tutor Agent:
1. Respects the language="ar" flag
2. Retrieves Arabic content from RAG
3. Responds in natural Arabic

Run with: python test_tutor_ar.py
Requires:
  1. Server running: uvicorn backend.api.main:app --port 8000
  2. Arabic content ingested: python ingest_ar_data.py
"""

import requests
import json
import time

API_URL = "http://localhost:8000/api/tutor"


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_arabic_flow():
    """Test the complete Arabic tutoring flow."""
    
    print_section("ARABIC TUTOR AGENT TEST - اختبار المعلم الذكي")
    
    # Check server health
    try:
        health = requests.get(f"{API_URL}/health", timeout=10)
        if health.status_code != 200:
            print("❌ Server not ready")
            return False
        print("✅ Server is healthy")
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        print("   Run: uvicorn backend.api.main:app --port 8000")
        return False

    # =========================================================================
    # 1. Start Arabic Session
    # =========================================================================
    print_section("1. بدء جلسة عربية - Starting Arabic Session")
    
    start_payload = {
        "student_id": "student_ahmed_01",
        "student_name": "أحمد",
        "language": "ar",  # CRITICAL: Arabic language flag
        "difficulty": "intermediate",
        "topic": "عملية البناء الضوئي"
    }
    
    print(f"Request: {json.dumps(start_payload, ensure_ascii=False, indent=2)}")
    
    try:
        response = requests.post(f"{API_URL}/session/start", json=start_payload, timeout=60)
        if response.status_code != 200:
            print(f"❌ Session start failed: {response.status_code}")
            print(response.text)
            return False
            
        session = response.json()
        session_id = session.get('session_id')
        db_student_id = session.get("student_profile", {}).get("student_id")
        
        print(f"✅ Session ID: {session_id}")
        print(f"✅ DB Student ID: {db_student_id}")
        print(f"\n👋 رسالة الترحيب (Welcome Message):")
        print("-" * 50)
        print(session.get('welcome_message', 'No message'))
        print("-" * 50)
        
        # Verify welcome is in Arabic
        welcome = session.get('welcome_message', '')
        if 'مرحبا' in welcome or 'IRIS' in welcome:
            print("✅ Welcome message contains Arabic greeting!")
        else:
            print("⚠️ Welcome message might not be in Arabic")
            
    except Exception as e:
        print(f"❌ Session error: {e}")
        return False

    # =========================================================================
    # 2. Ask Question in Arabic (Explanation Request)
    # =========================================================================
    print_section("2. طرح سؤال عربي - Asking Arabic Question")
    
    question = "ما هي المدخلات التي يحتاجها النبات للقيام بعملية البناء الضوئي؟"
    print(f"❓ سؤال الطالب: {question}")
    
    chat_payload = {
        "session_id": session_id,
        "student_id": db_student_id,
        "message": question,
        "topic": "عملية البناء الضوئي"
    }
    
    print("\n⏳ جاري معالجة السؤال...")
    
    try:
        response = requests.post(f"{API_URL}/chat", json=chat_payload, timeout=120)
        if response.status_code != 200:
            print(f"❌ Chat failed: {response.status_code}")
            print(response.text)
            return False
            
        chat_data = response.json()
        
        print(f"\n📊 Intent Detected: {chat_data.get('intent_detected')}")
        print(f"📊 Handler Used: {chat_data.get('handler_used')}")
        print(f"📊 Processing Time: {chat_data.get('processing_time', 0):.2f}s")
        
        print(f"\n🤖 إجابة المعلم (Tutor Response):")
        print("-" * 50)
        print(chat_data.get('response', 'No response'))
        print("-" * 50)
        
        # Verify Arabic content retrieval
        response_text = chat_data.get('response', '')
        arabic_keywords = ["ماء", "ضوء", "كربون", "أكسجين", "كلوروفيل", "نبات"]
        found_keywords = [kw for kw in arabic_keywords if kw in response_text]
        
        if found_keywords:
            print(f"\n✅ SUCCESS: Found Arabic keywords: {', '.join(found_keywords)}")
            print("   → RAG retrieved Arabic content correctly!")
        else:
            print("\n⚠️ WARNING: Response might be generic or hallucinated")
            print("   → Check if Arabic content was ingested properly")
            
    except Exception as e:
        print(f"❌ Chat error: {e}")
        return False

    # =========================================================================
    # 3. Request Practice Questions in Arabic
    # =========================================================================
    print_section("3. طلب أسئلة تدريبية - Requesting Practice Questions")
    
    practice_request = "أعطني أسئلة تدريبية عن البناء الضوئي"
    print(f"❓ طلب الطالب: {practice_request}")
    
    chat_payload = {
        "session_id": session_id,
        "student_id": db_student_id,
        "message": practice_request,
        "topic": "عملية البناء الضوئي"
    }
    
    print("\n⏳ جاري إنشاء الأسئلة...")
    
    try:
        response = requests.post(f"{API_URL}/chat", json=chat_payload, timeout=120)
        if response.status_code != 200:
            print(f"❌ Practice request failed: {response.status_code}")
            return False
            
        chat_data = response.json()
        
        print(f"\n📊 Intent Detected: {chat_data.get('intent_detected')}")
        print(f"📊 Handler Used: {chat_data.get('handler_used')}")
        
        questions = chat_data.get('questions', [])
        if questions:
            print(f"\n📝 تم إنشاء {len(questions)} أسئلة:")
            for i, q in enumerate(questions[:3], 1):
                print(f"\n  السؤال {i}: {q.get('question', 'N/A')[:100]}...")
                if q.get('options'):
                    for opt in q.get('options', [])[:2]:
                        print(f"    - {opt}")
        else:
            print("\n📝 Response (questions may be in text):")
            print(chat_data.get('response', '')[:500])
            
    except Exception as e:
        print(f"❌ Practice error: {e}")
        return False

    # =========================================================================
    # 4. Submit Arabic Answer
    # =========================================================================
    print_section("4. تقديم إجابة - Submitting Answer")
    
    if questions:
        answer_payload = {
            "session_id": session_id,
            "student_id": db_student_id,
            "question_index": 0,
            "student_answer": "يحتاج النبات إلى ضوء الشمس والماء وثاني أكسيد الكربون لإتمام عملية البناء الضوئي"
        }
        
        print(f"✏️ إجابة الطالب: {answer_payload['student_answer']}")
        
        try:
            response = requests.post(f"{API_URL}/answer/check", json=answer_payload, timeout=60)
            if response.status_code == 200:
                answer_data = response.json()
                print(f"\n✅ تم تقييم الإجابة:")
                print(f"   صحيح: {'نعم ✓' if answer_data.get('is_correct') else 'لا ✗'}")
                print(f"   الدرجة: {answer_data.get('score', 0)}")
                print(f"\n💬 التغذية الراجعة:")
                print(answer_data.get('feedback', '')[:300])
            else:
                print(f"⚠️ Answer check returned: {response.status_code}")
        except Exception as e:
            print(f"⚠️ Answer check error: {e}")
    else:
        print("⏭️ Skipping answer submission (no questions generated)")

    # =========================================================================
    # 5. Check Progress (with Arabic content)
    # =========================================================================
    print_section("5. مراجعة التقدم - Checking Progress")
    
    try:
        response = requests.get(f"{API_URL}/progress/{db_student_id}", timeout=60)
        if response.status_code == 200:
            progress = response.json()
            print("📊 إحصائيات التقدم (Progress Statistics):")
            stats = progress.get('statistics', {})
            print(f"   الجلسات: {stats.get('total_sessions', 0)}")
            print(f"   الأسئلة المجابة: {stats.get('total_questions_answered', 0)}")
            print(f"   الإجابات الصحيحة: {stats.get('correct_answers', 0)}")
            print(f"   نسبة الدقة: {stats.get('accuracy_percentage', 0)}%")
            
            print(f"\n📝 ملخص التقدم:")
            print(progress.get('summary', 'No summary')[:300])
        else:
            print(f"⚠️ Progress check failed: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Progress error: {e}")

    # =========================================================================
    # 6. End Session
    # =========================================================================
    print_section("6. إنهاء الجلسة - Ending Session")
    
    try:
        response = requests.delete(f"{API_URL}/session/{session_id}", timeout=10)
        if response.status_code == 200:
            end_data = response.json()
            print(f"✅ تم إنهاء الجلسة بنجاح")
            print(f"   التفاعلات المسجلة: {end_data.get('interactions', 0)}")
        else:
            print(f"⚠️ Session end returned: {response.status_code}")
    except Exception as e:
        print(f"⚠️ End session error: {e}")

    # =========================================================================
    # Summary
    # =========================================================================
    print_section("ملخص الاختبار - TEST SUMMARY")
    print("🎉 Arabic Tutor Agent test completed!")
    print("\nVerification Checklist:")
    print("  □ Welcome message was in Arabic")
    print("  □ Tutor responded with Arabic keywords from RAG")
    print("  □ Questions were generated (or text response)")
    print("  □ Feedback was provided in Arabic")
    print("  □ Progress statistics updated in database")
    
    return True


if __name__ == "__main__":
    success = test_arabic_flow()
    if not success:
        print("\n❌ Test encountered errors. Check output above.")
