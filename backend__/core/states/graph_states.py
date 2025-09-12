from typing_extensions import TypedDict,List, Dict, Any
from typing import List, Optional
from langchain.schema import Document
from pydantic import BaseModel, Field



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

class QAPair(BaseModel):
    question: str = Field(description="A question about the content")
    answer: str = Field(description="The answer to the question")
    difficulty: str = Field(description="easy, medium, or hard")

class LearningUnit(BaseModel):
    title: str = Field(description="Clear, concise title for the learning unit")
    subtopics: List[str] = Field(description="List of subtopics covered in this unit")
    detailed_explanation: str = Field(description="Comprehensive explanation of the topic")
    key_points: List[str] = Field(description="Important concepts and facts")
    difficulty_level: str = Field(description="easy, medium, or hard")
    learning_objectives: List[str] = Field(description="What students should learn")
    keywords: List[str] = Field(description="Important terms and concepts")


class UnitGenerationState(TypedDict):
    document_content: str
    metadata: Dict[str, Any]
    adaptation_instruction: Optional[str]  
    generated_units: List[Dict[str, Any]]
    processing_status: str
    error_message: str
