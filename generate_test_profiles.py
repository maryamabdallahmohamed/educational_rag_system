#!/usr/bin/env python3
"""
Test Learner Profile Generator for TutorAgent Testing

This script generates diverse, realistic learner profiles in the database
to comprehensively test the TutorAgent's personalization capabilities.
"""

import asyncio
import sys
import os
from uuid import uuid4
from datetime import datetime, timedelta
import random

# Add the backend to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.database.db import NeonDatabase
from backend.database.repositories.learner_profile_repo import LearnerProfileRepository
from backend.database.repositories.tutoring_session_repo import TutoringSessionRepository
from backend.database.repositories.learner_interaction_repo import LearnerInteractionRepository

class TestProfileGenerator:
    """Generates comprehensive test learner profiles for TutorAgent testing"""
    
    def __init__(self):
        self.profile_repo = None
        self.session_repo = None
        self.interaction_repo = None
        self.created_profiles = []

    async def setup_repositories(self, session):
        """Initialize repositories with database session"""
        self.profile_repo = LearnerProfileRepository(session)
        self.session_repo = TutoringSessionRepository(session)
        self.interaction_repo = LearnerInteractionRepository(session)

    async def generate_test_profiles(self, session):
        """Generate diverse test learner profiles"""
        
        print("🎯 Generating Test Learner Profiles...")
        print("="*60)
        
        # Define 8 diverse learner archetypes
        profiles_data = [
            # 1. Visual Learner - High Performer
            {
                "name": "Emma Visual",
                "grade_level": 10,
                "learning_style": "Visual",
                "preferred_language": "en",
                "difficulty_preference": "medium",
                "avg_response_time": 8.5,
                "accuracy_rate": 0.87,
                "completion_rate": 0.92,
                "total_sessions": 15,
                "interaction_patterns": {
                    "preferred_formats": ["diagrams", "charts", "infographics", "visual_aids"],
                    "engagement_times": ["morning", "afternoon"],
                    "session_length_preference": "30-45 minutes",
                    "attention_span": "good",
                    "response_to_visuals": "excellent"
                },
                "learning_struggles": [],
                "mastered_topics": [
                    {
                        "topic": "Linear Equations", 
                        "mastery_level": "expert", 
                        "date_mastered": "2024-09-15",
                        "confidence": 0.95
                    },
                    {
                        "topic": "Geometry Basics", 
                        "mastery_level": "proficient", 
                        "date_mastered": "2024-10-01",
                        "confidence": 0.82
                    }
                ],
                "preferred_explanation_styles": [
                    {"style": "visual_step_by_step", "effectiveness": 0.95},
                    {"style": "diagram_based", "effectiveness": 0.91},
                    {"style": "color_coded", "effectiveness": 0.88}
                ]
            },
            
            # 2. Struggling Learner - Needs Support
            {
                "name": "Marcus Struggling",
                "grade_level": 8,
                "learning_style": "Kinesthetic",
                "preferred_language": "en", 
                "difficulty_preference": "easy",
                "avg_response_time": 25.3,
                "accuracy_rate": 0.42,
                "completion_rate": 0.65,
                "total_sessions": 8,
                "interaction_patterns": {
                    "preferred_formats": ["hands_on", "interactive", "games", "real_world_examples"],
                    "engagement_times": ["afternoon", "evening"],
                    "session_length_preference": "15-20 minutes",
                    "break_frequency": "every_10_minutes",
                    "motivation_needed": "high",
                    "confidence_level": "low"
                },
                "learning_struggles": [
                    {
                        "topic": "Fractions", 
                        "struggle_type": "conceptual_understanding", 
                        "severity": "high", 
                        "identified_date": "2024-09-20",
                        "support_strategies": ["visual_models", "real_world_examples"]
                    },
                    {
                        "topic": "Word Problems", 
                        "struggle_type": "reading_comprehension", 
                        "severity": "medium", 
                        "identified_date": "2024-10-05",
                        "support_strategies": ["breaking_down_steps", "vocabulary_support"]
                    }
                ],
                "mastered_topics": [
                    {
                        "topic": "Basic Addition", 
                        "mastery_level": "proficient", 
                        "date_mastered": "2024-08-10",
                        "confidence": 0.78
                    }
                ],
                "preferred_explanation_styles": [
                    {"style": "very_simple", "effectiveness": 0.85},
                    {"style": "encouraging", "effectiveness": 0.82},
                    {"style": "hands_on_examples", "effectiveness": 0.79}
                ]
            },
            
            # 3. Advanced Learner - Accelerated
            {
                "name": "Sophia Advanced",
                "grade_level": 12,
                "learning_style": "Analytical",
                "preferred_language": "en",
                "difficulty_preference": "challenging", 
                "avg_response_time": 12.1,
                "accuracy_rate": 0.94,
                "completion_rate": 0.98,
                "total_sessions": 22,
                "interaction_patterns": {
                    "preferred_formats": ["detailed_explanations", "proofs", "research_based", "theoretical"],
                    "engagement_times": ["evening", "night"],
                    "session_length_preference": "60+ minutes",
                    "depth_preference": "comprehensive",
                    "challenge_seeking": "high"
                },
                "learning_struggles": [
                    {
                        "topic": "Staying Engaged", 
                        "struggle_type": "boredom_with_basics", 
                        "severity": "low", 
                        "identified_date": "2024-09-12",
                        "support_strategies": ["advanced_problems", "extension_activities"]
                    }
                ],
                "mastered_topics": [
                    {
                        "topic": "Calculus I", 
                        "mastery_level": "expert", 
                        "date_mastered": "2024-08-01",
                        "confidence": 0.96
                    },
                    {
                        "topic": "Statistics", 
                        "mastery_level": "expert", 
                        "date_mastered": "2024-09-10",
                        "confidence": 0.94
                    },
                    {
                        "topic": "Linear Algebra", 
                        "mastery_level": "proficient", 
                        "date_mastered": "2024-10-01",
                        "confidence": 0.89
                    }
                ],
                "preferred_explanation_styles": [
                    {"style": "rigorous_mathematical", "effectiveness": 0.95},
                    {"style": "proof_based", "effectiveness": 0.92},
                    {"style": "challenging_extensions", "effectiveness": 0.90}
                ]
            },
            
            # 4. Auditory Learner - Moderate
            {
                "name": "James Auditory", 
                "grade_level": 9,
                "learning_style": "Auditory",
                "preferred_language": "en",
                "difficulty_preference": "medium",
                "avg_response_time": 15.7,
                "accuracy_rate": 0.73,
                "completion_rate": 0.81,
                "total_sessions": 12,
                "interaction_patterns": {
                    "preferred_formats": ["verbal_explanations", "discussions", "audio_content", "read_aloud"],
                    "engagement_times": ["morning", "evening"], 
                    "session_length_preference": "30-45 minutes",
                    "learning_through": "listening_and_talking",
                    "note_taking": "minimal"
                },
                "learning_struggles": [
                    {
                        "topic": "Graph Interpretation", 
                        "struggle_type": "visual_spatial_processing", 
                        "severity": "medium", 
                        "identified_date": "2024-09-25",
                        "support_strategies": ["verbal_descriptions", "step_by_step_narration"]
                    }
                ],
                "mastered_topics": [
                    {
                        "topic": "Quadratic Equations", 
                        "mastery_level": "proficient", 
                        "date_mastered": "2024-09-01",
                        "confidence": 0.81
                    }
                ],
                "preferred_explanation_styles": [
                    {"style": "conversational", "effectiveness": 0.89},
                    {"style": "verbal_step_by_step", "effectiveness": 0.85},
                    {"style": "discussion_based", "effectiveness": 0.83}
                ]
            },
            
            # 5. ESL Learner - Language Support Needed
            {
                "name": "Maria ESL",
                "grade_level": 7, 
                "learning_style": "Visual",
                "preferred_language": "es",  # Spanish
                "difficulty_preference": "easy",
                "avg_response_time": 22.4,
                "accuracy_rate": 0.58,
                "completion_rate": 0.72,
                "total_sessions": 6,
                "interaction_patterns": {
                    "preferred_formats": ["bilingual_support", "visual_aids", "simple_language", "translated_content"],
                    "engagement_times": ["afternoon"],
                    "session_length_preference": "20-30 minutes",
                    "language_support_needed": "high",
                    "vocabulary_level": "developing"
                },
                "learning_struggles": [
                    {
                        "topic": "Mathematical Vocabulary", 
                        "struggle_type": "language_barrier", 
                        "severity": "high", 
                        "identified_date": "2024-10-01",
                        "support_strategies": ["bilingual_explanations", "visual_vocabulary_aids"]
                    },
                    {
                        "topic": "Word Problems", 
                        "struggle_type": "reading_comprehension_english", 
                        "severity": "high", 
                        "identified_date": "2024-10-03",
                        "support_strategies": ["simplified_language", "step_by_step_translation"]
                    }
                ],
                "mastered_topics": [
                    {
                        "topic": "Basic Arithmetic", 
                        "mastery_level": "proficient", 
                        "date_mastered": "2024-09-15",
                        "confidence": 0.76
                    }
                ],
                "preferred_explanation_styles": [
                    {"style": "bilingual", "effectiveness": 0.88},
                    {"style": "visual_with_simple_text", "effectiveness": 0.82},
                    {"style": "culturally_relevant_examples", "effectiveness": 0.79}
                ]
            },
            
            # 6. ADHD Learner - Attention Challenges
            {
                "name": "Alex ADHD",
                "grade_level": 6,
                "learning_style": "Kinesthetic", 
                "preferred_language": "en",
                "difficulty_preference": "medium",
                "avg_response_time": 18.9,
                "accuracy_rate": 0.67,
                "completion_rate": 0.59,
                "total_sessions": 10,
                "interaction_patterns": {
                    "preferred_formats": ["interactive", "gamified", "short_segments", "movement_breaks"],
                    "engagement_times": ["morning"],  # Best focus time
                    "session_length_preference": "10-15 minutes",
                    "break_frequency": "every_5_minutes",
                    "attention_span": "short",
                    "hyperactivity_level": "moderate"
                },
                "learning_struggles": [
                    {
                        "topic": "Sustained Attention", 
                        "struggle_type": "attention_regulation", 
                        "severity": "high", 
                        "identified_date": "2024-09-18",
                        "support_strategies": ["frequent_breaks", "gamification", "movement_integration"]
                    },
                    {
                        "topic": "Multi-step Problems", 
                        "struggle_type": "working_memory", 
                        "severity": "medium", 
                        "identified_date": "2024-09-22",
                        "support_strategies": ["break_into_steps", "visual_organizers"]
                    }
                ],
                "mastered_topics": [
                    {
                        "topic": "Single-digit Multiplication", 
                        "mastery_level": "proficient", 
                        "date_mastered": "2024-09-08",
                        "confidence": 0.73
                    }
                ],
                "preferred_explanation_styles": [
                    {"style": "gamified", "effectiveness": 0.87},
                    {"style": "bite_sized_chunks", "effectiveness": 0.84},
                    {"style": "highly_engaging", "effectiveness": 0.81}
                ]
            },
            
            # 7. Gifted Creative Learner
            {
                "name": "Luna Creative",
                "grade_level": 11,
                "learning_style": "Creative",
                "preferred_language": "en",
                "difficulty_preference": "challenging",
                "avg_response_time": 10.2,
                "accuracy_rate": 0.91,
                "completion_rate": 0.88,
                "total_sessions": 18,
                "interaction_patterns": {
                    "preferred_formats": ["open_ended_problems", "creative_applications", "connections", "artistic_integration"],
                    "engagement_times": ["evening", "night"],
                    "session_length_preference": "45-60 minutes",
                    "creativity_focus": "high",
                    "pattern_recognition": "excellent"
                },
                "learning_struggles": [
                    {
                        "topic": "Repetitive Practice", 
                        "struggle_type": "boredom_with_routine", 
                        "severity": "low", 
                        "identified_date": "2024-09-12",
                        "support_strategies": ["creative_variations", "real_world_applications"]
                    }
                ],
                "mastered_topics": [
                    {
                        "topic": "Trigonometry", 
                        "mastery_level": "expert", 
                        "date_mastered": "2024-08-20",
                        "confidence": 0.93
                    },
                    {
                        "topic": "Pre-Calculus", 
                        "mastery_level": "proficient", 
                        "date_mastered": "2024-09-28",
                        "confidence": 0.88
                    }
                ],
                "preferred_explanation_styles": [
                    {"style": "creative_analogies", "effectiveness": 0.95},
                    {"style": "real_world_connections", "effectiveness": 0.91},
                    {"style": "exploratory_discovery", "effectiveness": 0.89}
                ]
            },
            
            # 8. Returning/Comeback Learner - Knowledge Gaps
            {
                "name": "David Comeback",
                "grade_level": 10,
                "learning_style": "Methodical",
                "preferred_language": "en", 
                "difficulty_preference": "easy",
                "avg_response_time": 28.1,
                "accuracy_rate": 0.51,
                "completion_rate": 0.78,
                "total_sessions": 4,
                "interaction_patterns": {
                    "preferred_formats": ["structured_review", "foundation_building", "confidence_boosting", "patient_pacing"],
                    "engagement_times": ["evening"],
                    "session_length_preference": "30-45 minutes",
                    "review_frequency": "high",
                    "confidence_building_needed": "critical"
                },
                "learning_struggles": [
                    {
                        "topic": "Foundation Skills", 
                        "struggle_type": "knowledge_gaps", 
                        "severity": "high", 
                        "identified_date": "2024-10-10",
                        "support_strategies": ["diagnostic_assessment", "targeted_remediation", "scaffolded_learning"]
                    },
                    {
                        "topic": "Mathematical Confidence", 
                        "struggle_type": "anxiety_and_self_doubt", 
                        "severity": "medium", 
                        "identified_date": "2024-10-10",
                        "support_strategies": ["positive_reinforcement", "success_experiences", "growth_mindset"]
                    }
                ],
                "mastered_topics": [],  # Starting fresh
                "preferred_explanation_styles": [
                    {"style": "patient_and_supportive", "effectiveness": 0.86},
                    {"style": "structured_progression", "effectiveness": 0.83},
                    {"style": "confidence_building", "effectiveness": 0.81}
                ]
            }
        ]
        
        created_profiles = []
        
        for i, profile_data in enumerate(profiles_data, 1):
            print(f"\n📝 Creating Profile {i}: {profile_data['name']}")
            
            try:
                # Create the learner profile
                profile = await self.profile_repo.create_profile(
                    grade_level=profile_data["grade_level"],
                    learning_style=profile_data["learning_style"], 
                    preferred_language=profile_data["preferred_language"],
                    difficulty_preference=profile_data["difficulty_preference"],
                    avg_response_time=profile_data["avg_response_time"],
                    accuracy_rate=profile_data["accuracy_rate"],
                    completion_rate=profile_data["completion_rate"],
                    total_sessions=profile_data["total_sessions"],
                    interaction_patterns=profile_data["interaction_patterns"],
                    learning_struggles=profile_data["learning_struggles"],
                    mastered_topics=profile_data["mastered_topics"],
                    preferred_explanation_styles=profile_data["preferred_explanation_styles"]
                )
                
                created_profiles.append({
                    "id": profile.id,
                    "name": profile_data["name"],
                    "grade_level": profile.grade_level,
                    "learning_style": profile.learning_style,
                    "accuracy_rate": profile.accuracy_rate,
                    "struggles": len(profile_data["learning_struggles"]),
                    "mastered": len(profile_data["mastered_topics"]),
                    "data": profile_data
                })
                
                print(f"   ✅ Created: {profile_data['name']} (ID: {str(profile.id)[:8]}...)")
                print(f"      Grade: {profile.grade_level}, Style: {profile.learning_style}")
                print(f"      Accuracy: {profile.accuracy_rate*100:.1f}%, Sessions: {profile.total_sessions}")
                
            except Exception as e:
                print(f"   ❌ Error creating {profile_data['name']}: {e}")
                
        return created_profiles
    
    async def create_sample_sessions(self, session, profiles):
        """Create sample tutoring sessions for testing"""
        print(f"\n🎯 Creating Sample Tutoring Sessions...")
        print("="*60)
        
        sessions_created = 0
        
        # Create sessions for first 4 profiles to have varied test data
        for profile in profiles[:4]:
            try:
                # Create a tutoring session
                tutoring_session = await self.session_repo.create_session(
                    session, profile["id"]
                )
                
                # Create sample session state based on learner type
                sample_state = self._generate_session_state(profile["data"])
                
                # Update session with realistic state
                updated_session = await self.session_repo.update_session_state(
                    session, tutoring_session.id, sample_state
                )
                
                # Create some sample interactions
                await self._create_sample_interactions(session, tutoring_session.id, profile["data"])
                
                sessions_created += 1
                print(f"   ✅ Session created for {profile['name']} (ID: {str(tutoring_session.id)[:8]}...)")
                
            except Exception as e:
                print(f"   ❌ Error creating session for {profile['name']}: {e}")
        
        print(f"\n📊 Summary: Created {sessions_created} sample sessions with interactions")
        
    def _generate_session_state(self, profile_data):
        """Generate realistic session state based on learner profile"""
        topics = ["Algebra", "Geometry", "Fractions", "Equations", "Graphing"]
        current_topic = random.choice(topics)
        
        return {
            "current_topic": current_topic,
            "difficulty_level": profile_data["difficulty_preference"],
            "session_goals": [
                f"Practice {current_topic}",
                "Build confidence",
                "Address specific struggles"
            ],
            "progress_tracking": {
                "problems_attempted": random.randint(3, 12),
                "problems_correct": random.randint(1, 8),
                "concepts_covered": [current_topic],
                "time_spent_minutes": random.randint(10, 45)
            },
            "personalization_notes": {
                "learning_style_accommodations": profile_data["learning_style"],
                "struggle_areas": [s["topic"] for s in profile_data["learning_struggles"]],
                "preferred_formats": profile_data["interaction_patterns"]["preferred_formats"]
            }
        }
    
    async def _create_sample_interactions(self, session, session_id, profile_data):
        """Create sample interactions for a tutoring session"""
        interactions = [
            {
                "interaction_type": "greeting",
                "query_text": "Hi! I need help with math.",
                "response_text": f"Hello! I'm here to help with {profile_data['learning_style']} learning. What would you like to work on today?",
                "response_time_seconds": random.uniform(2, 5),
                "difficulty_rating": 1,
                "was_helpful": True
            },
            {
                "interaction_type": "question",
                "query_text": "Can you explain fractions to me?",
                "response_text": "I'll explain fractions using your preferred visual learning style with diagrams and examples...",
                "response_time_seconds": random.uniform(8, 15),
                "difficulty_rating": random.randint(2, 4),
                "was_helpful": True
            },
            {
                "interaction_type": "practice",
                "query_text": "Let me try this problem: What is 2/3 + 1/4?",
                "response_text": "Great! Let me guide you through this step by step...",
                "response_time_seconds": random.uniform(10, 25),
                "difficulty_rating": random.randint(3, 5),
                "was_helpful": random.choice([True, True, False])  # Mostly helpful
            }
        ]
        
        for interaction in interactions:
            try:
                await self.interaction_repo.log_interaction(
                    session, session_id, **interaction
                )
            except Exception as e:
                print(f"      Warning: Could not create interaction: {e}")
    
    async def generate_all_test_data(self):
        """Generate all test data - main entry point"""
        print("🚀 GENERATING COMPREHENSIVE TEST DATA FOR TUTOR AGENT")
        print("="*80)
        
        # Initialize database
        NeonDatabase.init()
        session = NeonDatabase.get_session()
        
        try:
            await self.setup_repositories(session)
            
            # Generate learner profiles
            profiles = await self.generate_test_profiles(session)
            
            # Create sample sessions
            await self.create_sample_sessions(session, profiles)
            
            # Save profile information for easy reference
            await self._save_profile_reference(profiles)
            
        finally:
            await session.close()
        
        # Final summary
        print("\n" + "="*80)
        print("✅ TEST DATA GENERATION COMPLETE!")
        print("="*80)
        print(f"📝 Created {len(profiles)} diverse learner profiles:")
        
        for profile in profiles:
            print(f"   • {profile['name']:<15} (Grade {profile['grade_level']}, "
                  f"{profile['learning_style']:<12}, {profile['accuracy_rate']*100:.0f}% accuracy)")
        
        print(f"\n🎯 Test the TutorAgent with these scenarios:")
        print(f"   • High performer (Emma): Visual learning, advanced topics")
        print(f"   • Struggling learner (Marcus): Needs encouragement, simpler explanations")
        print(f"   • Advanced student (Sophia): Challenging problems, theoretical depth")
        print(f"   • ESL learner (Maria): Bilingual support, vocabulary help")
        print(f"   • ADHD learner (Alex): Short sessions, gamification")
        
        print(f"\n🔧 Next Steps:")
        print(f"   1. Run: python tests/manual_test_tutor.py")
        print(f"   2. Test with profile IDs from: test_profile_ids.txt")
        print(f"   3. Observe TutorAgent personalization for each learner type")
        
        return profiles

    async def _save_profile_reference(self, profiles):
        """Save profile IDs and info to reference file"""
        try:
            os.makedirs("tests", exist_ok=True)
            with open("tests/test_profile_ids.txt", "w", encoding='utf-8') as f:
                f.write("# Test Learner Profile IDs for TutorAgent Testing\n")
                f.write(f"# Generated: {datetime.now().isoformat()}\n\n")
                
                for profile in profiles:
                    f.write(f"# {profile['name']} - {profile['data']['learning_style']} Learner\n")
                    f.write(f"{profile['name'].replace(' ', '_').lower()}_id = \"{profile['id']}\"\n")
                    f.write(f"# Grade {profile['grade_level']}, {profile['accuracy_rate']*100:.0f}% accuracy, {profile['struggles']} struggles, {profile['mastered']} mastered topics\n\n")
            
            print(f"\n📄 Profile IDs saved to: tests/test_profile_ids.txt")
            
        except Exception as e:
            print(f"⚠️ Could not save profile reference file: {e}")

async def main():
    """Main function to generate all test data"""
    generator = TestProfileGenerator()
    
    try:
        profiles = await generator.generate_all_test_data()
        print(f"\n🎉 Successfully generated {len(profiles)} test learner profiles!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error generating test data: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Configure Python environment
    import configparser
    
    print("🔧 Setting up environment...")
    
    # Run the generator
    success = asyncio.run(main())
    
    if success:
        print("\n" + "="*80)
        print("🎉 TEST LEARNER PROFILES READY FOR TUTOR AGENT TESTING!")
        print("="*80)
        print("Your database now contains 8 diverse learner profiles representing:")
        print("• High performers, struggling learners, and advanced students")
        print("• Different learning styles (Visual, Auditory, Kinesthetic, etc.)")
        print("• Various challenges (ESL, ADHD, knowledge gaps)")
        print("• Realistic performance metrics and learning histories")
        print("\nUse these profiles to comprehensively test TutorAgent personalization!")
    else:
        print("\n💥 Test data generation failed. Check error messages above.")
