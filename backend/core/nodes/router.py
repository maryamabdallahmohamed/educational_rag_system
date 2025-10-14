from langgraph.types import RunnableConfig
from backend.core.states.graph_states import  RouterOutput
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

async def router_node(query):
    """Router node that determines next step based on user input"""

    user_input = query.strip()

    try:
        # Run LLM classification in a thread 
        routing_result = await asyncio.to_thread(
            lambda: chain.invoke({
                "user_input": user_input,
                "format_instructions": parser.get_format_instructions()
            })
        )

        route = routing_result["route"]

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

                decision = await decision_repo.create(
                    query=user_input,
                    chosen_route=route_enum
                )
                logger.info(f"Router decision saved successfully: {decision.id}")
                return route
        except Exception as db_error:
            logger.error(f"Failed to save router decision: {db_error}")

    except Exception as e:
        logger.error(f"Router node error: {e}")

def router_runnable() -> RunnableConfig:
    return RunnableConfig(
        runnable=router_node,
        name="router_node",
        description="Routes the query to the appropriate next step based on its content.",
        tags=["router", "classification", "llm"]
    )