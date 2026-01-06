from typing import List
import asyncio
from backend.utils.logger_config import get_logger
from backend.loaders.prompt_loaders.prompt_loader import PromptLoader
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from backend.models.llms.ollama_llm import OllamaLLM
from backend.database.repositories.qa_repo import QuestionAnswerRepository
from backend.database.db import NeonDatabase
from backend.utils.singleton import SingletonMeta

from pydantic import BaseModel, Field

class QuestionPair(BaseModel):
    question: str = Field(description="A question about the content")
    generated_difficulty: str = Field(description="easy, medium, or hard")

class QuestionOnlyResponse(BaseModel):
    qa_pairs: List[QuestionPair] = Field(description="List of questions generated from the content")
    total_questions: int = Field(description="Total number of questions generated")

class QANode(metaclass=SingletonMeta):
    """Modular Q&A generation node for RAG system."""

    def __init__(self, default_question_count: int = 10):
        if getattr(self, "_initialized", False):
            return
        self.logger = get_logger("qa_node")
        self.llm = OllamaLLM()
        self.default_question_count = default_question_count

        template = PromptLoader.load_system_prompt("prompts/qa_prompt.yaml")
        self.prompt = ChatPromptTemplate.from_template(template)
        self.chain = self.prompt | self.llm.llm
        self._initialized = True
        self.logger.info("QA Node initialized successfully")

    async def process(self, query, documents: List, session_id: str) -> List[dict]:
        language = documents[0].metadata['language']
        context = "\n\n".join(doc.page_content for doc in documents)
        question_count = self.default_question_count
        self.logger.info("Processing Q&A generation for query: %s", query)
        try:
            qa_response = await self._generate_qa_pairs(
                context=context,
                lang=language,
                count=question_count
            )

            await self._add_to_db(qa_response, session_id=session_id)
            self.logger.info("Q&A generation and storage completed successfully")

            return qa_response

        except Exception as e:
            self.logger.error("Error during Q&A processing: %s", str(e))
            raise
    def serialize_ai_message(self,msg):

        return {
            "content": msg
        }



    async def _generate_qa_pairs(self, context: str, lang: str, count: int) -> dict:

        return await asyncio.to_thread(lambda: self.chain.invoke({
            "context": context,
            "detected_lang": lang,
            "Questions": count
        }))

    async def _add_to_db(self, qa_items,session_id: str):
        """Save Q&A pairs to the database."""
        async with NeonDatabase.get_session() as session:
            qa_pairs_serialized = [
            self.serialize_ai_message(pair) for pair in qa_items]
            qa_repo = QuestionAnswerRepository(session)
            qa_record = await qa_repo.create(qa_data={"qa_pairs": qa_pairs_serialized},session_id=session_id)
            await session.flush()
            await session.commit()