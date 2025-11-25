"""
Feedback Handler

Provides constructive feedback on student submissions and answers.
This handler evaluates student work and provides encouraging,
educational feedback to support learning.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from .base_tutor_handler import BaseTutorHandler
from backend.core.agents.tutor_agent.tutor_state import TutorState
from backend.database.models.tutor_models import (
    LearnerInteractionModel,
    LearnerProfileModel,
    TopicProgressModel
)
from backend.utils.logger_config import get_logger

logger = get_logger(__name__)


class FeedbackHandler(BaseTutorHandler):
    """
    Provides constructive feedback on student submissions.
    
    Evaluates student answers, provides detailed feedback,
    and suggests improvements while maintaining an encouraging tone.
    """
    
    async def handle(
        self, 
        state: TutorState,
        db_session: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """
        Provide feedback on the student's work or answer.
        
        Args:
            state: The current tutor state
            db_session: Optional database session for persistence
            
        Returns:
            Dictionary containing feedback and evaluation
        """
        try:
            # Get the answer/work being evaluated
            student_answer = state.query
            
            # Get context for evaluation
            context = await self.retrieve_context(
                state.current_topic or student_answer,
                state.current_document_id
            )
            
            # Generate comprehensive feedback
            feedback = await self._generate_feedback(state, student_answer, context)
            
            # Persist to database if session provided
            if db_session:
                await self._persist_interaction(
                    db_session=db_session,
                    state=state,
                    student_answer=student_answer,
                    feedback=feedback
                )
            
            return {
                "response": feedback["message"],
                "is_correct": feedback["is_correct"],
                "score": feedback["score"],
                "strengths": feedback["strengths"],
                "improvements": feedback["improvements"],
                "encouragement": feedback["encouragement"],
                "handler": "feedback"
            }
            
        except Exception as e:
            return self._handle_error(e, "generating feedback")
    
    async def _persist_interaction(
        self,
        db_session: AsyncSession,
        state: TutorState,
        student_answer: str,
        feedback: Dict[str, Any]
    ) -> None:
        """
        Persist the interaction and update learner profile.
        
        Args:
            db_session: The database session
            state: Current tutor state
            student_answer: The student's answer
            feedback: The generated feedback
        """
        try:
            student_id = state.student_profile.student_id
            is_correct = feedback.get("is_correct", False)
            score = feedback.get("score", 0.0)
            
            # 1. Create LearnerInteraction record
            interaction = LearnerInteractionModel(
                id=uuid.uuid4(),
                session_id=uuid.UUID(state.session_id) if state.session_id else None,
                interaction_type="answer_check",
                query_text=student_answer,
                response_text=feedback.get("message", "")[:5000],  # Truncate if too long
                was_helpful=is_correct,
                difficulty_rating=int(score * 5),  # Convert score to 1-5 rating
                interaction_metadata={
                    "topic": state.current_topic,
                    "is_correct": is_correct,
                    "score": score,
                    "difficulty": str(state.current_difficulty)
                }
            )
            db_session.add(interaction)
            
            # 2. Update or create LearnerProfile
            result = await db_session.execute(
                select(LearnerProfileModel).where(
                    LearnerProfileModel.id == uuid.UUID(student_id) if self._is_uuid(student_id) else None
                )
            )
            profile = result.scalar_one_or_none()
            
            if profile:
                # Update existing profile
                profile.total_sessions = (profile.total_sessions or 0) + 1
                profile.accuracy_rate = self._calculate_new_accuracy(
                    profile.accuracy_rate or 0.0,
                    profile.total_sessions or 1,
                    is_correct
                )
                profile.updated_at = datetime.utcnow()
                self.logger.info(f"Updated learner profile for {student_id}")
            else:
                self.logger.info(f"No profile found for {student_id}, skipping profile update")
            
            # 3. Update TopicProgress if we have a topic
            if state.current_topic:
                await self._update_topic_progress(
                    db_session=db_session,
                    student_id=student_id,
                    topic=state.current_topic,
                    is_correct=is_correct,
                    score=score
                )
            
            # Commit all changes
            await db_session.commit()
            self.logger.info(f"Persisted interaction for student {student_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to persist interaction: {e}")
            await db_session.rollback()
            # Don't raise - we don't want DB errors to break the tutoring flow
    
    async def _update_topic_progress(
        self,
        db_session: AsyncSession,
        student_id: str,
        topic: str,
        is_correct: bool,
        score: float
    ) -> None:
        """Update topic-specific progress."""
        try:
            # Try to find existing topic progress
            if not self._is_uuid(student_id):
                return
                
            learner_uuid = uuid.UUID(student_id)
            
            result = await db_session.execute(
                select(TopicProgressModel).where(
                    TopicProgressModel.learner_id == learner_uuid,
                    TopicProgressModel.topic_name == topic
                )
            )
            progress = result.scalar_one_or_none()
            
            if progress:
                # Update existing progress
                progress.practice_attempts = (progress.practice_attempts or 0) + 1
                if is_correct:
                    progress.practice_correct = (progress.practice_correct or 0) + 1
                progress.last_accessed = datetime.utcnow()
                
                # Recalculate mastery
                if progress.practice_attempts > 0:
                    accuracy = progress.practice_correct / progress.practice_attempts
                    progress.mastery_level = min(1.0, accuracy * 0.8 + 0.1)  # Scale to mastery
                    progress.confidence_score = min(1.0, progress.practice_attempts * 0.05)
            else:
                # Create new topic progress
                new_progress = TopicProgressModel(
                    id=uuid.uuid4(),
                    learner_id=learner_uuid,
                    topic_id=topic.lower().replace(" ", "_"),
                    topic_name=topic,
                    practice_attempts=1,
                    practice_correct=1 if is_correct else 0,
                    mastery_level=0.5 if is_correct else 0.2,
                    confidence_score=0.1
                )
                db_session.add(new_progress)
                
            self.logger.info(f"Updated topic progress for {topic}")
            
        except Exception as e:
            self.logger.error(f"Failed to update topic progress: {e}")
    
    def _is_uuid(self, value: str) -> bool:
        """Check if a string is a valid UUID."""
        try:
            uuid.UUID(value)
            return True
        except (ValueError, AttributeError):
            return False
    
    def _calculate_new_accuracy(
        self, 
        current_accuracy: float, 
        total_attempts: int, 
        is_correct: bool
    ) -> float:
        """Calculate new accuracy with weighted average."""
        if total_attempts <= 1:
            return 1.0 if is_correct else 0.0
        
        # Weighted moving average
        weight = 1 / total_attempts
        new_value = 1.0 if is_correct else 0.0
        return current_accuracy * (1 - weight) + new_value * weight
    
    async def _generate_feedback(
        self, 
        state: TutorState, 
        student_answer: str,
        context: List[str]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive feedback on student work.
        
        Args:
            state: Current tutor state
            student_answer: The student's answer or work
            context: Retrieved context for evaluation
            
        Returns:
            Structured feedback dictionary
        """
        
        context_text = chr(10).join(context[:2]) if context else "Use your knowledge to evaluate."
        
        prompt = f"""You are a supportive and encouraging educational tutor providing feedback.

STUDENT PROFILE:
- Level: {state.current_difficulty}
- Language: {state.language}

TOPIC: {state.current_topic or "General"}

REFERENCE MATERIAL:
{context_text}

STUDENT'S ANSWER/WORK:
{student_answer}

Provide feedback following this structure:
1. ACKNOWLEDGMENT: Start with something specific and positive about their attempt
2. CORRECTNESS: Evaluate if the answer is correct/partially correct/incorrect
3. STRENGTHS: List 1-2 specific things they did well
4. IMPROVEMENTS: Gently suggest 1-2 areas for improvement
5. EXPLANATION: If incorrect, explain the correct approach clearly
6. ENCOURAGEMENT: End with encouragement and a motivating statement

IMPORTANT GUIDELINES:
- Be constructive, specific, and encouraging
- Never be harsh, dismissive, or discouraging
- Focus on the learning process, not just right/wrong
- Celebrate effort and progress
- Use age-appropriate language for their level

{self._get_language_instruction(state.language)}

Respond with a natural, conversational feedback message."""

        response = await self.generate_response(prompt)
        
        # Analyze the response for metrics
        analysis = await self._analyze_feedback(response, student_answer)
        
        return {
            "message": response,
            "is_correct": analysis["is_correct"],
            "score": analysis["score"],
            "strengths": analysis["strengths"],
            "improvements": analysis["improvements"],
            "encouragement": self._get_encouragement(analysis["is_correct"], state.language)
        }
    
    async def _analyze_feedback(
        self, 
        feedback_response: str, 
        student_answer: str
    ) -> Dict[str, Any]:
        """Analyze the feedback to extract structured metrics."""
        
        # Use heuristics to determine correctness from feedback
        response_lower = feedback_response.lower()
        
        # Positive indicators
        positive_words = ["correct", "right", "excellent", "perfect", "great", 
                         "well done", "exactly", "صحيح", "ممتاز", "رائع"]
        # Negative indicators
        negative_words = ["incorrect", "wrong", "not quite", "mistake", "error",
                         "غير صحيح", "خطأ"]
        
        positive_count = sum(1 for word in positive_words if word in response_lower)
        negative_count = sum(1 for word in negative_words if word in response_lower)
        
        is_correct = positive_count > negative_count
        
        # Calculate score based on indicators
        if is_correct and negative_count == 0:
            score = 1.0
        elif is_correct:
            score = 0.8
        elif negative_count == 0:
            score = 0.6
        else:
            score = 0.4
        
        return {
            "is_correct": is_correct,
            "score": score,
            "strengths": ["Good attempt", "Shows understanding"],
            "improvements": ["Consider adding more detail"] if not is_correct else []
        }
    
    def _get_encouragement(self, is_correct: bool, language: str) -> str:
        """Get an encouraging message based on result."""
        if is_correct:
            encouragements = {
                "en": [
                    "Keep up the excellent work! 🌟",
                    "You're doing amazing! 🎉",
                    "That's the spirit! Keep going! 💪"
                ],
                "ar": [
                    "استمر في العمل الرائع! 🌟",
                    "أنت تقوم بعمل مذهل! 🎉",
                    "هذه هي الروح! استمر! 💪"
                ]
            }
        else:
            encouragements = {
                "en": [
                    "Don't worry, mistakes help us learn! 📚",
                    "You're on the right track, keep trying! 💪",
                    "Every expert was once a beginner! 🌱"
                ],
                "ar": [
                    "لا تقلق، الأخطاء تساعدنا على التعلم! 📚",
                    "أنت على الطريق الصحيح، استمر في المحاولة! 💪",
                    "كل خبير كان مبتدئًا في يوم من الأيام! 🌱"
                ]
            }
        
        import random
        messages = encouragements.get(language, encouragements["en"])
        return random.choice(messages)
    
    async def evaluate_multiple_answers(
        self, 
        state: TutorState, 
        answers: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Evaluate multiple answers (e.g., for a quiz).
        
        Args:
            state: Current tutor state
            answers: List of {question, student_answer, correct_answer} dicts
            
        Returns:
            Overall evaluation with per-question feedback
        """
        results = []
        correct_count = 0
        
        for answer_data in answers:
            prompt = f"""Evaluate this answer briefly:
Question: {answer_data.get('question', '')}
Correct Answer: {answer_data.get('correct_answer', '')}
Student Answer: {answer_data.get('student_answer', '')}

Is it correct? Provide brief feedback (1-2 sentences).
{self._get_language_instruction(state.language)}"""

            response = await self.generate_response(prompt)
            is_correct = "correct" in response.lower() and "incorrect" not in response.lower()
            
            if is_correct:
                correct_count += 1
            
            results.append({
                "question": answer_data.get('question', ''),
                "is_correct": is_correct,
                "feedback": response
            })
        
        total = len(answers)
        score = correct_count / total if total > 0 else 0
        
        return {
            "results": results,
            "total_correct": correct_count,
            "total_questions": total,
            "score": score,
            "grade": self._get_grade(score),
            "overall_feedback": self._get_overall_feedback(score, state.language)
        }
    
    def _get_grade(self, score: float) -> str:
        """Convert score to letter grade."""
        if score >= 0.9:
            return "A"
        elif score >= 0.8:
            return "B"
        elif score >= 0.7:
            return "C"
        elif score >= 0.6:
            return "D"
        else:
            return "F"
    
    def _get_overall_feedback(self, score: float, language: str) -> str:
        """Get overall feedback based on score."""
        if score >= 0.9:
            return "Outstanding performance! 🏆" if language == "en" else "أداء متميز! 🏆"
        elif score >= 0.7:
            return "Good job! Keep practicing! 👍" if language == "en" else "عمل جيد! استمر في التدريب! 👍"
        elif score >= 0.5:
            return "You're improving! Review the material. 📚" if language == "en" else "أنت تتحسن! راجع المادة. 📚"
        else:
            return "Let's review together. You've got this! 💪" if language == "en" else "دعنا نراجع معاً. يمكنك ذلك! 💪"
