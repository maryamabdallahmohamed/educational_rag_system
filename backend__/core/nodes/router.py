from langgraph.types import RunnableConfig
from backend__.core.states.graph_states import RAGState, RouterOutput
from backend__.utils.logger_config import get_logger
from langchain_core.output_parsers import JsonOutputParser
from backend__.models.llms.groq_llm import GroqLLM
from langchain_core.prompts import ChatPromptTemplate
from backend__.loaders.prompt_loaders.prompt_loader import PromptLoader

logger = get_logger("router_node")
model = GroqLLM()
llm = model.llm

parser = JsonOutputParser(pydantic_object=RouterOutput)

# Load prompt template from YAML file
prompt_template = PromptLoader.load_system_prompt("prompts/router_agent_prompt.yaml")

prompt = ChatPromptTemplate.from_messages([
    ("system", prompt_template),
    ("human", "User message: {user_input}")
])

chain = prompt | llm | parser

def router_node(state: RAGState, config: RunnableConfig = None) -> RAGState:
    """Router node that determines next step based on user input"""
    
    user_input = state.get("query", "").strip()
    
    if not user_input:
        logger.warning("No user input found in state")
        state["next_step"] = "content_processor_agent"
        return state
    
    try:
        
        routing_result = chain.invoke({
            "user_input": user_input,
            "format_instructions": parser.get_format_instructions()
        })
        
        state["next_step"] = routing_result["route"]
        state["router_confidence"] = routing_result.get("confidence", 0.0)
        state["router_reasoning"] = routing_result.get("reasoning", "LLM classification")
        
        logger.info("Router decision: '%s' -> %s", user_input[:50], routing_result["route"])
        
    except Exception as e:
        logger.error("Router classification failed: %s", str(e))
        state["next_step"] = "content_processor_agent"  # Fallback
        
    return state

def classify_with_llm(user_input: str) -> dict:
    """Use chain with JsonOutputParser to classify user intent"""
    
    return chain.invoke({
        "user_input": user_input,
        "format_instructions": parser.get_format_instructions()
    })

