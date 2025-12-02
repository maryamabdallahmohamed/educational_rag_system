from langchain_core.tools import Tool
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from backend.core.agents.base_handler import BaseHandler
from backend.models.llms.groq_llm import GroqLLM
from backend.core.states.graph_states import Summary, QAResponse, LearningUnit
from backend.core.agents.tutor_agent_handlers.load_data import (
    extract_data_from_summary,
    extract_data_from_qa_response,
    extract_data_from_learning_unit
)
import json

class PhrasingInfoHandler(BaseHandler):
    """
    Handler responsible for processing educational content (Summary, QAResponse, LearningUnit)
    and passing it to an LLM for phrasing or further processing.
    """

    def __init__(self):
        super().__init__()
        self.llm_wrapper = GroqLLM()
        self.llm = self.llm_wrapper.llm
        self.parser = StrOutputParser()

        self.base_prompt = PromptTemplate(
            input_variables=["data_type", "data"],
            template="""
        You are an educational assistant who rewrites content to make it extremely easy for Egyptian students to understand.  
        Your job is to explain the material simply, clearly, and in a friendly teaching tone.

        Guidelines:
        - Break down difficult ideas into simple steps.
        - Use examples, scenarios, or analogies that Egyptian students can relate to.
        - Keep the explanation concise but meaningful.
        - Avoid overly academic or formal language.
        - If the content is technical, simplify it without losing accuracy.
        - Add a small, simple practice question at the end to check understanding.

        Rewrite the following content clearly and in an Egypt-friendly educational style.

        Data Type: {data_type}

        Content:
        {data}

        Now provide:
        1. A simplified explanation  
        2. A relatable example  
        3. A quick practice question  
            """
        )

    self.chain = self.base_prompt | self.llm | self.parser

    def tool(self) -> Tool:
        """Return configured LangChain Tool"""
        return Tool(
            name="phrasing_info_tool",
            description="Refines units to make it easy for students to understand.",
            func=self._process_sync,
        )

    def _process_sync(self, input_data) -> str:
        """Synchronous wrapper for processing"""
        return self.process_data(input_data)

    async def process_data(self, input_data):
        try:
            type_map = {
                Summary: ("Summary", extract_data_from_summary),
                QAResponse: ("QAResponse", extract_data_from_qa_response),
                LearningUnit: ("LearningUnit", extract_data_from_learning_unit),
            }

            for cls, (data_type, extractor) in type_map.items():
                if isinstance(input_data, cls):
                    return await self.chain.ainvoke({
                        "data_type": data_type,
                        "data": extractor(input_data)
                    })
            self.logger.warning(f"Unsupported data type: {type(input_data)}")
            return f"Error: Unsupported data type {type(input_data)}"

        except Exception as e:
            self.logger.error(f"Error in PhrasingInfoHandler: {e}")
            return f"Error processing request: {str(e)}"
