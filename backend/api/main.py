import tempfile
from pathlib import Path
from typing import Dict, Any
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
import asyncio
import os

# ===== RAG Imports =====
from backend.core.agents.content_processor_agent import ContentProcessorAgent
from backend.core.agents.tutor_agent import TutorAgent
from backend.core.nodes.loader import PDFLoader
from backend.core.nodes.chunk_store import ChunkAndStoreNode
from backend.core.nodes.qa_node import QANode
from backend.core.nodes.summarizer import SummarizationNode
from backend.core.nodes.router import router_node
from backend.core.action_agent.handlers.dispatchers import dispatch_action, init_dispatchers
from backend.core.action_agent.chains import FULL_ROUTER_CHAIN, full_router_async

# ===== STT Imports =====
from backend.core.stt_dev_seamless.app.seamless_model import SeamlessModel
from backend.core.stt_dev_seamless.app.utils import clean_arabic_text
from backend.core.stt_dev_seamless.app.seamless_model import SeamlessModel

# ===== FastAPI Setup =====
app = FastAPI(
    title="Integrated Educational API",
    version="2.0",
    description="Document Processing + Speech-to-Text (Egyptian Arabic)"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== RAG Components =====
from backend.api.routers import sessions

app = FastAPI(title="Educational RAG API", version="1.0")

app.include_router(sessions.router)

# Node initialization
document_loader = PDFLoader()
chunk_store_node = ChunkAndStoreNode()
qa_node = QANode()
summarization_node = SummarizationNode()
cpa_agent = ContentProcessorAgent()
tutor_agent = TutorAgent()
seamless_model = SeamlessModel()
# In-memory store
uploaded_documents: Dict[str, Any] = {}
current_query: Dict[str, Any] = {}

# ===== STT Components =====
stt: SeamlessModel | None = None
SUPPORTED_AUDIO_FORMATS = {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac", ".opus"}


# ============================================================================
# STARTUP / SHUTDOWN
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize SeamlessM4Tv2 model on startup."""
    global stt
    
    # Initialize dispatchers with shared instances
    init_dispatchers(
        qa_node=qa_node,
        summarization_node=summarization_node,
        cpa_agent=cpa_agent,
        tutor_agent=tutor_agent,
        uploaded_documents=uploaded_documents,
        current_query=current_query
    )
    print("[startup] ✓ Dispatchers initialized")
    
    print("\n[startup] Initializing SeamlessM4Tv2 model...")
    stt = SeamlessModel(
        model_name="facebook/seamless-m4t-v2-large",
        device=-1,  # CPU by default
    )
    print("[startup] ✓ Ready to accept requests\n")


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health")
async def health() -> dict:
    """
    Health check endpoint for both RAG and STT systems.
    
    Returns status of document processing and speech recognition.
    """
    return {
        "status": "ok",
        "services": {
            "rag": "operational",
            "stt": "operational" if stt and stt.loaded else "initializing",
        },
        "stt": {
            "model_loaded": stt is not None and stt.loaded if stt else False,
            "model_name": stt.model_name if stt else None,
            "supported_audio_formats": list(SUPPORTED_AUDIO_FORMATS),
        }
    }


# ============================================================================
# DOCUMENT PROCESSING ENDPOINTS
# ============================================================================

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...), session_id: str = Form(None)):
    """Upload and store a document."""
    file_path = f"/tmp/{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())

    document = document_loader.load_document(file_path)
    if document is None:
        raise HTTPException(status_code=400, detail="Failed to load document.")

    await chunk_store_node.process([document], metadata=document.metadata, session_id=session_id)

    # Save document in memory for later use
    uploaded_documents["latest"] = document
    uploaded_documents["latest_metadata"] = document.metadata

    return {
        "status": "uploaded",
        "filename": file.filename,
        "service": "RAG - Document Processing"
    }


@app.post("/api/router")
async def route_query(query: str = Form(...)):
    """Route a query to QA or Summarization."""
    routing_result = await router_node(query)
    route = routing_result.lower()
    return {
        "decision": route,
        "service": "RAG - Query Router"
    }


@app.post("/api/qa")
async def qa_endpoint(query: str = Form(...)):
    """Answer questions using the latest uploaded document."""
    if "latest" not in uploaded_documents:
        return {"error": "No document uploaded yet."}
    current_query["latest"] = query
    document = uploaded_documents["latest"]
    result = await qa_node.process(query=query, documents=[document])

    return {
        "result": result
    }


@app.post("/api/summarize")
async def summarize_endpoint(query: str = Form(...), session_id: str = Form(None)):
    """Summarize the latest uploaded document."""
    if "latest" not in uploaded_documents:
        return {"error": "No document uploaded yet."}
    current_query["latest"] = query
    document = uploaded_documents["latest"]
    result = await summarization_node.process(query=query, documents=[document],session_id=session_id)
    return {
        "result": result,
    }



# ---------------------------------------------------------------------------- #
# Tutor  Agent Endpoint
# ---------------------------------------------------------------------------- #
@app.post("/api/agents")
async def tutor_agent_endpoint(query: str = Form(...)):
    """Run the Tutor Agent on the latest uploaded document."""
    if "latest" not in uploaded_documents:
        return {"error": "No document uploaded yet."}
    previous_query = current_query.get("latest", None)
    current_query["latest"] = query
    document = uploaded_documents["latest"]
    cpa_result = await cpa_agent.process(query=query, document=document)
    tutor_result = await tutor_agent.process(
        query=query,
        cpa_result=cpa_result,
        current_query=current_query,
        previous_query=previous_query
    )
    return {
        "query": query,
        "result": tutor_result,
        "service": "RAG - Content Processor Agent"
    }


@app.post("/api/action_route")
async def route_message(query: str = Form(...), session_id: str = Form(None)):
    """
    Smart routing endpoint:
    1. Classifies intent (query vs action)
    2. Routes to appropriate handler
    3. Executes and returns result
    """
    result = await full_router_async(
        {
            "user_message": query,
            "session_id": session_id,
            "dispatch_action": dispatch_action,
        }
    )
    return result
# ---------------------------------------------------------------------------- #
# LearnableUnitsGenerator Endpoint
# ---------------------------------------------------------------------------- #
@app.post("/api/learnable_units_generator")
async def learnable_units_generator(session_id: str = Form(None)):
    """
    Generate learnable units using the LearnableUnitsGenerator.
    """
    document = uploaded_documents["latest"]
    summary_result = await summarization_node.process(query=' ', documents=[document])
    
    # Extract text properly from the summary result dict
    if isinstance(summary_result, dict):
        # Build a proper query from the summary components
        title = summary_result.get('title', '')
        content = summary_result.get('content', '')
        key_points = summary_result.get('key_points', [])
        
        # Combine into a meaningful query string
        if key_points and isinstance(key_points, list):
            key_points_text = "\n".join(f"- {point}" for point in key_points)
        else:
            key_points_text = ""
        
        summary_text = f"{title}\n\n{content}\n\nKey Points:\n{key_points_text}"
    else:
        summary_text = str(summary_result) if summary_result else "Generate learning units from the document"
    
    cpa_result = await cpa_agent.process(query=summary_text, document=document)
    

    tutor_query = "Present this in a learnable units format."
    tutor_result = await tutor_agent.process(
        query=tutor_query, 
        cpa_result=cpa_result, 
        current_query=current_query, 
        previous_query=None
    )
    print("Result:", tutor_result)
    return {'result': tutor_result}


# ============================================================================
# INTERACTIVE ASSISTANT
# ============================================================================

@app.post("/api/assistant")
async def assistant(
    session_id: str = Form(None),
    message: str | None = Form(None, description="Optional user message or query"),
    audio_file: UploadFile | None = File(None, description="Optional audio file")
) -> dict:
    """
    Smart assistant:
    - Processes user message or transcribed audio
    - Routes to appropriate service
    """

    # If audio provided, transcribe it
    if audio_file:
        suffix = Path(audio_file.filename or "audio.tmp").suffix

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await audio_file.read())
            tmp_path = tmp.name

        try:
            audio_result = await run_in_threadpool(
                seamless_model.transcribe,
                audio_path=tmp_path
            )
            message = audio_result.get("text", "")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


    # Route the message using async router
    result = await full_router_async(
        {
            "user_message": message,
            "session_id": session_id,
            "dispatch_action": dispatch_action,
        }
    )

    return {
        "message": message,
        "route": result.get("query_route") or result.get("action_route"),
        "result": result.get("dispatch_result"),
        "service": "Integrated Assistant"
    }



# ============================================================================
# ROOT ENDPOINT
# ============================================================================

@app.get("/")
async def root():
    """API information and available endpoints."""
    return {
        "title": "Integrated Educational API",
        "version": "2.0",
        "description": "Combines RAG + Speech-to-Text",
        "services": {
            "RAG": [
                "/api/upload - Upload PDF",
                "/api/qa - Answer questions",
                "/api/summarize - Summarize document",
                "/api/router - Route queries",
                "/api/cpa_agent - Content processor",
            ],
            "STT": [
                "/api/transcribe - Transcribe audio",
            ],
            "Integrated": [
                "/api/transcribe_and_process - Transcribe + process",
                "/api/assistant - Smart assistant",
            ]
        },
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)