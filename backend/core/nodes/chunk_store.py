from langchain.schema import Document
from backend.loaders.document_loaders.text_splitter import document_chunk
from backend.utils.logger_config import get_logger
from backend.database.db import NeonDatabase
from backend.database.repositories.document_repo import DocumentRepository
from backend.database.repositories.chunk_repo import ChunkRepository
from backend.core.builders.document_builder import DocumentBuilder
from backend.models.embedders.hf_embedder import HFEmbedder
from backend.utils.helpers.language_detection import returnlang
from typing import List, Set

logger = get_logger("chunk_and_store")


class ChunkAndStoreNode:
    def __init__(self):
        self.embedder = HFEmbedder()
        self.builder = DocumentBuilder()
        self.processed_chunks = set()
        logger.debug("ChunkAndStoreNode initialized", extra={
            "embedder": type(self.embedder).__name__,
            "builder": type(self.builder).__name__
        })

    async def _insert_document(self, session, doc: Document):
        doc_repo = DocumentRepository(session)
        doc_dto = await doc_repo.add(
            title=(doc.metadata or {}).get("title", "Untitled"),
            content=doc.page_content,
            doc_metadata=doc.metadata or {},
        )
        logger.debug("Inserted document DTO", extra={"doc_id": getattr(doc_dto, 'id', None)})
        return doc_dto

    async def _insert_chunk(self, session, chunk_doc: Document, doc_id: int):
        chunk_repo = ChunkRepository(session)
        embedding = await self.embedder.embed_query(chunk_doc.page_content)
        chunk_dto = await chunk_repo.add(
            document_id=doc_id,
            content=chunk_doc.page_content,
            embedding=embedding,
        )
        logger.debug("Inserted chunk DTO", extra={"chunk_id": getattr(chunk_dto, 'id', None), "document_id": doc_id})
        return chunk_dto

    async def process(self, documents: List[Document]) -> List[Document]:
        """Chunks, embeds, and stores documents in DB."""
        if not documents:
            logger.warning("No new documents found in state.")
            return documents
        inserted_doc_ids = []
        inserted_chunks = []

        logger.info("Starting process of documents", extra={"num_documents": len(documents)})

        try:
            async with NeonDatabase.get_session() as session:
                for doc_idx, doc in enumerate(documents):
                    logger.debug("Processing document", extra={"index": doc_idx, "source": (doc.metadata or {}).get('source')})

                    # 1️⃣ Insert document
                    doc_dto = await self._insert_document(session, doc)
                    inserted_doc_ids.append(getattr(doc_dto, 'id', None))

                    # 2️⃣ Chunking
                    language = returnlang(doc.page_content)
                    chunks = document_chunk(doc.page_content)
                    logger.debug("Document chunked", extra={"num_chunks": len(chunks), "language": language})

                    for i, chunk in enumerate(chunks):
                        chunk_key = hash(chunk)
                        if chunk_key in self.processed_chunks:
                            logger.debug("Skipping already processed chunk", extra={"doc_index": doc_idx, "chunk_index": i})
                            continue
                        self.processed_chunks.add(chunk_key)

                        # 3️⃣ Build chunk doc
                        chunk_doc = (
                            self.builder
                            .set_content(chunk)
                            .set_metadata({
                                **(doc.metadata or {}),
                                "chunk_id": i,
                                "language": language,
                                "parent_id": doc_dto.id,
                            })
                            .build()
                        )
                        logger.debug("Built chunk document", extra={"parent_doc_id": doc_dto.id, "chunk_index": i})

                        # 4️⃣ Insert chunk
                        chunk_dto = await self._insert_chunk(session, chunk_doc, doc_dto.id)
                        inserted_chunks.append(getattr(chunk_dto, 'id', None))
                await session.commit()

            logger.info("Finished processing documents", extra={"inserted_documents": len(inserted_doc_ids), "inserted_chunks": len(inserted_chunks)})
        except Exception as e:
            logger.exception("Error processing documents", extra={"error": str(e)})

        return documents
