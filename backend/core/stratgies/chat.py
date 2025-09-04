from langchain.prompts import ChatPromptTemplate
from backend.retrievers.supabase_store import chunk_store
from backend.config import GLOBAL_K
from backend.models.reranker_model.reranker import Reranker
from backend.models.llms.groq_llm import GroqLLM
import logging as logger
from backend.core.graph_states import RAGState


def chat_node(state: RAGState) -> dict:
    """
    Chat node:
    - Retrieve and rerank relevant chunks for the user query
    - If no chunks, fall back to LLM-only
    - Save the answer and sources into state
    """
    query = state["query"]
    logger.info(f"💬 Chat node processing query: {query}")

    reranker = Reranker()
    llm = GroqLLM()

    # Step 1. Retrieve chunks
    retrieved_chunks = chunk_store.similarity_search(query, GLOBAL_K)
    if not retrieved_chunks:
        logger.warning("⚠️ No chunks retrieved, falling back to LLM only...")
        state["answer"] = llm.invoke(
            ChatPromptTemplate.from_messages([
                ("system", "You are a helpful assistant."),
                ("user", query)
            ]).format_messages()
        )
        return state


    reranked_chunks = reranker.rerank_chunks(query, retrieved_chunks)


    context = "\n\n".join([chunk['page_content'] for chunk in reranked_chunks])
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant that answers questions based on the provided context."),
        ("user", f"Query: {query}\n\nContext:\n{context}\n\nAnswer:")
    ])


    state["answer"] = llm.invoke(prompt.format_messages())
    # state["sources"] = [c.metadata for c in reranked_chunks]

    logger.info("✅ Chat response generated successfully")
    return state


