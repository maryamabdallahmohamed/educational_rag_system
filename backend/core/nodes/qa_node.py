from typing import List
import asyncio
from backend.utils.logger_config import get_logger
from backend.loaders.prompt_loaders.prompt_loader import PromptLoader
from langchain_core.output_parsers import JsonOutputParser
from langchain.prompts import ChatPromptTemplate
from backend.models.llms.groq_llm import GroqLLM
from backend.core.states.graph_states import QAResponse
from backend.database.repositories.qa_repo import QuestionAnswerRepository
from backend.database.repositories.qa_item_repo import QuestionAnswerItemRepository
from backend.database.db import NeonDatabase
from langgraph.types import RunnableConfig
from langchain_core.runnables import RunnableLambda

class QANode:
    """Modular Q&A generation node for RAG system."""

    def __init__(self, default_question_count: int = 10):
        self.logger = get_logger("qa_node")
        self.llm = GroqLLM()
        self.default_question_count = default_question_count
        self.parser = JsonOutputParser(pydantic_object=QAResponse)

        template = PromptLoader.load_system_prompt("prompts/qa_prompt.yaml")
        self.prompt = ChatPromptTemplate.from_template(template)
        self.chain = self.prompt | self.llm.llm | self.parser

        self.logger.info("QA Node initialized successfully")

    async def process(self, query, documents: List) -> QAResponse:
        language = documents[0].metadata['language']
        context = "\n\n".join(doc.page_content for doc in documents)
        question_count = self.default_question_count
        self.logger.info("Processing Q&A generation for query: %s", query)
        try:
            qa_response = await self._generate_qa_pairs(
                context=context,
                instruction=query,
                lang=language,
                count=question_count
            )

            qa_pairs = qa_response.get('qa_pairs') 
            # await self._add_to_db(qa_pairs)
            self.logger.info("Q&A generation and storage completed successfully")

            return qa_pairs 

        except Exception as e:
            self.logger.error("Error during Q&A processing: %s", str(e))
            raise


    async def _generate_qa_pairs(self, context: str, instruction: str, lang: str, count: int) -> QAResponse:

        return await asyncio.to_thread(lambda: self.chain.invoke({
            "context": context,
            "instruction": instruction,
            "detected_lang": lang,
            "Questions": count,
            "format_instructions": self.parser.get_format_instructions(),
        }))

    async def _add_to_db(self, qa_items):
        """Save Q&A pairs to the database."""
        async with NeonDatabase.get_session() as session:
            qa_repo = QuestionAnswerRepository(session)
            item_repo = QuestionAnswerItemRepository(session)

            qa_record = await qa_repo.create(qa_data={"qa_pairs": qa_items})
            await session.flush()

            for idx, pair in enumerate(qa_items):
                await item_repo.create(
                    question_answer_id=qa_record.id,
                    qa_index=idx,
                    question_text=pair.get("question", ""),
                    answer_text=pair.get("answer", "")
                )

            await session.commit()
            self.logger.info("Saved %d Q&A pairs to database (QA ID: %s)", len(qa_items), qa_record.id)