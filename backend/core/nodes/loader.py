from datetime import datetime
import json
from typing import List, Set, Optional
from langchain_core.documents import Document
from backend.core.ocr_module.ocr_orchestrator import upload_document
from backend.utils.helpers.language_detection import returnlang
from backend.utils.logger_config import get_logger
from backend.core.builders.document_builder import DocumentBuilder

logger = get_logger("pdf_loader")


class PDFLoader:
    """Handles PDF ingestion with OCR fallback and LangChain integration."""

    def __init__(self):
        self.ingested_documents: Set[str] = set()
        self.builder = DocumentBuilder()
        logger.debug("PDFLoader initialized")

    def _load_pdf(self, path: str) -> Optional[tuple[dict, str, dict]]:
        """Extract text and metadata from PDF (OCR if needed)."""
        result = upload_document(path)
        if not result:
            return None, None, None
        dict_text, metadata = result
        if isinstance(dict_text, dict): 
            text = "\n".join(dict_text.values())
        else:
            text = dict_text
            dict_text = {"1": text}
        metadata["source"] = path
        metadata["loaded_at"] = datetime.now().isoformat()
        return dict_text, text, metadata

    def load_document(self, path: str) -> Optional[Document]:
        """Load a single PDF document and return a LangChain Document."""
        if path in self.ingested_documents:
            logger.info("Document already ingested", extra={"path": path})
            return None

        if not path.lower().endswith(".pdf"):
            logger.warning("Unsupported file type", extra={"path": path})
            return None

        try:
            dict_text, text, metadata = self._load_pdf(path)
            if not dict_text: 
                logger.warning("No valid content extracted", extra={"path": path})
                return None

            content_for_doc = json.dumps(dict_text)
            language = returnlang(text)
            built_doc = (
                self.builder
                    .set_content(content_for_doc)
                    .set_metadata(metadata)      
                    .add_metadata("language", language) 
                    .build()
            )
            self.ingested_documents.add(path)
            logger.info("PDF ingested successfully", extra={
                "path": path, "language": language, "method": metadata.get("method")
            })
            return built_doc

        except Exception as e:
            logger.exception("Error loading PDF", extra={"path": path, "error": str(e)})
            return None

    def load_all(self, paths: List[str]) -> List[Document]:
        """Batch load PDFs and return LangChain Document list."""
        logger.info("Starting batch PDF load", extra={"num_files": len(paths)})
        documents = []
        for path in paths:
            doc = self.load_document(path)
            if doc:
                documents.append(doc)
        logger.info("Batch load complete", extra={"num_loaded": len(documents)})
        return documents
