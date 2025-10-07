from typing import List
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
        learner_id = state.get("learner_id", "default_learner")
        learner_profile = state.get("learner_profile", {})
        
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
                    })
                    run_tree.update(metadata=metadata)
                    logger.debug(f"Added metadata to trace: {metadata}")
            except Exception as e:
                logger.debug(f"Could not add metadata to trace: {e}")

        try:
            logger.info(f"Processing tutoring request for learner: {learner_id}")

            # Set current state for all handlers
            self._set_handler_states(state)

            # Ensure we have an active tutoring session
            session_id = await self._ensure_session_active(learner_id)
            state["tutoring_session_id"] = session_id

            # Detect language for response
            documents = state.get('documents', [])
            detected_language = returnlang(documents) if documents else "English"
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
                result = await session_handler.tool().afunc("continue")
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
        
        # Build learner context
        learner_context = ""
        if learner_profile:
            grade_level = learner_profile.get("grade_level", "unknown")
            learning_style = learner_profile.get("learning_style", "mixed")
            difficulty_pref = learner_profile.get("difficulty_preference", "medium")
            accuracy_rate = learner_profile.get("accuracy_rate", 0)
            mastered_topics = learner_profile.get("mastered_topics", [])
            learning_struggles = learner_profile.get("learning_struggles", [])
            
            learner_context = f"""
Learner Profile:
- Grade Level: {grade_level}
- Learning Style: {learning_style}
- Difficulty Preference: {difficulty_pref}
- Current Accuracy Rate: {accuracy_rate:.2f}
- Mastered Topics: {', '.join(mastered_topics) if mastered_topics else 'None recorded'}
- Learning Struggles: {', '.join(learning_struggles) if learning_struggles else 'None identified'}

Adapt your response to match this learner's level and preferences.
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

        # Combine all elements
        enhanced_query = f"""{language_instruction}

{learner_context}

{capabilities_context}

Learner Query: {query}

Remember to:
1. Ensure session is active and manage learner context using "manage_tutoring_session"
2. Use "generate_explanation" for concepts that need clarification (choose appropriate style)
3. Use "generate_practice" when learner needs reinforcement or assessment
4. Use "request_content_adaptation" when content doesn't match learner's needs
5. Update learner model based on performance indicators using "update_learner_model"
6. Log this interaction for learning analytics using "log_interaction"

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
