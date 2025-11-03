from langchain_core.tools import Tool
from backend.core.agents.base_handler import BaseHandler
from backend.database.repositories.tutoring_session_repo import TutoringSessionRepository
from backend.database.repositories.learner_profile_repo import LearnerProfileRepository
from backend.database.db import NeonDatabase
import time
import uuid
import asyncio
from datetime import datetime
from typing import Dict, Any


class SessionManagerHandler(BaseHandler):
    """
    Manages tutoring session lifecycle and learner context
    """

    def __init__(self):
        super().__init__()
    
    def tool(self) -> Tool:
        """Return configured LangChain Tool for session management"""
        return Tool(
            name="manage_tutoring_session",
            description="Manage tutoring session lifecycle - start, continue, or end sessions. Load learner profile and session context.",
            func=self._process_wrapper
        )
    
    def _process_wrapper(self, action: str) -> str:
        """Wrapper for tool execution with error handling"""
        try:   
            return asyncio.run(self._process(action))
        except Exception as e:
            return self._handle_error(e, "session_management")
    
    async def _process(self, action: str) -> str:
        """Process session management request"""
        start_time = time.time()
        
        try:
            self.logger.info(f"Starting session management action: {action}")

            if not self._validate_state():
                return "Unable to process session management - no state available"

            # Get learner_id from state
            learner_id = self.current_state.get("learner_id")
            if not learner_id:
                return "No learner ID provided in state. Cannot manage session."

            # Check if this is a guest session
            is_guest_session = self.current_state.get("guest_session", False) or learner_id.startswith("guest_")
            
            if is_guest_session:
                self.logger.info("Guest session detected - providing simplified session management")
                return self._handle_guest_session(action, learner_id)

            result = ""
            
            if action == "start":
                session_data = await self._start_session(learner_id)
                result = f"Started new tutoring session {session_data['session_id']} for learner {learner_id}. " \
                        f"Loaded profile: Grade {session_data['profile']['grade_level']}, " \
                        f"Learning style: {session_data['profile'].get('learning_style', 'not specified')}"
                
            elif action == "continue":
                context_data = await self._load_learner_context(learner_id)
                if context_data.get('active_session'):
                    result = f"Continuing session {context_data['active_session']['session_id']}. " \
                            f"Current topic: {context_data['active_session'].get('current_topic', 'none set')}"
                else:
                    # No active session, start new one
                    session_data = await self._start_session(learner_id)
                    result = f"No active session found. Started new session {session_data['session_id']}"
                    
            elif action == "end":
                session_id = self.current_state.get("tutoring_session_id")
                if not session_id:
                    return "No active session to end"
                
                # Create performance summary from current state
                summary = self._create_performance_summary()
                end_data = await self._end_current_session(session_id, summary)
                result = f"Ended session {session_id}. Duration: {end_data.get('duration', 'unknown')}, " \
                        f"Performance summary saved."
                
            elif action == "load_context":
                context_data = await self._load_learner_context(learner_id)
                result = f"Loaded context for learner {learner_id}. " \
                        f"Profile: Grade {context_data['profile']['grade_level']}, " \
                        f"Total sessions: {context_data['profile']['total_sessions']}"
                        
            else:
                return f"Unknown session management action: {action}. " \
                       f"Supported actions: start, continue, end, load_context"

            # Calculate processing time
            processing_time = int((time.time() - start_time) * 1000)
            self.logger.info(f"Processed session management in {processing_time}ms")

            return result

        except Exception as e:
            self.logger.error(f"Error in session management: {e}")
            return f"I encountered an error while managing the tutoring session: {str(e)}"

    async def _start_session(self, learner_id: str) -> Dict[str, Any]:
        """Start a new tutoring session and load learner profile"""
        async with NeonDatabase.get_session() as session:
            try:
                # Load repositories
                session_repo = TutoringSessionRepository(session)
                profile_repo = LearnerProfileRepository(session)
                
                # Load learner profile
                profile = await profile_repo.get_by_id(uuid.UUID(learner_id))
                if not profile:
                    raise ValueError(f"Learner profile not found for ID: {learner_id}")
                
                # Check if there's an active session and end it first
                active_session = await session_repo.get_active_session(uuid.UUID(learner_id))
                if active_session:
                    await session_repo.end_session(
                        active_session.id,
                        {"reason": "new_session_started", "ended_by": "system"}
                    )
                    self.logger.info(f"Ended previous active session: {active_session.id}")
                
                # Create new session
                new_session = await session_repo.create_session(
                    learner_id=uuid.UUID(learner_id)
                )
                
                # Convert profile to dict for state
                profile_dict = {
                    "id": str(profile.id),
                    "grade_level": profile.grade_level,
                    "learning_style": profile.learning_style,
                    "preferred_language": profile.preferred_language,
                    "difficulty_preference": profile.difficulty_preference,
                    "accuracy_rate": profile.accuracy_rate,
                    "avg_response_time": profile.avg_response_time,
                    "total_sessions": profile.total_sessions,
                    "mastered_topics": profile.mastered_topics or []
                }
                
                # Update state with learner context
                self.current_state["learner_profile"] = profile_dict
                self.current_state["tutoring_session_id"] = str(new_session.id)
                self.current_state["session_state"] = {
                    "started_at": new_session.started_at.isoformat(),
                    "is_active": True,
                    "current_topic": None,
                    "progress_percent": 0
                }
                
                self.logger.info(f"Started new session: {new_session.id} for learner: {learner_id}")
                
                return {
                    "session_id": str(new_session.id),
                    "profile": profile_dict,
                    "session": {
                        "started_at": new_session.started_at.isoformat(),
                        "is_active": True
                    }
                }
                
            except Exception as e:
                self.logger.error(f"Error starting session: {e}")
                raise

    async def _load_learner_context(self, learner_id: str) -> Dict[str, Any]:
        """Load learner profile and active session context"""
        async with NeonDatabase.get_session() as session:
            try:
                # Load repositories
                session_repo = TutoringSessionRepository(session)
                profile_repo = LearnerProfileRepository(session)
                
                # Load learner profile
                profile = await profile_repo.get_by_id(uuid.UUID(learner_id))
                if not profile:
                    raise ValueError(f"Learner profile not found for ID: {learner_id}")
                
                # Load active session if exists
                active_session = await session_repo.get_active_session(uuid.UUID(learner_id))
                
                # Convert profile to dict
                profile_dict = {
                    "id": str(profile.id),
                    "grade_level": profile.grade_level,
                    "learning_style": profile.learning_style,
                    "preferred_language": profile.preferred_language,
                    "difficulty_preference": profile.difficulty_preference,
                    "accuracy_rate": profile.accuracy_rate,
                    "avg_response_time": profile.avg_response_time,
                    "total_sessions": profile.total_sessions,
                    "mastered_topics": profile.mastered_topics or []
                }
                
                # Update state with profile
                self.current_state["learner_profile"] = profile_dict
                
                result = {"profile": profile_dict}
                
                if active_session:
                    session_dict = {
                        "session_id": str(active_session.id),
                        "started_at": active_session.started_at.isoformat(),
                        "current_topic": active_session.current_topic,
                        "session_state": active_session.session_state or {},
                        "is_active": active_session.is_active
                    }
                    
                    # Update state with session context
                    self.current_state["tutoring_session_id"] = str(active_session.id)
                    self.current_state["session_state"] = session_dict["session_state"]
                    
                    result["active_session"] = session_dict
                    
                self.logger.info(f"Loaded context for learner: {learner_id}")
                
                return result
                
            except Exception as e:
                self.logger.error(f"Error loading learner context: {e}")
                raise

    async def _end_current_session(self, session_id: str, summary: Dict[str, Any]) -> Dict[str, Any]:
        """End the current tutoring session with performance summary"""
        async with NeonDatabase.get_session() as session:
            try:
                session_repo = TutoringSessionRepository(session)
                
                # End the session
                ended_session = await session_repo.end_session(
                    session_id=uuid.UUID(session_id),
                    performance_summary=summary
                )
                
                if not ended_session:
                    raise ValueError(f"Failed to end session: {session_id}")
                
                # Calculate session duration
                duration_seconds = None
                if ended_session.started_at and ended_session.ended_at:
                    duration = ended_session.ended_at - ended_session.started_at
                    duration_seconds = int(duration.total_seconds())
                
                # Clear session-related state
                self.current_state["tutoring_session_id"] = None
                self.current_state["session_state"] = None
                
                self.logger.info(f"Ended session: {session_id}")
                
                return {
                    "session_id": session_id,
                    "ended_at": ended_session.ended_at.isoformat(),
                    "duration": f"{duration_seconds // 60}min {duration_seconds % 60}s" if duration_seconds else "unknown",
                    "performance_summary": summary
                }
                
            except Exception as e:
                self.logger.error(f"Error ending session: {e}")
                raise

    def _create_performance_summary(self) -> Dict[str, Any]:
        """Create performance summary from current state"""
        summary = {
            "session_ended_at": datetime.utcnow().isoformat(),
            "ended_by": "session_manager"
        }
        
        # Add any available metrics from state
        if self.current_state.get("learning_progress"):
            summary.update(self.current_state["learning_progress"])
            
        if self.current_state.get("interaction_history"):
            interactions = self.current_state["interaction_history"]
            summary["total_interactions"] = len(interactions)
            summary["interaction_types"] = list(set(i.get("type", "unknown") for i in interactions))
            
        return summary

    def _handle_guest_session(self, action: str, learner_id: str) -> str:
        """Handle session management for guest users without database operations"""
        
        if action == "start":
            # Guest session is already initialized in TutorAgent
            profile = self.current_state.get("learner_profile", {})
            session_id = self.current_state.get("tutoring_session_id", f"guest_session_{learner_id}")
            
            return f"Welcome to your tutoring session! I've created a personalized learning profile based on your query. " \
                   f"Grade level: {profile.get('grade_level', 'middle school')}, " \
                   f"Learning style: {profile.get('learning_style', 'mixed')}, " \
                   f"Difficulty: {profile.get('difficulty_preference', 'medium')}. " \
                   f"Let's start learning together!"
                   
        elif action == "continue":
            return "Your guest session is active. What would you like to learn about next?"
            
        elif action == "end":
            return "Thank you for using our tutoring service! Your guest session has ended. " \
                   "Feel free to ask me any questions anytime."
                   
        elif action == "load_context":
            profile = self.current_state.get("learner_profile", {})
            return f"Guest learner profile: Grade {profile.get('grade_level', 'unknown')}, " \
                   f"Learning style: {profile.get('learning_style', 'mixed')}, " \
                   f"Language: {profile.get('preferred_language', 'English')}"
                   
        else:
            return f"Guest session active. I can help you learn regardless of the session state. " \
                   f"What would you like to explore?"
