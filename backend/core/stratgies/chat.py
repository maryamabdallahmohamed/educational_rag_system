from langchain.prompts import ChatPromptTemplate
from backend.data.stores.supabase_store import chunk_store
from backend__.config import GLOBAL_K
from backend.models.reranker_model.reranker import Reranker
from backend.models.llms.groq_llm import GroqLLM
import logging as logger
from backend.core.graph.states.graph_states import RAGState
from backend.loaders.prompt_loaders.prompt_loader import PromptLoader


def chat_node(state: RAGState) -> dict:
    """
    Chat node:
    - Retrieve and rerank relevant chunks for the user query
    - Decide whether to use RAG or fallback to LLM knowledge
    - Save the answer and sources into state
    """
    query = state["query"]
    logger.info(f"💬 Chat node processing query: {query}")

    reranker = Reranker()
    llm = GroqLLM()
    
    # Load system-level rules
    rag_system_prompt = PromptLoader.load_system_prompt("prompts/rag_prompt.yaml")
    chat_prompt = PromptLoader.load_system_prompt("prompts/chat_prompt.yaml")

    # Step 1. Retrieve chunks
    retrieved_chunks = chunk_store.similarity_search(query, GLOBAL_K)

    if not retrieved_chunks:
        logger.info("⚠️ No chunks retrieved → using LLM knowledge only.")
        messages = [
            ("system", chat_prompt),
            ("user", f"Query: {query}\n\nAnswer (use your own knowledge) and message history if found:")
        ]
        state["answer"] = llm.invoke(messages)
        return state

    # Step 2. Rerank chunks
    reranked_chunks = reranker.rerank_chunks(query, retrieved_chunks)

    # Step 3. Check rerank confidence
    top_score = reranked_chunks[0].metadata["rerank_score"] if reranked_chunks else 0.0
    score_threshold = 0.7  
    use_rag = top_score >= score_threshold

    if use_rag:
        logger.info(f"✅ Using RAG (top rerank score={top_score:.3f})")
        context_parts = []
        for chunk in reranked_chunks:
            lang = chunk.metadata.get("language", "ar") 
            content = chunk.page_content
            context_parts.append(f"[Language: {lang}] {content}")

        context = "\n\n".join(context_parts)

        messages = [
            ("system", rag_system_prompt),
            ("user", f"Query: {query}\n\nContext:\n{context}\n\nAnswer:")
        ]
    else:
        logger.info(f"⚠️ Low rerank score ({top_score:.3f}) → using LLM knowledge only.")
        messages = [
            ("system", chat_prompt),
            ("user", f"Query: {query}\n\nAnswer (use your own knowledge):")
        ]


    state["answer"] = llm.invoke(messages)

    logger.info("✅ Chat response generated successfully")
    return state
