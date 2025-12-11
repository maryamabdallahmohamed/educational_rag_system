from typing import List
import asyncio
from backend.utils.logger_config import get_logger
from backend.loaders.prompt_loaders.prompt_loader import PromptLoader
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from backend.models.llms.ollama_llm import OllamaLLM
from backend.core.states.graph_states import QAResponse, QAPair
from backend.database.repositories.qa_repo import QuestionAnswerRepository
from backend.database.repositories.qa_item_repo import QuestionAnswerItemRepository
from backend.database.db import NeonDatabase
from backend.utils.singleton import SingletonMeta
from pydantic import ValidationError
from typing import Any

class QANode(metaclass=SingletonMeta):
    """Modular Q&A generation node for RAG system."""

    def __init__(self, default_question_count: int = 10):
        if getattr(self, "_initialized", False):
            return
        self.logger = get_logger("qa_node")
        self.llm = OllamaLLM()
        self.default_question_count = default_question_count
        self.parser = JsonOutputParser(pydantic_object=QAResponse)

        template = PromptLoader.load_system_prompt("prompts/qa_prompt.yaml")
        self.prompt = ChatPromptTemplate.from_template(template)
        self.chain = self.prompt | self.llm.llm | self.parser
        self._initialized = True
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

                self.logger.debug("Parsed response from chain: %s", qa_response)

                try:
                    validated = QAResponse(**qa_response)
                except ValidationError as ve:
                    self.logger.error("Validation error for QAResponse: %s", ve)
                    raise

                # Persist serialized copy to DB, keep graph state models in memory
                await self._add_to_db(validated.qa_pairs)
                self.logger.info("Q&A generation and storage completed successfully")

                return validated 

            except Exception as e:
                self.logger.error("Error during Q&A processing: %s", str(e))
                raise


    async def _generate_qa_pairs(self, context: str, instruction: str, lang: str, count: int) -> str:
        """Generate Q&A pairs using the chain and return raw JSON output."""
        return await asyncio.to_thread(lambda: self.chain.invoke({
            "context": context,
            "instruction": instruction,
            "detected_lang": lang,
            "Questions": count,
            "format_instructions": self.parser.get_format_instructions(),
        }))

    async def _add_to_db(self, qa_items: List[QAPair]):
        """Save Q&A pairs to the database."""
        async with NeonDatabase.get_session() as session:
            qa_repo = QuestionAnswerRepository(session)
            item_repo = QuestionAnswerItemRepository(session)

            # Store serialized items inside qa_data JSONB column
            serialized_items = self._serialize_qa_items(qa_items)
            qa_record = await qa_repo.create(qa_data={"qa_pairs": serialized_items})
            await session.flush()

            for idx, pair in enumerate(serialized_items):
                await item_repo.create(
                    question_answer_id=qa_record.id,
                    qa_index=idx,
                    question_text=pair.get("question", ""),
                    answer_text=pair.get("answer", "")
                )

            await session.commit()
            self.logger.info("Saved %d Q&A pairs to database (QA ID: %s)", len(serialized_items), qa_record.id)

    def _serialize_qa_items(self, qa_items: List[Any]) -> List[dict]:
        """Convert QA items (possibly Pydantic models) into plain dicts."""
        serialized = []
        for item in qa_items:
            # Pydantic v2
            if hasattr(item, "model_dump"):
                serialized.append(item.model_dump())
                continue
            # Pydantic v1
            if hasattr(item, "dict"):
                serialized.append(item.dict())
                continue
            # Already a dict
            if isinstance(item, dict):
                serialized.append(item)
                continue
            # Fallback: attempt generic conversion
            try:
                serialized.append(dict(item))
            except Exception:
                # As last resort, convert via vars
                serialized.append(vars(item))
        return serialized