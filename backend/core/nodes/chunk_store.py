from langchain_core.documents import Document
import json
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

    async def _insert_document(self, session, doc: Document, doc_dict, session_id=None):
        doc_repo = DocumentRepository(session)
        metadata = doc.metadata or {}

        doc_dto = await doc_repo.add(
            title=doc.metadata.get("file_name"),
            content=doc_dict,
            doc_metadata=metadata,
            session_id=session_id
        )
        logger.debug("Inserted document DTO", extra={"doc_id": getattr(doc_dto, 'id', None)})
        return doc_dto


    async def _insert_chunk(self, session, chunk_doc: Document, doc_id: int, from_page: str):
        chunk_repo = ChunkRepository(session)
        embedding = await self.embedder.embed_query(chunk_doc.page_content)
        
        chunk_dto = await chunk_repo.add(
            document_id=doc_id,
            content=chunk_doc.page_content,
            embedding=embedding,
            from_page=str(from_page) 
        )
        logger.debug("Inserted chunk DTO", extra={"chunk_id": getattr(chunk_dto, 'id', None), "document_id": doc_id})
        return chunk_dto

    async def process(self, documents: List[Document], metadata, session_id=None) -> List[Document]:
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
                    logger.debug("Processing document", extra={"index": doc_idx, "source": (metadata['file_name'])})

                    doc_dict = {}
                    try:
                        if isinstance(doc.page_content, str):
                            parsed = json.loads(doc.page_content)
                            if isinstance(parsed, dict):
                                doc_dict = parsed
                            else:
                                doc_dict = {"1": doc.page_content}
                        elif isinstance(doc.page_content, dict):
                             doc_dict = doc.page_content
                        else:
                             doc_dict = {"1": str(doc.page_content)}
                    except (json.JSONDecodeError, TypeError):
                        doc_dict = {"1": doc.page_content}

                    full_text_content = "\n".join(str(v) for v in doc_dict.values())

                    # 1️⃣ Insert document
                    doc_dto = await self._insert_document(session, doc, doc_dict, session_id=session_id)
                    inserted_doc_ids.append(getattr(doc_dto, 'id', None))

                    # 2️⃣ Chunking (Per Page)
                    language = returnlang(full_text_content)
                    
                    for page_num, page_text in doc_dict.items():
                        
                        # Chunk ONLY this page's text to preserve page mapping
                        chunks = document_chunk(str(page_text))
                        
                        logger.debug(f"Page {page_num} chunked", extra={"num_chunks": len(chunks)})

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
                                    **(metadata or {}),
                                    "chunk_id": i,
                                    "language": language,
                                    "parent_id": doc_dto.id,
                                    "from_page": page_num 
                                })
                                .build()
                            )

                            # 4️⃣ Insert chunk with page number
                            chunk_dto = await self._insert_chunk(
                                session, 
                                chunk_doc, 
                                doc_dto.id, 
                                from_page=page_num
                            )
                            inserted_chunks.append(getattr(chunk_dto, 'id', None))
                            
                await session.commit()

            logger.info("Finished processing documents", extra={"inserted_documents": len(inserted_doc_ids), "inserted_chunks": len(inserted_chunks)})
        except Exception as e:
            logger.exception("Error processing documents", extra={"error": str(e)})

        return documents