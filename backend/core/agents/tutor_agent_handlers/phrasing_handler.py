from langchain_core.tools import Tool
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from backend.core.agents.base_handler import BaseHandler
from backend.models.llms.groq_llm import GroqLLM
import json

class PhrasingInfoHandler(BaseHandler):
    """
    Simplified handler to extract educational content from any dict input
    and rephrase it for Egyptian students.
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
                            """
                        )

        self.chain = self.base_prompt | self.llm | self.parser

    # ---------------------------------------------------------------------
    # TOOL
    # ---------------------------------------------------------------------
    def tool(self) -> Tool:
        """Return the synchronous phrasing tool."""
        return Tool(
            name="phrasing_info_tool",
            description="Rephrases any educational content in a dictionary format to make it easy to understand.",
            func=self._run_tool_sync,
        )

    # ---------------------------------------------------------------------
    # MAIN SYNC TOOL EXECUTION
    # ---------------------------------------------------------------------
    def _run_tool_sync(self, state: dict) -> str:
        """
        Extracts whatever is in the dict and passes it to the LLM.
        """
        if isinstance(state, str):
            try:
                state = json.loads(state)
            except json.JSONDecodeError:
                pass

        if not isinstance(state, dict) or not state:
            return "No educational content available to process."

        # Use the whole dict as content
        extracted = state
        data_type = "General Content"

        readable_data = json.dumps(extracted, ensure_ascii=False, indent=2)

        try:
            result = self.chain.invoke({
                "data_type": data_type,
                "data": readable_data
            })
            return result
        except Exception as e:
            return f"Error processing phrasing: {str(e)}"
