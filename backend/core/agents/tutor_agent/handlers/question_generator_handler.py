"""
Question Generator Handler

Generates practice questions adapted to the student's level.
This handler creates quizzes and practice problems to help
students reinforce their learning.
"""

from typing import Dict, Any, List, Optional
import json

from sqlalchemy.ext.asyncio import AsyncSession

from .base_tutor_handler import BaseTutorHandler
from backend.core.agents.tutor_agent.tutor_state import TutorState, DifficultyLevel
from backend.utils.logger_config import get_logger

logger = get_logger(__name__)


class QuestionGeneratorHandler(BaseTutorHandler):
    """
    Generates practice questions adapted to student level.
    
    Creates various question types (multiple choice, short answer,
    true/false) with hints and explanations to support learning.
    """
    
    async def handle(
        self, 
        state: TutorState,
        db_session: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """
        Generate practice questions for the student.
        
        Args:
            state: The current tutor state
            db_session: Optional database session (not used in this handler)
            
        Returns:
            Dictionary containing questions and formatted response
        """
        try:
            # Get context from documents
            context = await self.retrieve_context(
                state.current_topic or state.query,
                state.current_document_id
            )
            
            # Generate questions
            questions = await self._generate_questions(state, context)
            
            # Format response for display
            response = self._format_questions_response(questions, state.language)
            
            return {
                "response": response,
                "questions": questions,
                "handler": "question_generator",
                "question_count": len(questions)
            }
            
        except Exception as e:
            return self._handle_error(e, "generating practice questions")
    
    async def _generate_questions(
        self, 
        state: TutorState, 
        context: List[str]
    ) -> List[Dict[str, Any]]:
        """Generate a set of practice questions."""
        
        difficulty_map = {
            DifficultyLevel.BEGINNER: "very easy",
            DifficultyLevel.ELEMENTARY: "easy",
            DifficultyLevel.INTERMEDIATE: "medium",
            DifficultyLevel.ADVANCED: "hard",
            DifficultyLevel.EXPERT: "very hard"
        }
        
        difficulty_str = difficulty_map.get(
            state.current_difficulty if isinstance(state.current_difficulty, DifficultyLevel)
            else DifficultyLevel(state.current_difficulty),
            "medium"
        )
        
        context_text = chr(10).join(context[:3]) if context else "Use general knowledge about the topic."
        
        prompt = f"""Generate 5 practice questions about: {state.current_topic or state.query}

STUDENT LEVEL: {difficulty_str}
LANGUAGE: {state.language}

REFERENCE MATERIAL:
{context_text}

Generate questions in this exact JSON format (respond with ONLY valid JSON, no markdown):
[
  {{
    "question": "The question text",
    "type": "multiple_choice",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer": "Option A",
    "explanation": "Why this is the correct answer",
    "difficulty": "{difficulty_str}",
    "hints": ["First hint", "Second hint"]
  }},
  {{
    "question": "Another question",
    "type": "short_answer",
    "correct_answer": "Expected answer",
    "explanation": "Explanation of the answer",
    "difficulty": "{difficulty_str}",
    "hints": ["Hint 1"]
  }},
  {{
    "question": "A true/false statement",
    "type": "true_false",
    "correct_answer": "true",
    "explanation": "Why this is true/false",
    "difficulty": "{difficulty_str}",
    "hints": []
  }}
]

Generate 5 varied questions mixing different types.
{"Generate questions in Arabic." if state.language == "ar" else ""}"""

        response = await self.generate_response(prompt)
        
        # Parse JSON response
        return self._parse_questions(response)
    
    def _parse_questions(self, response: str) -> List[Dict[str, Any]]:
        """Parse the LLM response into structured questions."""
        try:
            # Clean the response - remove markdown code blocks if present
            cleaned = response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            elif cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            
            questions = json.loads(cleaned)
            
            # Validate and clean questions
            valid_questions = []
            for q in questions:
                if isinstance(q, dict) and "question" in q:
                    # Ensure required fields
                    q.setdefault("type", "short_answer")
                    q.setdefault("correct_answer", "")
                    q.setdefault("explanation", "")
                    q.setdefault("hints", [])
                    q.setdefault("difficulty", "medium")
                    valid_questions.append(q)
            
            return valid_questions if valid_questions else self._get_fallback_questions()
            
        except json.JSONDecodeError as e:
            self.logger.warning(f"Failed to parse questions JSON: {e}")
            return self._get_fallback_questions()
    
    def _get_fallback_questions(self) -> List[Dict[str, Any]]:
        """Return fallback questions if parsing fails."""
        return [{
            "question": "Can you explain the main concept in your own words?",
            "type": "short_answer",
            "correct_answer": "Open-ended response",
            "explanation": "This helps reinforce understanding",
            "difficulty": "medium",
            "hints": ["Think about what you just learned"]
        }]
    
    def _format_questions_response(
        self, 
        questions: List[Dict], 
        language: str
    ) -> str:
        """Format questions for display to the student."""
        if not questions:
            return (
                "Let me prepare some questions for you..." 
                if language == "en" 
                else "دعني أعد لك بعض الأسئلة..."
            )
        
        header = (
            "📝 **Practice Questions**\n\n" 
            if language == "en" 
            else "📝 **أسئلة التدريب**\n\n"
        )
        
        lines = [header]
        
        for i, q in enumerate(questions, 1):
            question_type = q.get('type', 'short_answer')
            lines.append(f"**Question {i}:** {q.get('question', '')}")
            
            if question_type == 'multiple_choice' and q.get('options'):
                for j, opt in enumerate(q['options']):
                    lines.append(f"   {chr(65+j)}. {opt}")
            elif question_type == 'true_false':
                lines.append("   A. True")
                lines.append("   B. False")
            
            lines.append("")  # Empty line between questions
        
        footer = (
            "\n💡 Take your time! Let me know when you're ready to check your answers, "
            "or if you need any hints."
        ) if language == "en" else (
            "\n💡 خذ وقتك! أخبرني عندما تكون مستعداً للتحقق من إجاباتك، "
            "أو إذا كنت بحاجة إلى أي تلميحات."
        )
        
        lines.append(footer)
        
        return "\n".join(lines)
    
    async def check_answer(
        self, 
        state: TutorState, 
        question_index: int, 
        student_answer: str
    ) -> Dict[str, Any]:
        """
        Check a student's answer to a generated question.
        
        Args:
            state: Current tutor state
            question_index: Index of the question being answered
            student_answer: The student's answer
            
        Returns:
            Feedback on the answer
        """
        if question_index >= len(state.generated_questions):
            return {
                "is_correct": False,
                "feedback": "Question not found. Please try again."
            }
        
        question = state.generated_questions[question_index]
        correct = question.get("correct_answer", "")
        
        # Use LLM to evaluate answer similarity
        prompt = f"""Evaluate if the student's answer is correct.

Question: {question.get('question')}
Correct Answer: {correct}
Student's Answer: {student_answer}

Respond with JSON:
{{"is_correct": true/false, "feedback": "Brief encouraging feedback"}}"""

        response = await self.generate_response(prompt)
        
        try:
            # Clean and parse response
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
            result = json.loads(cleaned)
            result["explanation"] = question.get("explanation", "")
            return result
        except:
            return {
                "is_correct": False,
                "feedback": "Let me help you understand this better.",
                "explanation": question.get("explanation", "")
            }
