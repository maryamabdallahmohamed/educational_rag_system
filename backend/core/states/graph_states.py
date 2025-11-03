from typing_extensions import TypedDict,List
from typing import Optional
from langchain.schema import Document
from pydantic import BaseModel,Field



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
    conversation_id: str
    qa_pairs: List[dict]
    question_count: int
    summary: str
    summary_title: str
    summary_key_points: List[str]
    feedback_loop: str
    generated_units: List[dict]  
    conversation_history: List[dict] 
    rag_context_used: bool 
    intent_classification: str 
    documents_available: bool  
    
    # Tutor Agent fields for personalized learning
    learner_id: Optional[str]  # Unique identifier for the learner
    learner_profile: Optional[dict]  # Loaded learner profile data (grade, preferences, performance)
    tutoring_session_id: Optional[str]  # Current active tutoring session ID
    session_state: Optional[dict]  # Current session context (topic, progress, difficulty)
    adaptation_requests: Optional[List[dict]]  # Requests to CPA for content adaptation
    personalized_content: Optional[List[dict]]  # Content adapted for this learner
    interaction_history: Optional[List[dict]]  # Conversation flow within current session
    learning_progress: Optional[dict]  # Current session progress metrics and analytics  

class cpa_processor_state(TypedDict, total=False):
    chunks: List
    similarity_scores: List[float]
    tool_used: str



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



