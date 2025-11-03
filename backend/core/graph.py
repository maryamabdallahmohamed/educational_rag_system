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

# Class instances - keeping agents separate and independent
chunk_store_instance = ChunkAndStoreNode()
content_processor_instance = ContentProcessorAgent()
tutor_instance = TutorAgent()

async def chunk_store_node(state: RAGState, config: RunnableConfig = None) -> RAGState:
    result = await chunk_store_instance.process(state)
    return result

async def content_processor_agent_node(state: RAGState, config: RunnableConfig = None) -> RAGState:
    """Content processor agent - decides whether to handle directly or delegate to TutorAgent"""
    logger.info("Content processor agent called")
    
    # Check if this should be delegated to TutorAgent
    query = state.get("query", "").strip().lower()
    tutoring_indicators = [
        'explain', 'teach', 'learn', 'understand', 'help me with',
        'how to', 'why does', 'can you help',
        'math', 'mathematics', 'algebra', 'calculus', 'geometry',
        'physics', 'chemistry', 'biology', 'science',
        'practice', 'exercise', 'quiz', 'test', 'homework',
        'step by step', 'break down', 'simplify', 'confused',
        'tutor', 'learning', 'studying'
    ]
    
    # More specific educational patterns
    educational_patterns = [
        'what is' + ('.*' if 'math' in query or 'physics' in query or 'chemistry' in query or 'biology' in query else ''),
        'how does.*work',
        'can you.*explain',
        'help.*understand',
        'teach.*about'
    ]
    
    is_tutoring_request = (
        any(indicator in query for indicator in tutoring_indicators) or
        any('what is' in query and subject in query for subject in ['math', 'physics', 'chemistry', 'biology', 'science', 'algebra', 'calculus'])
    )
    
    if is_tutoring_request:
        logger.info("CPA detected tutoring request - delegating to TutorAgent")
        state["next_step"] = "tutor_agent"
        state["delegated_by_cpa"] = True
        return state
    else:
        logger.info("CPA handling request directly")
        result = await content_processor_instance.process(state)
        return result

async def tutor_agent_node(state: RAGState, config: RunnableConfig = None) -> RAGState:
    """Personalized tutoring agent - processes request and goes directly to END"""
    logger.info("Tutor agent node called (delegated from CPA)")
    try:
        result = await tutor_instance.process(state)
        result["processed_by_tutor"] = True
        return result
    except Exception as e:
        logger.error(f"Error in tutor agent node: {e}")
        state["answer"] = "I encountered an error while processing your tutoring request. Please try again."
        return state

# Create the workflow
workflow = StateGraph(RAGState)

# Add nodes - simplified hierarchy: Router -> CPA -> TutorAgent -> END
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

# Router only routes to main processing nodes (not TutorAgent directly)
workflow.add_conditional_edges(
    "router",
    lambda state: state["next_step"],
    {
        "qa": "qa", 
        "summarization": "summarization", 
        "content_processor_agent": "content_processor_agent"
    }
)

# CPA can delegate to TutorAgent or handle directly
workflow.add_conditional_edges(
    "content_processor_agent",
    lambda state: state.get("next_step", "END"),
    {
        "tutor_agent": "tutor_agent",
        "END": END
    }
)

# Simple hierarchy: TutorAgent goes directly to END
workflow.add_edge("tutor_agent", END)

# Other nodes go directly to END
workflow.add_edge("qa", END)
workflow.add_edge("summarization", END)

# Compile the workflow
app = workflow.compile()

