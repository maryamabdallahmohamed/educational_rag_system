from typing import List
from langchain_core.documents import Document
from backend.models.embedders.hf_embedder import HFEmbedder
from backend.database.repositories.chunk_repo import ChunkRepository
from backend.database.db import NeonDatabase
from backend.core.builders.document_builder import DocumentBuilder
import logging


class RAGRetriever:
    """Handles document retrieval from the database using embeddings"""

    def __init__(self):
        self.embedder = HFEmbedder()
        self.logger = logging.getLogger(__name__)

    async def retrieve_documents(self, query: str, top_k: int = 10) -> List[Document]:
        """Retrieve similar documents for a given query"""
        try:
            query_embedding = await self.embedder.embed_query(query)

            async with NeonDatabase.get_session() as session:
                chunk_repo = ChunkRepository(session=session)
                chunks = await chunk_repo.get_similar_chunks(query_embedding, top_k=top_k)

                # Convert chunks to Documents with similarity scores
                documents = [
                    DocumentBuilder()
                    .set_content(chunk.content)
                    .set_metadata({
                        "id": str(chunk.id),
                        "source": getattr(chunk, 'source', f"Chunk {chunk.id}"),
                        "similarity_score": getattr(chunk, 'similarity_score', 0.0),
                        "similarity_distance": getattr(chunk, 'similarity_distance', 999.0)
                    })
                    .build()
                    for chunk in chunks
                ]

                self.logger.info(f"Retrieved {len(documents)} documents for query")
                return documents

        except Exception as e:
            self.logger.error(f"Error retrieving documents: {e}")
            return []