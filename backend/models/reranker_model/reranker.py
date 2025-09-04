from sentence_transformers import CrossEncoder
import logging as logger
from langchain.schema import Document
from backend.config import CACHE_DIR

class Reranker:
    def __init__(self, model_name=None):
        if model_name is None:
            model_name = 'BAAI/bge-reranker-v2-m3'
        self.reranker = CrossEncoder(model_name, cache_folder=str(CACHE_DIR))
        logger.info("✅ Reranker model loaded successfully")



    def rerank_chunks(self, query, chunks):
        """
        Rerank the retrieved chunks using BGE reranker.
        Returns a list of Document objects sorted by relevance score.
        """        
        logger.info(f"🔄 Reranking {len(chunks)} chunks...")
        

        pairs = [(query, chunk.page_content) for chunk in chunks]

        scores = self.reranker.predict(pairs)
        scored_chunks = sorted(zip(chunks, scores), key=lambda x: x[1], reverse=True)

        reranked_docs = []
        for i, (chunk, score) in enumerate(scored_chunks):
            reranked_docs.append(
                Document(
                    page_content=chunk.page_content,
                    metadata={
                        **(chunk.metadata or {}),
                        "rerank_score": float(score),
                        "rerank_position": i + 1,
                    }
                )
            )

        logger.info(f"✅ Chunks reranked - Best score: {reranked_docs[0].metadata['rerank_score']:.3f}")
        return reranked_docs
