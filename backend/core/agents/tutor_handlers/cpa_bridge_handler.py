import json
import asyncio
import time
from typing import Dict, Any, Optional
from langchain_core.tools import Tool
from backend.core.agents.base_handler import BaseHandler
from backend.core.agents.content_processor_agent import ContentProcessorAgent
from backend.core.states.graph_states import RAGState
from backend.utils.logger_config import get_logger


class CPABridgeHandler(BaseHandler):
    """
    Bridge handler for communication between Tutor Agent and Content Processing Agent
    Enables content adaptation based on learner needs and preferences
    """

    def __init__(self):
        super().__init__()
        self.cpa_agent = None  # Initialize lazily to avoid circular imports
        
    def tool(self) -> Tool:
        """Return configured LangChain Tool for CPA content adaptation"""
        return Tool(
            name="request_content_adaptation",
            description="Request content adaptation from CPA based on learner needs. Use when content is too complex, needs different explanation style, or requires additional examples.",
            func=self._process_wrapper
        )
    
    def _process_wrapper(self, adaptation_request: str) -> str:
        """Wrapper for tool execution with error handling"""
        try:
            return asyncio.run(self._process(adaptation_request))
        except Exception as e:
            return self._handle_error(e, "content_adaptation")
    
    async def _process(self, adaptation_request: str) -> str:
        """Process content adaptation request"""
        start_time = time.time()
        
        try:
            self.logger.info(f"Starting content adaptation request: {adaptation_request}")

            if not self._validate_state():
                return "Unable to process content adaptation - no state available"

            # Parse the adaptation request
            request_data = await self._parse_adaptation_request(adaptation_request)
            if not request_data:
                return "Invalid adaptation request format. Please specify what content to adapt and how."

            # Get learner context from current state
            learner_context = await self._extract_learner_context()
            if not learner_context:
                return "No learner profile available for personalized content adaptation."

            # Build detailed adaptation instruction
            adaptation_instruction = await self._build_adaptation_instruction(request_data, learner_context)
            
            # Create state for CPA processing
            adaptation_state = await self._prepare_cpa_state(adaptation_instruction, request_data)
            
            # Call CPA for content adaptation
            self.logger.info("Requesting content adaptation from CPA...")
            adapted_content = await self._call_cpa_for_adaptation(adaptation_state)
            
            # Format and store adapted content
            formatted_content = await self._format_adapted_content(adapted_content)
            
            # Store in state for future use
            if "personalized_content" not in self.current_state:
                self.current_state["personalized_content"] = []
            
            self.current_state["personalized_content"].append({
                "request_id": request_data.get("id", f"req_{int(time.time())}"),
                "original_topic": request_data.get("topic", "Unknown"),
                "adaptation_type": request_data.get("adaptation_type", "general"),
                "adapted_content": formatted_content,
                "learner_id": learner_context.get("id"),
                "created_at": time.time()
            })
            
            processing_time = time.time() - start_time
            self.logger.info(f"Content adaptation completed in {processing_time:.2f}s")
            
            return formatted_content

        except Exception as e:
            self.logger.error(f"Error in content adaptation: {e}")
            return self._handle_error(e, "content_adaptation")

    async def _parse_adaptation_request(self, request: str) -> Optional[Dict[str, Any]]:
        """Parse adaptation request string into structured data"""
        try:
            # Try to parse as JSON first
            if request.strip().startswith('{'):
                return json.loads(request)
            
            # Otherwise, parse natural language request
            request_lower = request.lower()
            parsed_request = {
                "id": f"adapt_{int(time.time())}",
                "topic": "",
                "adaptation_type": "general",
                "reason": request
            }
            
            # Extract topic/content identifier
            if "topic:" in request_lower:
                topic_part = request.split("topic:")[1].split(",")[0].strip()
                parsed_request["topic"] = topic_part
            elif "unit:" in request_lower:
                unit_part = request.split("unit:")[1].split(",")[0].strip()
                parsed_request["learning_unit_id"] = unit_part
                parsed_request["topic"] = unit_part
            
            # Determine adaptation type
            if any(word in request_lower for word in ["simplify", "easier", "simple"]):
                parsed_request["adaptation_type"] = "simplify"
            elif any(word in request_lower for word in ["example", "examples", "demonstrate"]):
                parsed_request["adaptation_type"] = "add_examples"
            elif any(word in request_lower for word in ["style", "visual", "audio", "explain differently"]):
                parsed_request["adaptation_type"] = "change_style"
            elif any(word in request_lower for word in ["harder", "difficult", "advanced", "challenge"]):
                parsed_request["adaptation_type"] = "increase_difficulty"
            
            self.logger.info(f"Parsed adaptation request: {parsed_request}")
            return parsed_request
            
        except Exception as e:
            self.logger.error(f"Error parsing adaptation request: {e}")
            return None

    async def _extract_learner_context(self) -> Optional[Dict[str, Any]]:
        """Extract learner context from current state"""
        if not self.current_state:
            return None
            
        learner_profile = self.current_state.get("learner_profile", {})
        if not learner_profile:
            return None
            
        # Extract key learner characteristics
        context = {
            "id": self.current_state.get("learner_id"),
            "name": learner_profile.get("name", "Student"),
            "grade_level": learner_profile.get("grade_level", "Unknown"),
            "learning_style": learner_profile.get("learning_style", "General"),
            "preferred_language": learner_profile.get("preferred_language", "English"),
            "subjects_of_interest": learner_profile.get("subjects_of_interest", []),
            "accessibility_needs": learner_profile.get("accessibility_needs", {}),
            "performance_metrics": learner_profile.get("performance_metrics", {}),
            "mastered_topics": learner_profile.get("mastered_topics", []),
            "learning_struggles": learner_profile.get("learning_struggles", [])
        }
        
        # Add current session context if available
        if "session_state" in self.current_state:
            session = self.current_state["session_state"]
            context.update({
                "current_subject": session.get("subject"),
                "current_topic": session.get("topic"),
                "current_difficulty": session.get("difficulty_level"),
                "session_progress": session.get("interaction_history", [])
            })
        
        return context

    async def _build_adaptation_instruction(self, request: Dict[str, Any], learner_context: Dict[str, Any]) -> str:
        """Build detailed adaptation instruction for CPA"""
        adaptation_type = request.get("adaptation_type", "general")
        topic = request.get("topic", "the current topic")
        reason = request.get("reason", "learner requested adaptation")
        
        # Base instruction
        instruction = f"Adapt content about '{topic}' for a {learner_context.get('grade_level', 'student')} level learner.\n\n"
        
        # Add learner-specific context
        instruction += f"Learner Profile:\n"
        instruction += f"- Learning Style: {learner_context.get('learning_style', 'General')}\n"
        instruction += f"- Preferred Language: {learner_context.get('preferred_language', 'English')}\n"
        
        if learner_context.get("accessibility_needs"):
            accessibility = learner_context["accessibility_needs"]
            instruction += f"- Accessibility Needs: {', '.join([k for k, v in accessibility.items() if v])}\n"
        
        if learner_context.get("learning_struggles"):
            struggles = learner_context["learning_struggles"]
            instruction += f"- Areas of Difficulty: {', '.join(struggles)}\n"
        
        if learner_context.get("mastered_topics"):
            mastered = learner_context["mastered_topics"]
            instruction += f"- Already Mastered: {', '.join(mastered)}\n"
        
        # Add adaptation-specific instructions
        instruction += f"\nAdaptation Request: {adaptation_type}\n"
        
        if adaptation_type == "simplify":
            instruction += "- Break down complex concepts into smaller, easier-to-understand parts\n"
            instruction += "- Use simpler vocabulary and shorter sentences\n"
            instruction += "- Provide step-by-step explanations\n"
        elif adaptation_type == "add_examples":
            instruction += "- Include concrete, relatable examples\n"
            instruction += "- Provide multiple examples showing different applications\n"
            instruction += "- Use examples relevant to the learner's interests\n"
        elif adaptation_type == "change_style":
            learning_style = learner_context.get("learning_style", "General")
            if learning_style == "Visual":
                instruction += "- Describe visual representations and diagrams\n"
                instruction += "- Use spatial and graphic analogies\n"
                instruction += "- Structure content with clear visual hierarchy\n"
            elif learning_style == "Auditory":
                instruction += "- Use rhythm and patterns in explanations\n"
                instruction += "- Include verbal mnemonics and sound-based learning aids\n"
                instruction += "- Structure content for clear verbal delivery\n"
            elif learning_style == "Kinesthetic":
                instruction += "- Include hands-on activities and movement\n"
                instruction += "- Use tactile analogies and physical examples\n"
                instruction += "- Suggest interactive learning approaches\n"
        elif adaptation_type == "increase_difficulty":
            instruction += "- Add more complex concepts and applications\n"
            instruction += "- Include challenging problems and edge cases\n"
            instruction += "- Connect to advanced topics and real-world applications\n"
        
        instruction += f"\nReason for Adaptation: {reason}\n"
        instruction += f"\nPlease generate adapted educational content that addresses these specific learner needs."
        
        return instruction

    async def _prepare_cpa_state(self, instruction: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare state object for CPA processing"""
        
        # Create a modified state for CPA processing
        cpa_state = RAGState()
        
        # Copy relevant information from current state
        if self.current_state:
            cpa_state.update({
                "query": instruction,
                "documents": self.current_state.get("documents", []),
                "chunks": self.current_state.get("chunks", []),
                "conversation_id": self.current_state.get("conversation_id"),
                "file_paths": self.current_state.get("file_paths", []),
                "ingested_sources": self.current_state.get("ingested_sources", []),
                "documents_available": self.current_state.get("documents_available", False)
            })
        
        # Add adaptation-specific context
        cpa_state.update({
            "intent_classification": "content_adaptation",
            "adaptation_request": request_data,
            "learner_context": await self._extract_learner_context()
        })
        
        return cpa_state

    async def _call_cpa_for_adaptation(self, adaptation_state: Dict[str, Any]) -> Dict[str, Any]:
        """Call Content Processing Agent for content adaptation"""
        try:
            # Initialize CPA agent if not already done
            if not self.cpa_agent:
                self.cpa_agent = ContentProcessorAgent()
            
            # Process the adaptation request through CPA
            result = await self.cpa_agent.process(adaptation_state)
            
            self.logger.info("CPA adaptation completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Error calling CPA for adaptation: {e}")
            raise

    async def _format_adapted_content(self, cpa_result: Dict[str, Any]) -> str:
        """Format adapted content for tutoring use"""
        try:
            # Extract the main content from CPA result
            adapted_content = cpa_result.get("answer", "")
            
            if not adapted_content:
                # Try alternative fields
                adapted_content = cpa_result.get("generated_units", "")
                if isinstance(adapted_content, list) and adapted_content:
                    # If it's learning units, format them nicely
                    formatted_units = []
                    for unit in adapted_content:
                        if isinstance(unit, dict):
                            title = unit.get("title", "Learning Unit")
                            explanation = unit.get("detailed_explanation", unit.get("content", ""))
                            formatted_units.append(f"**{title}**\\n{explanation}")
                    adapted_content = "\\n\\n".join(formatted_units)
            
            if not adapted_content:
                adapted_content = "Content adaptation completed, but no specific content was generated."
            
            # Add adaptation metadata
            adaptation_meta = f"\\n\\n---\\n*Content adapted based on your learning profile and preferences.*"
            
            return adapted_content + adaptation_meta
            
        except Exception as e:
            self.logger.error(f"Error formatting adapted content: {e}")
            return "Content adaptation was attempted, but formatting failed. Please try rephrasing your request."

    def _validate_state(self) -> bool:
        """Validate that current state is available and contains required information"""
        if not self.current_state:
            self.logger.warning("No current state available for content adaptation")
            return False
            
        if not self.current_state.get("learner_profile"):
            self.logger.warning("No learner profile available in current state")
            return False
            
        return True
