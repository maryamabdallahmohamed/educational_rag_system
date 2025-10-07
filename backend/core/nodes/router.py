from langgraph.types import RunnableConfig
from backend.core.states.graph_states import RAGState, RouterOutput
from backend.utils.logger_config import get_logger
from langchain_core.output_parsers import JsonOutputParser
from backend.models.llms.groq_llm import GroqLLM
from langchain_core.prompts import ChatPromptTemplate
from backend.loaders.prompt_loaders.prompt_loader import PromptLoader
from backend.database.repositories.router_decision_repository import RouterDecisionRepository
from backend.database.db import NeonDatabase
from backend.database.models.router import RouteType
import asyncio
logger = get_logger("router_node")
model = GroqLLM()
Database=NeonDatabase()

llm = model.llm

parser = JsonOutputParser(pydantic_object=RouterOutput)

# Load prompt template from YAML file
prompt_template = PromptLoader.load_system_prompt("prompts/router_agent_prompt.yaml")

prompt = ChatPromptTemplate.from_messages([
    ("system", prompt_template),
    ("human", "User message: {user_input}")
])

chain = prompt | llm | parser

def _get_route_description(route: str) -> str:
    """Get description of what each route handles"""
    descriptions = {
        "qa": "Simple factual questions or Q&A generation from documents",
        "summarization": "Content summaries and overviews", 
        "content_processor_agent": "Document processing, learning units creation, and general conversation",
        "tutor_agent": "Personalized tutoring, adaptive learning, educational explanations, practice, and assessment"
    }
    return descriptions.get(route, "Unknown route")

async def router_node(state: RAGState, config: RunnableConfig = None) -> RAGState:
    """Router node that determines next step based on user input"""

    user_input = state.get("query", "").strip()
    if not user_input:
        state["next_step"] = "content_processor_agent"
        return state

    try:
        # Run LLM classification in a thread 
        routing_result = await asyncio.to_thread(
            lambda: chain.invoke({
                "user_input": user_input,
                "format_instructions": parser.get_format_instructions()
            })
        )

        route = routing_result["route"]
        state["next_step"] = route
        state["router_confidence"] = routing_result.get("confidence", 0.0)
        state["router_reasoning"] = routing_result.get("reasoning", "LLM classification")
        
        logger.info(f"Router decision: '{user_input}' -> {route} ({_get_route_description(route)}) "
                   f"[confidence: {state['router_confidence']:.2f}]")

        # Save to DB asynchronously
        try:
            async with NeonDatabase.get_session() as session:
                decision_repo = RouterDecisionRepository(session)
                logger.info(f"Saving router decision: query='{user_input}', route='{route}'")


                try:
                    route_enum = RouteType(route)
                except ValueError:
                    logger.warning(f"Unknown route type: {route}, defaulting to CONTENT_PROCESSOR")
                    route_enum = RouteType.CONTENT_PROCESSOR
                    # Update state to reflect the fallback
                    state["next_step"] = "content_processor_agent"

                decision = await decision_repo.create(
                    query=user_input,
                    chosen_route=route_enum
                )
                logger.info(f"Router decision saved successfully: {decision.id}")
        except Exception as db_error:
            logger.error(f"Failed to save router decision: {db_error}")

    except Exception as e:
        logger.error(f"Router classification failed for '{user_input}': {e}")
        # Intelligent fallback based on keywords
        user_lower = user_input.lower()
        if any(keyword in user_lower for keyword in ["tutor", "teach", "explain", "help me learn", "struggling", "practice", "assess"]):
            state["next_step"] = "tutor_agent"
            logger.info("Fallback: Detected tutoring keywords, routing to tutor_agent")
        elif any(keyword in user_lower for keyword in ["summary", "summarize", "overview", "main points"]):
            state["next_step"] = "summarization" 
            logger.info("Fallback: Detected summary keywords, routing to summarization")
        elif any(keyword in user_lower for keyword in ["question", "qa", "quiz", "test"]):
            state["next_step"] = "qa"
            logger.info("Fallback: Detected QA keywords, routing to qa")
        else:
            state["next_step"] = "content_processor_agent"
            logger.info("Fallback: No specific keywords detected, routing to content_processor_agent")

    return state
