from typing import List
from langchain_core.documents import Document
import logging


class RAGContextBuilder:
    """Handles context preparation from documents"""

    def __init__(self, max_docs: int = 3, max_content_length: int = 1000):
        self.max_docs = max_docs
        self.max_content_length = max_content_length
        self.logger = logging.getLogger(__name__)

    def build_context(self, documents: List[Document]) -> str:
        """Build context string from documents"""
        try:
            if not documents:
                return "No relevant documents found."

            # Take top documents (already sorted by similarity)
            top_docs = documents[:self.max_docs]

            # Prepare context parts
            context_parts = []
            for i, doc in enumerate(top_docs, 1):
                # Limit content length
                content = doc.page_content
                if len(content) > self.max_content_length:
                    content = content[:self.max_content_length] + "..."

                # Extract metadata
                source = doc.metadata.get("source", f"Document {i}")
                similarity_score = doc.metadata.get("similarity_score", 0.0)

                # Build context part
                context_part = f"Source: {source}"
                if similarity_score > 0:
                    context_part += f" (Similarity: {similarity_score:.3f})"
                context_part += f"\nContent: {content}"

                context_parts.append(context_part)

            context = "\n\n---\n\n".join(context_parts)
            self.logger.info(f"Built context from {len(top_docs)} documents")
            return context

        except Exception as e:
            self.logger.error(f"Error building context: {e}")
            # Fallback: simple concatenation
            return "\n\n".join([doc.page_content[:500] for doc in documents[:2]])

    def build_structured_context(self, documents: List[Document]) -> dict:
        """Build structured context with metadata"""
        try:
            if not documents:
                return {"context": "No relevant documents found.", "sources": []}

            top_docs = documents[:self.max_docs]

            sources = []
            context_parts = []

            for i, doc in enumerate(top_docs, 1):
                content = doc.page_content
                if len(content) > self.max_content_length:
                    content = content[:self.max_content_length] + "..."

                source_info = {
                    "id": doc.metadata.get("id", f"doc_{i}"),
                    "source": doc.metadata.get("source", f"Document {i}"),
                    "similarity_score": doc.metadata.get("similarity_score", 0.0)
                }
                sources.append(source_info)
                context_parts.append(content)

            return {
                "context": "\n\n".join(context_parts),
                "sources": sources,
                "total_documents": len(top_docs)
            }

        except Exception as e:
            self.logger.error(f"Error building structured context: {e}")
            return {"context": "Error building context", "sources": []}