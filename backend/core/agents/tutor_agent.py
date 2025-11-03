from typing import List
import time
import re
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import Tool
from backend.core.states.graph_states import RAGState
from backend.models.llms.groq_llm import GroqLLM
from backend.core.agents.tutor_handlers.session_manager import SessionManagerHandler
from backend.core.agents.tutor_handlers.learner_model_manager import LearnerModelManagerHandler
from backend.core.agents.tutor_handlers.interaction_logger import InteractionLoggerHandler
from backend.core.agents.tutor_handlers.cpa_bridge_handler import CPABridgeHandler
from backend.core.agents.tutor_handlers.explanation_engine import ExplanationEngineHandler
from backend.core.agents.tutor_handlers.practice_generator import PracticeGeneratorHandler
from backend.utils.helpers.language_detection import returnlang
from backend.utils.logger_config import get_logger
from backend.loaders.prompt_loaders.prompt_loader import PromptLoader

# LangSmith imports for tracing
try:
    from langsmith import traceable
    from langsmith.run_helpers import get_current_run_tree
    LANGSMITH_AVAILABLE = True
except ImportError:
    LANGSMITH_AVAILABLE = False
    # Create dummy decorator if langsmith not installed
    def traceable(func):
        return func
    
from backend.utils.langsmith_config import (
    is_langsmith_enabled, 
    get_run_metadata,
    get_langsmith_url
)

logger = get_logger("tutor_agent")


class TutorAgent:
    """
    Personalized Tutoring Agent that adapts content based on learner profiles
    and provides interactive educational experiences using handler-based tools
    """

    def __init__(self):
        self.llm = GroqLLM().llm
        self.current_state = None

        # Initialize tutor handlers
        self.handlers = [
            SessionManagerHandler(),
            LearnerModelManagerHandler(),
            InteractionLoggerHandler(),
            CPABridgeHandler(),
            ExplanationEngineHandler(),
            PracticeGeneratorHandler()
        ]

        # Collect tools from handlers
        self.tools = self._collect_tools()
        self.agent_executor = self._create_agent()
        
        logger.info("TutorAgent initialized successfully")

    def _collect_tools(self) -> List[Tool]:
        """Collect tools from all handlers"""
        tools = []
        for handler in self.handlers:
            tool = handler.tool()
            tools.append(tool)
            logger.info(f"Collected tool: {tool.name} from {handler.__class__.__name__}")
        return tools

    def _create_agent(self) -> AgentExecutor:
        """Create personalized tutoring ReAct agent"""
        # Load prompt template from YAML
        prompt_template = PromptLoader.load_system_prompt("prompts/tutor_agent.yaml")

        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["input", "tools", "tool_names", "agent_scratchpad"]
        )

        # Create ReAct agent
        agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )

        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            max_iterations=5,
            handle_parsing_errors=True
        )

    @traceable(
        name="tutor_agent_process",
        run_type="chain",
        tags=["tutor-agent", "personalized-learning"]
    )
    async def process(self, state: RAGState) -> RAGState:
        """Process tutoring query with personalized context"""
        query = state.get("query", "").strip()
        if not query:
            state["answer"] = "I didn't receive any query. How can I help you with your learning today?"
            return state

        # Extract metadata for tracing
        learner_id = state.get("learner_id")
        learner_profile = state.get("learner_profile", {})
        
        # Handle guest session (no learner_id provided)
        if not learner_id:
            logger.info("No learner_id provided - creating guest session")
            learner_id = f"guest_{int(time.time())}"
            learner_profile = self._create_guest_profile(query)
            state["learner_id"] = learner_id
            state["learner_profile"] = learner_profile
            state["guest_session"] = True
            logger.info(f"Created guest session: {learner_id} with inferred profile: {learner_profile}")
        
        # Add metadata to trace if LangSmith is enabled
        if LANGSMITH_AVAILABLE and is_langsmith_enabled():
            try:
                run_tree = get_current_run_tree()
                if run_tree:
                    metadata = get_run_metadata(state)
                    metadata.update({
                        "agent_type": "tutor_agent",
                        "query_length": len(query),
                        "has_learner_profile": bool(learner_profile),
                        "learner_id": learner_id,
                        "is_guest_session": state.get("guest_session", False),
                    })
                    run_tree.update(metadata=metadata)
                    logger.debug(f"Added metadata to trace: {metadata}")
            except Exception as e:
                logger.debug(f"Could not add metadata to trace: {e}")

        try:
            logger.info(f"Processing tutoring request for learner: {learner_id}")

            # Set current state for all handlers
            self._set_handler_states(state)

            # For guest sessions, skip database session management
            if state.get("guest_session", False):
                logger.info("Guest session - skipping database session management")
                session_id = f"guest_session_{learner_id}"
                state["tutoring_session_id"] = session_id
            else:
                # Ensure we have an active tutoring session for registered users
                try:
                    session_id = await self._ensure_session_active(learner_id)
                    state["tutoring_session_id"] = session_id
                except Exception as e:
                    logger.error(f"Error ensuring active session: {e}")
                    # Fallback to creating a basic session ID
                    session_id = f"session_{learner_id}_{int(time.time())}"
                    state["tutoring_session_id"] = session_id

            # Detect language for response
            # For guest sessions, use the inferred language from profile
            if state.get("guest_session", False):
                detected_language = learner_profile.get("preferred_language", "English")
            else:
                # For registered users, try to detect from documents or query
                documents = state.get('documents', [])
                if documents and isinstance(documents, list) and len(documents) > 0:
                    # Extract text from documents for language detection
                    doc_text = " ".join([str(doc) for doc in documents[:3]])  # Use first 3 docs
                    detected_language = returnlang(doc_text) if doc_text.strip() else "English"
                else:
                    # Fallback to query language detection
                    detected_language = returnlang(query) if query.strip() else "English"
            logger.info(f"Detected language: {detected_language}")

            # Create personalized tutoring prompt
            tutoring_prompt = self._create_tutoring_prompt(query, learner_profile, detected_language)

            # Execute agent
            logger.info("Starting tutoring agent execution...")
            result = await self.agent_executor.ainvoke({
                "input": tutoring_prompt
            })

            # Extract the final answer
            answer = result.get("output", "I couldn't process your tutoring request properly.")
            state["answer"] = answer

            # Update state with session info
            if session_id:
                state["tutoring_session_id"] = session_id

            # Mark success in trace
            if LANGSMITH_AVAILABLE and is_langsmith_enabled():
                try:
                    run_tree = get_current_run_tree()
                    if run_tree:
                        run_tree.update(metadata={"success": True, "response_length": len(answer)})
                        logger.info(f"Trace URL: {get_langsmith_url(str(run_tree.id))}")
                except Exception as e:
                    logger.debug(f"Could not update trace: {e}")

            logger.info("Tutoring agent execution completed successfully")
            
            return state

        except Exception as e:
            logger.error(f"Error in tutor agent: {e}")
            
            # Mark error in trace
            if LANGSMITH_AVAILABLE and is_langsmith_enabled():
                try:
                    run_tree = get_current_run_tree()
                    if run_tree:
                        run_tree.update(metadata={"success": False, "error": str(e)})
                except Exception as trace_error:
                    logger.debug(f"Could not update trace with error: {trace_error}")
            
            state["answer"] = self._get_fallback_response(detected_language)
            return state
        finally:
            # Clear handler states
            self._clear_handler_states()

    def _set_handler_states(self, state: RAGState):
        """Set state for all handlers"""
        for handler in self.handlers:
            handler.set_state(state)
        logger.debug("Set state for all tutor handlers")
    
    def _clear_handler_states(self):
        """Clear state from all handlers"""
        for handler in self.handlers:
            handler.set_state(None)
        logger.debug("Cleared state from all tutor handlers")

    async def _ensure_session_active(self, learner_id: str) -> str:
        """Ensure there's an active tutoring session for the learner"""
        try:
            # Get session manager handler
            session_handler = None
            for handler in self.handlers:
                if isinstance(handler, SessionManagerHandler):
                    session_handler = handler
                    break

            if session_handler:
                # Try to continue existing session or start new one
                result = await session_handler._process("continue")
                logger.info(f"Session management result: {result}")
                
                # Extract session ID from current state after session management
                return self.current_state.get("tutoring_session_id") if self.current_state else None
            else:
                logger.warning("Session manager handler not found")
                return None

        except Exception as e:
            logger.error(f"Error ensuring active session: {e}")
            return None

    def _create_tutoring_prompt(self, query: str, learner_profile: dict, language: str) -> str:
        """Create personalized tutoring prompt based on learner context"""
        # Language instruction
        language_instruction = "Please respond in Arabic." if language == "Arabic" else "Please respond in English."
        
        # Check if this is a guest session
        is_guest = learner_profile.get("guest_session_info", {}).get("created_from_query", False)
        
        # Build learner context
        learner_context = ""
        if learner_profile:
            grade_level = learner_profile.get("grade_level", "unknown")
            learning_style = learner_profile.get("learning_style", "mixed")
            difficulty_pref = learner_profile.get("difficulty_preference", "medium")
            accuracy_rate = learner_profile.get("accuracy_rate", 0)
            mastered_topics = learner_profile.get("mastered_topics", [])
            learning_struggles = learner_profile.get("learning_struggles", [])
            
            if is_guest:
                learner_context = f"""
Guest Learner Profile (Inferred from Query):
- Estimated Grade Level: {grade_level}
- Detected Learning Style: {learning_style}
- Inferred Difficulty Preference: {difficulty_pref}
- This is a new learner with no previous session history
- Profile was created by analyzing the query language and context

Since this is a guest session:
1. Be welcoming and establish rapport
2. Ask clarifying questions if needed to better understand their level
3. Provide excellent first impression of personalized tutoring
4. Adapt based on their responses and engagement
"""
            else:
                learner_context = f"""
Registered Learner Profile:
- Grade Level: {grade_level}
- Learning Style: {learning_style}
- Difficulty Preference: {difficulty_pref}
- Current Accuracy Rate: {accuracy_rate:.2f}
- Mastered Topics: {', '.join([topic.get('topic', str(topic)) for topic in mastered_topics]) if mastered_topics else 'None recorded'}
- Learning Struggles: {', '.join([struggle.get('topic', str(struggle)) for struggle in learning_struggles]) if learning_struggles else 'None identified'}

Adapt your response to match this learner's established level and preferences.
"""

        # Available capabilities context  
        capabilities_context = """
Available Tutoring Capabilities:

EXPLANATION STYLES:
- simplified: Easy vocabulary, short sentences, confidence-building
- detailed: Comprehensive coverage with technical precision  
- analogy: Relatable metaphors and familiar comparisons
- step-by-step: Sequential, numbered progression
- visual: Spatial descriptions and mental imagery
- interactive: Engaging questions and thought experiments
- practical: Real-world applications and hands-on examples

PRACTICE TYPES:
- problems: Mathematical or conceptual problems with solutions
- quiz: Multiple choice or short answer questions
- exercises: Hands-on activities and practical tasks
- assessment: Comprehensive evaluation questions
- flashcards: Question-answer pairs for memorization

CONTENT ADAPTATION:
- simplify: Break down complex concepts, use easier vocabulary
- add_examples: Include concrete, relatable examples
- change_style: Adapt to visual/auditory/kinesthetic preferences
- increase_difficulty: Add complexity and advanced applications

Use these capabilities to provide the most effective learning experience for this specific learner.
"""

        # Session management instructions
        session_instructions = ""
        if is_guest:
            session_instructions = """
GUEST SESSION MANAGEMENT:
- This is a guest learner with no database profile
- Session management tools may not work as expected
- Focus on direct tutoring and explanation rather than complex session tracking
- Provide immediate value and educational support
- Be prepared to work without detailed learner history
"""
        else:
            session_instructions = """
SESSION MANAGEMENT:
1. Ensure session is active and manage learner context using "manage_tutoring_session"
2. Update learner model based on performance indicators using "update_learner_model"
3. Log this interaction for learning analytics using "log_interaction"
"""

        # Combine all elements
        enhanced_query = f"""{language_instruction}

{learner_context}

{capabilities_context}

{session_instructions}

Learner Query: {query}

Remember to:
1. Use "generate_explanation" for concepts that need clarification (choose appropriate style)
2. Use "generate_practice" when learner needs reinforcement or assessment
3. Use "request_content_adaptation" when content doesn't match learner's needs
4. Provide immediate educational value regardless of session type

Choose the most appropriate tools and approaches based on the learner's query and profile.
"""
        
        return enhanced_query

    def _get_fallback_response(self, language: str) -> str:
        """Get fallback response in appropriate language"""
        if language == "Arabic":
            return (
                "عذراً، واجهت خطأ في معالجة استفسارك التعليمي. "
                "يمكنني مساعدتك في التعلم الشخصي، إدارة جلسات التدريس، أو تتبع تقدمك. "
                "كيف يمكنني مساعدتك في رحلتك التعليمية؟"
            )
        else:
            return (
                "I'm sorry, I encountered an error processing your tutoring request. "
                "I can help with personalized learning, managing tutoring sessions, or tracking your progress. "
                "How can I assist you with your learning journey?"
            )

    def get_session_info(self) -> dict:
        """Get current tutoring session information"""
        if not self.current_state:
            return {"error": "No active state"}
        
        return {
            "learner_id": self.current_state.get("learner_id"),
            "session_id": self.current_state.get("tutoring_session_id"),
            "learner_profile": self.current_state.get("learner_profile"),
            "session_state": self.current_state.get("session_state"),
            "learning_progress": self.current_state.get("learning_progress")
        }

    def update_learner_context(self, learner_id: str, **context_updates):
        """Update learner context in current state"""
        if not self.current_state:
            self.current_state = {}
        
        self.current_state["learner_id"] = learner_id
        
        # Update learner profile if provided
        if "learner_profile" in context_updates:
            self.current_state["learner_profile"] = context_updates["learner_profile"]
        
        # Update any other context
        for key, value in context_updates.items():
            if key != "learner_profile":
                self.current_state[key] = value
                
        logger.info(f"Updated learner context for: {learner_id}")

    def clear_session(self):
        """Clear current tutoring session"""
        if self.current_state:
            self.current_state["tutoring_session_id"] = None
            self.current_state["session_state"] = None
            self.current_state["interaction_history"] = []
            
        self._clear_handler_states()
        logger.info("Cleared tutoring session")

    def _create_guest_profile(self, query: str) -> dict:
        """Create a guest learner profile by inferring characteristics from the query"""
        try:
            query_lower = query.lower()
            
            # Infer grade level from query context
            grade_level = 8  # Default middle school
            
            # Check for explicit grade mentions first
            import re
            grade_matches = re.findall(r'(\d+)\s*(?:st|nd|rd|th)?\s*grade', query_lower)
            if grade_matches:
                grade_level = int(grade_matches[0])
            elif any(word in query_lower for word in ['kindergarten', 'preschool', 'abc', 'counting']):
                grade_level = 1
            elif any(word in query_lower for word in ['elementary', 'addition', 'subtraction']):
                grade_level = 4
            elif any(word in query_lower for word in ['middle school', 'algebra']) and 'fraction' not in query_lower:
                grade_level = 8
            elif any(word in query_lower for word in ['high school', 'ap', 'trigonometry', 'calculus', 'chemistry', 'physics']):
                grade_level = 11
            elif any(word in query_lower for word in ['college', 'university', 'theoretical', 'complex analysis']):
                grade_level = 16
            # Handle fractions separately - can be elementary or middle
            elif 'fraction' in query_lower:
                if any(word in query_lower for word in ['3rd', '4th', 'elementary', 'simple']):
                    grade_level = 4
                else:
                    grade_level = 8
            
            # Infer learning style from query language
            learning_style = "Mixed"
            if any(word in query_lower for word in ['show me', 'diagram', 'picture', 'visual', 'see', 'draw', 'chart']):
                learning_style = "Visual"
            elif any(word in query_lower for word in ['explain', 'tell me', 'talk', 'listen', 'hear', 'discuss']):
                learning_style = "Auditory"
            elif any(word in query_lower for word in ['hands-on', 'practice', 'do', 'try', 'interactive', 'game']):
                learning_style = "Kinesthetic"
            elif any(word in query_lower for word in ['analyze', 'prove', 'theory', 'logic', 'detailed']):
                learning_style = "Analytical"
            elif any(word in query_lower for word in ['creative', 'imagine', 'design', 'artistic']):
                learning_style = "Creative"
            
            # Infer difficulty preference
            difficulty_preference = "medium"
            if any(word in query_lower for word in ['simple', 'easy', 'basic', 'confused', 'confusing', 'don\'t understand', 'hard for me', 'help me', 'struggling']):
                difficulty_preference = "easy"
            elif any(word in query_lower for word in ['challenging', 'advanced', 'complex', 'difficult', 'in-depth', 'theoretical', 'rigorous']):
                difficulty_preference = "challenging"
            
            # Infer language preference
            preferred_language = "English"
            if any(word in query for word in ['español', '¿', '¡', 'por favor', 'gracias']):
                preferred_language = "Spanish"
            elif any(word in query for word in ['العربية', 'عربي', 'أريد']):
                preferred_language = "Arabic"
            
            # Create guest profile
            guest_profile = {
                "grade_level": grade_level,
                "learning_style": learning_style,
                "preferred_language": preferred_language,
                "difficulty_preference": difficulty_preference,
                "avg_response_time": 15.0,  # Default
                "accuracy_rate": 0.7,      # Default moderate accuracy
                "completion_rate": 0.8,     # Default good completion
                "total_sessions": 0,        # New guest
                "interaction_patterns": {
                    "preferred_formats": self._get_format_preferences(learning_style),
                    "session_type": "exploration",
                    "guest_session": True
                },
                "learning_struggles": [],
                "mastered_topics": [],
                "preferred_explanation_styles": [
                    {"style": learning_style.lower(), "effectiveness": 0.9},
                    {"style": "encouraging", "effectiveness": 0.8}
                ],
                "guest_session_info": {
                    "created_from_query": True,
                    "inferred_characteristics": {
                        "grade_level_indicators": self._extract_grade_indicators(query_lower),
                        "learning_style_indicators": self._extract_style_indicators(query_lower),
                        "difficulty_indicators": self._extract_difficulty_indicators(query_lower)
                    }
                }
            }
            
            logger.info(f"Created guest profile: Grade {grade_level}, Style {learning_style}, Difficulty {difficulty_preference}")
            return guest_profile
            
        except Exception as e:
            logger.error(f"Error creating guest profile: {e}")
            # Return minimal default profile
            return {
                "grade_level": 8,
                "learning_style": "Mixed",
                "preferred_language": "English",
                "difficulty_preference": "medium",
                "avg_response_time": 15.0,
                "accuracy_rate": 0.7,
                "completion_rate": 0.8,
                "total_sessions": 0,
                "interaction_patterns": {"guest_session": True},
                "learning_struggles": [],
                "mastered_topics": [],
                "preferred_explanation_styles": [{"style": "encouraging", "effectiveness": 0.8}]
            }
    
    def _get_format_preferences(self, learning_style: str) -> list:
        """Get format preferences based on learning style"""
        format_map = {
            "Visual": ["diagrams", "charts", "step-by-step_visuals", "infographics"],
            "Auditory": ["verbal_explanations", "discussions", "audio_content"],
            "Kinesthetic": ["hands_on", "interactive", "practice_exercises"],
            "Analytical": ["detailed_explanations", "logical_proofs", "systematic_approach"],
            "Creative": ["open_ended", "artistic_connections", "real_world_applications"],
            "Mixed": ["varied_approaches", "multi_modal", "adaptive_content"]
        }
        return format_map.get(learning_style, format_map["Mixed"])
    
    def _extract_grade_indicators(self, query: str) -> list:
        """Extract words that indicate grade level"""
        indicators = []
        grade_words = {
            'elementary': ['elementary', 'basic', 'simple', 'counting'],
            'middle': ['middle', 'algebra', 'fraction', 'geometry'],
            'high': ['high school', 'trigonometry', 'calculus', 'chemistry', 'physics'],
            'college': ['college', 'university', 'advanced', 'complex', 'theoretical']
        }
        
        for level, words in grade_words.items():
            for word in words:
                if word in query:
                    indicators.append(f"{level}:{word}")
        return indicators
    
    def _extract_style_indicators(self, query: str) -> list:
        """Extract words that indicate learning style"""
        indicators = []
        style_words = {
            'visual': ['show', 'see', 'diagram', 'picture', 'chart', 'visual', 'draw'],
            'auditory': ['explain', 'tell', 'discuss', 'listen', 'hear'],
            'kinesthetic': ['do', 'practice', 'hands-on', 'interactive', 'game'],
            'analytical': ['analyze', 'prove', 'theory', 'logic', 'detailed'],
            'creative': ['creative', 'imagine', 'design', 'artistic']
        }
        
        for style, words in style_words.items():
            for word in words:
                if word in query:
                    indicators.append(f"{style}:{word}")
        return indicators
    
    def _extract_difficulty_indicators(self, query: str) -> list:
        """Extract words that indicate difficulty preference"""
        indicators = []
        difficulty_words = {
            'easy': ['simple', 'easy', 'basic', 'confused', 'confusing', "don't understand", 'help me', 'struggling'],
            'hard': ['challenging', 'advanced', 'complex', 'difficult', 'in-depth', 'theoretical', 'rigorous']
        }
        
        for level, words in difficulty_words.items():
            for word in words:
                if word in query:
                    indicators.append(f"{level}:{word}")
        return indicators
