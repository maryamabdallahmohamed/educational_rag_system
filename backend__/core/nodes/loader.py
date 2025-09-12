import os
from datetime import datetime
from langgraph.types import RunnableConfig
from backend__.core.states.graph_states import RAGState
from backend__.loaders.document_loaders.json_loader import JSONPreprocessor
from backend__.utils.helpers.language_detection import returnlang
from langchain.schema import Document

def load_node(state: RAGState, config: RunnableConfig = None) -> RAGState:
    """Load only not-yet-ingested documents from file paths in state/config.

    Stores freshly loaded docs in state["new_documents"] so downstream nodes can
    add only new chunks/DB rows. Persistent totals remain in state["documents"].
    """

    # Get file paths from state first, then from config
    file_paths = state.get("file_paths")

    if not file_paths and config:
        configurable = config.get("configurable", {})
        file_paths = configurable.get("file_paths")

    if file_paths is None:
        file_paths = []
    elif isinstance(file_paths, str):
        file_paths = [file_paths]
    elif isinstance(file_paths, list):
        # Flatten in case someone passed [["path.json"]] instead of ["path.json"]
        flat_paths = []
        for p in file_paths:
            if isinstance(p, list):
                flat_paths.extend(p)
            else:
                flat_paths.append(p)
        file_paths = flat_paths
    else:
        print(f"⚠️ Unexpected file_paths type: {type(file_paths)}")
        file_paths = []

    # 3️⃣ Filter out invalid paths and those already ingested
    valid_paths = []
    already = set(state.get("ingested_sources") or [])
    for path in file_paths:
        if not isinstance(path, str):
            print(f"⚠️ Skipping non-string path: {path}")
            continue
        if not os.path.exists(path):
            print(f"⚠️ Path does not exist: {path}")
        elif os.path.isdir(path):
            print(f"⚠️ Skipping directory: {path}")
        elif path in already:
            continue
        else:
            valid_paths.append(path)

    if not valid_paths:
        # Nothing new to load
        return state

    print(f"Loading documents from: {valid_paths}") 

    # Load documents 
    preprocessor = JSONPreprocessor()
    loaded_docs = []
    for path in valid_paths:
        try:
            content = preprocessor.load_and_preprocess_data(path)
            if content and isinstance(content, str) and content.strip():
                loaded_docs.append(
                    Document(
                        page_content=content,
                        metadata={
                            "source": path,
                            "loaded_at": datetime.now().isoformat(),
                            "language": returnlang(content)
                        },
                    )
                )
            else:
                print(f"⚠️ No textual content extracted from: {path}")
        except Exception as e:
            print(f"❌ Failed to load {path}: {e}")

    if loaded_docs:
        state["new_documents"] = (state.get("new_documents") or []) + loaded_docs
    return state