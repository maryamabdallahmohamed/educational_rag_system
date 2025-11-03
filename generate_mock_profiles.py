#!/usr/bin/env python3
"""
Simple Test Profile Generator (Database-Independent)

Creates test learner profile data structures and IDs 
that can be used to test TutorAgent personalization.
This version creates mock profiles without database dependencies.
"""

import os
from uuid import uuid4
from datetime import datetime

class MockProfileGenerator:
    """Generates mock test profiles for TutorAgent testing"""
    
    def generate_test_profiles(self):
        """Generate mock learner profiles with realistic data"""
        
        print("🎯 Generating Mock Test Learner Profiles...")
        print("="*60)
        
        profiles = [
            # 1. Visual Learner - High Performer
            {
                "id": str(uuid4()),
                "name": "Emma Visual",
                "grade_level": 10,
                "learning_style": "Visual",
                "preferred_language": "en",
                "difficulty_preference": "medium",
                "avg_response_time": 8.5,
                "accuracy_rate": 0.87,
                "completion_rate": 0.92,
                "total_sessions": 15,
                "description": "High-performing visual learner who excels with diagrams and charts",
                "test_queries": [
                    "Can you show me how to solve quadratic equations with visual examples?",
                    "I need a diagram to understand the Pythagorean theorem",
                    "Can you draw me a graph of this function?"
                ]
            },
            
            # 2. Struggling Learner - Needs Support
            {
                "id": str(uuid4()),
                "name": "Marcus Struggling", 
                "grade_level": 8,
                "learning_style": "Kinesthetic",
                "preferred_language": "en",
                "difficulty_preference": "easy",
                "avg_response_time": 25.3,
                "accuracy_rate": 0.42,
                "completion_rate": 0.65,
                "total_sessions": 8,
                "description": "Struggling learner who needs encouragement and hands-on examples",
                "test_queries": [
                    "I really don't understand fractions. They're so confusing!",
                    "Math is really hard for me, where should I start?",
                    "Can you make this problem easier to understand?"
                ]
            },
            
            # 3. Advanced Learner - Accelerated
            {
                "id": str(uuid4()),
                "name": "Sophia Advanced",
                "grade_level": 12,
                "learning_style": "Analytical", 
                "preferred_language": "en",
                "difficulty_preference": "challenging",
                "avg_response_time": 12.1,
                "accuracy_rate": 0.94,
                "completion_rate": 0.98,
                "total_sessions": 22,
                "description": "Advanced analytical learner who seeks theoretical depth",
                "test_queries": [
                    "Can you explain the mathematical foundations of integration?",
                    "I want challenging calculus problems to solve",
                    "Show me the theoretical proof behind this theorem"
                ]
            },
            
            # 4. Auditory Learner - Moderate
            {
                "id": str(uuid4()),
                "name": "James Auditory",
                "grade_level": 9,
                "learning_style": "Auditory",
                "preferred_language": "en",
                "difficulty_preference": "medium",
                "avg_response_time": 15.7,
                "accuracy_rate": 0.73,
                "completion_rate": 0.81,
                "total_sessions": 12,
                "description": "Auditory learner who prefers verbal explanations and discussions",
                "test_queries": [
                    "Can you explain this concept out loud to me?",
                    "I learn better when you talk me through the steps",
                    "Let's discuss how this formula works"
                ]
            },
            
            # 5. ESL Learner - Language Support
            {
                "id": str(uuid4()),
                "name": "Maria ESL",
                "grade_level": 7,
                "learning_style": "Visual",
                "preferred_language": "es",
                "difficulty_preference": "easy", 
                "avg_response_time": 22.4,
                "accuracy_rate": 0.58,
                "completion_rate": 0.72,
                "total_sessions": 6,
                "description": "Spanish-speaking visual learner who needs bilingual support",
                "test_queries": [
                    "¿Puedes explicarme las fracciones en español?",
                    "I need help with math vocabulary in simple English",
                    "Can you use easy words to explain this?"
                ]
            },
            
            # 6. ADHD Learner - Special Needs
            {
                "id": str(uuid4()),
                "name": "Alex ADHD",
                "grade_level": 6,
                "learning_style": "Kinesthetic",
                "preferred_language": "en",
                "difficulty_preference": "medium",
                "avg_response_time": 18.9,
                "accuracy_rate": 0.67,
                "completion_rate": 0.59,
                "total_sessions": 10,
                "description": "Kinesthetic learner with ADHD who needs short, engaging sessions",
                "test_queries": [
                    "I have trouble focusing, can you make this fun?",
                    "Can we play a math game instead?",
                    "I need short, simple explanations please"
                ]
            },
            
            # 7. Gifted Creative Learner
            {
                "id": str(uuid4()),
                "name": "Luna Creative",
                "grade_level": 11,
                "learning_style": "Creative",
                "preferred_language": "en",
                "difficulty_preference": "challenging",
                "avg_response_time": 10.2,
                "accuracy_rate": 0.91,
                "completion_rate": 0.88,
                "total_sessions": 18,
                "description": "Creative gifted learner who enjoys open-ended problems",
                "test_queries": [
                    "Can you show me creative ways to solve this problem?",
                    "I want to explore the artistic side of mathematics",
                    "How does this concept connect to real-world applications?"
                ]
            },
            
            # 8. Returning Student - Knowledge Gaps
            {
                "id": str(uuid4()),
                "name": "David Comeback",
                "grade_level": 10,
                "learning_style": "Methodical",
                "preferred_language": "en",
                "difficulty_preference": "easy",
                "avg_response_time": 28.1,
                "accuracy_rate": 0.51,
                "completion_rate": 0.78,
                "total_sessions": 4,
                "description": "Returning student with knowledge gaps who needs confidence building",
                "test_queries": [
                    "I haven't done math in years, where should I start?",
                    "I feel really behind, can you help me catch up?",
                    "Can you be patient with me while I relearn this?"
                ]
            }
        ]
        
        # Display created profiles
        for i, profile in enumerate(profiles, 1):
            print(f"\n📝 Profile {i}: {profile['name']}")
            print(f"   ID: {profile['id'][:8]}...")
            print(f"   Grade: {profile['grade_level']}, Style: {profile['learning_style']}")
            print(f"   Accuracy: {profile['accuracy_rate']*100:.1f}%, Sessions: {profile['total_sessions']}")
            print(f"   Description: {profile['description']}")
        
        return profiles
    
    def save_profile_reference(self, profiles):
        """Save profile information for testing"""
        
        # Create tests directory
        os.makedirs("tests", exist_ok=True)
        
        # Save detailed profile information
        with open("tests/test_profile_ids.txt", "w", encoding='utf-8') as f:
            f.write("# Test Learner Profile IDs for TutorAgent Testing\n")
            f.write(f"# Generated: {datetime.now().isoformat()}\n")
            f.write("# NOTE: These are mock profiles for testing TutorAgent personalization\n\n")
            
            for profile in profiles:
                f.write(f"# {profile['name']} - {profile['learning_style']} Learner\n")
                f.write(f"{profile['name'].replace(' ', '_').lower()}_id = \"{profile['id']}\"\n")
                f.write(f"# Grade {profile['grade_level']}, {profile['accuracy_rate']*100:.0f}% accuracy\n")
                f.write(f"# {profile['description']}\n\n")
        
        # Save test scenarios
        with open("tests/test_scenarios.txt", "w", encoding='utf-8') as f:
            f.write("# Test Scenarios for TutorAgent Personalization Testing\n")
            f.write(f"# Generated: {datetime.now().isoformat()}\n\n")
            
            for i, profile in enumerate(profiles, 1):
                f.write(f"{i}. {profile['name']} ({profile['learning_style']} Learner)\n")
                f.write(f"   Profile ID: {profile['id']}\n")
                f.write(f"   Test Queries:\n")
                for query in profile['test_queries']:
                    f.write(f"     • \"{query}\"\n")
                f.write(f"   Expected: Personalized response for {profile['learning_style'].lower()} learning style\n\n")
        
        print(f"\n📄 Files saved:")
        print(f"   • tests/test_profile_ids.txt - Profile IDs for testing")
        print(f"   • tests/test_scenarios.txt - Suggested test scenarios")

def main():
    """Generate mock test profiles"""
    
    print("🚀 GENERATING MOCK TEST PROFILES FOR TUTOR AGENT")
    print("="*80)
    print("NOTE: These are mock profiles for testing TutorAgent personalization")
    print("without requiring database setup.\n")
    
    generator = MockProfileGenerator()
    
    # Generate profiles
    profiles = generator.generate_test_profiles()
    
    # Save reference files
    generator.save_profile_reference(profiles)
    
    # Display summary
    print(f"\n" + "="*80)
    print("✅ MOCK TEST PROFILES GENERATED!")
    print("="*80)
    print(f"📝 Created {len(profiles)} diverse learner profiles:")
    
    for profile in profiles:
        print(f"   • {profile['name']:<15} ({profile['learning_style']:<12}, "
              f"Grade {profile['grade_level']}, {profile['accuracy_rate']*100:.0f}% accuracy)")
    
    print(f"\n🎯 Testing Instructions:")
    print(f"   1. Use profile IDs from: tests/test_profile_ids.txt") 
    print(f"   2. Test scenarios in: tests/test_scenarios.txt")
    print(f"   3. Run: python quick_test_tutor.py")
    print(f"   4. Observe TutorAgent personalization for each learner type")
    
    print(f"\n🔧 TutorAgent Testing Focus Areas:")
    print(f"   • Visual learners: Should get diagrams, charts, visual explanations")
    print(f"   • Struggling learners: Should get encouragement, simple language") 
    print(f"   • Advanced learners: Should get challenging problems, theory")
    print(f"   • ESL learners: Should get bilingual support, simple vocabulary")
    print(f"   • ADHD learners: Should get short, engaging, gamified responses")
    print(f"   • Creative learners: Should get open-ended, artistic approaches")
    
    print(f"\n🎉 Mock profiles ready for TutorAgent personalization testing!")
    
    return profiles

if __name__ == "__main__":
    main()
