from langchain.prompts import ChatPromptTemplate
from backend.retrievers.supabase_store import chunk_store
from backend.config import GLOBAL_K
from backend.models.reranker_model.reranker import Reranker
from backend.models.llms.groq_llm import GroqLLM
import logging as logger
from backend.core.graph_states import RAGState
from backend.utils.prompt_loader import PromptLoader

def chat_node(state: RAGState) -> dict:
    """
    Chat node:
    - Retrieve and rerank relevant chunks for the user query
    - Ensure responses use document metadata.language
    - Save the answer and sources into state
    """
    query = state["query"]
    logger.info(f"💬 Chat node processing query: {query}")

    reranker = Reranker()
    llm = GroqLLM()
    
    # Load system-level rules
    system_prompt = PromptLoader.load_system_prompt("backend/utils/prompts/chat_prompt.yaml")

    # Step 1. Retrieve chunks
    retrieved_chunks = chunk_store.similarity_search(query, GLOBAL_K)
    reranked_chunks = reranker.rerank_chunks(query, retrieved_chunks)

    context_parts = []
    for chunk in reranked_chunks:
        lang = chunk.metadata.get("language", "ar") 
        content = chunk.page_content
        context_parts.append(f"[Language: {lang}] {content}")


    context = "\n\n".join(context_parts)

    # Step 3. Build prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", f"Query: {query}\n\nContext:\n{context}\n\nAnswer:")
    ])

    # Step 4. Invoke model
    state["answer"] = llm.invoke(prompt.format_messages())

    logger.info("✅ Chat response generated successfully")
    return state
