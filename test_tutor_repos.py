"""
Simple test script to verify the new Tutor Agent repositories work correctly.
Run this after database initialization to test basic CRUD operations.
"""
import asyncio
import uuid
from backend.database.db import NeonDatabase
from backend.database.repositories.learner_profile_repo import LearnerProfileRepository
from backend.database.repositories.tutoring_session_repo import TutoringSessionRepository
from backend.database.repositories.learner_interaction_repo import LearnerInteractionRepository

async def test_repositories():
    """Test basic operations for all new repositories"""
    print("🧪 Testing Tutor Agent repositories...\n")
    
    async with NeonDatabase.get_session() as session:
        # Initialize repositories
        profile_repo = LearnerProfileRepository(session)
        session_repo = TutoringSessionRepository(session)
        interaction_repo = LearnerInteractionRepository(session)
        
        try:
            # Test 1: Create learner profile
            print("1️⃣ Testing LearnerProfile creation...")
            profile = await profile_repo.create_profile(
                grade_level=8,
                learning_style="visual",
                preferred_language="en"
            )
            print(f"   ✅ Created profile: {profile.id}")
            
            # Test 2: Create tutoring session
            print("\n2️⃣ Testing TutoringSession creation...")
            tutoring_session = await session_repo.create_session(
                learner_id=profile.id
            )
            print(f"   ✅ Created session: {tutoring_session.id}")
            
            # Test 3: Log interaction
            print("\n3️⃣ Testing LearnerInteraction logging...")
            interaction = await interaction_repo.log_interaction(
                session_id=tutoring_session.id,
                interaction_type="question",
                query_text="What is 2 + 2?",
                response_text="2 + 2 equals 4. This is basic addition.",
                response_time_seconds=3.5,
                difficulty_rating=2
            )
            print(f"   ✅ Logged interaction: {interaction.id}")
            
            # Test 4: Update performance metrics
            print("\n4️⃣ Testing performance metrics update...")
            updated_profile = await profile_repo.update_performance_metrics(
                profile_id=profile.id,
                new_accuracy=0.85,
                new_response_time=5.2,
                session_completed=True
            )
            print(f"   ✅ Updated metrics - Sessions: {updated_profile.total_sessions}, Accuracy: {updated_profile.accuracy_rate:.2f}")
            
            # Test 5: Update session state
            print("\n5️⃣ Testing session state update...")
            await session_repo.update_session_state(
                session_id=tutoring_session.id,
                state_updates={
                    "current_topic": "basic_arithmetic",
                    "progress_percent": 75,
                    "difficulty_level": "easy"
                }
            )
            print("   ✅ Session state updated")
            
            # Test 6: Add interaction feedback
            print("\n6️⃣ Testing interaction feedback...")
            await interaction_repo.update_feedback(
                interaction_id=interaction.id,
                was_helpful=True,
                difficulty_rating=2
            )
            print("   ✅ Interaction feedback added")
            
            # Test 7: Get session interactions
            print("\n7️⃣ Testing session interactions retrieval...")
            interactions = await interaction_repo.get_session_interactions(tutoring_session.id)
            print(f"   ✅ Found {len(interactions)} interactions in session")
            
            # Test 8: End session
            print("\n8️⃣ Testing session completion...")
            completed_session = await session_repo.end_session(
                session_id=tutoring_session.id,
                performance_summary={
                    "questions_asked": 1,
                    "accuracy_rate": 1.0,
                    "topics_covered": ["basic_arithmetic"],
                    "time_spent_minutes": 5
                }
            )
            print(f"   ✅ Session ended at: {completed_session.ended_at}")
            
            print("\n🎉 All repository tests passed!")
            
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(test_repositories())
