"""
Explanation Handler

Handles concept explanations with adaptive difficulty.
This handler is responsible for explaining topics to students
in a way that matches their current level and learning style.
"""

from typing import Dict, Any, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from .base_tutor_handler import BaseTutorHandler
from backend.core.agents.tutor_agent.tutor_state import TutorState, DifficultyLevel
from backend.utils.logger_config import get_logger

logger = get_logger(__name__)


class ExplanationHandler(BaseTutorHandler):
    """
    Handles concept explanations with adaptive difficulty.
    
    This handler generates explanations that are tailored to the
    student's current level, using appropriate language, examples,
    and analogies based on their profile.
    """
    
    # Difficulty-specific instruction prompts
    DIFFICULTY_PROMPTS = {
        DifficultyLevel.BEGINNER: (
            "Explain like I'm 10 years old. Use very simple words, "
            "fun analogies, and real-world examples a child would understand."
        ),
        DifficultyLevel.ELEMENTARY: (
            "Explain in simple terms with basic examples. "
            "Avoid jargon and use everyday language."
        ),
        DifficultyLevel.INTERMEDIATE: (
            "Provide a balanced explanation with some technical details. "
            "Include examples and explain key terminology."
        ),
        DifficultyLevel.ADVANCED: (
            "Provide a detailed technical explanation with nuances. "
            "Include edge cases and deeper insights."
        ),
        DifficultyLevel.EXPERT: (
            "Provide comprehensive expert-level analysis with edge cases, "
            "research references, and advanced implementation details."
        )
    }
    
    async def handle(
        self, 
        state: TutorState,
        db_session: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """
        Generate an explanation adapted to the student's level.
        
        Args:
            state: The current tutor state
            db_session: Optional database session (not used in this handler)
            
        Returns:
            Dictionary containing the explanation and next steps
        """
        try:
            # Get context from documents if available
            context = await self.retrieve_context(
                state.query, 
                state.current_document_id
            )
            
            # Build explanation prompt
            difficulty_instruction = self.DIFFICULTY_PROMPTS.get(
                state.current_difficulty if isinstance(state.current_difficulty, DifficultyLevel) 
                else DifficultyLevel(state.current_difficulty),
                self.DIFFICULTY_PROMPTS[DifficultyLevel.INTERMEDIATE]
            )
            
            prompt = self._build_explanation_prompt(
                state=state,
                context=context,
                difficulty_instruction=difficulty_instruction
            )
            
            # Generate explanation
            response = await self.generate_response(prompt)
            
            # Generate next steps for continued learning
            next_steps = await self._generate_next_steps(state, response)
            
            return {
                "response": response,
                "next_steps": next_steps,
                "handler": "explanation",
                "context_used": len(context) > 0
            }
            
        except Exception as e:
            return self._handle_error(e, "generating explanation")
    
    def _build_explanation_prompt(
        self, 
        state: TutorState, 
        context: List[str],
        difficulty_instruction: str
    ) -> str:
        """Build the explanation prompt for the LLM."""
        
        language_instruction = self._get_language_instruction(state.language)
        
        context_section = (
            f"Relevant learning material:\n{chr(10).join(context)}"
            if context else "No specific material provided. Use your knowledge."
        )
        
        prompt = f"""You are IRIS, a patient and encouraging educational tutor.

STUDENT PROFILE:
- Current Level: {state.current_difficulty}
- Preferred Language: {state.language}
- Learning Style: {state.student_profile.learning_style if state.student_profile else 'reading_writing'}

INSTRUCTION: {difficulty_instruction}

PREVIOUS CONVERSATION:
{state.format_history_for_prompt(5)}

{context_section}

STUDENT'S QUESTION: {state.query}

YOUR TASK:
Provide a clear, engaging explanation that:
1. Acknowledges the student's question warmly
2. Explains the concept step by step
3. Uses relevant examples or analogies appropriate to their level
4. Highlights key points they should remember
5. Ends with a thought-provoking question to check understanding

{language_instruction}

Remember: Be encouraging, patient, and adapt your language to the student's level."""

        return prompt
    
    async def _generate_next_steps(
        self, 
        state: TutorState, 
        response: str
    ) -> List[str]:
        """Generate suggested next steps for the student."""
        try:
            prompt = f"""Based on this tutoring exchange, suggest 3 brief next steps for the student:

Topic discussed: {state.current_topic or state.query}
Explanation given: {response[:500]}...

Provide exactly 3 short, actionable next steps (one line each).
Format as a simple list, no numbers or bullets.

{self._get_language_instruction(state.language)}"""

            result = await self.generate_response(prompt)
            
            # Parse the result into a list
            steps = [
                step.strip().lstrip('•-123456789. ')
                for step in result.strip().split("\n") 
                if step.strip() and len(step.strip()) > 5
            ][:3]
            
            return steps if steps else ["Practice with examples", "Ask follow-up questions", "Try to explain this to someone else"]
            
        except Exception as e:
            self.logger.warning(f"Failed to generate next steps: {e}")
            return ["Continue exploring this topic", "Practice with examples", "Ask more questions"]
