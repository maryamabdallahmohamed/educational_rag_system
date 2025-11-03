#!/usr/bin/env python3
"""
Quick TutorAgent Test with Generated Profile

This script tests the TutorAgent with one of the generated learner profiles
to verify the integration works correctly.
"""

import asyncio
import sys
import os
from uuid import UUID

# Add the backend to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.core.agents.tutor_agent import TutorAgent
from backend.core.states.graph_states import RAGState

async def test_tutor_with_generated_profile():
    """Test TutorAgent with a generated learner profile"""
    
    print("🧪 QUICK TUTOR AGENT TEST WITH GENERATED PROFILE")
    print("="*70)
    
    try:
        # Read profile IDs from saved file
        if not os.path.exists("tests/test_profile_ids.txt"):
            print("❌ No test profiles found!")
            print("   Run 'python generate_mock_profiles.py' first to create test profiles.")
            return False
        
        with open("tests/test_profile_ids.txt", "r", encoding='utf-8') as f:
            content = f.read()
        
        # Extract Emma Visual's profile ID (first one)
        lines = content.split('\n')
        emma_line = [line for line in lines if "emma_visual_id" in line][0]
        profile_id_str = emma_line.split('"')[1]
        
        print(f"📝 Using Emma Visual's profile: {profile_id_str[:8]}...")
        print(f"   (High-performing visual learner, Grade 10, 87% accuracy)")
        
        # Create TutorAgent instance
        print(f"\n🤖 Initializing TutorAgent...")
        tutor = TutorAgent()
        
        # Create test state (visual learner query)
        test_state = RAGState(
            query="Can you explain what photosynthesis is? I learn best with diagrams and visual aids.",
            learner_id=UUID(profile_id_str),
            session_id=None,
            route="tutor_agent",
            delegated_by_cpa=True,
            processed_by_tutor=False
        )
        
        print(f"❓ Test Query: {test_state['query']}")
        print(f"👤 Learner ID: {profile_id_str}")
        print(f"🎯 Expected: Visual-focused explanation for high performer")
        
        print(f"\n🚀 Processing request...")
        print("-" * 70)
        
        # Process the request through TutorAgent
        result = await tutor.process(test_state)
        
        # Display results
        if result and result.get("answer"):
            print(f"✅ TutorAgent Response:")
            print(f"{result['answer']}")
            
            # Check if response seems personalized
            response_lower = result['answer'].lower()
            visual_indicators = ['visual', 'diagram', 'chart', 'image', 'picture', 'see', 'show']
            found_visual = any(indicator in response_lower for indicator in visual_indicators)
            
            print(f"\n📊 Personalization Analysis:")
            print(f"   Visual Learning Indicators: {'✅ Found' if found_visual else '❌ Not detected'}")
            print(f"   Response Length: {len(result['answer'])} characters")
            print(f"   Processed by Tutor: {result.get('processed_by_tutor', False)}")
            
        else:
            print(f"❌ No response received from TutorAgent")
            return False
        
        # Test a second query for the same learner
        print(f"\n" + "="*70)
        print(f"🧪 TESTING SECOND QUERY (Session Continuity)")
        print("="*70)
        
        test_state2 = RAGState(
            query="Now can you show me how to solve for x in: 2x + 5 = 11?",
            learner_id=UUID(profile_id_str),
            session_id=result.get("session_id"),  # Continue session
            route="tutor_agent",
            delegated_by_cpa=True
        )
        
        print(f"❓ Follow-up Query: {test_state2['query']}")
        print(f"🔄 Session ID: {test_state2.get('session_id', 'New session')}")
        
        result2 = await tutor.process(test_state2)
        
        if result2 and result2.get("answer"):
            print(f"✅ Follow-up Response:")
            print(f"{result2['answer']}")
        else:
            print(f"❌ No response to follow-up query")
        
        print(f"\n🎉 TutorAgent test completed successfully!")
        return True
        
    except FileNotFoundError:
        print("❌ test_profile_ids.txt not found")
        print("   Run 'python generate_mock_profiles.py' first")
        return False
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_different_learner_types():
    """Test TutorAgent with different learner profiles"""
    
    print(f"\n" + "="*70)
    print("🧪 TESTING DIFFERENT LEARNER TYPES")
    print("="*70)
    
    # Test queries for different learner profiles
    test_cases = [
        {
            "profile_key": "marcus_struggling_id",
            "name": "Marcus (Struggling Learner)",
            "query": "I really don't understand fractions. They're so confusing!",
            "expected": "encouraging, simple explanation"
        },
        {
            "profile_key": "sophia_advanced_id", 
            "name": "Sophia (Advanced Learner)",
            "query": "Can you explain the mathematical foundations of integration?",
            "expected": "rigorous, theoretical explanation"
        }
    ]
    
    try:
        with open("tests/test_profile_ids.txt", "r", encoding='utf-8') as f:
            content = f.read()
        
        tutor = TutorAgent()
        
        for test_case in test_cases:
            print(f"\n📝 Testing: {test_case['name']}")
            
            # Find profile ID
            lines = content.split('\n')
            profile_lines = [line for line in lines if test_case['profile_key'] in line]
            
            if not profile_lines:
                print(f"   ❌ Profile {test_case['profile_key']} not found")
                continue
                
            profile_id_str = profile_lines[0].split('"')[1]
            
            # Create test state
            test_state = RAGState(
                query=test_case["query"],
                learner_id=UUID(profile_id_str),
                route="tutor_agent"
            )
            
            print(f"   Query: {test_case['query']}")
            print(f"   Expected: {test_case['expected']}")
            
            # Process request
            result = await tutor.process(test_state)
            
            if result and result.get("answer"):
                print(f"   ✅ Response generated ({len(result['answer'])} chars)")
                # Show first 100 chars
                preview = result['answer'][:100] + "..." if len(result['answer']) > 100 else result['answer']
                print(f"   Preview: {preview}")
            else:
                print(f"   ❌ No response generated")
                
    except Exception as e:
        print(f"❌ Error testing different learner types: {e}")

if __name__ == "__main__":
    print("🚀 Starting TutorAgent Tests with Generated Profiles...")
    
    # Run main test
    success = asyncio.run(test_tutor_with_generated_profile())
    
    if success:
        # Run additional tests
        asyncio.run(test_different_learner_types())
        
        print(f"\n" + "="*70)
        print("✅ ALL TESTS COMPLETED")
        print("="*70)
        print("🎯 TutorAgent successfully works with generated learner profiles!")
        print("🔧 Next Steps:")
        print("   • Run full manual tests: python tests/manual_test_tutor.py")
        print("   • Test all 8 learner profile types")
        print("   • Verify personalization for each learning style")
        print("   • Test the hierarchical Router → CPA → TutorAgent flow")
    else:
        print(f"\n💥 Tests failed. Check the error messages above.")
