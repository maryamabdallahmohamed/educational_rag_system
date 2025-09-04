from langchain.prompts import ChatPromptTemplate
from backend.retrievers.supabase_store import doc_store  
from backend.models.llms.groq_llm import GroqLLM
import logging as logger
from backend.core.graph_states import RAGState

def summary_node(state:  RAGState) ->  RAGState:
    llm = GroqLLM()

    # 1. Get query string from state (NOT documents)
    query = state.get("query", "Summarize this document")

    # 2. Retrieve from documents table (whole-doc level)
    docs = doc_store.similarity_search(query, k=1)

    if not docs:
        state["answer"] = "No document found to summarize."
        return state

    # 3. Take the first document’s full content
    context = docs[0].page_content

    # 4. Build summarization prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant that summarizes documents."),
        ("user", "{context}\n\nProvide a concise summary:")
    ])

    messages = prompt.format_messages(context=context)

    # 5. Call LLM
    state["answer"] = llm.invoke(messages)
    logger.info("✅ Summary generated successfully")
    return state
