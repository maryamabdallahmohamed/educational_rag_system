"""
Tutor Agent API Routes

API endpoints for the AI Tutor Agent, providing:
- Session management
- Chat interface
- Progress tracking
- Practice question generation
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, AsyncGenerator
from datetime import datetime
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.agents.tutor_agent import (
    TutorAgent, 
    TutorState, 
    StudentProfile, 
    DifficultyLevel
)
from backend.models.llms.groq_llm import GroqLLM
from backend.models.embedders.hf_embedder import HFEmbedder
from backend.core.rag.rag_orchestrator import RAGOrchestrator
from backend.database.db import NeonDatabase
from backend.utils.logger_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/tutor", tags=["Tutor Agent"])


# ============================================================================ #
# Request/Response Models
# ============================================================================ #

class StartSessionRequest(BaseModel):
    """Request to start a new tutoring session."""
    student_id: str
    student_name: Optional[str] = None
    document_id: Optional[str] = None
    topic: Optional[str] = None
    language: str = "en"
    difficulty: str = "intermediate"


class StartSessionResponse(BaseModel):
    """Response after starting a session."""
    session_id: str
    welcome_message: str
    suggested_topics: List[str] = Field(default_factory=list)
    student_profile: Dict[str, Any]


class TutorChatRequest(BaseModel):
    """Request for a chat interaction."""
    session_id: str
    student_id: str
    message: str
    document_id: Optional[str] = None
    topic: Optional[str] = None


class TutorChatResponse(BaseModel):
    """Response from a chat interaction."""
    response: str
    intent_detected: Optional[str] = None
    handler_used: Optional[str] = None
    next_steps: List[str] = Field(default_factory=list)
    questions: Optional[List[Dict]] = None
    processing_time: float = 0.0


class ProgressRequest(BaseModel):
    """Request for progress report."""
    student_id: str


class ProgressResponse(BaseModel):
    """Response with progress data."""
    summary: str
    statistics: Dict[str, Any]
    recommendations: List[str]
    topic_progress: List[Dict]
    achievements: List[Dict] = Field(default_factory=list)


class GeneratePracticeRequest(BaseModel):
    """Request to generate practice questions."""
    topic: str
    difficulty: str = "intermediate"
    count: int = 5
    language: str = "en"
    student_id: Optional[str] = None


class GeneratePracticeResponse(BaseModel):
    """Response with practice questions."""
    questions: List[Dict]
    topic: str
    difficulty: str
    count: int


class CheckAnswerRequest(BaseModel):
    """Request to check a student's answer."""
    session_id: str
    student_id: str
    question_index: int
    student_answer: str


class CheckAnswerResponse(BaseModel):
    """Response with answer feedback."""
    is_correct: bool
    feedback: str
    explanation: Optional[str] = None
    score: float = 0.0


# ============================================================================ #
# Session Storage (In-Memory - Replace with Database in Production)
# ============================================================================ #

# Store active sessions in memory
active_sessions: Dict[str, TutorState] = {}
tutor_agent_instance: Optional[TutorAgent] = None
rag_orchestrator_instance: Optional[RAGOrchestrator] = None


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session."""
    session = NeonDatabase.get_session()
    try:
        yield session
    finally:
        await session.close()


def get_rag_orchestrator() -> RAGOrchestrator:
    """Get or create the RAG orchestrator instance."""
    global rag_orchestrator_instance
    if rag_orchestrator_instance is None:
        logger.info("Initializing RAG Orchestrator for Tutor Agent...")
        rag_orchestrator_instance = RAGOrchestrator(
            similarity_threshold=0.3,
            top_k=10,
            max_context_docs=5,
            max_content_length=5000
        )
        logger.info("RAG Orchestrator initialized")
    return rag_orchestrator_instance


def get_tutor_agent() -> TutorAgent:
    """Get or create the tutor agent instance with RAG integration."""
    global tutor_agent_instance
    if tutor_agent_instance is None:
        logger.info("Initializing Tutor Agent with RAG...")
        llm = GroqLLM()
        embedder = HFEmbedder()
        rag = get_rag_orchestrator()
        tutor_agent_instance = TutorAgent(
            llm=llm, 
            embedder=embedder,
            vector_store=rag  # Inject RAG orchestrator as the vector store
        )
        logger.info("Tutor Agent initialized successfully with RAG integration")
    return tutor_agent_instance


# ============================================================================ #
# API Endpoints
# ============================================================================ #

@router.post("/session/start", response_model=StartSessionResponse)
async def start_tutoring_session(
    request: StartSessionRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Start a new tutoring session.
    
    Creates a new session with personalized settings based on student preferences.
    Also creates database records for learner profile and session.
    """
    try:
        from backend.database.models.tutor_models import (
            LearnerProfileModel,
            TutoringSessionDBModel
        )
        import uuid as uuid_lib
        
        tutor = get_tutor_agent()
        
        # Create or get learner profile in database
        learner_id = uuid_lib.uuid4()
        
        # Check if learner exists by some identifier (simplified for demo)
        # In production, you'd look up by a stable identifier
        learner = LearnerProfileModel(
            id=learner_id,
            grade_level=8,
            preferred_language=request.language,
            difficulty_preference=request.difficulty,
            total_sessions=1
        )
        db.add(learner)
        await db.flush()  # Get the ID without committing
        
        # Create tutoring session in database
        session_id = uuid_lib.uuid4()
        db_session_record = TutoringSessionDBModel(
            id=session_id,
            learner_id=learner_id,
            current_topic=request.topic,
            is_active=True
        )
        db.add(db_session_record)
        await db.commit()
        
        # Now start the in-memory state with database IDs
        state = await tutor.start_session(
            student_id=str(learner_id),  # Use database learner ID
            document_id=request.document_id,
            topic=request.topic,
            language=request.language,
            difficulty=request.difficulty
        )
        
        # Override the session_id with database session ID
        state.session_id = str(session_id)
        state.student_profile.student_id = str(learner_id)
        
        # Update student name if provided
        if request.student_name:
            state.student_profile.name = request.student_name
        
        # Store session in memory (with database IDs)
        active_sessions[state.session_id] = state
        
        # Prepare suggested topics
        suggested_topics = [
            "Ask me to explain a concept",
            "Request practice questions",
            "Check your understanding",
            "Review your progress"
        ]
        if request.language == "ar":
            suggested_topics = [
                "اطلب مني شرح مفهوم",
                "اطلب أسئلة للتدريب",
                "تحقق من فهمك",
                "راجع تقدمك"
            ]
        
        logger.info(f"Started session {state.session_id} for student {request.student_id} (DB learner: {learner_id})")
        
        return StartSessionResponse(
            session_id=state.session_id,
            welcome_message=state.response,
            suggested_topics=suggested_topics,
            student_profile={
                "student_id": state.student_profile.student_id,
                "name": state.student_profile.name,
                "level": state.student_profile.current_level,
                "language": state.student_profile.preferred_language
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to start session: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat", response_model=TutorChatResponse)
async def tutor_chat(
    request: TutorChatRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Send a message to the tutor and get a response.
    
    The tutor will classify the intent and route to the appropriate handler.
    Database persistence is enabled for tracking interactions.
    """
    try:
        tutor = get_tutor_agent()
        
        # Get or create session
        if request.session_id in active_sessions:
            state = active_sessions[request.session_id]
        else:
            # Create new session if not exists
            state = await tutor.start_session(
                student_id=request.student_id,
                document_id=request.document_id,
                topic=request.topic
            )
            active_sessions[state.session_id] = state
        
        # Update query and context
        state.query = request.message
        if request.document_id:
            state.current_document_id = request.document_id
        if request.topic:
            state.current_topic = request.topic
        
        # Process with tutor agent (pass db_session for persistence)
        result_state = await tutor.process(state, db_session=db)
        
        # Update stored session
        active_sessions[request.session_id] = result_state
        
        return TutorChatResponse(
            response=result_state.response or "I'm thinking...",
            intent_detected=result_state.intent,
            handler_used=result_state.handler_used,
            next_steps=result_state.next_steps,
            questions=result_state.generated_questions if result_state.generated_questions else None,
            processing_time=result_state.processing_time
        )
        
    except Exception as e:
        logger.error(f"Tutor chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/progress/{student_id}", response_model=ProgressResponse)
async def get_student_progress(
    student_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get the learning progress for a student.
    
    The student_id can be either the learner UUID or a session UUID.
    Returns statistics from database, achievements, and recommendations.
    """
    try:
        tutor = get_tutor_agent()
        
        # Find session for this student (matches on student_profile.student_id)
        student_state = None
        for session_id, state in active_sessions.items():
            if state.student_profile.student_id == student_id:
                student_state = state
                break
            # Also check if the provided ID is actually a session_id
            if session_id == student_id:
                student_state = state
                break
        
        if not student_state:
            # Create a minimal state for progress check with the provided ID as session_id
            # This allows looking up by either learner_id or session_id
            student_state = TutorState(
                session_id=student_id,  # Try using the ID as session_id for DB lookup
                student_profile=StudentProfile(student_id=student_id),
                query="Show my progress"
            )
        
        # Get progress from handler (pass db_session to load real data)
        handler = tutor.get_handler("progress_tracker")
        result = await handler.handle(student_state, db_session=db)
        
        return ProgressResponse(
            summary=result.get("response", "No progress data available."),
            statistics=result.get("statistics", {}),
            recommendations=result.get("recommendations", []),
            topic_progress=result.get("topic_progress", []),
            achievements=result.get("achievements", [])
        )
        
    except Exception as e:
        logger.error(f"Progress fetch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/practice/generate", response_model=GeneratePracticeResponse)
async def generate_practice_questions(request: GeneratePracticeRequest):
    """
    Generate practice questions for a topic.
    
    Creates various question types adapted to the specified difficulty.
    """
    try:
        tutor = get_tutor_agent()
        
        # Create state for question generation
        state = TutorState(
            session_id=str(uuid.uuid4()),
            student_profile=StudentProfile(
                student_id=request.student_id or "anonymous",
                current_level=DifficultyLevel(request.difficulty)
            ),
            query=f"Generate {request.count} practice questions about {request.topic}",
            current_topic=request.topic,
            language=request.language,
            current_difficulty=DifficultyLevel(request.difficulty)
        )
        
        # Generate questions
        handler = tutor.get_handler("question_generator")
        result = await handler.handle(state)
        
        questions = result.get("questions", [])
        
        return GeneratePracticeResponse(
            questions=questions,
            topic=request.topic,
            difficulty=request.difficulty,
            count=len(questions)
        )
        
    except Exception as e:
        logger.error(f"Practice generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/answer/check", response_model=CheckAnswerResponse)
async def check_student_answer(
    request: CheckAnswerRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Check a student's answer to a practice question.
    
    Provides feedback and explanation, persists interaction to database.
    """
    try:
        tutor = get_tutor_agent()
        
        # Get session
        if request.session_id not in active_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        state = active_sessions[request.session_id]
        
        # Check if we have questions
        if not state.generated_questions or request.question_index >= len(state.generated_questions):
            raise HTTPException(status_code=400, detail="Question not found")
        
        question = state.generated_questions[request.question_index]
        
        # Use feedback handler to evaluate
        handler = tutor.get_handler("feedback")
        
        # Prepare evaluation context
        eval_state = TutorState(
            session_id=request.session_id,
            student_profile=state.student_profile,
            query=f"Check answer: {request.student_answer}",
            current_topic=question.get("question", ""),
            language=state.language
        )
        
        # Pass db_session for persistence
        result = await handler.handle(eval_state, db_session=db)
        
        return CheckAnswerResponse(
            is_correct=result.get("is_correct", False),
            feedback=result.get("response", ""),
            explanation=question.get("explanation", ""),
            score=result.get("score", 0.0)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Answer check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/difficulty/adjust")
async def adjust_difficulty(
    session_id: str,
    direction: str  # "increase" or "decrease"
):
    """
    Manually adjust the difficulty level for a session.
    """
    try:
        if session_id not in active_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        state = active_sessions[session_id]
        current = state.current_difficulty
        
        if isinstance(current, str):
            current = DifficultyLevel(current)
        
        levels = list(DifficultyLevel)
        current_idx = levels.index(current)
        
        if direction == "increase" and current_idx < len(levels) - 1:
            new_level = levels[current_idx + 1]
        elif direction == "decrease" and current_idx > 0:
            new_level = levels[current_idx - 1]
        else:
            new_level = current
        
        state.current_difficulty = new_level
        active_sessions[session_id] = state
        
        return {
            "previous_level": current.value,
            "new_level": new_level.value,
            "message": f"Difficulty adjusted to {new_level.value}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Difficulty adjustment error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/session/{session_id}")
async def end_session(session_id: str):
    """
    End a tutoring session.
    """
    try:
        if session_id in active_sessions:
            state = active_sessions.pop(session_id)
            logger.info(f"Ended session {session_id}")
            return {
                "message": "Session ended successfully",
                "session_id": session_id,
                "interactions": len(state.conversation_history)
            }
        else:
            raise HTTPException(status_code=404, detail="Session not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"End session error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/active")
async def get_active_sessions():
    """
    Get list of active sessions (for debugging/admin).
    """
    return {
        "count": len(active_sessions),
        "sessions": [
            {
                "session_id": sid,
                "student_id": state.student_profile.student_id,
                "topic": state.current_topic,
                "interactions": len(state.conversation_history)
            }
            for sid, state in active_sessions.items()
        ]
    }


# ============================================================================ #
# Health Check
# ============================================================================ #

@router.get("/health")
async def tutor_health():
    """Health check for tutor agent."""
    tutor = get_tutor_agent()
    return {
        "status": "ok",
        "agent_initialized": tutor is not None,
        "active_sessions": len(active_sessions)
    }
