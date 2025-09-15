from types import CodeType
from langchain.prompts import ChatPromptTemplate
from backend__.models.llms.groq_llm import GroqLLM
from backend__.utils.logger_config import get_logger
from backend__.core.states.graph_states import RAGState, Summary
from backend__.loaders.prompt_loaders.prompt_loader import PromptLoader
from langchain_core.output_parsers import JsonOutputParser
from pydantic import ValidationError
from typing import List

logger = get_logger("summerization_module")

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

    def process(self, state: RAGState) -> RAGState:
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
            
            title = result['title']
            content = result['content']
            key_points = result['key_points']
            
            # Validate and store results
            state['summary_title'] = title
            state['summary'] = content
            state['key_points'] = key_points
            
            self.logger.info("Summary generated successfully")
            
        except ValidationError as e:
            self.logger.error("Pydantic validation failed: %s", str(e))
            state["summary_title"] = None
            state["summary"] = "Error: Invalid summary format generated."
            
        except Exception as e:
            self.logger.error("Summary generation failed: %s", str(e))
            state["summary_title"] = None
            state["summary"] = "Error during summary generation."
        
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


_summarization_node_instance = None

def get_summarization_node() -> SummarizationNode:
    """Get a singleton summarization node instance for reuse across calls."""
    global _summarization_node_instance
    if _summarization_node_instance is None:
        _summarization_node_instance = SummarizationNode()
    return _summarization_node_instance

def summarization_node_singleton(state: RAGState) -> RAGState:
    """
    Singleton wrapper for summarization node - reuses the same instance.
    More efficient for multiple calls.
    """
    summarization_node = get_summarization_node()
    return summarization_node.process(state)
