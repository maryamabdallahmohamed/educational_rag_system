from typing_extensions import TypedDict,List, Dict, Any
from typing import List, Optional
from langchain.schema import Document
from pydantic import BaseModel, Field



# Define state with qa_pairs field
class RAGState(TypedDict, total=False):
    query: str
    documents: List[Document]
    chunks: List[Document]
    results: List[Document]
    answer: str
    route: str
    file_paths: List[str]
    ingested: bool
    ingested_sources: List[str]
    new_documents: List[Document]
    new_chunks: List[Document]
    conversation_id: str
    qa_pairs: List[dict]  # Added this field for Q&A pairs
    question_count: int   # Added this field for question count
    summary: str
    summary_title:str
    summary_key_points=List[str] 
    question: str = Field(description="A question about the content")
    answer: str = Field(description="The answer to the question")
    generated_difficulty: str = Field(description="easy, medium, or hard")

class QAPair(BaseModel):
    question: str = Field(description="A question about the content")
    answer: str = Field(description="The answer to the question")
    generated_difficulty: str = Field(description="easy, medium, or hard")

class QAResponse(BaseModel):
    qa_pairs: List[QAPair] = Field(description="List of Q&A pairs generated from the content")
    total_questions: int = Field(description="Total number of questions generated")


class RouterOutput(BaseModel):
    route: str = Field(description="The routing decision: qa, summarization, or content_processor_agent")
    confidence: float = Field(description="Confidence score between 0 and 1")
    reasoning: str = Field(description="Brief explanation for the routing decision")


class QAPair(BaseModel):
    question: str = Field(description="A question about the content")
    answer: str = Field(description="The answer to the question")
    generated_difficulty: str = Field(description="easy, medium, or hard")

class Summary(BaseModel):
    title: str = Field(description="Title or main topic of the summary")
    content: str = Field(description="The summarized content")
    key_points: List[str] = Field(description="Main points extracted from the content")
    language: str = Field(description="Language of the summary")

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

