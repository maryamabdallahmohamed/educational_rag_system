import tempfile
from pathlib import Path
from typing import Dict, Any
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import asyncio

# ===== RAG Imports =====
from backend.core.agents.content_processor_agent import ContentProcessorAgent
from backend.core.nodes.loader import PDFLoader
from backend.core.nodes.chunk_store import ChunkAndStoreNode
from backend.core.nodes.qa_node import QANode
from backend.core.nodes.summarizer import SummarizationNode
from backend.core.nodes.router import router_node
from backend.core.action_agent.handlers.dispatchers import dispatch_action, dispatch_query
from backend.core.action_agent.chains import FULL_ROUTER_CHAIN

# ===== STT Imports =====
from backend.core.stt_dev_seamless.app.seamless_model import SeamlessModel
from backend.core.stt_dev_seamless.app.utils import clean_arabic_text

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
document_loader = PDFLoader()
chunk_store_node = ChunkAndStoreNode()
qa_node = QANode()
summarization_node = SummarizationNode()
cpa_agent = ContentProcessorAgent()
uploaded_documents: Dict[str, Any] = {}

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
async def upload_file(file: UploadFile = File(...)):
    """Upload and store a document (PDF)."""
    file_path = f"/tmp/{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())

    document = document_loader.load_document(file_path)
    if document is None:
        raise HTTPException(status_code=400, detail="Failed to load document.")

    await chunk_store_node.process([document], metadata=document.metadata)
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
        raise HTTPException(status_code=400, detail="No document uploaded yet.")

    document = uploaded_documents["latest"]
    result = await qa_node.process(query=query, documents=[document])

    return {
        "query": query,
        "result": result,
        "service": "RAG - Q&A"
    }


@app.post("/api/summarize")
async def summarize_endpoint(query: str = Form(...)):
    """Summarize the latest uploaded document."""
    if "latest" not in uploaded_documents:
        raise HTTPException(status_code=400, detail="No document uploaded yet.")

    document = uploaded_documents["latest"]
    result = await summarization_node.process(query=query, documents=[document])

    return {
        "query": query,
        "result": result,
        "service": "RAG - Summarization"
    }


@app.post("/api/cpa_agent")
async def cpa_agent_endpoint(query: str = Form(...)):
    """Run the Content Processor Agent (CPA) on the latest uploaded document."""
    if "latest" not in uploaded_documents:
        raise HTTPException(status_code=400, detail="No document uploaded yet.")

    document = uploaded_documents["latest"]
    result = await cpa_agent.process(query=query, document=document)

    return {
        "query": query,
        "result": result,
        "service": "RAG - Content Processor Agent"
    }


@app.post("/api/action_route")
def route_message(query: str = Form(...)):
    """Route a message using the Action Agent's router chain."""
    result = FULL_ROUTER_CHAIN.invoke({
        "user_message": query,
        "dispatch_action": dispatch_action,
        "dispatch_query": dispatch_query,
    })
    return {
        "result": result,
        "service": "RAG - Action Agent"
    }


# ============================================================================
# SPEECH-TO-TEXT ENDPOINTS (SEAMLESSM4TV2)
# ============================================================================

@app.post("/api/transcribe")
async def transcribe(
    file: UploadFile = File(..., description="Audio file (MP3, WAV, FLAC, OGG, etc.)"),
    tgt_lang: str = Form("arb", description="Target language code (default: Egyptian Arabic)"),
    clean: bool = Form(False, description="Apply Arabic text cleaning"),
    max_duration_sec: float = Form(30.0, description="Max audio duration in seconds"),
) -> dict:
    global stt

    if stt is None:
        raise HTTPException(status_code=500, detail="STT model not initialized")

    try:
        # 1. Validate file format
        file_ext = Path(file.filename).suffix.lower() if file.filename else ""
        
        if not file_ext:
            raise HTTPException(
                status_code=400,
                detail=f"File has no extension. Supported: {', '.join(SUPPORTED_AUDIO_FORMATS)}"
            )
        
        if file_ext not in SUPPORTED_AUDIO_FORMATS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported format: {file_ext}. Supported: {', '.join(SUPPORTED_AUDIO_FORMATS)}"
            )

        print(f"\n[transcribe] ✓ File format validated: {file_ext}")

        # 2. Save uploaded file to temp
        suffix = file_ext if file_ext else ".mp3"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = tmp.name

        print(f"[transcribe] Processing: {file.filename} ({len(contents) / 1024 / 1024:.1f}MB)")

        # 3. Transcribe
        result = stt.transcribe(
            tmp_path,
            tgt_lang=tgt_lang,
            max_duration_sec=max_duration_sec,
        )

        text = result["text"]

        # 4. Optional Arabic cleaning
        if clean:
            print("[transcribe] Applying Arabic text cleaning...")
            text = clean_arabic_text(text)

        print(f"[transcribe] ✓ Transcription complete\n")

        # 5. Clean up
        Path(tmp_path).unlink(missing_ok=True)

        return {
            "status": "success",
            "text": text,
            "language": tgt_lang,
            "duration_sec": result["duration_sec"],
            "file": file.filename,
            "file_format": file_ext,
            "cleaned": clean,
            "service": "STT - SeamlessM4Tv2 (Egyptian Arabic)"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"[transcribe] ERROR: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {e}")


# ============================================================================
# COMBINED WORKFLOW: TRANSCRIBE + PROCESS + QA
# ============================================================================

@app.post("/api/transcribe_and_process")
async def transcribe_and_process(
    audio_file: UploadFile = File(..., description="Audio file for transcription"),
    document_file: UploadFile | None = File(None, description="Optional: Document for Q&A"),
    tgt_lang: str = Form("arb", description="Language for transcription"),
    query: str = Form("", description="Optional: Query for Q&A on document"),
    clean: bool = Form(True, description="Clean transcribed text"),
) -> dict:
    """
    Advanced workflow:
    1. Transcribe audio file
    2. If document provided: upload and process
    3. If query provided: answer questions using both transcript and document
    
    This demonstrates integration of STT + RAG systems.
    """
    
    # Step 1: Transcribe audio
    audio_result = await transcribe(
        file=audio_file,
        tgt_lang=tgt_lang,
        clean=clean,
    )
    
    transcript = audio_result["text"]
    
    # Step 2: Process document if provided
    if document_file:
        await upload_file(document_file)
    
    # Step 3: Q&A with context
    qa_result = None
    if query and "latest" in uploaded_documents:
        qa_result = await qa_endpoint(query)
    
    return {
        "status": "success",
        "workflow": "transcribe_and_process",
        "transcription": {
            "text": transcript,
            "language": tgt_lang,
            "duration_sec": audio_result["duration_sec"],
            "file": audio_result["file"],
            "cleaned": clean,
        },
        "qa_result": qa_result,
        "service": "Integrated STT + RAG"
    }


# ============================================================================
# INTERACTIVE ASSISTANT
# ============================================================================

@app.post("/api/assistant")
async def assistant(
    message: str = Form(..., description="User message or query"),
    audio_file: UploadFile | None = File(None, description="Optional audio file"),
) -> dict:
    """
    Smart assistant that:
    - Processes user message or transcribed audio
    - Routes to appropriate service (Q&A, summarization, routing)
    - Returns structured response
    """
    
    # If audio provided, transcribe it first
    if audio_file:
        result = await transcribe(file=audio_file)
        message = result["text"]
    
    # Route the message to appropriate service
    routing = await route_query(message)
    route = routing["decision"]
    
    response = {
        "message": message,
        "route": route,
        "service": "Integrated Assistant"
    }
    
    # Execute based on route
    if route == "qa":
        if "latest" in uploaded_documents:
            qa_result = await qa_endpoint(message)
            response["result"] = qa_result["result"]
        else:
            response["result"] = "No document uploaded. Please upload a document first."
    
    elif route == "summarize":
        if "latest" in uploaded_documents:
            sum_result = await summarize_endpoint(message)
            response["result"] = sum_result["result"]
        else:
            response["result"] = "No document uploaded. Please upload a document first."
    
    else:
        response["result"] = "Message routed to action agent."
    
    return response


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