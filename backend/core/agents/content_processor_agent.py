from typing import List, Optional
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import Tool
from backend.core.states.graph_states import RAGState
from backend.models.llms.groq_llm import GroqLLM
from backend.core.agents.cpa_handlers.explainable_units_handler import ExplainableUnitsHandler
from backend.core.agents.cpa_handlers.rag_chat_handler import RAGChatHandler
from backend.core.agents.cpa_handlers.document_analysis_handler import DocumentAnalysisHandler
from backend.utils.helpers.language_detection import returnlang
from backend.utils.logger_config import get_logger
from backend.loaders.prompt_loaders.prompt_loader import PromptLoader

logger = get_logger("content_processor_agent")


class ContentProcessorAgent:
    """
    Simplified LangChain Agent for Content Processing
    Uses handler-based tools for RAG chat, unit generation, and document analysis
    """

    def __init__(self):
        self.llm = GroqLLM().llm
        self.current_state = None


        self.handlers = [
            ExplainableUnitsHandler(),
            RAGChatHandler(),
            DocumentAnalysisHandler()
        ]

        # Collect tools from handlers
        self.tools = self._collect_tools()
        self.agent_executor = self._create_agent()

    def _collect_tools(self) -> List[Tool]:
        """Collect tools from all handlers"""
        tools = []
        for handler in self.handlers:
            try:
                tool = handler.tool()
                tools.append(tool)
                logger.info(f"Collected tool: {tool.name} from {handler.__class__.__name__}")
            except Exception as e:
                logger.error(f"Error collecting tool from {handler.__class__.__name__}: {e}")
        
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

    async def process(self, state: RAGState) -> RAGState:
        """Process query using simplified agent"""
        query = state.get("query", "").strip()
        if not query:
            state["answer"] = "I didn't receive any query. How can I help you?"
            return state

        try:
            # Set current state for all handlers
            self._set_handler_states(state)
            
            # Detect language for response
            detected_language = returnlang(query)
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
            state["answer"] = answer
            
            logger.info("Agent execution completed successfully")
            return state

        except Exception as e:
            logger.error(f"Error in content processor agent: {e}")
            state["answer"] = self._get_fallback_response(detected_language if 'detected_language' in locals() else 'English')
            return state
        finally:
            # Clean up handler states
            self._clear_handler_states()
    
    def _set_handler_states(self, state: RAGState):
        """Set state for all handlers"""
        for handler in self.handlers:
            handler.set_state(state)
    
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
