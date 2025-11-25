"""
Tutor Agent State Definitions

This module defines all the data models and state classes used by the Tutor Agent
for managing student profiles, learning progress, and tutoring sessions.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class DifficultyLevel(str, Enum):
    """Difficulty levels for educational content."""
    BEGINNER = "beginner"
    ELEMENTARY = "elementary"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class LearningStyle(str, Enum):
    """Learning style preferences for adaptive teaching."""
    VISUAL = "visual"
    AUDITORY = "auditory"
    READING_WRITING = "reading_writing"
    KINESTHETIC = "kinesthetic"


class StudentProfile(BaseModel):
    """
    Student profile for personalized learning.
    
    Contains all information needed to adapt the tutoring experience
    to the individual student's needs, preferences, and progress.
    """
    student_id: str
    name: Optional[str] = None
    current_level: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    learning_style: LearningStyle = LearningStyle.READING_WRITING
    preferred_language: str = "en"
    subjects_of_interest: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    areas_for_improvement: List[str] = Field(default_factory=list)
    total_sessions: int = 0
    total_questions_answered: int = 0
    correct_answers: int = 0
    
    class Config:
        use_enum_values = True


class LearningProgress(BaseModel):
    """
    Track learning progress for a specific topic.
    
    Maintains detailed metrics about a student's journey
    through a particular topic or subject area.
    """
    topic_id: str
    topic_name: str
    mastery_level: float = 0.0  # 0.0 to 1.0
    concepts_covered: List[str] = Field(default_factory=list)
    concepts_mastered: List[str] = Field(default_factory=list)
    concepts_struggling: List[str] = Field(default_factory=list)
    practice_attempts: int = 0
    practice_correct: int = 0
    time_spent_minutes: int = 0
    last_accessed: Optional[datetime] = None
    
    @property
    def accuracy(self) -> float:
        """Calculate accuracy percentage."""
        if self.practice_attempts == 0:
            return 0.0
        return self.practice_correct / self.practice_attempts


class TutorMessage(BaseModel):
    """
    A message in the tutoring conversation.
    
    Tracks individual messages exchanged between the student
    and the tutor agent with metadata for analysis.
    """
    role: str  # "student" or "tutor"
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        arbitrary_types_allowed = True


class TutorState(BaseModel):
    """
    Complete state for the tutor agent.
    
    This is the main state object that flows through the tutor agent,
    containing all context needed for personalized tutoring.
    """
    # Session info
    session_id: str
    student_profile: StudentProfile
    
    # Current interaction
    query: str
    intent: Optional[str] = None
    response: Optional[str] = None
    
    # Context
    current_topic: Optional[str] = None
    current_document_id: Optional[str] = None
    retrieved_context: List[str] = Field(default_factory=list)
    
    # Conversation
    conversation_history: List[TutorMessage] = Field(default_factory=list)
    
    # Learning tracking
    learning_progress: Dict[str, LearningProgress] = Field(default_factory=dict)
    current_difficulty: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    
    # Tutoring state
    is_assessing: bool = False
    assessment_questions: List[Dict[str, Any]] = Field(default_factory=list)
    pending_feedback: Optional[str] = None
    
    # Generated content
    generated_questions: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Next steps
    next_steps: List[str] = Field(default_factory=list)
    suggested_topics: List[str] = Field(default_factory=list)
    
    # Metadata
    language: str = "en"
    error: Optional[str] = None
    processing_time: float = 0.0
    handler_used: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True
        use_enum_values = True
    
    def add_message(self, role: str, content: str, metadata: Dict[str, Any] = None):
        """Add a message to conversation history."""
        message = TutorMessage(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        self.conversation_history.append(message)
    
    def get_recent_history(self, n: int = 5) -> List[TutorMessage]:
        """Get the n most recent messages."""
        return self.conversation_history[-n:] if self.conversation_history else []
    
    def format_history_for_prompt(self, n: int = 5) -> str:
        """Format recent history as a string for LLM prompts."""
        history = self.get_recent_history(n)
        if not history:
            return "No previous conversation."
        return "\n".join([f"{m.role}: {m.content}" for m in history])
