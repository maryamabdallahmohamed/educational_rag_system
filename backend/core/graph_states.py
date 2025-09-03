from typing_extensions import TypedDict
from typing import List
from langchain.schema import Document


# Define state
class RAGState(TypedDict):
    query: str
    documents: tuple[Document]
    chunks: List[Document]
    results: List[Document]
    answer: str
    task_choice:str
    route=str
    file_paths: List[str]


