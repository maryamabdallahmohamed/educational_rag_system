from langchain_core.tools import Tool
from backend.core.agents.base_handler import BaseHandler
from backend.database.repositories.learner_profile_repo import LearnerProfileRepository
from backend.database.db import NeonDatabase
import time
import uuid
import asyncio
import json
from typing import Dict, Any
from backend.utils.logger_config import get_logger


class LearnerModelManagerHandler(BaseHandler):
    """
    Manages and updates learner profile data based on interactions
    """

    def __init__(self):
        super().__init__()
    
    def tool(self) -> Tool:
        """Return configured LangChain Tool for learner model management"""
        return Tool(
            name="update_learner_model",
            description="Update learner profile based on performance, add mastered topics, or log learning struggles",
            func=self._process_wrapper
        )
    
    def _process_wrapper(self, update_type_and_data: str) -> str:
        """Wrapper for tool execution with error handling"""
        try:
            # Parse the input string to extract update_type and data
            parts = update_type_and_data.split(":", 1)
            if len(parts) != 2:
                return "Invalid input format. Expected 'update_type:data'"
            
            update_type, data = parts[0].strip(), parts[1].strip()
            return asyncio.run(self._process(update_type, data))
        except Exception as e:
            return self._handle_error(e, "learner_model_update")
    
    async def _process(self, update_type: str, data: str) -> str:
        """Process learner model update request"""
        start_time = time.time()
        
        try:
            self.logger.info(f"Starting learner model update: {update_type}")

            if not self._validate_state():
                return "Unable to process learner model update - no state available"

            # Get learner_id from state
            learner_id = self.current_state.get("learner_id")
            if not learner_id:
                return "No learner ID provided in state. Cannot update learner model."

            result = ""
            
            if update_type == "performance":
                performance_data = await self._parse_performance_data(data)
                updated_profile = await self._update_performance_metrics(learner_id, performance_data)
                if updated_profile:
                    result = f"Updated performance metrics for learner {learner_id}. " \
                            f"New accuracy: {updated_profile.accuracy_rate:.2f}, " \
                            f"Avg response time: {updated_profile.avg_response_time:.1f}s, " \
                            f"Total sessions: {updated_profile.total_sessions}"
                    
                    # Update state with new profile data
                    await self._refresh_learner_profile_in_state(learner_id)
                else:
                    result = "Failed to update performance metrics"
                
            elif update_type == "mastered_topic":
                success = await self._add_mastered_topic(learner_id, data)
                if success:
                    result = f"Added '{data}' to mastered topics for learner {learner_id}"
                    await self._refresh_learner_profile_in_state(learner_id)
                else:
                    result = f"Failed to add mastered topic: {data}"
                    
            elif update_type == "struggle":
                struggle_data = await self._parse_struggle_data(data)
                success = await self._add_learning_struggle(learner_id, struggle_data)
                if success:
                    result = f"Logged learning struggle for learner {learner_id}: " \
                            f"{struggle_data['topic']} ({struggle_data['type']})"
                    await self._refresh_learner_profile_in_state(learner_id)
                else:
                    result = f"Failed to log learning struggle: {data}"
                    
            elif update_type == "preferences":
                preferences_data = await self._parse_preferences_data(data)
                updated_profile = await self._update_preferences(learner_id, preferences_data)
                if updated_profile:
                    result = f"Updated preferences for learner {learner_id}: " \
                            f"{', '.join([f'{k}={v}' for k, v in preferences_data.items()])}"
                    await self._refresh_learner_profile_in_state(learner_id)
                else:
                    result = f"Failed to update preferences: {data}"
                    
            else:
                return f"Unknown update type: {update_type}. " \
                       f"Supported types: performance, mastered_topic, struggle, preferences"

            # Calculate processing time
            processing_time = int((time.time() - start_time) * 1000)
            self.logger.info(f"Processed learner model update in {processing_time}ms")

            return result

        except Exception as e:
            self.logger.error(f"Error in learner model management: {e}")
            return f"I encountered an error while updating the learner model: {str(e)}"

    async def _parse_performance_data(self, data: str) -> Dict[str, Any]:
        """Parse performance data from string (JSON or simple format)"""
        try:
            # Try to parse as JSON first
            if data.strip().startswith('{'):
                performance_data = json.loads(data)
            else:
                # Parse simple format like "accuracy=0.85,response_time=12.5,completed=true"
                performance_data = {}
                pairs = data.split(',')
                for pair in pairs:
                    if '=' in pair:
                        key, value = pair.strip().split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Convert values to appropriate types
                        if key in ['accuracy', 'response_time']:
                            performance_data[key] = float(value)
                        elif key in ['completed', 'session_completed']:
                            performance_data[key] = value.lower() in ['true', '1', 'yes']
                        else:
                            performance_data[key] = value
            
            # Ensure required fields with defaults
            return {
                'new_accuracy': performance_data.get('accuracy', 0.0),
                'new_response_time': performance_data.get('response_time', 0.0),
                'session_completed': performance_data.get('completed', False) or performance_data.get('session_completed', False)
            }
            
        except (json.JSONDecodeError, ValueError) as e:
            self.logger.warning(f"Failed to parse performance data: {data}, error: {e}")
            # Return default values
            return {
                'new_accuracy': 0.0,
                'new_response_time': 0.0,
                'session_completed': False
            }

    async def _parse_struggle_data(self, data: str) -> Dict[str, str]:
        """Parse struggle data from string"""
        try:
            # Try JSON format first
            if data.strip().startswith('{'):
                struggle_data = json.loads(data)
                return {
                    'topic': struggle_data.get('topic', 'unknown'),
                    'type': struggle_data.get('type', 'general_difficulty')
                }
            else:
                # Parse simple format like "topic:fractions,type:conceptual"
                struggle_data = {'topic': 'unknown', 'type': 'general_difficulty'}
                pairs = data.split(',')
                for pair in pairs:
                    if ':' in pair:
                        key, value = pair.strip().split(':', 1)
                        key = key.strip()
                        value = value.strip()
                        if key in ['topic', 'type']:
                            struggle_data[key] = value
                
                # If no topic specified, use the whole data as topic
                if struggle_data['topic'] == 'unknown' and data:
                    struggle_data['topic'] = data
                    
                return struggle_data
                
        except (json.JSONDecodeError, ValueError) as e:
            self.logger.warning(f"Failed to parse struggle data: {data}, error: {e}")
            return {'topic': data if data else 'unknown', 'type': 'general_difficulty'}

    async def _parse_preferences_data(self, data: str) -> Dict[str, Any]:
        """Parse preferences data from string"""
        try:
            # Try JSON format first
            if data.strip().startswith('{'):
                return json.loads(data)
            else:
                # Parse simple format like "learning_style=visual,difficulty=medium"
                preferences = {}
                pairs = data.split(',')
                for pair in pairs:
                    if '=' in pair:
                        key, value = pair.strip().split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        preferences[key] = value
                return preferences
                
        except (json.JSONDecodeError, ValueError) as e:
            self.logger.warning(f"Failed to parse preferences data: {data}, error: {e}")
            return {}

    async def _update_performance_metrics(self, learner_id: str, performance_data: Dict[str, Any]) -> Any:
        """Update learner performance metrics"""
        async with NeonDatabase.get_session() as session:
            try:
                profile_repo = LearnerProfileRepository(session)
                
                updated_profile = await profile_repo.update_performance_metrics(
                    profile_id=uuid.UUID(learner_id),
                    new_accuracy=performance_data['new_accuracy'],
                    new_response_time=performance_data['new_response_time'],
                    session_completed=performance_data['session_completed']
                )
                
                self.logger.info(f"Updated performance metrics for learner: {learner_id}")
                return updated_profile
                
            except Exception as e:
                self.logger.error(f"Error updating performance metrics: {e}")
                raise

    async def _add_mastered_topic(self, learner_id: str, topic: str) -> bool:
        """Add a mastered topic to learner profile"""
        async with NeonDatabase.get_session() as session:
            try:
                profile_repo = LearnerProfileRepository(session)
                
                success = await profile_repo.add_mastered_topic(
                    profile_id=uuid.UUID(learner_id),
                    topic=topic
                )
                
                self.logger.info(f"Added mastered topic '{topic}' for learner: {learner_id}")
                return success
                
            except Exception as e:
                self.logger.error(f"Error adding mastered topic: {e}")
                raise

    async def _add_learning_struggle(self, learner_id: str, struggle_data: Dict[str, str]) -> bool:
        """Add a learning struggle to learner profile"""
        async with NeonDatabase.get_session() as session:
            try:
                profile_repo = LearnerProfileRepository(session)
                
                success = await profile_repo.add_learning_struggle(
                    profile_id=uuid.UUID(learner_id),
                    topic=struggle_data['topic'],
                    struggle_type=struggle_data['type']
                )
                
                self.logger.info(f"Added learning struggle for learner: {learner_id}")
                return success
                
            except Exception as e:
                self.logger.error(f"Error adding learning struggle: {e}")
                raise

    async def _update_preferences(self, learner_id: str, preferences: Dict[str, Any]) -> Any:
        """Update learner preferences"""
        async with NeonDatabase.get_session() as session:
            try:
                profile_repo = LearnerProfileRepository(session)
                
                updated_profile = await profile_repo.update_profile(
                    profile_id=uuid.UUID(learner_id),
                    **preferences
                )
                
                self.logger.info(f"Updated preferences for learner: {learner_id}")
                return updated_profile
                
            except Exception as e:
                self.logger.error(f"Error updating preferences: {e}")
                raise

    async def _refresh_learner_profile_in_state(self, learner_id: str):
        """Refresh the learner profile data in current state"""
        async with NeonDatabase.get_session() as session:
            try:
                profile_repo = LearnerProfileRepository(session)
                profile = await profile_repo.get_by_id(uuid.UUID(learner_id))
                
                if profile and self.current_state:
                    # Update state with fresh profile data
                    profile_dict = {
                        "id": str(profile.id),
                        "grade_level": profile.grade_level,
                        "learning_style": profile.learning_style,
                        "preferred_language": profile.preferred_language,
                        "difficulty_preference": profile.difficulty_preference,
                        "accuracy_rate": profile.accuracy_rate,
                        "avg_response_time": profile.avg_response_time,
                        "total_sessions": profile.total_sessions,
                        "mastered_topics": profile.mastered_topics or [],
                        "learning_struggles": profile.learning_struggles or []
                    }
                    
                    self.current_state["learner_profile"] = profile_dict
                    self.logger.debug(f"Refreshed learner profile in state for: {learner_id}")
                
            except Exception as e:
                self.logger.warning(f"Failed to refresh profile in state: {e}")
                # Don't raise - this is not critical
