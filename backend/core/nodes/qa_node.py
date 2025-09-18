from typing import  List
from backend.utils.logger_config import get_logger
from backend.loaders.prompt_loaders.prompt_loader import PromptLoader
from langchain_core.output_parsers import JsonOutputParser
from langchain.prompts import ChatPromptTemplate
from backend.models.llms.groq_llm import GroqLLM
from backend.core.states.graph_states import RAGState,QAResponse
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
    
    def process(self, state: RAGState) -> RAGState:
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
    




_qa_node_instance = None

def get_qa_node() -> QANode:
    """Get a singleton QA node instance for reuse across calls."""
    global _qa_node_instance
    if _qa_node_instance is None:
        _qa_node_instance = QANode()
    return _qa_node_instance

def qa_node_singleton(state: RAGState) -> RAGState:
    """
    Singleton wrapper for QA node - reuses the same instance.
    More efficient for multiple calls.
    """
    qa_node = get_qa_node()
    return qa_node.process(state)
