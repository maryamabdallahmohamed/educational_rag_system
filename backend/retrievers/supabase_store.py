import os
from supabase import create_client, Client
from langchain_community.vectorstores import SupabaseVectorStore
from dotenv import load_dotenv
from backend.models.embedders.hf_embedder import HFEmbedder
load_dotenv()



SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
embedder_model=HFEmbedder()


chunk_store = SupabaseVectorStore(
    embedding=embedder_model,
    client=supabase,
    table_name="chunks",
    query_name="match_chunks"
)


doc_store = SupabaseVectorStore(
    embedding=embedder_model,
    client=supabase,
    table_name="documents",
    query_name="match_documents"
)
