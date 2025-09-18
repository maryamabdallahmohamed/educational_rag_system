import os
from datetime import datetime
from langgraph.types import RunnableConfig
from backend.core.states.graph_states import RAGState
from backend.loaders.document_loaders.json_loader import JSONPreprocessor
from backend.utils.helpers.language_detection import returnlang
from langchain.schema import Document

from backend.utils.logger_config import get_logger

# Initialize module-level logger
logger = get_logger("loader")

def load_node(state: RAGState, config: RunnableConfig = None) -> RAGState:

    logger.debug("Entered load_node with state keys: %s", list(state.keys()))

    # Get file paths from state first, then from config
    file_paths = state.get("file_paths")
    logger.info("Received %d file paths from state.", len(file_paths) if file_paths else 0)

    if not file_paths:
        logger.warning("No file paths found in state.")
        return state

    # Filter out invalid paths and those already ingested
    valid_paths = []
    already = set(state.get("ingested_sources") or [])
    logger.info("Already ingested sources: %s", already)
    
    for path in file_paths:
        if path in already:
            logger.debug("Skipping already-ingested file: %s", path)
            continue
        else:
            valid_paths.append(path)
            logger.debug("Will process new file: %s", path)

    if not valid_paths:
        logger.info("No new valid paths to process. Returning state unchanged.")
        return state

    logger.info("Preparing to load documents from %s", valid_paths)

    # Load documents 
    preprocessor = JSONPreprocessor()
    loaded_docs = []
    successfully_loaded_paths = []
    
    for path in valid_paths:
        try:
            logger.debug("Loading file: %s", path)
            content = preprocessor.load_and_preprocess_data(path)
            if content and isinstance(content, str) and content.strip():
                doc = Document(
                    page_content=content,
                    metadata={
                        "source": path,
                        "loaded_at": datetime.now().isoformat(),
                        "language": returnlang(content)
                    },
                )
                loaded_docs.append(doc)
                successfully_loaded_paths.append(path)
                logger.info("Successfully loaded and processed file: %s", path)
            else:
                logger.warning("No textual content extracted from: %s", path)
        except Exception as e:
            logger.error("Failed to load %s: %s", path, str(e), exc_info=True)

    if loaded_docs:
        logger.info("Adding %d new documents to state.", len(loaded_docs))

        # Store just the new docs
        state["new_documents"] = loaded_docs  

        # Append to the total docs 
        existing_docs = state.get("documents", [])
        state["documents"] = existing_docs + loaded_docs
        
        # Update ingested sources to prevent reprocessing
        existing_sources = set(state.get("ingested_sources", []))
        existing_sources.update(successfully_loaded_paths)
        state["ingested_sources"] = list(existing_sources)
        
        logger.info("Total documents in state: %d", len(state["documents"]))
        logger.info("Total ingested sources: %d", len(state["ingested_sources"]))
        logger.info("Updated ingested_sources: %s", state["ingested_sources"])
    else:
        logger.warning("No documents loaded from valid paths: %s", valid_paths)

    logger.debug("Exiting load_node. State keys now: %s", list(state.keys()))
    return state
