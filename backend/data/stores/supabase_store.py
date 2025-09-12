import os
from supabase import create_client, Client
from langchain_community.vectorstores import SupabaseVectorStore
from dotenv import load_dotenv
from backend__.models.embedders.hf_embedder import HFEmbedder

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
embedder_model = HFEmbedder()

"This function retrieves the most relevant chunks (sections) of documents based on vector similarity."
chunk_store = SupabaseVectorStore(
    embedding=embedder_model,
    client=supabase,
    table_name="chunks",
    query_name="match_chunks"
)
"This function retrieves the most relevant entire documents based on vector similarity to a query embedding."
doc_store = SupabaseVectorStore(
    embedding=embedder_model,
    client=supabase,
    table_name="documents",
    query_name="match_documents"
)

def create_conversation() -> str:
    """Create a new conversation and return its ID."""
    response = supabase.table("conversations").insert({}).execute()
    return response.data[0]["conversation_id"]


def log_message(conversation_id: str, query : None, answer: str, strategy: str):
    """Insert a new row into messages."""
    supabase.table("messages").insert({
        "conversation_id": conversation_id,
        "user_query": query,
        "bot_answer": answer,
        "strategy": strategy
    }).execute()

def get_conversation_messages(conversation_id: str):
    """Fetch all messages for a given conversation."""
    response = supabase.table("messages") \
        .select("*") \
        .eq("conversation_id", conversation_id) \
        .order("created_at") \
        .execute()
    return response.data


def execute_query(query, params = None):
    try:
        result = supabase.rpc('execute_sql', {
            'query_text': query,
            'params': params or []
        }).execute()
        
        return result.data if result.data else []
        
    except Exception as e:
        print(f"Query execution failed: {e}")
        raise