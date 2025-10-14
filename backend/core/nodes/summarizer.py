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
import json

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

    async def process(self, query, documents) -> RAGState:
        """
        Generate a concise study summary from documents stored in state.
        """
        
        # Get query string (instruction), fallback if missing
        query = query
        self.logger.debug("Received query: %s", query)
        
        # Load documents and prepare context
        language = documents[0].metadata['language']
        context = documents
        self.logger.debug("Loaded %d documents", len(documents))
        self.logger.debug("Detected language: %s", language)

        if not context:
            self.logger.warning("No documents available in state")
            return None
        self.logger.debug("Prepared context of length: %d characters", len(context))
        
        try:
            # Generate summary using the chain
            result = self._generate_summary(context, query, language)
            self.logger.debug("Raw LLM output: %s", result)
            
            # Handle case where result might be a string instead of dict
            if isinstance(result, str):
                self.logger.warning("LLM returned string instead of JSON, attempting to parse")
                try:
                    result = json.loads(result)
                except json.JSONDecodeError:
                    # Fallback: create a basic summary structure
                    self.logger.warning("Failed to parse JSON, creating fallback summary")
                    result = {
                        "title": "Document Summary",
                        "content": result[:500] + "..." if len(result) > 500 else result,
                        "key_points": ["Summary generated from document content"],
                        "language": language
                    }
            
            title = result.get('title', 'Document Summary')
            content = result.get('content', 'Summary not available')
            key_points = result.get('key_points', ['No key points extracted'])
            language = result.get('language', language)
            
            self.logger.info("Summary generated successfully")
            
            # Save to database
            await self.add_to_db(title, content, key_points, language)
            
        except ValidationError as e:
            self.logger.error("Pydantic validation failed: %s", str(e))

        except Exception as e:
            self.logger.error("Summary generation failed: %s", str(e), exc_info=True)

        return result

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
