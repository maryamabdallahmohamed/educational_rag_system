from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Set, Optional
from langchain.schema import Document
from backend.loaders.document_loaders.json_loader import JSONPreprocessor
from backend.utils.helpers.language_detection import returnlang
from backend.utils.logger_config import get_logger
from backend.core.builders.document_builder import DocumentBuilder

logger = get_logger("loader")
@dataclass
class RAGState:
    file_paths: List[str] = field(default_factory=list)
    documents: List[Document] = field(default_factory=list)
    ingested_sources: Set[str] = field(default_factory=set)



class LoadDocuments:
    def __init__(self):
        self.ingested_documents: Set[str] = set()
        self.processor = JSONPreprocessor()
        self.builder = DocumentBuilder()
        logger.debug("LoadDocuments initialized", extra={
            "processor": type(self.processor).__name__,
            "builder": type(self.builder).__name__
        })
    def load_document(self, path: str) -> Optional[Document]:
        """Load a single document if not already ingested.

        Returns the built Document on success, or None on failure / if skipped.
        """
        logger.debug("load_document called", extra={"path": path})
        if path in self.ingested_documents:
            logger.info("Document already ingested", extra={"path": path})
            return

        try:
            content = self.processor.load_and_preprocess_data(path)
            if not content or not isinstance(content, str) or not content.strip():
                logger.warning("No valid content", extra={"path": path})
                return None


            content_len = len(content)
            logger.debug("Content loaded",
                         extra={"path": path, "content_len": content_len, "snippet": content[:200]})

            language = returnlang(content)
            logger.debug("Language detected", extra={"path": path, "language": language})

            built_doc = (
                self.builder.set_content(content)
                .add_metadata("source", path)
                .add_metadata("loaded_at", datetime.now().isoformat())
                .add_metadata("language", language)
                .build()
            )

            # mark as ingested and log summary info
            self.ingested_documents.add(path)
            logger.info("Document ingested", extra={"path": path, "content_len": content_len, "language": language})
            logger.debug("Built document metadata", extra={"path": path, "metadata_keys": list(built_doc.metadata.keys()) if hasattr(built_doc, 'metadata') else None})
            return built_doc

        except Exception as e:
            logger.exception("Error loading document", extra={"path": path, "error": str(e)})
            return None



