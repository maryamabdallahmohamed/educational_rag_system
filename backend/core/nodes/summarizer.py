# backend/core/nodes/summarization_node.py
from langchain.prompts import ChatPromptTemplate
from backend.models.llms.groq_llm import GroqLLM
from backend.utils.logger_config import get_logger
from backend.core.states.graph_states import RAGState, Summary
from backend.loaders.prompt_loaders.prompt_loader import PromptLoader
from langchain_core.output_parsers import JsonOutputParser
from pydantic import ValidationError
from typing import List
from backend.database.repositories.summary_repo import SummaryRepository
from backend.database.db import NeonDatabase


class SummarizationNode:
    """
    Modular summarization node for RAG system.
    Generates concise summaries from documents with structured output.
    """
    
    def __init__(self):
        self.logger = get_logger("summarization_node")
        llm_wrapper = GroqLLM()
        self.llm = llm_wrapper.llm
        
        # Setup JSON output parser
        self.parser = JsonOutputParser(pydantic_object=Summary)
        
        # Load system prompt template
        self.template = PromptLoader.load_system_prompt("prompts/summerize_prompt.yaml")
        
        # Build prompt template
        self.prompt = ChatPromptTemplate.from_template(self.template)
        
        # Create the processing chain
        self.chain = self.prompt | self.llm | self.parser
        
        self.logger.info("Summarization Node initialized successfully")

    async def process(self, state: RAGState) -> RAGState:
        """
        Generate a concise study summary from documents stored in state.
        """
        
        # Get query string (instruction), fallback if missing
        query = state.get("query", "Generate a comprehensive summary of this document")
        self.logger.debug("Received query: %s", query)
        
        # Load documents and prepare context
        docs, detected_lang = self._load_content(state)
        self.logger.debug("Loaded %d documents", len(docs))
        self.logger.debug("Detected language: %s", detected_lang)
        
        if not docs:
            self.logger.warning("No documents available in state")
            state["summary"] = None
            state["answer"] = "No documents available in state to summarize."
            return state
        
        # Prepare context from documents
        context = self._prepare_context(docs)
        self.logger.debug("Prepared context of length: %d characters", len(context))
        
        try:
            # Generate summary using the chain
            result = self._generate_summary(context, query, detected_lang)
            self.logger.debug("Raw LLM output: %s", result)
            
            # Handle case where result might be a string instead of dict
            if isinstance(result, str):
                self.logger.warning("LLM returned string instead of JSON, attempting to parse")
                import json
                try:
                    result = json.loads(result)
                except json.JSONDecodeError:
                    # Fallback: create a basic summary structure
                    self.logger.warning("Failed to parse JSON, creating fallback summary")
                    result = {
                        "title": "Document Summary",
                        "content": result[:500] + "..." if len(result) > 500 else result,
                        "key_points": ["Summary generated from document content"],
                        "language": detected_lang
                    }
            
            title = result.get('title', 'Document Summary')
            content = result.get('content', 'Summary not available')
            key_points = result.get('key_points', ['No key points extracted'])
            language = result.get('language', detected_lang)
            
            # Validate and store results in state
            state['summary_title'] = title
            state['summary'] = content
            state['key_points'] = key_points
            
            self.logger.info("Summary generated successfully")
            
            # Save to database
            await self.add_to_db(title, content, key_points, language)
            
        except ValidationError as e:
            self.logger.error("Pydantic validation failed: %s", str(e))
            state["summary_title"] = "Summary Error"
            state["summary"] = "Error: Invalid summary format generated."
            state["key_points"] = ["Error in summary generation"]
            
        except Exception as e:
            self.logger.error("Summary generation failed: %s", str(e), exc_info=True)
            state["summary_title"] = "Summary Error"
            state["summary"] = "Error during summary generation."
            state["key_points"] = ["Error in summary generation"]
        
        return state

    def _load_content(self, state: RAGState) -> tuple[List, str]:
        """Load documents from state and detect language."""
        docs = state.get("documents", [])
        detected_lang = "ar"
        if docs:
            detected_lang = docs[0].metadata.get("language", "ar")
        return docs, detected_lang

    def _prepare_context(self, docs: List) -> str:
        """Combine document contents into a single context string."""
        return "\n\n".join(doc.page_content for doc in docs)

    def _generate_summary(self, context: str, query: str, detected_lang: str):
        """Generate summary using the LLM chain - returns Summary object directly."""
        self.logger.debug("Invoking chain with query='%s' and lang='%s'", query, detected_lang)
        return self.chain.invoke({
            "context": context,
            "instruction": query,
            "detected_lang": detected_lang,
            "format_instructions": self.parser.get_format_instructions()
        })
    
    async def add_to_db(self, title: str, content: str, key_points: List[str], language: str):
        """Save summary to database."""
        if not title or not content:
            self.logger.warning("No summary to save to database")
            return
        
        session = NeonDatabase.get_session()
        
        try:
            repo = SummaryRepository(session)
            
            # Create the summary record
            summary_record = await repo.create(
                title=title,
                content=content,
                key_points=key_points,
                language=language
            )
            
            # Commit the transaction
            await session.commit()
            
            self.logger.info("Successfully saved summary to database with ID: %s", summary_record.id)
            
        except Exception as e:
            self.logger.error("Failed to save summary to database: %s", str(e), exc_info=True)
            await session.rollback()
        finally:
            await session.close()


_summarization_node_instance = None


def get_summarization_node() -> SummarizationNode:
    """Get a singleton summarization node instance for reuse across calls."""
    global _summarization_node_instance
    if _summarization_node_instance is None:
        _summarization_node_instance = SummarizationNode()
    return _summarization_node_instance


async def summarization_node_singleton(state: RAGState) -> RAGState:
    """
    Async singleton wrapper for summarization node - reuses the same instance.
    More efficient for multiple calls.
    """
    summarization_node = get_summarization_node()
    return await summarization_node.process(state)