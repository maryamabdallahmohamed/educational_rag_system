from fastapi import FastAPI, UploadFile, File, Form
from typing import Dict, Any
import asyncio
from backend.core.agents.content_processor_agent import ContentProcessorAgent
from backend.core.nodes.loader import PDFLoader
from backend.core.nodes.chunk_store import ChunkAndStoreNode
from backend.core.nodes.qa_node import QANode
from backend.core.nodes.summarizer import SummarizationNode
from backend.core.nodes.router import router_node
from backend.core.action_agent.handlers.dispatchers import dispatch_action, dispatch_query
from backend.core.action_agent.chains import FULL_ROUTER_CHAIN
from backend.api.routers import sessions

app = FastAPI(title="Educational RAG API", version="1.0")

app.include_router(sessions.router)

# Node initialization
document_loader = PDFLoader()
chunk_store_node = ChunkAndStoreNode()
qa_node = QANode()
summarization_node = SummarizationNode()
cpa_agent = ContentProcessorAgent()
# In-memory store
uploaded_documents: Dict[str, Any] = {}

# ---------------------------------------------------------------------------- #
# Upload Document Endpoint
# ---------------------------------------------------------------------------- #
@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...), session_id: str = Form(None)):
    """Upload and store a document."""
    file_path = f"/tmp/{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # Build a LangChain Document instead of raw text
    document = document_loader.load_document(file_path)
    if document is None:
        return {"error": "Failed to load document."}

    await chunk_store_node.process([document], metadata=document.metadata, session_id=session_id)

    # Save document in memory for later use
    uploaded_documents["latest"] = document
    uploaded_documents["latest_metadata"] = document.metadata

    return {"status": "uploaded", "filename": file.filename}

# ---------------------------------------------------------------------------- #
# Router Endpoint
# ---------------------------------------------------------------------------- #
@app.post("/api/router")
async def route_query(query: str = Form(...)):
    """Route a query to QA or Summarization."""
    routing_result = await router_node(query)
    route = routing_result.lower()
    return {"decision": route}


# ---------------------------------------------------------------------------- #
# QA Endpoint
# ---------------------------------------------------------------------------- #
@app.post("/api/qa")
async def qa_endpoint(query: str = Form(...)):
    """Answer questions using the latest uploaded document."""
    if "latest" not in uploaded_documents:
        return {"error": "No document uploaded yet."}

    document = uploaded_documents["latest"]
    result = await qa_node.process(query=query, documents=[document])
    return {"query": query, "result": result}


# ---------------------------------------------------------------------------- #
# Summarization Endpoint
# ---------------------------------------------------------------------------- #
@app.post("/api/summarize")
async def summarize_endpoint(query: str = Form(...)):
    """Summarize the latest uploaded document."""
    if "latest" not in uploaded_documents:
        return {"error": "No document uploaded yet."}

    document = uploaded_documents["latest"]
    result = await summarization_node.process(query=query, documents=[document])
    return {"query": query, "result": result}

# ---------------------------------------------------------------------------- #
# CPA Agent Endpoint
# ---------------------------------------------------------------------------- #


@app.post("/api/cpa_agent")
async def cpa_agent_endpoint(query: str = Form(...)):
    """Run the Content Processor Agent (CPA) on the latest uploaded document."""
    if "latest" not in uploaded_documents:
        return {"error": "No document uploaded yet."}

    document = uploaded_documents["latest"]
    result = await cpa_agent.process(query=query, document=document)
    return {"query": query, "result": result}

# ---------------------------------------------------------------------------- #
# Action Agent Route Endpoint
# ---------------------------------------------------------------------------- #
@app.post("/api/action_route")
def route_message(query: str = Form(...), session_id: str = Form(None)):
    """
    Route a message using the Action Agent's router chain.
    """
    result = FULL_ROUTER_CHAIN.invoke(
        {
            "user_message": query,
            "session_id": session_id,
            "dispatch_action": dispatch_action,
            "dispatch_query": dispatch_query,
        }
    )
    return result



# ---------------------------------------------------------------------------- #
# Health Check
# ---------------------------------------------------------------------------- #
@app.get("/health")
async def health():
    return {"status": "ok"}
