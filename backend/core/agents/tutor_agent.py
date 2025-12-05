from typing import List
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import Tool
from backend.models.llms.groq_llm import GroqLLM
from backend.core.agents.tutor_agent_handlers.phrasing_handler import PhrasingInfoHandler
from backend.utils.logger_config import get_logger
from backend.loaders.prompt_loaders.prompt_loader import PromptLoader

logger = get_logger("tutor_agent")


class TutorAgent:
    """Tutor Agent responsible for phrasing/simplification tasks for students."""

    def __init__(self):
        self.llm = GroqLLM().llm
        self.current_state = {}

        # Register handlers & tools
        self.handlers = [PhrasingInfoHandler()]
        self.tools = [handler.tool() for handler in self.handlers]

        for tool in self.tools:
            logger.info(f"Loaded tool: {tool.name}")

        self.agent_executor = self._create_agent()

    # ----------------------------------------------------------------------
    # Agent Creation
    # ----------------------------------------------------------------------
    def _create_agent(self) -> AgentExecutor:
        """Create the ReAct agent with fallback prompt."""
            
        prompt = PromptTemplate(
            template="""
        You are a helpful Tutor Agent. Your job is to help students understand and simplify educational content.

        You have access to the following tools:
        {tools}

        Use this reasoning format:

        Question: {input}
        Thought: think step-by-step about whether you need to use a tool.
        {agent_scratchpad}
        Action: the tool to use (one of [{tool_names}])
        Action Input: the exact input for the tool
        Observation: the tool output
        Thought: continue reasoning
        Final Answer: your final answer to the user

        Begin!
        """,
            input_variables=["input", "tools", "tool_names", "agent_scratchpad"]
        )

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
                    handle_parsing_errors=True,
                    max_execution_time=500
                )

    # ----------------------------------------------------------------------
    # Agent Processing Logic
    # ----------------------------------------------------------------------
    async def process(self, query: str, result=None, input_data=None):
        """Run the agent on the given query."""
        query = query.strip()

        if not query:
            return "I didn't receive any query. How can I help you?"

        # Prefer input_data from result if provided
        if result and not input_data:
            input_data = result

        try:
            if input_data:
                self._set_handler_states(input_data)

            logger.info("TutorAgent: Executing query...")
            output = await self.agent_executor.ainvoke({"input": query})
            answer = output.get("output", "I couldn't process your request.")

            self.current_state["answer"] = answer
            logger.info("TutorAgent: Execution complete.")

            return self.current_state

        except Exception as e:
            logger.error(f"TutorAgent processing error: {e}")
            return {"answer": f"Error: {str(e)}"}

        finally:
            self._clear_handler_states()

    # ----------------------------------------------------------------------
    # State Management
    # ----------------------------------------------------------------------
    def _set_handler_states(self, state):
        for handler in self.handlers:
            handler.set_state(state)

    def _clear_handler_states(self):
        for handler in self.handlers:
            if hasattr(handler, "set_state"):
                handler.set_state(None)
