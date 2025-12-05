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


class PhrasingInfoHandler(BaseHandler):
    """
    Handles phrasing of educational content (Summary, QAResponse, LearningUnit)
    using a simple synchronous chain compatible with ReAct agents.
    """

    def __init__(self):
        super().__init__()
        self.llm = GroqLLM().llm
        self.parser = StrOutputParser()

        self.base_prompt = PromptTemplate(
            input_variables=["data_type", "data"],
            template="""
You are an educational assistant who rewrites content to make it extremely easy for Egyptian students.

Guidelines:
- Break down concepts simply
- Use relatable examples
- Avoid academic language
- Keep explanations friendly
- Add one short practice question at the end

Rewrite the following clearly in an Egypt-friendly style:

Data Type: {data_type}

Content:
{data}

Provide:
1. Simplified explanation  
2. A relatable example  
3. One practice question  
            """,
        )

        self.chain = self.base_prompt | self.llm | self.parser

    # ---------------------------------------------------------------------
    # TOOL
    # ---------------------------------------------------------------------
    def tool(self) -> Tool:
        """Return the synchronous phrasing tool."""
        return Tool(
            name="phrasing_info_tool",
            description="Rephrases educational content to make it easy for students to understand.",
            func=self._run_tool_sync,
        )

    # ---------------------------------------------------------------------
    # MAIN SYNC TOOL EXECUTION
    # ---------------------------------------------------------------------
    def _run_tool_sync(self, _: str) -> str:
        """
        The tool is synchronous and ignores the input string.
        It uses the current stored state (Summary, QAResponse, LearningUnit).
        """

        if not self._validate_state():
            return "No educational content available to process."

        state = self.current_state

        # ---- Identify type & extract content ---------------------------------
        if isinstance(state, Summary):
            extracted = extract_data_from_summary(state)
            data_type = "Summary"

        elif isinstance(state, QAResponse):
            extracted = extract_data_from_qa_response(state)
            data_type = "QAResponse"

        elif isinstance(state, LearningUnit):
            extracted = extract_data_from_learning_unit(state)
            data_type = "LearningUnit"

        else:
            return "Unsupported content type."

        # Convert to readable string
        readable_data = json.dumps(extracted, ensure_ascii=False, indent=2)

        # ---- Run synchronous LLM chain ---------------------------------------
        try:
            result = self.chain.invoke({
                "data_type": data_type,
                "data": readable_data
            })
            return result
        except Exception as e:
            return f"Error processing phrasing: {str(e)}"
