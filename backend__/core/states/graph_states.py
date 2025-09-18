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
    qa_pairs: List[dict] 
    question_count: int  
    summary: str
    summary_title: str
    summary_key_points: List[str]
    feedback_loop: str
    generated_units: List[dict]  # For storing generated learning units
    conversation_history: List[dict]  # For storing conversation context
    rag_context_used: bool  # Flag to indicate if RAG context was used
    intent_classification: str  # Classified user intent

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



