from langgraph.graph import StateGraph, START, END
from langgraph.types import RunnableConfig
from backend.core.states.graph_states import RAGState
from backend.utils.logger_config import get_logger
from backend.core.nodes.chunk_store import ChunkAndStoreNode
from backend.core.nodes.loader import load_node
from backend.core.nodes.router import router_node
from backend.core.nodes.qa_node import qa_node_singleton
from backend.core.nodes.summarizer import summarization_node_singleton
from backend.core.agents.content_processor_agent import ContentProcessorAgent
logger = get_logger("main_graph")

# Class instances
chunk_store_instance = ChunkAndStoreNode()
content_processor_instance = ContentProcessorAgent()

def chunk_store_node(state: RAGState, config: RunnableConfig = None) -> RAGState:
    """Wrapper for ChunkAndStoreNode.process()"""
    return chunk_store_instance.process(state)

async def content_processor_agent_node(state: RAGState, config: RunnableConfig = None) -> RAGState:
    """Enhanced content processor agent with RAG chat and explainable units"""
    logger.info("Content processor agent called")
    return await content_processor_instance.process(state)

# Create the workflow
workflow = StateGraph(RAGState)

# Add nodes
workflow.add_node("loader", load_node)
workflow.add_node("chunk_store", chunk_store_node)
workflow.add_node("router", router_node)
workflow.add_node("qa", qa_node_singleton)
workflow.add_node("summarization", summarization_node_singleton)
workflow.add_node("content_processor_agent", content_processor_agent_node)

# Define the main flow
workflow.add_edge(START, "loader")
workflow.add_edge("loader", "chunk_store")
workflow.add_edge("chunk_store", "router")

# Fixed conditional edges
workflow.add_conditional_edges(
    "router",
    lambda state: state["next_step"],
    {
        "qa": "qa", 
        "summarization": "summarization", 
        "content_processor_agent": "content_processor_agent"
    }
)

# Add edges from processing nodes to END
workflow.add_edge("qa", END)
workflow.add_edge("summarization", END)
workflow.add_edge("content_processor_agent", END)

# Compile the workflow
app = workflow.compile()

