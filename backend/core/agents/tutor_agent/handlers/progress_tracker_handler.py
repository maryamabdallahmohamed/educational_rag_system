"""
Progress Tracker Handler

Tracks and reports student learning progress.
This handler provides comprehensive progress reports,
analytics, and learning recommendations.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from .base_tutor_handler import BaseTutorHandler
from backend.core.agents.tutor_agent.tutor_state import TutorState
from backend.database.models.tutor_models import (
    LearnerProfileModel,
    LearnerInteractionModel,
    TopicProgressModel
)
from backend.utils.logger_config import get_logger

logger = get_logger(__name__)


class ProgressTrackerHandler(BaseTutorHandler):
    """
    Tracks and reports student learning progress.
    
    Generates progress reports, visualizes learning journey,
    and provides data-driven recommendations for improvement.
    """
    
    async def handle(
        self, 
        state: TutorState, 
        db_session: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """
        Generate a progress report for the student.
        
        Args:
            state: The current tutor state
            db_session: Database session for loading real statistics
            
        Returns:
            Dictionary containing progress report and recommendations
        """
        try:
            # Generate comprehensive progress report (with DB data if available)
            report = await self._generate_progress_report(state, db_session)
            
            return {
                "response": report["summary"],
                "statistics": report["statistics"],
                "topic_progress": report["topic_progress"],
                "achievements": report["achievements"],
                "recommendations": report["recommendations"],
                "learning_streak": report["learning_streak"],
                "handler": "progress_tracker"
            }
            
        except Exception as e:
            return self._handle_error(e, "generating progress report")
    
    async def _generate_progress_report(
        self, 
        state: TutorState,
        db_session: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive progress report.
        
        Args:
            state: Current tutor state
            db_session: Optional database session for loading real data
            
        Returns:
            Complete progress report
        """
        profile = state.student_profile
        progress = state.learning_progress
        
        # Load real statistics from database if session available
        db_statistics = None
        db_topic_progress = []
        
        if db_session and state.session_id:
            try:
                db_statistics = await self._load_statistics_from_db(
                    db_session, 
                    state.session_id
                )
                db_topic_progress = await self._load_topic_progress_from_db(
                    db_session,
                    state.session_id
                )
            except Exception as e:
                logger.warning(f"Failed to load stats from DB: {e}")
        
        # Calculate statistics (prefer DB data)
        if db_statistics:
            statistics = db_statistics
        else:
            statistics = self._calculate_statistics(profile, progress)
        
        # Get topic-specific progress (prefer DB data)
        if db_topic_progress:
            topic_progress = db_topic_progress
        else:
            topic_progress = self._get_topic_progress(progress)
        
        # Calculate achievements
        achievements = self._calculate_achievements(profile, statistics)
        
        # Generate personalized summary using LLM
        summary = await self._generate_summary(state, statistics, achievements)
        
        # Get recommendations
        recommendations = self._generate_recommendations(statistics, topic_progress)
        
        # Calculate learning streak (placeholder - would need session dates)
        learning_streak = self._calculate_streak(profile)
        
        return {
            "summary": summary,
            "statistics": statistics,
            "topic_progress": topic_progress,
            "achievements": achievements,
            "recommendations": recommendations,
            "learning_streak": learning_streak
        }
    
    async def _load_statistics_from_db(
        self,
        db_session: AsyncSession,
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """Load real statistics from database."""
        try:
            from backend.database.models.tutor_models import TutoringSessionDBModel
            import uuid
            
            session_uuid = uuid.UUID(session_id)
            
            # Get the session and learner info
            result = await db_session.execute(
                select(TutoringSessionDBModel)
                .where(TutoringSessionDBModel.id == session_uuid)
            )
            session_record = result.scalar_one_or_none()
            
            if not session_record or not session_record.learner_id:
                return None
            
            learner_id = session_record.learner_id
            
            # Get learner profile
            profile_result = await db_session.execute(
                select(LearnerProfileModel)
                .where(LearnerProfileModel.id == learner_id)
            )
            learner = profile_result.scalar_one_or_none()
            
            if not learner:
                return None
            
            # Count total interactions (questions)
            interaction_result = await db_session.execute(
                select(func.count(LearnerInteractionModel.id))
                .where(LearnerInteractionModel.session_id.in_(
                    select(TutoringSessionDBModel.id)
                    .where(TutoringSessionDBModel.learner_id == learner_id)
                ))
            )
            total_interactions = interaction_result.scalar() or 0
            
            # Count correct answers from interaction metadata
            correct_result = await db_session.execute(
                select(func.count(LearnerInteractionModel.id))
                .where(
                    LearnerInteractionModel.session_id.in_(
                        select(TutoringSessionDBModel.id)
                        .where(TutoringSessionDBModel.learner_id == learner_id)
                    ),
                    LearnerInteractionModel.was_helpful == True
                )
            )
            correct_count = correct_result.scalar() or 0
            
            # Get topic progress count
            topic_result = await db_session.execute(
                select(func.count(TopicProgressModel.id))
                .where(TopicProgressModel.learner_id == learner_id)
            )
            total_topics = topic_result.scalar() or 0
            
            # Count mastered topics
            mastered_result = await db_session.execute(
                select(func.count(TopicProgressModel.id))
                .where(
                    TopicProgressModel.learner_id == learner_id,
                    TopicProgressModel.mastery_level >= 0.8
                )
            )
            mastered_topics = mastered_result.scalar() or 0
            
            # Calculate accuracy
            accuracy = (correct_count / total_interactions * 100) if total_interactions > 0 else 0
            
            return {
                "total_sessions": learner.total_sessions or 0,
                "total_questions_answered": total_interactions,
                "correct_answers": correct_count,
                "accuracy_percentage": round(accuracy, 1),
                "total_topics_studied": total_topics,
                "topics_mastered": mastered_topics,
                "topics_in_progress": total_topics - mastered_topics,
                "total_time_minutes": 0,
                "current_level": learner.difficulty_preference or "intermediate",
                "strengths_count": len(learner.mastered_topics or []),
                "improvement_areas_count": len(learner.learning_struggles or [])
            }
            
        except Exception as e:
            logger.error(f"Error loading DB statistics: {e}")
            return None
    
    async def _load_topic_progress_from_db(
        self,
        db_session: AsyncSession,
        session_id: str
    ) -> List[Dict[str, Any]]:
        """Load topic progress from database."""
        try:
            from backend.database.models.tutor_models import TutoringSessionDBModel
            import uuid
            
            session_uuid = uuid.UUID(session_id)
            
            # Get learner_id from session
            result = await db_session.execute(
                select(TutoringSessionDBModel.learner_id)
                .where(TutoringSessionDBModel.id == session_uuid)
            )
            learner_id = result.scalar_one_or_none()
            
            if not learner_id:
                return []
            
            # Get all topic progress records
            progress_result = await db_session.execute(
                select(TopicProgressModel)
                .where(TopicProgressModel.learner_id == learner_id)
                .order_by(TopicProgressModel.mastery_level.desc())
            )
            progress_records = progress_result.scalars().all()
            
            topic_list = []
            for tp in progress_records:
                topic_accuracy = (
                    tp.practice_correct / tp.practice_attempts * 100
                    if tp.practice_attempts > 0 else 0
                )
                
                # Determine status
                if tp.mastery_level >= 0.8:
                    status, emoji = "mastered", "🏆"
                elif tp.mastery_level >= 0.5:
                    status, emoji = "progressing", "📈"
                elif tp.mastery_level >= 0.3:
                    status, emoji = "learning", "📚"
                else:
                    status, emoji = "started", "🌱"
                
                topic_list.append({
                    "topic_id": tp.topic_id,
                    "topic_name": tp.topic_name,
                    "mastery_level": round(tp.mastery_level * 100, 1),
                    "accuracy": round(topic_accuracy, 1),
                    "attempts": tp.practice_attempts,
                    "time_spent": tp.time_spent_minutes,
                    "status": status,
                    "emoji": emoji,
                    "concepts_mastered": len(tp.concepts_mastered or []),
                    "concepts_struggling": tp.concepts_struggling or []
                })
            
            return topic_list
            
        except Exception as e:
            logger.error(f"Error loading topic progress from DB: {e}")
            return []
    
    def _calculate_statistics(
        self, 
        profile, 
        progress: Dict
    ) -> Dict[str, Any]:
        """Calculate overall learning statistics."""
        
        total_questions = profile.total_questions_answered
        correct = profile.correct_answers
        accuracy = (correct / total_questions * 100) if total_questions > 0 else 0
        
        total_topics = len(progress)
        mastered_topics = sum(
            1 for p in progress.values() 
            if p.mastery_level >= 0.8
        )
        in_progress_topics = sum(
            1 for p in progress.values() 
            if 0.3 <= p.mastery_level < 0.8
        )
        
        total_time = sum(p.time_spent_minutes for p in progress.values())
        
        return {
            "total_sessions": profile.total_sessions,
            "total_questions_answered": total_questions,
            "correct_answers": correct,
            "accuracy_percentage": round(accuracy, 1),
            "total_topics_studied": total_topics,
            "topics_mastered": mastered_topics,
            "topics_in_progress": in_progress_topics,
            "total_time_minutes": total_time,
            "current_level": profile.current_level,
            "strengths_count": len(profile.strengths),
            "improvement_areas_count": len(profile.areas_for_improvement)
        }
    
    def _get_topic_progress(self, progress: Dict) -> List[Dict[str, Any]]:
        """Get progress details for each topic."""
        topic_list = []
        
        for topic_id, topic_progress in progress.items():
            topic_accuracy = (
                topic_progress.practice_correct / topic_progress.practice_attempts * 100
                if topic_progress.practice_attempts > 0 else 0
            )
            
            # Determine status based on mastery level
            if topic_progress.mastery_level >= 0.8:
                status = "mastered"
                emoji = "🏆"
            elif topic_progress.mastery_level >= 0.5:
                status = "progressing"
                emoji = "📈"
            elif topic_progress.mastery_level >= 0.3:
                status = "learning"
                emoji = "📚"
            else:
                status = "started"
                emoji = "🌱"
            
            topic_list.append({
                "topic_id": topic_id,
                "topic_name": topic_progress.topic_name,
                "mastery_level": round(topic_progress.mastery_level * 100, 1),
                "accuracy": round(topic_accuracy, 1),
                "attempts": topic_progress.practice_attempts,
                "time_spent": topic_progress.time_spent_minutes,
                "status": status,
                "emoji": emoji,
                "concepts_mastered": len(topic_progress.concepts_mastered),
                "concepts_struggling": topic_progress.concepts_struggling
            })
        
        # Sort by mastery level (highest first)
        topic_list.sort(key=lambda x: x["mastery_level"], reverse=True)
        
        return topic_list
    
    def _calculate_achievements(
        self, 
        profile, 
        statistics: Dict
    ) -> List[Dict[str, Any]]:
        """Calculate earned achievements."""
        achievements = []
        
        # Session-based achievements
        if statistics["total_sessions"] >= 1:
            achievements.append({
                "id": "first_session",
                "name": "First Steps 👣",
                "description": "Completed your first tutoring session"
            })
        
        if statistics["total_sessions"] >= 5:
            achievements.append({
                "id": "dedicated_learner",
                "name": "Dedicated Learner 📚",
                "description": "Completed 5 tutoring sessions"
            })
        
        if statistics["total_sessions"] >= 10:
            achievements.append({
                "id": "committed",
                "name": "Committed Scholar 🎓",
                "description": "Completed 10 tutoring sessions"
            })
        
        # Accuracy achievements
        if statistics["accuracy_percentage"] >= 80 and statistics["total_questions_answered"] >= 10:
            achievements.append({
                "id": "sharp_mind",
                "name": "Sharp Mind 🧠",
                "description": "Achieved 80%+ accuracy on 10+ questions"
            })
        
        if statistics["accuracy_percentage"] >= 90 and statistics["total_questions_answered"] >= 20:
            achievements.append({
                "id": "perfectionist",
                "name": "Perfectionist ⭐",
                "description": "Achieved 90%+ accuracy on 20+ questions"
            })
        
        # Mastery achievements
        if statistics["topics_mastered"] >= 1:
            achievements.append({
                "id": "first_mastery",
                "name": "Master of One 🏆",
                "description": "Mastered your first topic"
            })
        
        if statistics["topics_mastered"] >= 3:
            achievements.append({
                "id": "triple_mastery",
                "name": "Triple Crown 👑",
                "description": "Mastered 3 topics"
            })
        
        # Question achievements
        if statistics["total_questions_answered"] >= 50:
            achievements.append({
                "id": "question_warrior",
                "name": "Question Warrior ⚔️",
                "description": "Answered 50 questions"
            })
        
        if statistics["total_questions_answered"] >= 100:
            achievements.append({
                "id": "century",
                "name": "Centurion 💯",
                "description": "Answered 100 questions"
            })
        
        return achievements
    
    async def _generate_summary(
        self, 
        state: TutorState,
        statistics: Dict,
        achievements: List
    ) -> str:
        """Generate a personalized progress summary using LLM."""
        
        prompt = f"""Generate an encouraging, personalized progress report for a student.

STUDENT STATISTICS:
- Total Sessions: {statistics['total_sessions']}
- Questions Answered: {statistics['total_questions_answered']}
- Accuracy: {statistics['accuracy_percentage']}%
- Topics Mastered: {statistics['topics_mastered']} of {statistics['total_topics_studied']}
- Current Level: {statistics['current_level']}
- Strengths: {', '.join(state.student_profile.strengths) or 'Still discovering'}
- Areas to Improve: {', '.join(state.student_profile.areas_for_improvement) or 'None identified'}
- Achievements Earned: {len(achievements)}

LANGUAGE: {state.language}

Write a brief (3-4 sentences), encouraging progress summary that:
1. Highlights their accomplishments
2. Mentions specific statistics in a positive way
3. Provides motivation to continue
4. Feels personal and warm

{self._get_language_instruction(state.language)}"""

        summary = await self.generate_response(prompt)
        
        # Add statistics emoji header
        header = "📊 **Your Learning Journey**\n\n" if state.language == "en" else "📊 **رحلتك التعليمية**\n\n"
        
        return header + summary
    
    def _generate_recommendations(
        self, 
        statistics: Dict,
        topic_progress: List
    ) -> List[str]:
        """Generate personalized learning recommendations."""
        recommendations = []
        
        accuracy = statistics["accuracy_percentage"]
        
        # Accuracy-based recommendations
        if accuracy < 50:
            recommendations.append("Review foundational concepts before moving forward")
            recommendations.append("Focus on understanding 'why' rather than just 'what'")
        elif accuracy < 70:
            recommendations.append("Practice more with varied question types")
            recommendations.append("Take notes while learning to reinforce concepts")
        elif accuracy < 85:
            recommendations.append("Challenge yourself with harder problems")
            recommendations.append("Try teaching concepts to others to deepen understanding")
        else:
            recommendations.append("Explore advanced topics in areas you've mastered")
            recommendations.append("Help others learn to solidify your expertise")
        
        # Topic-based recommendations
        struggling_topics = [t for t in topic_progress if t["status"] in ["started", "learning"]]
        if struggling_topics:
            recommendations.append(f"Focus on: {struggling_topics[0]['topic_name']}")
        
        # Session-based recommendations
        if statistics["total_sessions"] < 3:
            recommendations.append("Build a consistent learning routine")
        
        # General recommendations
        recommendations.append("Celebrate small wins along the way! 🎉")
        
        return recommendations[:5]  # Return top 5
    
    def _calculate_streak(self, profile) -> Dict[str, Any]:
        """Calculate learning streak (simplified version)."""
        # This is a placeholder - in production, you'd track actual session dates
        return {
            "current_streak": min(profile.total_sessions, 7),
            "longest_streak": profile.total_sessions,
            "streak_message": "Keep the momentum going! 🔥"
        }
    
    def format_progress_for_display(
        self, 
        statistics: Dict, 
        topic_progress: List,
        language: str = "en"
    ) -> str:
        """Format progress data as a readable string."""
        
        lines = []
        
        # Header
        if language == "en":
            lines.append("📊 **Progress Report**\n")
            lines.append(f"**Sessions:** {statistics['total_sessions']}")
            lines.append(f"**Questions Answered:** {statistics['total_questions_answered']}")
            lines.append(f"**Accuracy:** {statistics['accuracy_percentage']}%")
            lines.append(f"**Topics Mastered:** {statistics['topics_mastered']}/{statistics['total_topics_studied']}")
            lines.append(f"**Current Level:** {statistics['current_level']}\n")
            
            if topic_progress:
                lines.append("**Topic Progress:**")
                for topic in topic_progress[:5]:
                    lines.append(f"  {topic['emoji']} {topic['topic_name']}: {topic['mastery_level']}%")
        else:
            lines.append("📊 **تقرير التقدم**\n")
            lines.append(f"**الجلسات:** {statistics['total_sessions']}")
            lines.append(f"**الأسئلة المجابة:** {statistics['total_questions_answered']}")
            lines.append(f"**الدقة:** {statistics['accuracy_percentage']}%")
            lines.append(f"**المواضيع المتقنة:** {statistics['topics_mastered']}/{statistics['total_topics_studied']}")
            lines.append(f"**المستوى الحالي:** {statistics['current_level']}\n")
        
        return "\n".join(lines)
