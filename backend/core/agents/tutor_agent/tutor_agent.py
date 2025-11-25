"""
Tutor Agent - Main Orchestrator

The main Tutor Agent class that orchestrates personalized learning experiences.
It routes student queries to specialized handlers based on intent classification.
"""

from typing import Optional, Dict, Any
import time
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.llms.groq_llm import GroqLLM
from backend.models.embedders.hf_embedder import HFEmbedder
from backend.utils.logger_config import get_logger

from .tutor_state import TutorState, StudentProfile, DifficultyLevel, TutorMessage
from .handlers import (
    BaseTutorHandler,
    ExplanationHandler,
    QuestionGeneratorHandler,
    AdaptiveLearningHandler,
    FeedbackHandler,
    ProgressTrackerHandler
)

logger = get_logger(__name__)


class TutorAgent:
    """
    AI Tutor Agent that provides personalized educational experiences.
    
    This is the main orchestrator that:
    1. Receives student queries
    2. Classifies the intent
    3. Routes to the appropriate handler
    4. Returns structured responses
    
    Capabilities:
    - Adaptive learning based on student level
    - Socratic questioning method
    - Progress tracking
    - Multi-modal explanations
    - Practice question generation
    - Performance feedback
    - Arabic and English language support
    """
    
    # Intent types that the agent can recognize
    INTENTS = [
        "EXPLAIN",           # Student wants explanation of a concept
        "PRACTICE",          # Student wants practice questions/exercises
        "CHECK_ANSWER",      # Student wants to verify their answer
        "ASK_QUESTION",      # Student has a specific question
        "GET_FEEDBACK",      # Student submitted work and wants feedback
        "REVIEW_PROGRESS",   # Student wants to see their progress
        "CHANGE_DIFFICULTY", # Student wants easier/harder content
        "GREETING",          # Student is greeting
        "GENERAL_CHAT"       # General conversation
    ]
    
    def __init__(
        self,
        llm: GroqLLM = None,
        embedder: HFEmbedder = None,
        vector_store: Any = None,
        student_id: Optional[str] = None
    ):
        """
        Initialize the Tutor Agent.
        
        Args:
            llm: Language model for generating responses
            embedder: Embedding model for semantic operations
            vector_store: Vector store for RAG operations
            student_id: Optional student ID for personalization
        """
        # Initialize models (use provided or create new)
        self.llm = llm or GroqLLM()
        self.embedder = embedder or HFEmbedder()
        self.vector_store = vector_store
        self.student_id = student_id
        
        # Initialize handlers
        self.handlers: Dict[str, BaseTutorHandler] = {
            "explanation": ExplanationHandler(self.llm, self.embedder, self.vector_store),
            "question_generator": QuestionGeneratorHandler(self.llm, self.embedder, self.vector_store),
            "adaptive_learning": AdaptiveLearningHandler(self.llm, self.embedder, self.vector_store),
            "feedback": FeedbackHandler(self.llm, self.embedder, self.vector_store),
            "progress_tracker": ProgressTrackerHandler(self.llm, self.embedder, self.vector_store),
        }
        
        # System prompt for tutoring
        self.system_prompt = """You are IRIS, an intelligent educational tutor.

Your teaching philosophy:
1. Use the Socratic method - guide students to discover answers
2. Adapt explanations to student's current understanding level
3. Provide encouragement and constructive feedback
4. Break complex concepts into digestible parts
5. Use analogies and real-world examples
6. Ask probing questions to assess understanding
7. Support both Arabic and English languages seamlessly

When tutoring:
- First assess what the student already knows
- Identify misconceptions gently
- Build on existing knowledge
- Celebrate progress and effort
- Provide practice opportunities
"""
        
        logger.info("TutorAgent initialized successfully")
    
    async def process(
        self, 
        state: TutorState, 
        db_session: Optional[AsyncSession] = None
    ) -> TutorState:
        """
        Main processing loop for tutor interactions.
        
        Args:
            state: The current tutor state
            db_session: Optional database session for persistence
            
        Returns:
            Updated tutor state with response
        """
        start_time = time.time()
        
        try:
            logger.info(f"Processing query: {state.query[:100]}...")
            
            # Add student message to history
            state.add_message("student", state.query)
            
            # Classify intent
            intent = await self._classify_intent(state)
            state.intent = intent
            logger.info(f"Classified intent: {intent}")
            
            # Route to appropriate handler
            handler = self._route_to_handler(intent)
            state.handler_used = handler.handler_name
            
            # Process with handler (pass db_session for persistence)
            result = await handler.handle(state, db_session=db_session)
            
            # Update state with results
            state.response = result.get("response", "I'm not sure how to help with that.")
            state.next_steps = result.get("next_steps", [])
            
            # Handle special result fields
            if "questions" in result:
                state.generated_questions = result["questions"]
            if "new_difficulty" in result:
                state.current_difficulty = result["new_difficulty"]
            
            # Add tutor response to history
            state.add_message("tutor", state.response, {
                "intent": intent,
                "handler": state.handler_used
            })
            
            # Calculate processing time
            state.processing_time = time.time() - start_time
            
            logger.info(f"Processed successfully in {state.processing_time:.2f}s")
            
            return state
            
        except Exception as e:
            logger.error(f"Tutor agent error: {e}")
            state.error = str(e)
            state.response = self._get_error_response(state.language)
            state.processing_time = time.time() - start_time
            return state
    
    async def _classify_intent(self, state: TutorState) -> str:
        """
        Classify the student's intent from their query.
        
        Args:
            state: Current tutor state
            
        Returns:
            Intent classification string
        """
        query = state.query.lower()
        
        # Quick pattern matching for common intents
        intent = self._quick_intent_match(query)
        if intent:
            return intent
        
        # Use LLM for more complex classification
        from langchain_core.messages import HumanMessage
        
        intent_prompt = f"""Classify the student's intent into exactly ONE of these categories:

EXPLAIN - Student wants explanation of a concept (e.g., "what is", "explain", "how does", "tell me about")
PRACTICE - Student wants practice questions or exercises (e.g., "quiz me", "give me questions", "test me")
CHECK_ANSWER - Student is submitting an answer to check (e.g., "is this correct", "my answer is")
ASK_QUESTION - Student has a specific factual question (e.g., "why does", "what happens when")
GET_FEEDBACK - Student wants feedback on their work (e.g., "review my", "grade this", "what do you think")
REVIEW_PROGRESS - Student wants to see their progress (e.g., "how am I doing", "my progress", "statistics")
CHANGE_DIFFICULTY - Student wants to change difficulty level (e.g., "too hard", "make it easier", "challenge me")
GREETING - Student is greeting (e.g., "hello", "hi", "good morning")
GENERAL_CHAT - General conversation that doesn't fit other categories

Student's message: {state.query}

Respond with ONLY the category name (e.g., "EXPLAIN" or "PRACTICE"), nothing else."""

        try:
            messages = [HumanMessage(content=intent_prompt)]
            response = self.llm.invoke(messages)
            intent = response.strip().upper().replace(" ", "_")
            
            # Validate intent
            if intent not in self.INTENTS:
                logger.warning(f"Unknown intent '{intent}', defaulting to EXPLAIN")
                return "EXPLAIN"
            
            return intent
            
        except Exception as e:
            logger.error(f"Intent classification error: {e}")
            return "EXPLAIN"  # Default to explanation
    
    def _quick_intent_match(self, query: str) -> Optional[str]:
        """Quick pattern matching for common intents."""
        
        # Greeting patterns
        greeting_words = ["hello", "hi", "hey", "مرحبا", "السلام", "صباح", "مساء"]
        if any(word in query for word in greeting_words) and len(query.split()) <= 5:
            return "GREETING"
        
        # Practice patterns
        practice_words = ["quiz", "test me", "practice", "questions", "exercise", 
                         "اختبر", "أسئلة", "تمارين", "امتحن"]
        if any(word in query for word in practice_words):
            return "PRACTICE"
        
        # Progress patterns
        progress_words = ["progress", "how am i doing", "my stats", "تقدم", "إحصائيات"]
        if any(word in query for word in progress_words):
            return "REVIEW_PROGRESS"
        
        # Difficulty change patterns
        difficulty_words = ["too hard", "too easy", "easier", "harder", "challenge",
                           "صعب جدا", "سهل جدا", "أسهل", "أصعب"]
        if any(word in query for word in difficulty_words):
            return "CHANGE_DIFFICULTY"
        
        # Check answer patterns
        check_words = ["is this correct", "check my answer", "my answer is", 
                      "هل هذا صحيح", "إجابتي"]
        if any(word in query for word in check_words):
            return "CHECK_ANSWER"
        
        return None  # Use LLM for classification
    
    def _route_to_handler(self, intent: str) -> BaseTutorHandler:
        """
        Route to the appropriate handler based on intent.
        
        Args:
            intent: Classified intent
            
        Returns:
            The handler to process this intent
        """
        routing = {
            "EXPLAIN": self.handlers["explanation"],
            "PRACTICE": self.handlers["question_generator"],
            "CHECK_ANSWER": self.handlers["feedback"],
            "ASK_QUESTION": self.handlers["explanation"],
            "GET_FEEDBACK": self.handlers["feedback"],
            "REVIEW_PROGRESS": self.handlers["progress_tracker"],
            "CHANGE_DIFFICULTY": self.handlers["adaptive_learning"],
            "GREETING": self.handlers["explanation"],  # Friendly greeting handler
            "GENERAL_CHAT": self.handlers["explanation"],
        }
        
        return routing.get(intent, self.handlers["explanation"])
    
    def _get_error_response(self, language: str) -> str:
        """Get user-friendly error response."""
        if language == "ar":
            return "عذراً، واجهت مشكلة. هل يمكنك إعادة صياغة سؤالك؟"
        return "I apologize, I encountered an issue. Could you please rephrase your question?"
    
    async def start_session(
        self,
        student_id: str,
        document_id: Optional[str] = None,
        topic: Optional[str] = None,
        language: str = "en",
        difficulty: str = "intermediate"
    ) -> TutorState:
        """
        Start a new tutoring session.
        
        Args:
            student_id: ID of the student
            document_id: Optional document to focus on
            topic: Optional topic to start with
            language: Preferred language (en/ar)
            difficulty: Starting difficulty level
            
        Returns:
            Initialized TutorState
        """
        session_id = str(uuid.uuid4())
        
        # Create student profile
        profile = StudentProfile(
            student_id=student_id,
            current_level=DifficultyLevel(difficulty),
            preferred_language=language
        )
        
        # Create initial state
        state = TutorState(
            session_id=session_id,
            student_profile=profile,
            query="",
            current_topic=topic,
            current_document_id=document_id,
            language=language,
            current_difficulty=DifficultyLevel(difficulty)
        )
        
        # Generate welcome message
        welcome = await self._generate_welcome(state)
        state.response = welcome
        state.add_message("tutor", welcome)
        
        logger.info(f"Started new session {session_id} for student {student_id}")
        
        return state
    
    async def _generate_welcome(self, state: TutorState) -> str:
        """Generate a personalized welcome message."""
        
        if state.language == "ar":
            base = "مرحباً! أنا IRIS، معلمك الشخصي. "
            if state.current_topic:
                base += f"أرى أنك تريد التعلم عن {state.current_topic}. "
            base += "كيف يمكنني مساعدتك اليوم؟ 📚"
        else:
            base = "Hello! I'm IRIS, your personal tutor. "
            if state.current_topic:
                base += f"I see you want to learn about {state.current_topic}. "
            base += "How can I help you today? 📚"
        
        return base
    
    def get_handler(self, handler_name: str) -> Optional[BaseTutorHandler]:
        """Get a specific handler by name."""
        return self.handlers.get(handler_name)
    
    async def generate_practice(
        self,
        state: TutorState,
        topic: str,
        count: int = 5,
        db_session: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """
        Convenience method to generate practice questions.
        
        Args:
            state: Current tutor state
            topic: Topic for questions
            count: Number of questions
            db_session: Optional database session
            
        Returns:
            Dictionary with questions
        """
        state.current_topic = topic
        state.query = f"Generate {count} practice questions about {topic}"
        
        handler = self.handlers["question_generator"]
        return await handler.handle(state, db_session=db_session)
    
    async def check_understanding(
        self,
        state: TutorState,
        topic: str,
        db_session: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """
        Check student's understanding of a topic.
        
        Args:
            state: Current tutor state
            topic: Topic to assess
            db_session: Optional database session
            
        Returns:
            Assessment results with recommendations
        """
        state.current_topic = topic
        state.query = f"Assess my understanding of {topic}"
        
        handler = self.handlers["adaptive_learning"]
        return await handler.handle(state, db_session=db_session)
