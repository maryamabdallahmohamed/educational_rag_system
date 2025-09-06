from typing_extensions import TypedDict
from typing import List, Optional
from langchain.schema import Document


# Define state
class RAGState(TypedDict, total=False):
    query: str
    documents: List[Document]
    chunks: List[Document]
    results: List[Document]
    answer: str
    task_choice: str
    route: str
    file_paths: List[str]
    ingested: bool
    ingested_sources: List[str]
    new_documents: List[Document]
    new_chunks: List[Document]
    conversation_id: str



