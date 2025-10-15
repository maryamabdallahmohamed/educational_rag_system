from typing import Dict, Any
from backend.core.nodes.loader import LoadDocuments
from backend.core.nodes.chunk_store import ChunkAndStoreNode
from backend.core.nodes.router import router_node
from backend.core.nodes.qa_node import QANode
from backend.core.nodes.summarizer import SummarizationNode

# Initialize modules
document_loader = LoadDocuments()
chunk_store_node = ChunkAndStoreNode()
qa_node = QANode()
summarization_node = SummarizationNode()

# ---------------------- DOCUMENT HANDLING ----------------------
def load_document(file_path: str):
    """Load and return a document object."""
    return document_loader.load_document(file_path)

async def store_document(document):
    """Store document chunks in DB or vector store."""
    await chunk_store_node.process([document])
    return {"status": "success", "message": "Document stored successfully"}

# ---------------------- ROUTING & MODULE EXECUTION ----------------------
async def route_query(query: str) -> Dict[str, Any]:
    """Ask the router model to decide which node to use."""
    decision = await router_node(query)
    return decision

async def run_qa(query: str, document):
    """Run the QA module only."""
    return await qa_node.process(query=query, documents=[document])

async def run_summarization(query: str, document):
    """Run the Summarization module only."""
    return await summarization_node.process(query=query, documents=[document])
