from langchain.prompts import ChatPromptTemplate
from backend__.models.llms.groq_llm import GroqLLM
import logging as logger
from backend__.core.states.graph_states import RAGState
from backend__.loaders.prompt_loaders.prompt_loader import PromptLoader


def summary_node(state: RAGState) -> RAGState:
    """
    Generate a concise study summary directly from documents in state["documents"].
    """
    llm = GroqLLM()

    # 1. Get query string (default fallback)
    query = state.get("query", "Summarize this document")


    docs = state.get("documents", [])
    if not docs:
        state["answer"] = "No documents available in state to summarize."
        return state


    context = "\n\n".join(doc.page_content for doc in docs)


    detected_lang = docs[0].metadata.get("language", "ar")


    template = PromptLoader.load_system_prompt("prompts/summerize_prompt.yaml")
    final_prompt = template.format(
        context=context,
        instruction=query,
        detected_lang=detected_lang
    )


    prompt = ChatPromptTemplate.from_template(final_prompt)
    messages = prompt.format_messages()



    try:
        llm_response = llm.invoke(messages)
        state["answer"] = llm_response
        logger.info("✅ Summary generated successfully")
    except Exception as e:
        logger.error(f"❌ LLM call failed: {e}")
        state["answer"] = "Error during summary generation."

    return state
