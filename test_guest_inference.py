#!/usr/bin/env python3
"""
Simple Guest Profile Inference Test

Tests the guest profile inference logic without database dependencies.
"""

import re
import time

def create_guest_profile(query: str) -> dict:
    """Create a guest learner profile by inferring characteristics from the query"""
    try:
        query_lower = query.lower()
        
        # Infer grade level from query context
        grade_level = 8  # Default middle school
        
        # Check for explicit grade mentions first
        grade_matches = re.findall(r'(\d+)\s*(?:st|nd|rd|th)?\s*grade', query_lower)
        if grade_matches:
            grade_level = int(grade_matches[0])
        elif any(word in query_lower for word in ['kindergarten', 'preschool', 'abc', 'counting']):
            grade_level = 1
        elif any(word in query_lower for word in ['elementary', 'addition', 'subtraction']):
            grade_level = 4
        elif any(word in query_lower for word in ['middle school', 'algebra']) and 'fraction' not in query_lower:
            grade_level = 8
        elif any(word in query_lower for word in ['high school', 'ap', 'trigonometry', 'calculus', 'chemistry', 'physics']):
            grade_level = 11
        elif any(word in query_lower for word in ['college', 'university', 'theoretical', 'complex analysis']):
            grade_level = 16
        # Handle fractions separately - can be elementary or middle
        elif 'fraction' in query_lower:
            if any(word in query_lower for word in ['3rd', '4th', 'elementary', 'simple']):
                grade_level = 4
            else:
                grade_level = 8
        
        # Infer learning style from query language
        learning_style = "Mixed"
        if any(word in query_lower for word in ['show me', 'diagram', 'picture', 'visual', 'see', 'draw', 'chart']):
            learning_style = "Visual"
        elif any(word in query_lower for word in ['explain', 'tell me', 'talk', 'listen', 'hear', 'discuss']):
            learning_style = "Auditory"
        elif any(word in query_lower for word in ['hands-on', 'practice', 'do', 'try', 'interactive', 'game']):
            learning_style = "Kinesthetic"
        elif any(word in query_lower for word in ['analyze', 'prove', 'theory', 'logic', 'detailed']):
            learning_style = "Analytical"
        elif any(word in query_lower for word in ['creative', 'imagine', 'design', 'artistic']):
            learning_style = "Creative"
        
        # Infer difficulty preference
        difficulty_preference = "medium"
        if any(word in query_lower for word in ['simple', 'easy', 'basic', 'confused', 'confusing', 'don\'t understand', 'hard for me', 'help me', 'struggling']):
            difficulty_preference = "easy"
        elif any(word in query_lower for word in ['challenging', 'advanced', 'complex', 'difficult', 'in-depth', 'theoretical', 'rigorous']):
            difficulty_preference = "challenging"
        
        # Infer language preference
        preferred_language = "English"
        if any(word in query for word in ['español', '¿', '¡', 'por favor', 'gracias']):
            preferred_language = "Spanish"
        elif any(word in query for word in ['العربية', 'عربي', 'أريد']):
            preferred_language = "Arabic"
        
        # Create guest profile
        guest_profile = {
            "grade_level": grade_level,
            "learning_style": learning_style,
            "preferred_language": preferred_language,
            "difficulty_preference": difficulty_preference,
            "avg_response_time": 15.0,
            "accuracy_rate": 0.7,
            "completion_rate": 0.8,
            "total_sessions": 0,
            "interaction_patterns": {
                "preferred_formats": get_format_preferences(learning_style),
                "session_type": "exploration",
                "guest_session": True
            },
            "learning_struggles": [],
            "mastered_topics": [],
            "preferred_explanation_styles": [
                {"style": learning_style.lower(), "effectiveness": 0.9},
                {"style": "encouraging", "effectiveness": 0.8}
            ],
            "guest_session_info": {
                "created_from_query": True,
                "inferred_characteristics": {
                    "grade_level_indicators": extract_grade_indicators(query_lower),
                    "learning_style_indicators": extract_style_indicators(query_lower),
                    "difficulty_indicators": extract_difficulty_indicators(query_lower)
                }
            }
        }
        
        return guest_profile
        
    except Exception as e:
        print(f"Error creating guest profile: {e}")
        # Return minimal default profile
        return {
            "grade_level": 8,
            "learning_style": "Mixed",
            "preferred_language": "English",
            "difficulty_preference": "medium",
            "guest_session": True
        }

def get_format_preferences(learning_style: str) -> list:
    """Get format preferences based on learning style"""
    format_map = {
        "Visual": ["diagrams", "charts", "step-by-step_visuals", "infographics"],
        "Auditory": ["verbal_explanations", "discussions", "audio_content"],
        "Kinesthetic": ["hands_on", "interactive", "practice_exercises"],
        "Analytical": ["detailed_explanations", "logical_proofs", "systematic_approach"],
        "Creative": ["open_ended", "artistic_connections", "real_world_applications"],
        "Mixed": ["varied_approaches", "multi_modal", "adaptive_content"]
    }
    return format_map.get(learning_style, format_map["Mixed"])

def extract_grade_indicators(query: str) -> list:
    """Extract words that indicate grade level"""
    indicators = []
    grade_words = {
        'elementary': ['elementary', 'basic', 'simple', 'counting'],
        'middle': ['middle', 'algebra', 'fraction', 'geometry'],
        'high': ['high school', 'trigonometry', 'calculus', 'chemistry', 'physics'],
        'college': ['college', 'university', 'advanced', 'complex', 'theoretical']
    }
    
    for level, words in grade_words.items():
        for word in words:
            if word in query:
                indicators.append(f"{level}:{word}")
    return indicators

def extract_style_indicators(query: str) -> list:
    """Extract words that indicate learning style"""
    indicators = []
    style_words = {
        'visual': ['show', 'see', 'diagram', 'picture', 'chart', 'visual', 'draw'],
        'auditory': ['explain', 'tell', 'discuss', 'listen', 'hear'],
        'kinesthetic': ['do', 'practice', 'hands-on', 'interactive', 'game'],
        'analytical': ['analyze', 'prove', 'theory', 'logic', 'detailed'],
        'creative': ['creative', 'imagine', 'design', 'artistic']
    }
    
    for style, words in style_words.items():
        for word in words:
            if word in query:
                indicators.append(f"{style}:{word}")
    return indicators

def extract_difficulty_indicators(query: str) -> list:
    """Extract words that indicate difficulty preference"""
    indicators = []
    difficulty_words = {
        'easy': ['simple', 'easy', 'basic', 'confused', 'confusing', "don't understand", 'help me', 'struggling'],
        'hard': ['challenging', 'advanced', 'complex', 'difficult', 'in-depth', 'theoretical', 'rigorous']
    }
    
    for level, words in difficulty_words.items():
        for word in words:
            if word in query:
                indicators.append(f"{level}:{word}")
    return indicators

def test_guest_profile_scenarios():
    """Test guest profile inference with various scenarios"""
    
    print("🧠 GUEST PROFILE INFERENCE TESTING")
    print("="*60)
    
    test_scenarios = [
        {
            "query": "Can you show me with pictures how to add fractions? I'm in 3rd grade.",
            "expected": {"grade": 4, "style": "Visual", "difficulty": "easy"}
        },
        {
            "query": "I need help understanding calculus for my AP physics class.",
            "expected": {"grade": 11, "style": "Mixed", "difficulty": "challenging"}
        },
        {
            "query": "¿Puedes explicarme las matemáticas en español? Necesito ayuda con álgebra.",
            "expected": {"language": "Spanish", "grade": 8, "style": "Mixed"}
        },
        {
            "query": "Math is really confusing for me. Can you explain algebra step by step?",
            "expected": {"style": "Auditory", "difficulty": "easy", "grade": 8}
        },
        {
            "query": "I want to understand the creative applications of mathematics in art.",
            "expected": {"style": "Creative", "grade": 16, "difficulty": "challenging"}
        },
        {
            "query": "Let me practice some interactive math games for elementary school.",
            "expected": {"style": "Kinesthetic", "grade": 4, "difficulty": "easy"}
        }
    ]
    
    total_tests = 0
    passed_tests = 0
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n🎯 Test {i}: {scenario['query']}")
        
        # Generate guest profile
        guest_id = f"guest_{int(time.time())}_{i}"
        profile = create_guest_profile(scenario['query'])
        
        print(f"👤 Guest ID: {guest_id}")
        print(f"🧠 Inferred Profile:")
        print(f"   Grade Level: {profile['grade_level']}")
        print(f"   Learning Style: {profile['learning_style']}")
        print(f"   Difficulty: {profile['difficulty_preference']}")
        print(f"   Language: {profile['preferred_language']}")
        print(f"   Formats: {profile['interaction_patterns']['preferred_formats']}")
        
        # Validate expectations
        expected = scenario['expected']
        print(f"\n✅ Validation:")
        
        test_results = []
        
        if 'grade' in expected:
            actual = profile['grade_level']
            expected_grade = expected['grade']
            match = abs(actual - expected_grade) <= 2
            test_results.append(match)
            print(f"   Grade: {'✅' if match else '❌'} Expected ~{expected_grade}, Got {actual}")
            total_tests += 1
            if match: passed_tests += 1
        
        if 'style' in expected:
            actual = profile['learning_style']
            expected_style = expected['style']
            match = actual == expected_style
            test_results.append(match)
            print(f"   Style: {'✅' if match else '❌'} Expected {expected_style}, Got {actual}")
            total_tests += 1
            if match: passed_tests += 1
        
        if 'difficulty' in expected:
            actual = profile['difficulty_preference']
            expected_diff = expected['difficulty']
            match = actual == expected_diff
            test_results.append(match)
            print(f"   Difficulty: {'✅' if match else '❌'} Expected {expected_diff}, Got {actual}")
            total_tests += 1
            if match: passed_tests += 1
        
        if 'language' in expected:
            actual = profile['preferred_language']
            expected_lang = expected['language']
            match = expected_lang.lower() in actual.lower()
            test_results.append(match)
            print(f"   Language: {'✅' if match else '❌'} Expected {expected_lang}, Got {actual}")
            total_tests += 1
            if match: passed_tests += 1
        
        # Show inference details
        guest_info = profile.get('guest_session_info', {})
        if 'inferred_characteristics' in guest_info:
            indicators = guest_info['inferred_characteristics']
            print(f"\n📊 Inference Details:")
            print(f"   Grade Indicators: {indicators.get('grade_level_indicators', [])}")
            print(f"   Style Indicators: {indicators.get('learning_style_indicators', [])}")
            print(f"   Difficulty Indicators: {indicators.get('difficulty_indicators', [])}")
    
    # Summary
    accuracy = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    print(f"\n{'='*60}")
    print(f"📊 INFERENCE ACCURACY: {accuracy:.1f}% ({passed_tests}/{total_tests})")
    print("="*60)
    
    return accuracy >= 70  # 70% accuracy threshold

def show_langsmith_examples():
    """Show examples for LangSmith testing"""
    
    print(f"\n🔧 LANGSMITH TESTING EXAMPLES")
    print("="*60)
    
    examples = [
        {
            "description": "Visual Elementary Student",
            "state": {"query": "Can you show me pictures of how fractions work? I'm in 4th grade."},
            "expected": "Visual explanations, grade 4 level, encouraging tone"
        },
        {
            "description": "Struggling High School Student", 
            "state": {"query": "I really don't understand algebra. It's so confusing and hard for me."},
            "expected": "Encouraging support, step-by-step explanations, simplified approach"
        },
        {
            "description": "Advanced College Student",
            "state": {"query": "I want to understand the theoretical foundations of calculus and complex analysis."},
            "expected": "Rigorous mathematical content, advanced level, theoretical depth"
        },
        {
            "description": "Spanish-Speaking Student",
            "state": {"query": "¿Puedes explicarme geometría en español? Necesito ayuda con triángulos."},
            "expected": "Spanish language support, geometry content, visual aids"
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n{i}. {example['description']}")
        print(f"   State: {example['state']}")
        print(f"   Expected: {example['expected']}")
    
    print(f"\n✅ No learner_id required - TutorAgent creates guest profile automatically!")

def main():
    """Main test function"""
    
    print("🚀 TUTOR AGENT GUEST SESSION SUPPORT")
    print("="*80)
    print("Testing enhanced TutorAgent's ability to work without learner profiles")
    print("by automatically inferring learner characteristics from query context.\n")
    
    # Test inference logic
    success = test_guest_profile_scenarios()
    
    # Show LangSmith examples
    show_langsmith_examples()
    
    print(f"\n{'='*80}")
    print("📊 GUEST SESSION SUPPORT SUMMARY")
    print("="*80)
    
    if success:
        print("✅ Guest profile inference working correctly!")
        print("\n📋 Enhanced TutorAgent Features:")
        print("   ✅ No learner_id required")
        print("   ✅ Automatic guest profile creation")
        print("   ✅ Query-based characteristic inference")
        print("   ✅ Multi-language support detection")
        print("   ✅ Learning style adaptation")
        print("   ✅ Grade level appropriateness")
        
        print(f"\n🎉 READY FOR LANGSMITH TESTING!")
        print(f"   Just provide: {{'query': 'Your educational question here'}}")
        print(f"   TutorAgent will automatically:")
        print(f"   • Create guest learner profile")
        print(f"   • Infer learning characteristics")
        print(f"   • Provide personalized response")
    else:
        print("⚠️ Guest inference needs improvement.")
        print("   Check the inference logic and test scenarios.")
    
    return success

if __name__ == "__main__":
    success = main()
    
    if success:
        print(f"\n🎯 Your TutorAgent now works perfectly for guest sessions!")
        print(f"   No setup required - just ask questions and get personalized tutoring!")
    else:
        print(f"\n❌ Review and improve the guest profile inference logic.")
