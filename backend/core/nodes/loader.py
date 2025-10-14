from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Set, Optional
from langchain.schema import Document
from backend.loaders.document_loaders.json_loader import JSONPreprocessor
from backend.utils.helpers.language_detection import returnlang
from backend.utils.logger_config import get_logger
from backend.core.builders.document_builder import DocumentBuilder

logger = get_logger("loader")


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
        """Load and preprocess a single document. Returns a built Document."""
        if path in self.ingested_documents:
            logger.info("Document already ingested", extra={"path": path})
            return None

        try:
            content = self.processor.load_and_preprocess_data(path)
            if not content or not isinstance(content, str) or not content.strip():
                logger.warning("No valid content", extra={"path": path})
                return None

            language = returnlang(content)
            built_doc = (
                self.builder.set_content(content)
                .add_metadata("source", path)
                .add_metadata("loaded_at", datetime.now().isoformat())
                .add_metadata("language", language)
                .build()
            )

            self.ingested_documents.add(path)
            logger.info("Document ingested", extra={"path": path, "language": language})
            return built_doc

        except Exception as e:
            logger.exception("Error loading document", extra={"path": path, "error": str(e)})
            return None

    def load_all(self, paths: List[str]) -> List[Document]:
        """Load multiple documents and return them as a list."""
        logger.info("Starting batch load", extra={"num_files": len(paths)})
        documents = []
        for path in paths:
            doc = self.load_document(path)
            if doc:
                documents.append(doc)
        logger.info("Batch load complete", extra={"num_loaded": len(documents)})
        return documents
