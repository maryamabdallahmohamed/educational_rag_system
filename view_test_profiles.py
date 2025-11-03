#!/usr/bin/env python3
"""
View Test Learner Profiles

This script displays all generated test learner profiles
and their characteristics for TutorAgent testing.
"""

import asyncio
import sys
import os
from uuid import UUID

# Add the backend to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.database.db import NeonDatabase
from backend.database.repositories.learner_profile_repo import LearnerProfileRepository

async def view_all_profiles():
    """View all learner profiles in the database"""
    print("👥 TEST LEARNER PROFILES IN DATABASE")
    print("="*80)
    
    NeonDatabase.init()
    session = NeonDatabase.get_session()
    
    try:
        learner_repo = LearnerProfileRepository(session)
        
        try:
            # Get all profiles (you may need to implement get_all method)
            # For now, let's read from the saved IDs file
            
            if os.path.exists("tests/test_profile_ids.txt"):
                print("📄 Reading saved profile IDs:\n")
                with open("tests/test_profile_ids.txt", "r", encoding='utf-8') as f:
                    content = f.read()
                    print(content)
                
                # Extract IDs and display profile details
                print("\n" + "="*60)
                print("📊 DETAILED PROFILE INFORMATION")
                print("="*60)
                
                lines = content.split('\n')
                profile_lines = [line for line in lines if '_id = "' in line]
                
                for line in profile_lines:
                    try:
                        # Extract profile ID
                        profile_id_str = line.split('"')[1]
                        profile_id = UUID(profile_id_str)
                        
                        # Get profile from database
                        profile = await learner_repo.get_by_id(profile_id)
                        
                        if profile:
                            print(f"\n🎯 Profile: {profile_id_str[:8]}...")
                            print(f"   Grade Level: {profile.grade_level}")
                            print(f"   Learning Style: {profile.learning_style}")
                            print(f"   Language: {profile.preferred_language}")
                            print(f"   Difficulty Preference: {profile.difficulty_preference}")
                            print(f"   Accuracy Rate: {profile.accuracy_rate*100:.1f}%")
                            print(f"   Completion Rate: {profile.completion_rate*100:.1f}%")
                            print(f"   Total Sessions: {profile.total_sessions}")
                            print(f"   Avg Response Time: {profile.avg_response_time:.1f}s")
                            
                            # Show learning struggles
                            if profile.learning_struggles:
                                print(f"   Learning Struggles: {len(profile.learning_struggles)}")
                                for struggle in profile.learning_struggles:
                                    print(f"     • {struggle.get('topic', 'Unknown')} ({struggle.get('severity', 'unknown')} severity)")
                            
                            # Show mastered topics
                            if profile.mastered_topics:
                                print(f"   Mastered Topics: {len(profile.mastered_topics)}")
                                for topic in profile.mastered_topics:
                                    print(f"     • {topic.get('topic', 'Unknown')} ({topic.get('mastery_level', 'unknown')} level)")
                        else:
                            print(f"❌ Profile {profile_id_str[:8]}... not found in database")
                            
                    except Exception as e:
                        print(f"❌ Error processing profile line: {e}")
                        
            else:
                print("❌ No test_profile_ids.txt found.")
                print("   Run 'python generate_test_profiles.py' first to create test profiles.")
                
        except Exception as e:
            print(f"❌ Error accessing database: {e}")
            
    finally:
        await session.close()

async def show_test_scenarios():
    """Show suggested test scenarios"""
    print("\n" + "="*60)
    print("🧪 SUGGESTED TESTING SCENARIOS")
    print("="*60)
    
    scenarios = [
        {
            "scenario": "High-Performing Visual Learner",
            "profile": "Emma Visual",
            "test_queries": [
                "Can you show me how to solve quadratic equations?",
                "I need a visual explanation of the Pythagorean theorem",
                "Draw me a diagram of how fractions work"
            ]
        },
        {
            "scenario": "Struggling Kinesthetic Learner", 
            "profile": "Marcus Struggling",
            "test_queries": [
                "I don't understand fractions at all, can you help?",
                "Math is really hard for me, where should I start?",
                "Can you make this problem easier to understand?"
            ]
        },
        {
            "scenario": "Advanced Analytical Learner",
            "profile": "Sophia Advanced",
            "test_queries": [
                "I want to understand the theoretical foundation of calculus",
                "Can you give me challenging problems to solve?",
                "Explain the mathematical proof behind this theorem"
            ]
        },
        {
            "scenario": "ESL Visual Learner",
            "profile": "Maria ESL", 
            "test_queries": [
                "¿Puedes explicarme las fracciones en español?",
                "I need help with math vocabulary in English",
                "Can you use simple words to explain this?"
            ]
        },
        {
            "scenario": "ADHD Kinesthetic Learner",
            "profile": "Alex ADHD",
            "test_queries": [
                "I have trouble focusing, can you make this fun?",
                "Can we play a math game instead?",
                "I need short, simple explanations please"
            ]
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}. {scenario['scenario']}")
        print(f"   Profile: {scenario['profile']}")
        print(f"   Test Queries:")
        for query in scenario['test_queries']:
            print(f"     • \"{query}\"")

if __name__ == "__main__":
    print("🔍 Viewing Test Learner Profiles...")
    asyncio.run(view_all_profiles())
    asyncio.run(show_test_scenarios())
    
    print(f"\n🎯 To test TutorAgent:")
    print(f"   1. Copy a profile ID from above")
    print(f"   2. Run: python tests/manual_test_tutor.py") 
    print(f"   3. Use the profile ID when prompted")
    print(f"   4. Try the suggested test queries for that learner type")
