from sentence_transformers import CrossEncoder
import logging as logger
from typing import List
from backend.config import CACHE_DIR
from backend.core.builders.document_builder import DocumentBuilder
from langchain.schema import Document

class Reranker:
    def __init__(self, model_name: str = None):
        if model_name is None:
            model_name = "BAAI/bge-reranker-v2-m3"
        self.reranker = CrossEncoder(model_name, cache_folder=str(CACHE_DIR))
        logger.info("✅ Reranker model loaded successfully")

    def rerank_chunks(self, query: str, chunks: List[Document]) -> List[Document]:
        """
        Rerank the retrieved chunks using BGE reranker.
        Returns a list of Document objects sorted by relevance score.
        """
        if not chunks:
            return []

        logger.info(f"🔄 Reranking {len(chunks)} chunks...")

        # Prepare query-chunk pairs
        pairs = [(query, chunk.page_content) for chunk in chunks]

        # Get scores from the reranker
        scores = self.reranker.predict(pairs)

        # Sort chunks by descending relevance
        scored_chunks = sorted(zip(chunks, scores), key=lambda x: x[1], reverse=True)

        reranked_docs = []
        for i, (chunk, score) in enumerate(scored_chunks):
            # Build new Document using DocumentBuilder
            doc = (
                DocumentBuilder()
                .set_content(chunk.page_content)
                .set_metadata(chunk.metadata or {})
                .add_metadata("rerank_score", float(score))
                .add_metadata("rerank_position", i + 1)
                .build()
            )
            reranked_docs.append(doc)

        top_scores = [score for _, score in scored_chunks[:5]]
        logger.info(f"Top reranked scores: {top_scores}")

        return reranked_docs
