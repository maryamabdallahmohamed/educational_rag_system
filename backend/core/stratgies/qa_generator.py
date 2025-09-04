from langchain.prompts import ChatPromptTemplate
from backend.retrievers.supabase_store import doc_store  
from backend.models.llms.groq_llm import GroqLLM
import logging as logger
from backend.core.graph_states import RAGState

def QA(state: RAGState):
    llm = GroqLLM()

    # 1. Get query string from state (default to Q&A request)
    query = state.get("query", "Generate Q&A pairs from this document")

    # 2. Retrieve from documents table (whole-doc level)
    docs = doc_store.similarity_search(query, k=1)

    if not docs:
        state["qa_pairs"] = []
        state["answer"] = "No document found to generate Q&A."
        return state


    context = "\n\n".join(doc.page_content for doc in docs)

    # 4. Build Q&A generation prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant that generates Question & Answer pairs from documents."),
        ("user", """{context}

        Generate 5 diverse and meaningful Question & Answer pairs based on the above document. 
        Format your response as a JSON list of objects, where each object has 'question' and 'answer' fields.""")
            ])

    messages = prompt.format_messages(context=context)

    # 5. Call LLM
    llm_response = llm.invoke(messages)
    print(llm_response)

    # 6. Store results
    state["qa_pairs"] = llm_response
    state["answer"] = "Generated Q&A pairs successfully."

    return state
