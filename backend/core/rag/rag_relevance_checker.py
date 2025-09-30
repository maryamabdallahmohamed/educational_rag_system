from typing import List
from langchain.schema import Document
import logging
from backend.core.states.graph_states import cpa_processor_state

class RAGRelevanceChecker:
    """Handles relevance checking of documents based on similarity scores"""

    def __init__(self, similarity_threshold: float = 0.3):
        # Using similarity score threshold instead of reranker scores
        # Similarity scores range from 0-1, where higher is more similar
        self.similarity_threshold = similarity_threshold
        self.logger = logging.getLogger(__name__)
        self.cpa_processor_state=cpa_processor_state()
    def check_relevance(self, query: str, documents: List[Document]) -> bool:
        """Check if documents have relevant content based on similarity scores"""
        try:
            if not documents:
                self.logger.warning("No documents provided for relevance check")
                return False

            self.logger.info(f"Checking relevance for {len(documents)} documents")

            # Get the best similarity score from the documents
            best_score = max(
                (doc.metadata.get("similarity_score", 0.0) for doc in documents),
                default=0.0
            )

            is_relevant = best_score >= self.similarity_threshold

            # Log detailed scoring information
            all_scores = [doc.metadata.get("similarity_score", 0.0) for doc in documents[:5]]
            self.logger.info(f"Query: '{query[:50]}...'")
            self.logger.info(f"Top 5 similarity scores: {all_scores}")
            self.logger.info(f"Best similarity score: {best_score:.3f}, threshold: {self.similarity_threshold}, relevant: {is_relevant}")
            chunks=[doc.page_content for doc in documents[:5]]
            tool_used= "RAG"
            return is_relevant , all_scores, chunks,tool_used

        except Exception as e:
            self.logger.error(f"Error checking relevance: {e}")
            return True  # Default to True to allow processing

    def get_top_documents(self, documents: List[Document], top_k: int = 5) -> List[Document]:
        """Get top K documents based on similarity scores (already sorted from vector search)"""
        try:
            if not documents:
                return []
            top_docs = documents[:top_k]

            self.logger.info(f"Selected top {len(top_docs)} documents based on similarity")
            return top_docs

        except Exception as e:
            self.logger.error(f"Error selecting top documents: {e}")
            return documents[:top_k]  