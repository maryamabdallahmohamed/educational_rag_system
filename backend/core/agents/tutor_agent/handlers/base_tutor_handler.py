"""
Base Handler for Tutor Agent Handlers

This abstract base class provides the common interface and utilities
for all tutor agent handlers. Each handler specializes in a specific
tutoring capability (explanation, questions, feedback, etc.).
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.llms.groq_llm import GroqLLM
from backend.models.embedders.hf_embedder import HFEmbedder
from backend.utils.logger_config import get_logger

if TYPE_CHECKING:
    from backend.core.agents.tutor_agent.tutor_state import TutorState

logger = get_logger(__name__)


class BaseTutorHandler(ABC):
    """
    Base class for all tutor handlers.
    
    Provides common functionality for LLM access, embedding,
    context retrieval, and error handling.
    """
    
    def __init__(
        self, 
        llm: GroqLLM, 
        embedder: HFEmbedder, 
        vector_store: Any = None
    ):
        """
        Initialize the handler with required components.
        
        Args:
            llm: The language model for generating responses
            embedder: The embedding model for semantic operations
            vector_store: Optional vector store for RAG operations
        """
        self.llm = llm
        self.embedder = embedder
        self.vector_store = vector_store
        self.logger = get_logger(self.__class__.__name__)
    
    @abstractmethod
    async def handle(
        self, 
        state: "TutorState",
        db_session: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """
        Handle the tutoring request.
        
        Args:
            state: The current tutor state containing all context
            db_session: Optional async database session for persistence
            
        Returns:
            Dictionary containing the handler's response and any updates
        """
        pass
    
    @property
    def handler_name(self) -> str:
        """Return the handler name for logging and tracking."""
        return self.__class__.__name__
    
    async def generate_response(self, prompt: str) -> str:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: The prompt to send to the LLM
            
        Returns:
            The LLM's response text
        """
        try:
            from langchain_core.messages import HumanMessage
            messages = [HumanMessage(content=prompt)]
            response = self.llm.invoke(messages)
            return response
        except Exception as e:
            self.logger.error(f"LLM generation error: {e}")
            raise
    
    async def retrieve_context(
        self, 
        query: str, 
        document_id: Optional[str] = None, 
        k: int = 5
    ) -> List[str]:
        """
        Retrieve relevant context from the RAG orchestrator.
        
        Args:
            query: The query to search for
            document_id: Optional filter by document ID
            k: Number of results to return
            
        Returns:
            List of relevant text chunks
        """
        if not self.vector_store:
            self.logger.warning("No RAG orchestrator available for context retrieval")
            return []
        
        try:
            # Check if vector_store is a RAGOrchestrator (has process_query method)
            if hasattr(self.vector_store, 'process_query'):
                # Use RAGOrchestrator to retrieve context
                response = await self.vector_store.process_query(query, return_structured=False)
                
                # Get retrieval info for debugging
                retrieval_info = self.vector_store.get_last_retrieval_info()
                self.logger.info(f"RAG retrieved {retrieval_info['num_chunks']} chunks")
                
                # RAGOrchestrator returns a string response, we need to return it as context
                # The response is already processed, so we return it as a single context item
                if response and not response.startswith("I don't have") and not response.startswith("I couldn't find"):
                    return [response]
                else:
                    # Fallback: try to get raw documents via the retriever
                    if hasattr(self.vector_store, 'retriever'):
                        from backend.core.rag.rag_retriever import RAGRetriever
                        retriever: RAGRetriever = self.vector_store.retriever
                        documents = await retriever.retrieve_documents(query, top_k=k)
                        return [doc.page_content for doc in documents] if documents else []
                    return []
            
            # Legacy support: if vector_store has similarity_search method
            elif hasattr(self.vector_store, 'similarity_search'):
                query_embedding = await self.embedder.embed_query(query)
                filter_dict = {"document_id": document_id} if document_id else None
                results = await self.vector_store.similarity_search(
                    query_embedding, 
                    k=k,
                    filter=filter_dict
                )
                return [r.page_content for r in results] if results else []
            
            else:
                self.logger.warning("Vector store doesn't have a compatible interface")
                return []
            
        except Exception as e:
            self.logger.error(f"Context retrieval error: {e}")
            return []
    
    def _handle_error(self, error: Exception, context: str = "") -> Dict[str, Any]:
        """
        Consistent error handling for all handlers.
        
        Args:
            error: The exception that occurred
            context: Additional context about where the error occurred
            
        Returns:
            Error response dictionary
        """
        error_msg = f"Error in {self.handler_name}"
        if context:
            error_msg += f" ({context})"
        error_msg += f": {str(error)}"
        
        self.logger.error(error_msg)
        
        return {
            "response": "I encountered an issue while processing your request. "
                       "Could you please try again or rephrase your question?",
            "error": str(error),
            "handler": self.handler_name
        }
    
    def _get_language_instruction(self, language: str) -> str:
        """Get instruction for response language."""
        if language == "ar":
            return "Respond entirely in Arabic (العربية)."
        return ""
