#!/usr/bin/env python3
"""
Quick test of enhanced TutorAgent with guest session support
"""

import sys
import os
sys.path.append(os.path.abspath('.'))

from backend.core.agents.tutor_agent import TutorAgent

def test_guest_profile_creation():
    """Test guest profile creation directly"""
    
    print("🧪 TESTING ENHANCED TUTOR AGENT GUEST PROFILES")
    print("="*70)
    
    # Create TutorAgent instance
    tutor_agent = TutorAgent()
    
    test_queries = [
        "Can you show me pictures of how fractions work? I'm in 3rd grade.",
        "Math is really confusing for me. Can you explain algebra step by step?",
        "I need help understanding calculus for my AP physics class.",
        "¿Puedes explicarme geometría en español? Necesito ayuda con triángulos."
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🎯 Test {i}: {query}")
        
        try:
            # Test guest profile creation
            guest_profile = tutor_agent._create_guest_profile(query)
            
            print(f"✅ Guest Profile Created:")
            print(f"   Grade Level: {guest_profile['grade_level']}")
            print(f"   Learning Style: {guest_profile['learning_style']}")
            print(f"   Difficulty: {guest_profile['difficulty_preference']}")
            print(f"   Language: {guest_profile['preferred_language']}")
            print(f"   Formats: {guest_profile['interaction_patterns']['preferred_formats']}")
            
            # Show inference details
            if 'guest_session_info' in guest_profile:
                indicators = guest_profile['guest_session_info']['inferred_characteristics']
                print(f"   Inference Details:")
                print(f"     Grade Indicators: {indicators.get('grade_level_indicators', [])}")
                print(f"     Style Indicators: {indicators.get('learning_style_indicators', [])}")
                print(f"     Difficulty Indicators: {indicators.get('difficulty_indicators', [])}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\n{'='*70}")
    print("✅ Enhanced TutorAgent guest profile creation tested!")
    print("🎉 Ready for LangSmith testing with guest sessions!")

if __name__ == "__main__":
    test_guest_profile_creation()
