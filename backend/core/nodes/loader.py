from datetime import datetime
from langgraph.types import RunnableConfig
from backend.core.states.graph_states import RAGState
from backend.loaders.document_loaders.json_loader import JSONPreprocessor
from backend.utils.helpers.language_detection import returnlang
from langchain.schema import Document
from backend.utils.logger_config import get_logger
from backend.core.builders.document_builder import DocumentBuilder

logger = get_logger("loader")

class LoadDocuments:
    def __init__(self):
        self.ingested_documents = set()
        self.processor = JSONPreprocessor()
        self.builder= DocumentBuilder()

    def load_document(self, path: str, state: RAGState) -> RAGState:
        """Load a single document if not already ingested."""
        state.setdefault("documents", [])
        state.setdefault("ingested_sources", [])

        if path in self.ingested_documents or path in state["ingested_sources"]:
            logger.info(f"Document already ingested: {path}")
            return state

        try:
            content = self.processor.load_and_preprocess_data(path)

            if not content or not isinstance(content, str) or not content.strip():
                logger.warning(f"No valid content from {path}")
                return state

            
            built_doc = (
                self.builder.set_content(content)
                .add_metadata("source", path)
                .add_metadata("loaded_at", datetime.now().isoformat())
                .add_metadata("language", returnlang(content))
                .build()
            )

            self.ingested_documents.add(path)
            state["documents"].append(built_doc)
            state["ingested_sources"].append(path)

            logger.info(f"Document ingested: {path}")
            return state

        except Exception as e:
            logger.error(f"Error loading {path}: {e}", exc_info=True)
            return state
    def load_from_state(self, state: RAGState) -> RAGState:
        """Load all new documents from file_paths in the state."""
        file_paths = state.get("file_paths", [])
        if not file_paths:
            logger.warning("No file paths found in state.")
            return state

        logger.info("Received %d file paths.", len(file_paths))
        for path in file_paths:
            state = self.load_document(path, state)

        return state



loader = LoadDocuments()

def load_node(state: RAGState, config: RunnableConfig = None) -> RAGState:
    logger.debug("Entered load_node with state keys: %s", list(state.keys()))
    state = loader.load_from_state(state)
    logger.debug("Exiting load_node with state keys: %s", list(state.keys()))
    return state
