import json
from datetime import datetime
from backend.core.states.graph_states import RAGState
from backend.utils.helpers.language_detection import returnlang
from backend.loaders.document_loaders.text_splitter import document_chunk
from backend.utils.logger_config import get_logger
from backend.models.embedders.hf_embedder import HFEmbedder
from backend.db.connect_db import run_query
from backend.core.builders.document_builder import DocumentBuilder


class ChunkAndStoreNode:
    def __init__(self):
        self.embedder = HFEmbedder()
        self.db_runner = run_query
        self.logger = get_logger("chunk_and_store")
        self.builder = DocumentBuilder()

    def _insert_document(self, doc) -> int:
        """Insert a full document and return its ID."""
        embedding = self.embedder.embed_query(doc.page_content)
        metadata_json = json.dumps(doc.metadata or {})



    def _insert_chunk(self, chunk_doc, doc_id: int):
        """Insert a single chunk linked to a document ID."""
        embedding = self.embedder.embed_query(chunk_doc.page_content)
        metadata_json = json.dumps(chunk_doc.metadata or {})

        query = """
            INSERT INTO chunks (document_id, content, metadata, embedding)
            VALUES (%s, %s, %s::jsonb, %s::vector)
        """
        params = (doc_id, chunk_doc.page_content, metadata_json, embedding)
        self.db_runner(query, params, fetch=False)
    def process(self, state: RAGState) -> RAGState:
        documents = state.get("documents") or []
        if not documents:
            self.logger.info("No documents found in state. Skipping chunk and store.")
            return state

        inserted_doc_ids = []
        all_chunks = []

        for doc in documents:
            try:
                doc_id = self._insert_document(doc)
                inserted_doc_ids.append(doc_id)


                chunks = document_chunk(doc.page_content)
                for i, chunk in enumerate(chunks):
                    chunk_doc = (
                        self.builder
                        .set_content(chunk)
                        .set_metadata({
                            **doc.metadata,
                            "chunk_id": i,
                            "language": returnlang(chunk),
                            "parent_doc_id": doc_id,
                            "chunked_at": datetime.now().isoformat(),
                        })
                        .build()
                    )
                    all_chunks.append((chunk_doc, doc_id))
            except Exception as e:
                self.logger.error(f"Failed processing document: {e}", exc_info=True)

        # Insert chunks after building all
        for chunk_doc, doc_id in all_chunks:
            self._insert_chunk(chunk_doc, doc_id)

        # Update state with both IDs and chunks
        state["document_ids"] = inserted_doc_ids
        state["chunks"] = [chunk_doc for chunk_doc, _ in all_chunks]

        self.logger.info(
            "Inserted %d documents and %d chunks",
            len(inserted_doc_ids),
            len(all_chunks),
        )
        return state
