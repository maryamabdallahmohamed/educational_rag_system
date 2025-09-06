from langchain.prompts import ChatPromptTemplate
from backend.models.llms.groq_llm import GroqLLM
import logging as logger
from backend.core.graph_states import RAGState
from backend.utils.prompt_loader import PromptLoader

def QA(state: RAGState) -> RAGState:
    """
    Generate study Q&A pairs from documents stored in state["documents"].
    Ensures that the document content is passed into {context} in the prompt.
    """

    llm = GroqLLM()

    # 1. Get query string (instruction), fallback if missing
    query = state.get("query", "Generate Q&A pairs from this document")

    # 2. Get documents directly from state
    docs = state.get("documents", [])
    if not docs:
        state["qa_pairs"] = []
        state["answer"] = "No documents available in state to generate Q&A."
        return state

    # 3. Combine document contents into a single context string
    context = "\n\n".join(doc.page_content for doc in docs)

    # 4. Detect language (fallback to Arabic if not provided)
    detected_lang = None
    if hasattr(docs[0], "metadata"):
        detected_lang = docs[0].metadata.get("language", "ar")
    if not detected_lang:
        detected_lang = "ar"

    # 5. Load system prompt template from YAML
    template = PromptLoader.load_system_prompt("prompts/qa_prompt.yaml")

    # 6. Build ChatPromptTemplate
    prompt = ChatPromptTemplate.from_template(template)

    # 7. Format messages with actual context and instruction
    messages = prompt.format_messages(
        context=context,
        instruction=query,
        detected_lang=detected_lang,
        Questions=10  # enforce 10 questions
    )

    # 8. Call LLM
    try:
        llm_response = llm.invoke(messages)
        logger.info("✅ Q&A generation successful")
    except Exception as e:
        logger.error(f"❌ LLM call failed: {e}")
        state["qa_pairs"] = []
        state["answer"] = "Error during Q&A generation."
        return state

    # 9. Store results
    state["qa_pairs"] = llm_response
    state["answer"] = "Generated Q&A pairs successfully."

    return state
