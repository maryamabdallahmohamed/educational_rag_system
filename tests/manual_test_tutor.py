"""
Manual Test Script for TutorAgent with LangSmith Tracing

This script tests the TutorAgent with various learner scenarios.
Each test demonstrates different tutoring capabilities and personalization features.

Usage:
    python tests/manual_test_tutor.py [scenario_number]
    
    Without scenario number: Runs all scenarios
    With scenario number (1-6): Runs specific scenario

Requirements:
    - Set up your .env file with database and API keys
    - Optional: Enable LangSmith tracing for viewing traces

Examples:
    python tests/manual_test_tutor.py        # Run all scenarios
    python tests/manual_test_tutor.py 1      # Run scenario 1 only
    python tests/manual_test_tutor.py 4      # Run scenario 4 only
"""
import asyncio
import sys
import os
import uuid
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from backend.core.agents.tutor_agent import TutorAgent
from backend.database.db import NeonDatabase
from backend.database.repositories.learner_profile_repo import LearnerProfileRepository
from backend.database.models.learner_profile import LearnerProfile
from backend.utils.langsmith_config import is_langsmith_enabled, get_langsmith_project


# Test Scenarios
SCENARIOS = {
    1: {
        "name": "Visual Learner - Photosynthesis",
        "description": "Testing personalized explanation for visual learner",
        "state": {
            "query": "Explain photosynthesis to me",
            "learner_id": str(uuid.uuid4()),  # Generate valid UUID
            "learner_profile": {
                "grade_level": 8,
                "learning_style": "Visual",
                "difficulty_preference": "medium",
                "accuracy_rate": 0.72,
                "preferred_explanation_styles": ["visual", "diagrams"]
            }
        }
    },
    2: {
        "name": "Struggling Learner - Fractions",
        "description": "Testing adaptation for struggling learner",
        "state": {
            "query": "I don't understand fractions at all",
            "learner_id": str(uuid.uuid4()),  # Generate valid UUID
            "learner_profile": {
                "grade_level": 5,
                "learning_style": "Kinesthetic",
                "accuracy_rate": 0.45,
                "difficulty_preference": "easy",
                "learning_struggles": ["Fractions", "Division"]
            }
        }
    },
    3: {
        "name": "Advanced Learner - Calculus",
        "description": "Testing advanced content for high-performing learner",
        "state": {
            "query": "Explain the fundamental theorem of calculus",
            "learner_id": str(uuid.uuid4()),  # Generate valid UUID
            "learner_profile": {
                "grade_level": 12,
                "accuracy_rate": 0.92,
                "difficulty_preference": "hard",
                "mastered_topics": ["Algebra", "Geometry", "Trigonometry"],
                "learning_style": "Analytical"
            }
        }
    },
    4: {
        "name": "Practice Generation - Quadratic Equations",
        "description": "Testing practice problem generation",
        "state": {
            "query": "Give me practice problems on quadratic equations",
            "learner_id": str(uuid.uuid4()),  # Generate valid UUID
            "learner_profile": {
                "grade_level": 10,
                "accuracy_rate": 0.75,
                "difficulty_preference": "medium",
                "learning_style": "Practical"
            }
        }
    },
    5: {
        "name": "Step-by-Step Explanation",
        "description": "Testing detailed step-by-step problem solving",
        "state": {
            "query": "Show me step-by-step how to solve x² + 5x + 6 = 0",
            "learner_id": str(uuid.uuid4()),  # Generate valid UUID
            "learner_profile": {
                "grade_level": 9,
                "preferred_explanation_styles": ["step-by-step", "visual"],
                "learning_style": "Sequential",
                "accuracy_rate": 0.68
            }
        }
    },
    6: {
        "name": "Content Adaptation - Simplification",
        "description": "Testing content simplification request",
        "state": {
            "query": "This topic is too complicated. Can you make it simpler?",
            "learner_id": str(uuid.uuid4()),  # Generate valid UUID
            "learner_profile": {
                "grade_level": 7,
                "accuracy_rate": 0.55,
                "difficulty_preference": "easy",
                "learning_style": "Visual",
                "learning_struggles": ["Complex Concepts", "Abstract Thinking"]
            }
        }
    }
}


async def setup_test_learner_profiles():
    """Create test learner profiles in the database for testing"""
    print("\n🔧 Setting up test learner profiles...")
    
    try:
        db = NeonDatabase()
        engine = db.init()
        
        async with engine.begin() as conn:
            profile_repo = LearnerProfileRepository(conn)
            
            # Create profiles for each scenario
            for scenario_num, scenario in SCENARIOS.items():
                learner_id = uuid.UUID(scenario['state']['learner_id'])
                profile_data = scenario['state']['learner_profile']
                
                # Check if profile already exists
                try:
                    existing_profile = await profile_repo.get_by_id(learner_id)
                    if existing_profile:
                        print(f"   ✓ Profile for scenario {scenario_num} already exists")
                        continue
                except:
                    pass
                
                # Create new profile
                new_profile = LearnerProfile(
                    id=learner_id,
                    grade_level=profile_data.get('grade_level', 8),
                    learning_style=profile_data.get('learning_style'),
                    difficulty_preference=profile_data.get('difficulty_preference'),
                    accuracy_rate=profile_data.get('accuracy_rate', 0.0),
                    preferred_explanation_styles=profile_data.get('preferred_explanation_styles'),
                    learning_struggles=profile_data.get('learning_struggles'),
                    mastered_topics=profile_data.get('mastered_topics')
                )
                
                await profile_repo.create(new_profile)
                print(f"   ✓ Created profile for scenario {scenario_num}: {scenario['name']}")
        
        print("✅ Test learner profiles ready\n")
        return True
        
    except Exception as e:
        print(f"❌ Error setting up test profiles: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_scenario(scenario_num: int, tutor_agent: TutorAgent):
    """Run a single test scenario"""
    scenario = SCENARIOS[scenario_num]
    
    print("\n" + "=" * 80)
    print(f"📚 SCENARIO {scenario_num}: {scenario['name']}")
    print("=" * 80)
    print(f"Description: {scenario['description']}")
    print(f"\nQuery: \"{scenario['state']['query']}\"")
    print(f"\nLearner Profile:")
    profile = scenario['state']['learner_profile']
    for key, value in profile.items():
        print(f"  - {key}: {value}")
    print("\n" + "-" * 80)
    print("Processing...")
    
    start_time = datetime.now()
    
    try:
        # Process the query
        result_state = await tutor_agent.process(scenario['state'])
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Display results
        print("\n✅ Response Generated Successfully")
        print(f"⏱️  Duration: {duration:.2f}s")
        print("\n" + "-" * 80)
        print("📝 TUTOR RESPONSE:")
        print("-" * 80)
        print(result_state.get("answer", "No response generated"))
        print("-" * 80)
        
        # Show session info if available
        if result_state.get("tutoring_session_id"):
            print(f"\n🔗 Session ID: {result_state['tutoring_session_id']}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_scenarios():
    """Run all test scenarios"""
    print("\n" + "=" * 80)
    print("🎓 TUTOR AGENT MANUAL TESTING SUITE")
    print("=" * 80)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check LangSmith status
    if is_langsmith_enabled():
        print(f"\n🔍 LangSmith Tracing: ENABLED")
        print(f"   Project: {get_langsmith_project()}")
        print(f"   View traces at: https://smith.langchain.com")
    else:
        print(f"\n📊 LangSmith Tracing: DISABLED")
        print(f"   (Set LANGCHAIN_TRACING_V2=true to enable)")
    
    # Initialize database
    print("\n🔧 Initializing database connection...")
    try:
        NeonDatabase.init()
        print("✅ Database connected")
        
        # Setup test learner profiles
        await setup_test_learner_profiles()
        
    except Exception as e:
        print(f"⚠️  Database initialization issue: {e}")
        print("   (Some features may not work without database)")
    
    # Initialize TutorAgent
    print("\n🤖 Initializing TutorAgent...")
    tutor_agent = TutorAgent()
    print("✅ TutorAgent ready")
    
    # Run all scenarios
    results = {}
    for scenario_num in sorted(SCENARIOS.keys()):
        success = await run_scenario(scenario_num, tutor_agent)
        results[scenario_num] = success
        
        # Small delay between scenarios
        if scenario_num < max(SCENARIOS.keys()):
            print("\n⏸️  Pausing for 2 seconds...\n")
            await asyncio.sleep(2)
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    passed = sum(1 for success in results.values() if success)
    total = len(results)
    print(f"Scenarios Run: {total}")
    print(f"Successful: {passed}")
    print(f"Failed: {total - passed}")
    
    if is_langsmith_enabled():
        print(f"\n🔍 View all traces at:")
        print(f"   https://smith.langchain.com/o/default/projects/p/{get_langsmith_project()}")
    
    print("\n✨ Testing Complete!")
    print("=" * 80 + "\n")
    
    return passed == total


def print_usage():
    """Print usage information"""
    print("\n" + "=" * 80)
    print("🎓 TUTOR AGENT MANUAL TEST SCENARIOS")
    print("=" * 80)
    print("\nAvailable Scenarios:")
    for num, scenario in SCENARIOS.items():
        print(f"\n  {num}. {scenario['name']}")
        print(f"     {scenario['description']}")
    
    print("\n" + "-" * 80)
    print("Usage:")
    print("  python tests/manual_test_tutor.py           # Run all scenarios")
    print("  python tests/manual_test_tutor.py [1-6]     # Run specific scenario")
    print("  python tests/manual_test_tutor.py --help    # Show this help")
    print("=" * 80 + "\n")


async def main():
    """Main entry point"""
    # Check for help flag
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h', 'help']:
        print_usage()
        return
    
    # Check for specific scenario
    if len(sys.argv) > 1:
        try:
            scenario_num = int(sys.argv[1])
            if scenario_num not in SCENARIOS:
                print(f"\n❌ Error: Invalid scenario number: {scenario_num}")
                print(f"   Valid scenarios are: {', '.join(map(str, SCENARIOS.keys()))}")
                print_usage()
                return
            
            # Initialize
            print(f"\n🎓 Running Scenario {scenario_num} Only")
            if is_langsmith_enabled():
                print(f"🔍 LangSmith Tracing: ENABLED")
                print(f"   View at: https://smith.langchain.com")
            
            NeonDatabase.init()
            
            # Setup test learner profiles
            await setup_test_learner_profiles()
            
            tutor_agent = TutorAgent()
            
            # Run single scenario
            success = await run_scenario(scenario_num, tutor_agent)
            
            if success:
                print(f"\n✅ Scenario {scenario_num} completed successfully!")
            else:
                print(f"\n❌ Scenario {scenario_num} failed!")
                sys.exit(1)
                
        except ValueError:
            print(f"\n❌ Error: '{sys.argv[1]}' is not a valid scenario number")
            print_usage()
            return
    else:
        # Run all scenarios
        success = await run_all_scenarios()
        if not success:
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
