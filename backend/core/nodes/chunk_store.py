import json
import asyncio
from langchain.schema import Document
from backend.core.states.graph_states import RAGState
from backend.utils.helpers.language_detection import returnlang
from backend.loaders.document_loaders.text_splitter import document_chunk
from backend.utils.logger_config import get_logger
from backend.models.embedders.hf_embedder import HFEmbedder


from backend.database.db import NeonDatabase
from backend.database.repositories.document_repo import DocumentRepository
from backend.database.repositories.chunk_repo import ChunkRepository


class ChunkAndStoreNode:
    def __init__(self):
        self.embedder = HFEmbedder()
        self.logger = get_logger("chunk_and_store")

    async def _insert_document(self, session, doc: Document):
        doc_repo = DocumentRepository(session)

        # Save document
        doc_dto = await doc_repo.add(
            title=(doc.metadata or {}).get("title", "Untitled"),
            content=doc.page_content,
            doc_metadata=doc.metadata or {}
        )
        return doc_dto

    async def _insert_chunk(self, session,chunk_doc: Document, doc_id):
        chunk_repo = ChunkRepository(session)
        embedding = await self.embedder.embed_query(chunk_doc.page_content)

        chunk_dto = await chunk_repo.add(
            document_id=doc_id,
            content=chunk_doc.page_content,
            embedding=embedding,
        )
        return chunk_dto

    async def process(self, state: RAGState) -> RAGState:
        new_docs = state.get("documents") or []
        if not new_docs:
            return state

        inserted_doc_ids = []
        inserted_chunks = []

        async with NeonDatabase.get_session() as session:
            for doc in new_docs:
                # insert doc
                doc_dto = await self._insert_document(session, doc)
                inserted_doc_ids.append(doc_dto.id)
                language =returnlang(doc.page_content)
                # create chunks
                chunks = document_chunk(doc.page_content)
                for i, chunk in enumerate(chunks):
                    chunk_doc = Document(
                        page_content=chunk,
                        metadata={**(doc.metadata or {}), "chunk_id": i, "language":  language},

                    )
                    chunk_dto = await self._insert_chunk(session, chunk_doc, doc_dto.id)
                    inserted_chunks.append(chunk_dto)

        # update state
        state["document_ids"] = inserted_doc_ids
        state["chunks"] = inserted_chunks

        self.logger.info("Inserted %d documents and %d chunks", len(inserted_doc_ids), len(inserted_chunks))
        return state
