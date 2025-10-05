from typing import  List
from backend.utils.logger_config import get_logger
from backend.loaders.prompt_loaders.prompt_loader import PromptLoader
from langchain_core.output_parsers import JsonOutputParser
from langchain.prompts import ChatPromptTemplate
from backend.models.llms.groq_llm import GroqLLM
from backend.core.states.graph_states import RAGState,QAResponse
from backend.database.repositories.qa_repo import QuestionAnswerRepository
from backend.database.repositories.qa_item_repo import QuestionAnswerItemRepository
from backend.database.db import NeonDatabase, Base
class QANode:
    """
    Modular Q&A generation node for RAG system.
    Generates study Q&A pairs from documents with structured output.
    """
    
    def __init__(self, default_question_count: int = 10):
        self.logger = get_logger("qa_node")
        self.llm = GroqLLM()
        self.default_question_count = default_question_count
        
        # Setup JSON output parser
        self.parser = JsonOutputParser(pydantic_object=QAResponse)
        
        # Load system prompt template
        self.template = PromptLoader.load_system_prompt("prompts/qa_prompt.yaml")
        
        # Build prompt template
        self.prompt = ChatPromptTemplate.from_template(self.template)
        
        # Create the processing chain
        self.chain = self.prompt | self.llm.llm | self.parser
        
        self.logger.info("QA Node initialized successfully")
    
    async def process(self, state: RAGState) -> RAGState:
        """
        Generate study Q&A pairs from documents stored in state["documents"].
        
        """
        
        # Get query string (instruction), fallback if missing
        query = state.get("query", "Generate Q&A pairs from this document")
        
        # Get documents directly from state
        docs = state.get("documents", [])
        if not docs:
            self.logger.warning("No documents available in state")
            state["qa_pairs"] = []
            state["answer"] = "No documents available in state to generate Q&A."
            return state
        
        # Combine document contents into context
        context = self._prepare_context(docs)
        
        # Detect language
        detected_lang = self._detect_language(docs)
        
        # Get question count from state or use default
        question_count =self.default_question_count
        
        try:
            # Generate Q&A pairs using the chain
            result = self._generate_qa_pairs(context, query, detected_lang, question_count)
            
            # Store results in state
            state["qa_pairs"] = result.get("qa_pairs", [])
            state["answer"] = f"Generated {len(state['qa_pairs'])} Q&A pairs successfully."
            
            self.logger.info("Q&A generation successful - Generated %d pairs", len(state["qa_pairs"]))
            await self.add_to_db(result.get("qa_pairs", []))
            
        except Exception as e:
            self.logger.error("Q&A generation failed: %s", str(e))
            state["qa_pairs"] = []
            state["answer"] = f"Error during Q&A generation: {str(e)}"
        
        return state
    
    def _prepare_context(self, docs: List) -> str:
        """Combine document contents into a single context string."""
        return "\n\n".join(doc.page_content for doc in docs)
    
    def _detect_language(self, docs: List) -> str:
        """Detect language from document metadata, fallback to Arabic."""
        if docs :
            return docs[0].metadata.get("language", "ar")
        return "ar"
    
    def _generate_qa_pairs(self, context: str, instruction: str, detected_lang: str, question_count: int) -> dict:
        """Generate Q&A pairs using the LLM chain."""
        
        return self.chain.invoke({
            "context": context,
            "instruction": instruction,
            "detected_lang": detected_lang,
            "Questions": question_count,
            "format_instructions": self.parser.get_format_instructions()
        })
    
    def set_question_count(self, count: int):
        """Update the default question count."""
        self.default_question_count = count
        self.logger.info("Updated default question count to %d", count)

    async def add_to_db(self, qa_items):
        """Save Q&A pairs to database with individual item references."""
        session = NeonDatabase.get_session()
        
        try:
            qa_repo = QuestionAnswerRepository(session)
            item_repo = QuestionAnswerItemRepository(session)
            
            # Format data for JSONB storage
            qa_data = {"qa_pairs": qa_items}
            
            # Create the main QuestionAnswer record
            qa_record = await qa_repo.create(qa_data=qa_data)
            await session.flush()  # Ensure qa_record.id is available
            
            self.logger.info("Created QuestionAnswer record with ID: %s", qa_record.id)
            
            # Create individual QuestionAnswerItem records for each Q&A pair
            for index, qa_pair in enumerate(qa_items):
                question_text = qa_pair.get("question", "")
                answer_text = qa_pair.get("answer", "")
                
                await item_repo.create(
                    question_answer_id=qa_record.id,
                    qa_index=index,
                    question_text=question_text,
                    answer_text=answer_text
                )
            
            # Commit all changes
            await session.commit()
            
            self.logger.info(
                "Successfully saved %d Q&A pairs with %d individual items to database", 
                len(qa_items), 
                len(qa_items)
            )
            
        except Exception as e:
            self.logger.error("Failed to save Q&A pairs to database: %s", str(e), exc_info=True)
            await session.rollback()
            raise
        finally:
            await session.close()
_qa_node_instance = None

def get_qa_node() -> QANode:
    """Get a singleton QA node instance for reuse across calls."""
    global _qa_node_instance
    if _qa_node_instance is None:
        _qa_node_instance = QANode()
    return _qa_node_instance

async def qa_node_singleton(state: RAGState) -> RAGState:
    """
    Singleton wrapper for QA node - reuses the same instance.
    More efficient for multiple calls.
    """
    qa_node = get_qa_node()
    return await qa_node.process(state)
