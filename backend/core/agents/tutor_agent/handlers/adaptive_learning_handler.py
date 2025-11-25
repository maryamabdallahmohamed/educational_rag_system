"""
Adaptive Learning Handler

Handles adaptive learning adjustments based on student performance.
This handler analyzes how the student is doing and adjusts the
difficulty and approach accordingly.
"""

from typing import Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from .base_tutor_handler import BaseTutorHandler
from backend.core.agents.tutor_agent.tutor_state import TutorState, DifficultyLevel
from backend.utils.logger_config import get_logger

logger = get_logger(__name__)


class AdaptiveLearningHandler(BaseTutorHandler):
    """
    Handles adaptive learning adjustments.
    
    Monitors student performance and adjusts:
    - Difficulty level
    - Teaching approach
    - Content complexity
    - Pace of learning
    """
    
    # Thresholds for difficulty adjustment
    INCREASE_THRESHOLD = 0.85  # Accuracy above this -> increase difficulty
    DECREASE_THRESHOLD = 0.50  # Accuracy below this -> decrease difficulty
    MIN_QUESTIONS_FOR_ADJUSTMENT = 3  # Minimum questions before adjusting
    
    async def handle(
        self, 
        state: TutorState,
        db_session: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """
        Adapt learning experience based on student performance.
        
        Args:
            state: The current tutor state
            db_session: Optional database session (not used yet)
            
        Returns:
            Dictionary with adaptation details and response
        """
        try:
            # Analyze student's current performance
            performance = self._analyze_performance(state)
            
            # Determine if difficulty adjustment is needed
            adjustment = self._determine_adjustment(state, performance)
            
            # Calculate new difficulty level
            new_difficulty = self._calculate_new_difficulty(
                state.current_difficulty if isinstance(state.current_difficulty, DifficultyLevel)
                else DifficultyLevel(state.current_difficulty),
                adjustment
            )
            
            # Generate adaptive response
            response = await self._generate_adaptive_response(
                state, adjustment, performance
            )
            
            # Generate recommendations based on performance
            recommendations = self._generate_recommendations(state, performance)
            
            return {
                "response": response,
                "difficulty_adjustment": adjustment,
                "new_difficulty": new_difficulty.value,
                "performance_analysis": performance,
                "recommendations": recommendations,
                "handler": "adaptive_learning"
            }
            
        except Exception as e:
            return self._handle_error(e, "adapting learning")
    
    def _analyze_performance(self, state: TutorState) -> Dict[str, Any]:
        """
        Analyze the student's current performance.
        
        Args:
            state: Current tutor state
            
        Returns:
            Performance metrics dictionary
        """
        profile = state.student_profile
        
        # Calculate overall accuracy
        total_answered = profile.total_questions_answered
        correct = profile.correct_answers
        
        accuracy = correct / total_answered if total_answered > 0 else 0.5
        
        # Analyze topic-specific progress
        topic_accuracies = {}
        struggling_topics = []
        mastered_topics = []
        
        for topic_id, progress in state.learning_progress.items():
            if progress.practice_attempts > 0:
                topic_accuracy = progress.practice_correct / progress.practice_attempts
                topic_accuracies[topic_id] = topic_accuracy
                
                if topic_accuracy < 0.5:
                    struggling_topics.append(progress.topic_name)
                elif topic_accuracy >= 0.8 and progress.practice_attempts >= 5:
                    mastered_topics.append(progress.topic_name)
        
        # Analyze engagement (based on session count and questions attempted)
        engagement_score = min(1.0, (profile.total_sessions * 0.1) + (total_answered * 0.05))
        
        return {
            "accuracy": accuracy,
            "questions_attempted": total_answered,
            "correct_answers": correct,
            "sessions_completed": profile.total_sessions,
            "struggling_topics": struggling_topics,
            "mastered_topics": mastered_topics,
            "engagement_score": engagement_score,
            "topic_accuracies": topic_accuracies,
            "enough_data": total_answered >= self.MIN_QUESTIONS_FOR_ADJUSTMENT
        }
    
    def _determine_adjustment(
        self, 
        state: TutorState, 
        performance: Dict[str, Any]
    ) -> str:
        """
        Determine what difficulty adjustment to make.
        
        Args:
            state: Current tutor state
            performance: Performance analysis results
            
        Returns:
            Adjustment type: "increase", "decrease", or "maintain"
        """
        # Don't adjust if not enough data
        if not performance.get("enough_data", False):
            return "maintain"
        
        accuracy = performance.get("accuracy", 0.5)
        
        # Check for explicit difficulty change request
        query_lower = state.query.lower()
        if any(word in query_lower for word in ["harder", "more difficult", "challenge", "أصعب"]):
            return "increase"
        if any(word in query_lower for word in ["easier", "simpler", "too hard", "أسهل"]):
            return "decrease"
        
        # Automatic adjustment based on performance
        if accuracy >= self.INCREASE_THRESHOLD:
            return "increase"
        elif accuracy <= self.DECREASE_THRESHOLD:
            return "decrease"
        else:
            return "maintain"
    
    def _calculate_new_difficulty(
        self, 
        current: DifficultyLevel, 
        adjustment: str
    ) -> DifficultyLevel:
        """
        Calculate the new difficulty level.
        
        Args:
            current: Current difficulty level
            adjustment: Type of adjustment
            
        Returns:
            New difficulty level
        """
        levels = list(DifficultyLevel)
        current_idx = levels.index(current)
        
        if adjustment == "increase" and current_idx < len(levels) - 1:
            return levels[current_idx + 1]
        elif adjustment == "decrease" and current_idx > 0:
            return levels[current_idx - 1]
        
        return current
    
    async def _generate_adaptive_response(
        self, 
        state: TutorState, 
        adjustment: str,
        performance: Dict[str, Any]
    ) -> str:
        """Generate an encouraging response based on the adaptation."""
        
        accuracy_pct = performance.get("accuracy", 0.5) * 100
        
        messages = {
            "increase": {
                "en": f"🌟 Excellent work! You're achieving {accuracy_pct:.0f}% accuracy. "
                      f"Let's challenge you with more advanced material!",
                "ar": f"🌟 عمل ممتاز! أنت تحقق دقة {accuracy_pct:.0f}%. "
                      f"دعنا نتحداك بمواد أكثر تقدماً!"
            },
            "decrease": {
                "en": f"📚 Let's take a step back and reinforce the foundations. "
                      f"There's no rush - understanding deeply is what matters!",
                "ar": f"📚 دعنا نتراجع خطوة ونعزز الأساسيات. "
                      f"لا داعي للعجلة - الفهم العميق هو المهم!"
            },
            "maintain": {
                "en": f"👍 You're making good progress with {accuracy_pct:.0f}% accuracy. "
                      f"Let's continue at this pace!",
                "ar": f"👍 أنت تحرز تقدماً جيداً بدقة {accuracy_pct:.0f}%. "
                      f"دعنا نستمر بهذه الوتيرة!"
            }
        }
        
        base_message = messages.get(adjustment, messages["maintain"])
        message = base_message.get(state.language, base_message["en"])
        
        # Add specific feedback about struggling/mastered topics
        struggling = performance.get("struggling_topics", [])
        mastered = performance.get("mastered_topics", [])
        
        if struggling:
            topic_list = ", ".join(struggling[:3])
            if state.language == "ar":
                message += f"\n\n💪 نوصي بمراجعة: {topic_list}"
            else:
                message += f"\n\n💪 I recommend reviewing: {topic_list}"
        
        if mastered:
            topic_list = ", ".join(mastered[:3])
            if state.language == "ar":
                message += f"\n\n🏆 أتقنت: {topic_list}"
            else:
                message += f"\n\n🏆 You've mastered: {topic_list}"
        
        return message
    
    def _generate_recommendations(
        self, 
        state: TutorState, 
        performance: Dict[str, Any]
    ) -> list:
        """Generate personalized learning recommendations."""
        recommendations = []
        
        accuracy = performance.get("accuracy", 0.5)
        struggling = performance.get("struggling_topics", [])
        
        if accuracy < 0.5:
            recommendations.append("Review foundational concepts before moving on")
            recommendations.append("Try breaking down complex topics into smaller parts")
        elif accuracy < 0.7:
            recommendations.append("Practice more with varied question types")
            recommendations.append("Focus on understanding why answers are correct")
        else:
            recommendations.append("Try teaching the concept to someone else")
            recommendations.append("Explore related advanced topics")
        
        if struggling:
            recommendations.append(f"Revisit: {struggling[0]}")
        
        recommendations.append("Take regular breaks to consolidate learning")
        
        return recommendations[:4]  # Return top 4 recommendations
