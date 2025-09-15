from langgraph.graph import StateGraph, START, END
from langgraph.types import RunnableConfig
from backend__.core.states.graph_states import RAGState
from backend__.utils.logger_config import get_logger

# Import your nodes
from backend__.core.nodes.chunk_store import ChunkAndStoreNode
from backend__.core.nodes.loader import load_node
from backend__.core.nodes.router import router_node
from backend__.core.nodes.qa_node import qa_node_singleton
from backend__.core.nodes.summarizer import summarization_node_singleton
logger = get_logger("main_graph")

# Class instances
chunk_store_instance = ChunkAndStoreNode()

def chunk_store_node(state: RAGState, config: RunnableConfig = None) -> RAGState:
    """Wrapper for ChunkAndStoreNode.process()"""
    return chunk_store_instance.process(state)

# Placeholder nodes for testing (since you only have QA implemented)
def placeholder_summarization_node(state: RAGState, config: RunnableConfig = None) -> RAGState:
    """Placeholder for summarization node"""
    logger.info("Placeholder: Summarization node called")
    state["answer"] = "Summarization feature coming soon!"
    return state

def placeholder_content_processor_node(state: RAGState, config: RunnableConfig = None) -> RAGState:
    """Placeholder for content processor agent"""
    logger.info("Placeholder: Content processor agent called")
    state["answer"] = "Content processor feature coming soon!"
    return state

# Create the workflow
workflow = StateGraph(RAGState)

# Add nodes
workflow.add_node("loader", load_node)
workflow.add_node("chunk_store", chunk_store_node)
workflow.add_node("router", router_node)
workflow.add_node("qa", qa_node_singleton)
workflow.add_node("summarization", summarization_node_singleton)
workflow.add_node("content_processor", placeholder_content_processor_node)

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
        "content_processor_agent": "content_processor"  # Maps to actual node name
    }
)

# Add edges from processing nodes to END
workflow.add_edge("qa", END)
workflow.add_edge("summarization", END)
workflow.add_edge("content_processor", END)

# Compile the workflow
app = workflow.compile()

