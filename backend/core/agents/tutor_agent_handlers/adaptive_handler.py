from langchain_core.tools import Tool
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from backend.core.agents.base_handler import BaseHandler
from backend.models.llms.groq_llm import GroqLLM
from backend.core.states.graph_states import Summary, QAResponse, LearningUnit
from backend.core.agents.tutor_agent_handlers.data_extraction import (
    extract_data_from_summary,
    extract_data_from_qa_response,
    extract_data_from_learning_unit
)
import json


class AdaptiveHandler(BaseHandler):
    """
    Classifies the user's understanding level based on the previous and current queries.
    """

    def __init__(self):
        super().__init__()

        self.llm = GroqLLM().llm
        self.parser = StrOutputParser()

        self.base_prompt = PromptTemplate(
            input_variables=["previous_query", "current_query"],
            template="""
            You are an educational reasoning assistant.

            Your task is to analyze the student's previous query and their current query, and determine their level of understanding.

            Base logic:
            - If the student repeats the same question, looks confused, or asks for simpler explanation → label = "confusion"
            - If the student partially understands but still needs clarification → label = "partial"
            - If the student understands normally and follows the explanation well → label = "normal"
            - If the student clearly understood and asks deeper, more advanced questions → label = "advanced"

            Only consider what the queries imply about the student's knowledge.

            Return only one word:
            - confusion
            - partial
            - normal
            - advanced

            No explanation. No extra text.

            Previous Query:
            {previous_query}

            Current Query:
            {current_query}
            """
                    )

        self.chain = self.base_prompt | self.llm | self.parser


    # ---------------------------------------------------------------------
    # TOOL
    # ---------------------------------------------------------------------
    def tool(self) -> Tool:
        """Return the synchronous adaptive tool."""
        return Tool(
            name="adaptive_tool",
            description="Classifies the user's understanding level based on the previous and current queries.",
            func=self._run_tool_sync,
        )

    # ---------------------------------------------------------------------
    # MAIN SYNC TOOL EXECUTION
    # ---------------------------------------------------------------------
    def _run_tool_sync(self, _: str) -> str:
        # ---- Run synchronous LLM chain ---------------------------------------
        try:
            state = self.current_state or {}
            previous_query = state.get("previous_query", "")
            current_query = state.get("current_query", "")
            
            result = self.chain.invoke({
                "previous_query": previous_query,
                "current_query": current_query
            })
            return result
        except Exception as e:
            return f"Error processing adaptive handler: {str(e)}"
