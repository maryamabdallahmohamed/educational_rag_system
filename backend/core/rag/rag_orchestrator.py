from typing import Dict, Any, Optional
from backend.core.rag.rag_retriever import RAGRetriever
from backend.core.rag.rag_relevance_checker import RAGRelevanceChecker
from backend.core.rag.rag_context_builder import RAGContextBuilder
from backend.core.rag.rag_response_generator import RAGResponseGenerator
import logging


class RAGOrchestrator:
    """Orchestrates the RAG pipeline by coordinating all components"""

    def __init__(
        self, 
        similarity_threshold: float = 0.3, 
        top_k: int = 10, 
        max_context_docs: int = 5, 
        max_content_length: int = 5000, 
        use_json_output: bool = False, 
        use_learning_unit: bool = False
    ):
        self.retriever = RAGRetriever()
        self.relevance_checker = RAGRelevanceChecker(similarity_threshold)
        self.context_builder = RAGContextBuilder(max_context_docs, max_content_length)
        self.response_generator = RAGResponseGenerator(use_json_output, use_learning_unit)
        self.logger = logging.getLogger(__name__)

        # Configuration
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold
        self.use_json_output = use_json_output
        self.use_learning_unit = use_learning_unit

        # Track last retrieval for database logging
        self._last_retrieval_info = {
            "chunk_ids": [],
            "similarity_scores": [],
            "num_chunks": 0
        }

    async def process_query(self, query: str, return_structured: bool = False):
        """Process a RAG query through the complete pipeline"""
        try:
            self.logger.info(f"Processing RAG query: {query[:50]}...")

            # Step 1: Retrieve documents
            documents = await self.retriever.retrieve_documents(query, self.top_k)
            
            if not documents:
                # Reset retrieval info when no documents found
                self._last_retrieval_info = {
                    "chunk_ids": [],
                    "similarity_scores": [],
                    "num_chunks": 0
                }
                return self._handle_no_documents()

            # Store retrieval metadata for database tracking
            self._last_retrieval_info = {
                "chunk_ids": [
                    str(doc.metadata.get("id", doc.metadata.get("chunk_id", ""))) 
                    for doc in documents
                ],
                "similarity_scores": [
                    float(doc.metadata.get("similarity_score", 0.0)) 
                    for doc in documents
                ],
                "num_chunks": len(documents)
            }

            # Step 2: Check relevance
            if not self.relevance_checker.check_relevance(query, documents):
                return self._handle_low_relevance()

            # Step 3: Get top documents (already sorted by similarity)
            top_docs = self.relevance_checker.get_top_documents(documents, self.context_builder.max_docs)

            # Step 4: Build context
            if return_structured:
                structured_context = self.context_builder.build_structured_context(top_docs)
                # Step 5: Generate structured response
                return self.response_generator.generate_structured_response(query, structured_context)
            else:
                context = self.context_builder.build_context(top_docs)
                conversation_history = self.response_generator.get_conversation_history()
                # Step 5: Generate response
                return self.response_generator.generate_response(query, context, conversation_history)

        except Exception as e:
            self.logger.error(f"Error in RAG pipeline: {e}")
            # Reset retrieval info on error
            self._last_retrieval_info = {
                "chunk_ids": [],
                "similarity_scores": [],
                "num_chunks": 0
            }
            return self._handle_pipeline_error(e)

    async def check_query_relevance(self, query: str) -> bool:
        """Check if query has relevant content without generating full response"""
        try:
            documents = await self.retriever.retrieve_documents(query, self.top_k)
            
            if not documents:
                self._last_retrieval_info = {
                    "chunk_ids": [],
                    "similarity_scores": [],
                    "num_chunks": 0
                }
                return False
            
            # Store retrieval info even during relevance check
            self._last_retrieval_info = {
                "chunk_ids": [
                    str(doc.metadata.get("id", doc.metadata.get("chunk_id", ""))) 
                    for doc in documents
                ],
                "similarity_scores": [
                    float(doc.metadata.get("similarity_score", 0.0)) 
                    for doc in documents
                ],
                "num_chunks": len(documents)
            }
            
            return self.relevance_checker.check_relevance(query, documents)
            
        except Exception as e:
            self.logger.error(f"Error checking query relevance: {e}")
            self._last_retrieval_info = {
                "chunk_ids": [],
                "similarity_scores": [],
                "num_chunks": 0
            }
            return True

    def get_last_retrieval_info(self) -> Dict[str, Any]:
        """
        Get information about the last retrieval operation
        Returns dict with chunk_ids, similarity_scores, and num_chunks
        This is used by RAGChatHandler to save retrieval metadata to database
        """
        return self._last_retrieval_info.copy()

    def get_pipeline_info(self) -> Dict[str, Any]:
        """Get information about the RAG pipeline configuration"""
        return {
            "similarity_threshold": self.similarity_threshold,
            "top_k": self.top_k,
            "max_context_docs": self.context_builder.max_docs,
            "max_content_length": self.context_builder.max_content_length,
            "components": {
                "retriever": "RAGRetriever",
                "relevance_checker": "RAGRelevanceChecker (similarity-based)",
                "context_builder": "RAGContextBuilder",
                "response_generator": "RAGResponseGenerator"
            }
        }

    def update_configuration(
        self,
        similarity_threshold: Optional[float] = None,
        top_k: Optional[int] = None,
        max_context_docs: Optional[int] = None,
        max_content_length: Optional[int] = None
    ):
        """Update pipeline configuration"""
        if similarity_threshold is not None:
            self.similarity_threshold = similarity_threshold
            self.relevance_checker.similarity_threshold = similarity_threshold

        if top_k is not None:
            self.top_k = top_k

        if max_context_docs is not None:
            self.context_builder.max_docs = max_context_docs

        if max_content_length is not None:
            self.context_builder.max_content_length = max_content_length

        self.logger.info("RAG pipeline configuration updated")

    def clear_conversation_history(self):
        """Clear conversation memory"""
        self.response_generator.clear_memory()

    def _handle_no_documents(self) -> str:
        """Handle case when no documents are retrieved"""
        return "I don't have any documents to reference. Please upload documents first before asking questions about their content."

    def _handle_low_relevance(self) -> str:
        """Handle case when document relevance is too low"""
        return "I couldn't find relevant information in the uploaded documents to answer your question. Please try rephrasing your question or check if the documents contain the information you're looking for."

    def _handle_pipeline_error(self, error: Exception) -> str:
        """Handle pipeline errors"""
        return f"I encountered an error while processing your question: {str(error)}"