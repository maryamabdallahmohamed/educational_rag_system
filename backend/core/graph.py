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
from backend.core.agents.tutor_agent import TutorAgent
logger = get_logger("main_graph")

# Class instances
chunk_store_instance = ChunkAndStoreNode()
content_processor_instance = ContentProcessorAgent()
tutor_instance = TutorAgent()

async def chunk_store_node(state: RAGState, config: RunnableConfig = None) -> RAGState:
    result = await chunk_store_instance.process(state)
    return result

async def content_processor_agent_node(state: RAGState, config: RunnableConfig = None) -> RAGState:
    """Enhanced content processor agent with RAG chat and explainable units"""
    logger.info("Content processor agent called")
    return await content_processor_instance.process(state)

async def tutor_agent_node(state: RAGState, config: RunnableConfig = None) -> RAGState:
    """Personalized tutoring agent with session management and learner modeling"""
    logger.info("Tutor agent node called")
    try:
        return await tutor_instance.process(state)
    except Exception as e:
        logger.error(f"Error in tutor agent node: {e}")
        state["answer"] = "I encountered an error while processing your tutoring request. Please try again."
        return state

# Create the workflow
workflow = StateGraph(RAGState)

# Add nodes
workflow.add_node("loader", load_node)
workflow.add_node("chunk_store", chunk_store_node)
workflow.add_node("router", router_node)
workflow.add_node("qa", qa_node_singleton)
workflow.add_node("summarization", summarization_node_singleton)
workflow.add_node("content_processor_agent", content_processor_agent_node)
workflow.add_node("tutor_agent", tutor_agent_node)

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
        "content_processor_agent": "content_processor_agent",
        "tutor_agent": "tutor_agent"
    }
)

# Add edges from processing nodes to END
workflow.add_edge("qa", END)
workflow.add_edge("summarization", END)
workflow.add_edge("content_processor_agent", END)
workflow.add_edge("tutor_agent", END)

# Compile the workflow
app = workflow.compile()

