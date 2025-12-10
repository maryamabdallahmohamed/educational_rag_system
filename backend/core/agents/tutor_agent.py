from typing import List
from langchain.agents import create_agent
from langchain_classic.agents import AgentExecutor
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import Tool
from backend.models.llms.groq_llm import GroqLLM
from backend.core.agents.tutor_agent_handlers.phrasing_handler import PhrasingInfoHandler
from backend.core.agents.tutor_agent_handlers.adaptive_handler import AdaptiveHandler
from backend.utils.logger_config import get_logger
from backend.loaders.prompt_loaders.prompt_loader import PromptLoader
from backend.database.repositories.tutor_results_repo import TutorResultsRepository
from backend.database.repositories.tool_output import ToolOutputRepository
from backend.database.db import NeonDatabase
logger = get_logger("tutor_agent")


class TutorAgent:
    """Tutor Agent responsible for phrasing/simplification tasks for students."""

    def __init__(self):
        self.llm = GroqLLM().llm
        self.current_state = {}

        # Register handlers & tools
        self.handlers = [PhrasingInfoHandler(), AdaptiveHandler()]
        self.tools = [handler.tool() for handler in self.handlers]

        for tool in self.tools:
            logger.info(f"Loaded tool: {tool.name}")

        self.agent_executor = self._create_agent()

    # ----------------------------------------------------------------------
    # Agent Creation
    # ----------------------------------------------------------------------
    def _create_agent(self) -> AgentExecutor:
        """Create the ReAct agent with fallback prompt."""
            
        prompt_template = PromptLoader.load_system_prompt("prompts/tutor_agent.yaml")
        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["input","result", "tools", "tool_names", "agent_scratchpad", "previous_query", "current_query"]
        )

        agent = create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=str(prompt)
        )

        return AgentExecutor(
                    agent=agent,
                    tools=self.tools,
                    verbose=True,
                    max_iterations=5,
                    handle_parsing_errors=self._handle_error,
                    max_execution_time=800
                )

    def _handle_error(self, error) -> str:
        """
        Handle parsing errors by treating appropriate errors as the final answer.
        """
        response = str(error)
        if "Could not parse LLM output" in response or "Invalid Format" in response:
             if "`" in response:
                 return response.split("`")[1]
        return f"Error: {str(error)}"

    async def _save_db(self, query,cpa_result, tutor_result_text, tools_used):
        try:
            async with NeonDatabase.get_session() as session:
                tutor_results_repo = TutorResultsRepository(db=session)
                tools_output_repo = ToolOutputRepository(db=session)
                
                # Create the main result first
                saved_result = await tutor_results_repo.create(query=query,cpa_result=cpa_result, tutor_result_text=tutor_result_text)
                
                # Then create tool outputs linked to it
                for tool in tools_used:
                    await tools_output_repo.create(
                        tool_name=tool, 
                        input_state=cpa_result, 
                        output=tutor_result_text,
                        tutor_result_id=saved_result.result_id
                    )

                logger.info(f"Saved tutor operation to database: {saved_result.result_id}")
        except Exception as e:
            logger.error(f"Failed to save tutor operation to database: {e}")
        


    def scratchpad_parser(self, scratchpad):
        tools_used = []
        for line in scratchpad.splitlines():
            if "Action:" in line:
                # extract the tool name after "Action:"
                parts = line.split("Action:")
                if len(parts) > 1:
                    tools_used.append(parts[1].strip())
        return tools_used
        
    # ----------------------------------------------------------------------
    # Agent Processing Logic
    # ----------------------------------------------------------------------
    async def process(self, query: str, cpa_result,current_query=None, previous_query=None):
        """Run the agent on the given query."""
        query = query.strip()

        if not query:
            return "Please provide an input"

        try:
            if cpa_result:
                self._set_handler_states(cpa_result)

            logger.info("TutorAgent: Executing query...")
            tool_names = [tool.name for tool in self.tools]
            output = await self.agent_executor.ainvoke({
                "input": query,
                "result": cpa_result,
                "previous_query": previous_query,
                "current_query": query,
                "agent_scratchpad": ""
            })
            answer = output.get("output", "I couldn't process your request.")
            scratchpad = output.get("agent_scratchpad", "")
            tools_used = self.scratchpad_parser(scratchpad)
            logger.debug(f"Type of answer: {type(answer)}, Type of current_state['answer']: {type(self.current_state.get('answer'))}")
            if isinstance(self.current_state.get("answer"), dict) and isinstance(answer, dict):
                try:
                    self.current_state["answer"].update(answer)
                except Exception as e:
                    logger.error(f"Error while updating dictionaries: {e}")
            else:
                self.current_state["answer"] = answer
            await self._save_db(query,cpa_result, answer, tools_used)
            logger.info("TutorAgent: Execution complete.")

            return self.current_state   

        except Exception as e:
            logger.error(f"TutorAgent processing error: {e}")
            return {"answer": f"Error: {str(e)}"}

        finally:
            self._clear_handler_states()

    def _set_handler_states(self, state):
        for handler in self.handlers:
            handler.set_state(state)

    def _clear_handler_states(self):
        for handler in self.handlers:
            if hasattr(handler, "set_state"):
                handler.set_state(None)
