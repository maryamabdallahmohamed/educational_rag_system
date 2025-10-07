from langchain_core.tools import Tool
from backend.core.agents.base_handler import BaseHandler
from backend.database.repositories.learner_interaction_repo import LearnerInteractionRepository
from backend.database.repositories.tutoring_session_repo import TutoringSessionRepository
from backend.database.db import NeonDatabase
import time
import uuid
import asyncio
import json
from typing import Dict, Any, Optional
from backend.utils.logger_config import get_logger


class InteractionLoggerHandler(BaseHandler):
    """
    Logs all tutor-learner interactions for analytics
    """

    def __init__(self):
        super().__init__()
    
    def tool(self) -> Tool:
        """Return configured LangChain Tool for interaction logging"""
        return Tool(
            name="log_interaction",
            description="Log a tutoring interaction (question, explanation, practice, assessment, hint, feedback) with query and response",
            func=self._process_wrapper
        )
    
    def _process_wrapper(self, interaction_data: str) -> str:
        """Wrapper for tool execution with error handling"""
        try:   
            return asyncio.run(self._process(interaction_data))
        except Exception as e:
            return self._handle_error(e, "interaction_logging")
    
    async def _process(self, interaction_data: str) -> str:
        """Process interaction logging request"""
        start_time = time.time()
        
        try:
            self.logger.info("Starting interaction logging")

            if not self._validate_state():
                return "Unable to log interaction - no state available"

            # Get session_id from state
            session_id = self.current_state.get("tutoring_session_id")
            if not session_id:
                return "No active tutoring session found in state. Cannot log interaction."

            # Parse interaction data
            parsed_data = await self._parse_interaction_data(interaction_data)
            if not parsed_data:
                return "Failed to parse interaction data. Please provide valid JSON with interaction_type, query_text, and response_text."

            # Validate required fields
            required_fields = ['interaction_type', 'query_text', 'response_text']
            missing_fields = [field for field in required_fields if not parsed_data.get(field)]
            if missing_fields:
                return f"Missing required fields: {', '.join(missing_fields)}"

            # Log the interaction
            interaction = await self._log_interaction_to_database(session_id, parsed_data)
            if not interaction:
                return "Failed to log interaction to database"

            # Update session interaction history
            interaction_summary = await self._create_interaction_summary(parsed_data)
            history_updated = await self._update_session_history(session_id, interaction_summary)

            # Update state with latest interaction
            await self._update_state_with_interaction(interaction_summary)

            # Calculate processing time
            processing_time = int((time.time() - start_time) * 1000)
            self.logger.info(f"Logged interaction in {processing_time}ms")

            # Create response message
            result = f"Logged {parsed_data['interaction_type']} interaction {interaction.id}. "
            if parsed_data.get('learning_unit_id'):
                result += f"Learning unit: {parsed_data['learning_unit_id']}. "
            if parsed_data.get('difficulty_rating'):
                result += f"Difficulty: {parsed_data['difficulty_rating']}/5. "
            if history_updated:
                result += "Session history updated."
            else:
                result += "Warning: Session history update failed."

            return result

        except Exception as e:
            self.logger.error(f"Error in interaction logging: {e}")
            return f"I encountered an error while logging the interaction: {str(e)}"

    async def _parse_interaction_data(self, data: str) -> Optional[Dict[str, Any]]:
        """Parse interaction data from JSON string"""
        try:
            # Clean the data string
            data = data.strip()
            
            # Try to parse as JSON
            if data.startswith('{') and data.endswith('}'):
                interaction_data = json.loads(data)
            else:
                self.logger.warning(f"Data does not appear to be JSON: {data[:100]}...")
                return None

            # Validate and clean the parsed data
            cleaned_data = {}
            
            # Required fields
            if 'interaction_type' in interaction_data:
                cleaned_data['interaction_type'] = str(interaction_data['interaction_type']).lower()
            if 'query_text' in interaction_data:
                cleaned_data['query_text'] = str(interaction_data['query_text'])
            if 'response_text' in interaction_data:
                cleaned_data['response_text'] = str(interaction_data['response_text'])
            
            # Optional fields with type conversion
            if 'learning_unit_id' in interaction_data and interaction_data['learning_unit_id']:
                try:
                    cleaned_data['learning_unit_id'] = str(interaction_data['learning_unit_id'])
                except (ValueError, TypeError):
                    self.logger.warning(f"Invalid learning_unit_id: {interaction_data['learning_unit_id']}")
            
            if 'difficulty_rating' in interaction_data and interaction_data['difficulty_rating'] is not None:
                try:
                    rating = int(interaction_data['difficulty_rating'])
                    if 1 <= rating <= 5:
                        cleaned_data['difficulty_rating'] = rating
                    else:
                        self.logger.warning(f"Difficulty rating must be 1-5, got: {rating}")
                except (ValueError, TypeError):
                    self.logger.warning(f"Invalid difficulty_rating: {interaction_data['difficulty_rating']}")
            
            if 'response_time_seconds' in interaction_data and interaction_data['response_time_seconds'] is not None:
                try:
                    cleaned_data['response_time_seconds'] = float(interaction_data['response_time_seconds'])
                except (ValueError, TypeError):
                    self.logger.warning(f"Invalid response_time_seconds: {interaction_data['response_time_seconds']}")
            
            # Additional optional fields
            if 'was_helpful' in interaction_data and interaction_data['was_helpful'] is not None:
                cleaned_data['was_helpful'] = bool(interaction_data['was_helpful'])
            
            if 'adaptation_requested' in interaction_data:
                cleaned_data['adaptation_requested'] = bool(interaction_data['adaptation_requested'])
            
            if 'metadata' in interaction_data and isinstance(interaction_data['metadata'], dict):
                cleaned_data['metadata'] = interaction_data['metadata']

            return cleaned_data
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON interaction data: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error parsing interaction data: {e}")
            return None

    async def _create_interaction_summary(self, interaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary of the interaction for session history"""
        summary = {
            'type': interaction_data['interaction_type'],
            'query': interaction_data['query_text'][:200] + ('...' if len(interaction_data['query_text']) > 200 else ''),
            'response': interaction_data['response_text'][:200] + ('...' if len(interaction_data['response_text']) > 200 else ''),
            'timestamp': time.time()
        }
        
        # Add optional fields if present
        if 'difficulty_rating' in interaction_data:
            summary['difficulty'] = interaction_data['difficulty_rating']
        
        if 'response_time_seconds' in interaction_data:
            summary['response_time'] = interaction_data['response_time_seconds']
        
        if 'learning_unit_id' in interaction_data:
            summary['learning_unit'] = interaction_data['learning_unit_id']
        
        if 'was_helpful' in interaction_data:
            summary['helpful'] = interaction_data['was_helpful']

        return summary

    async def _log_interaction_to_database(self, session_id: str, interaction_data: Dict[str, Any]):
        """Log interaction to database using repository"""
        async with NeonDatabase.get_session() as session:
            try:
                interaction_repo = LearnerInteractionRepository(session)
                
                # Prepare kwargs for optional fields
                kwargs = {}
                for field in ['learning_unit_id', 'difficulty_rating', 'response_time_seconds', 
                             'was_helpful', 'adaptation_requested', 'metadata']:
                    if field in interaction_data:
                        kwargs[field] = interaction_data[field]
                
                # Convert learning_unit_id to UUID if present
                if 'learning_unit_id' in kwargs and kwargs['learning_unit_id']:
                    try:
                        kwargs['learning_unit_id'] = uuid.UUID(kwargs['learning_unit_id'])
                    except ValueError:
                        self.logger.warning(f"Invalid UUID for learning_unit_id: {kwargs['learning_unit_id']}")
                        del kwargs['learning_unit_id']
                
                interaction = await interaction_repo.log_interaction(
                    session_id=uuid.UUID(session_id),
                    interaction_type=interaction_data['interaction_type'],
                    query_text=interaction_data['query_text'],
                    response_text=interaction_data['response_text'],
                    **kwargs
                )
                
                self.logger.info(f"Logged interaction to database: {interaction.id}")
                return interaction
                
            except Exception as e:
                self.logger.error(f"Error logging interaction to database: {e}")
                raise

    async def _update_session_history(self, session_id: str, interaction_summary: Dict[str, Any]) -> bool:
        """Update session interaction history"""
        async with NeonDatabase.get_session() as session:
            try:
                session_repo = TutoringSessionRepository(session)
                
                success = await session_repo.add_to_interaction_history(
                    session_id=uuid.UUID(session_id),
                    interaction=interaction_summary
                )
                
                if success:
                    self.logger.debug(f"Updated session history for session: {session_id}")
                else:
                    self.logger.warning(f"Failed to update session history for session: {session_id}")
                
                return success
                
            except Exception as e:
                self.logger.error(f"Error updating session history: {e}")
                return False

    async def _update_state_with_interaction(self, interaction_summary: Dict[str, Any]):
        """Update current state with the latest interaction"""
        try:
            if not self.current_state:
                return

            # Add to interaction_history in state
            if 'interaction_history' not in self.current_state:
                self.current_state['interaction_history'] = []
            
            # Keep only last 50 interactions in state to prevent memory bloat
            interaction_history = self.current_state['interaction_history']
            interaction_history.append(interaction_summary)
            if len(interaction_history) > 50:
                interaction_history = interaction_history[-50:]
                self.current_state['interaction_history'] = interaction_history

            # Update learning progress if available
            if 'learning_progress' not in self.current_state:
                self.current_state['learning_progress'] = {}
            
            progress = self.current_state['learning_progress']
            
            # Count interactions by type
            interaction_type = interaction_summary['type']
            type_count_key = f"{interaction_type}_count"
            progress[type_count_key] = progress.get(type_count_key, 0) + 1
            
            # Track total interactions
            progress['total_interactions'] = progress.get('total_interactions', 0) + 1
            
            # Update recent interaction timestamp
            progress['last_interaction'] = interaction_summary['timestamp']
            
            # Track difficulty if provided
            if 'difficulty' in interaction_summary:
                if 'difficulty_ratings' not in progress:
                    progress['difficulty_ratings'] = []
                progress['difficulty_ratings'].append(interaction_summary['difficulty'])
                # Keep only last 20 ratings
                if len(progress['difficulty_ratings']) > 20:
                    progress['difficulty_ratings'] = progress['difficulty_ratings'][-20:]
            
            self.logger.debug("Updated state with interaction data")
            
        except Exception as e:
            self.logger.warning(f"Failed to update state with interaction: {e}")
            # Don't raise - this is not critical for the main workflow
