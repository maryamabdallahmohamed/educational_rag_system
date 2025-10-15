from typing import List
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import Tool
from backend.core.states.graph_states import RAGState
from backend.models.llms.groq_llm import GroqLLM
from backend.core.agents.cpa_handlers.explainable_units_handler import ExplainableUnitsHandler
from backend.core.agents.cpa_handlers.rag_chat_handler import RAGChatHandler
from backend.utils.helpers.language_detection import returnlang
from backend.utils.logger_config import get_logger
from backend.loaders.prompt_loaders.prompt_loader import PromptLoader
from backend.core.states.graph_states import cpa_processor_state

logger = get_logger("content_processor_agent")


class ContentProcessorAgent:
    """
    Simplified LangChain Agent for Content Processing
    Uses handler-based tools for RAG chat, unit generation, and document analysis
    """

    def __init__(self):
        self.llm = GroqLLM().llm
        self.current_state = None
        self.cpa_state = cpa_processor_state()

        self.handlers = [
            ExplainableUnitsHandler(),
            RAGChatHandler()
        ]

        # Collect tools from handlers
        self.tools = self._collect_tools()
        self.agent_executor = self._create_agent()

    def _collect_tools(self) -> List[Tool]:
        """Collect tools from all handlers"""
        tools = []
        for handler in self.handlers:
            tool = handler.tool()
            tools.append(tool)
            logger.info(f"Collected tool: {tool.name} from {handler.__class__.__name__}")
        return tools

    def _create_agent(self) -> AgentExecutor:
        """Create simplified ReAct agent"""
        # Load prompt template from YAML
        prompt_template = PromptLoader.load_system_prompt("prompts/content_processor_agent.yaml")

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
            max_iterations=3,
            handle_parsing_errors=True
        )

    async def process(self, query, document) -> RAGState:
        """Process query using simplified agent"""
        detected_language = document[0].metadata['language']
        query = query.strip()
        if not query:
            answer = "I didn't receive any query. How can I help you?"
            return answer

        try:
            # Set current state for all handlers
            self._set_handler_states()

            # Check if we have documents in database for RAG operations
            await self._check_rag_availability(query)

            # Detect language for response
            logger.info(f"Detected language: {detected_language}")

            # Add language instruction to query
            language_instruction = "Please respond in Arabic." if detected_language == "Arabic" else "Please respond in English."
            enhanced_query = f"{language_instruction}\n\nUser query: {query}"

            # Execute agent
            logger.info("Starting simplified agent execution...")
            result = await self.agent_executor.ainvoke({
                "input": enhanced_query
            })

            # Extract the final answer
            answer = result.get("output", "I couldn't process your request properly.")
            self.current_state["answer"] = answer

            # Update RAG context usage flag if it was used
            if self.current_state.get("rag_context_used", False):
                logger.info("RAG context was successfully used in response generation")

            logger.info("Agent execution completed successfully")


            return self.current_state

        except Exception as e:
            logger.error(f"Error in content processor agent: {e}")
            self.current_state["answer"] = self._get_fallback_response(detected_language)
            return self.current_state
        finally:

            self._clear_handler_states()
            self.cpa_state.clear()
    
    async def _check_rag_availability(self,query):
        """Check if RAG documents are available in database"""
        try:
            # Get RAG handler to check availability
            rag_handler = None
            for handler in self.handlers:
                if isinstance(handler, RAGChatHandler):
                    rag_handler = handler
                    break

            if rag_handler:
                # Quick relevance check to see if we have documents
                has_relevant, all_scores, chunks, tool_used = await rag_handler.check_relevance(query)
                
                if has_relevant:
                    logger.info("RAG documents available in database")
                    self.current_state["documents_available"] = True
                    # Store in CPA state for potential use by handlers
                    self.cpa_state["chunks"] = chunks
                    self.cpa_state["similarity_scores"] = all_scores
                    self.cpa_state["tool_used"] = tool_used
                else:
                    logger.info("No relevant documents found in database")
                    self.current_state["documents_available"] = False
            else:
                logger.warning("RAG handler not found")
                self.current_state["documents_available"] = False

        except Exception as e:
            logger.error(f"Error checking RAG availability: {e}")
            self.current_state["documents_available"] = False

    def _set_handler_states(self):
        """Set state for all handlers"""
        for handler in self.handlers:
            handler.set_state(self.current_state)
    
    def _clear_handler_states(self):
        """Clear state from all handlers"""
        for handler in self.handlers:
            handler.set_state(None)

    def _get_fallback_response(self, language: str) -> str:
        """Get fallback response in appropriate language"""
        if language == "Arabic":
            return (
                "عذراً، واجهت خطأ في معالجة استفسارك. "
                "يمكنني مساعدتك في تحليل المستندات، إنشاء وحدات تعليمية، أو الإجابة على الأسئلة العامة. "
                "كيف يمكنني مساعدتك؟"
            )
        else:
            return (
                "I'm sorry, I encountered an error processing your request. "
                "I can help with document analysis, creating learning units, or general questions. "
                "How can I assist you?"
            )