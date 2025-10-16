from typing import Dict, Any
from backend.core.nodes.loader import LoadDocuments
from backend.core.nodes.chunk_store import ChunkAndStoreNode
from backend.core.nodes.router import router_node
from backend.core.nodes.qa_node import QANode
from backend.core.nodes.summarizer import SummarizationNode
from backend.core.agents.content_processor_agent import ContentProcessorAgent
# Initialize modules
document_loader = LoadDocuments()
chunk_store_node = ChunkAndStoreNode()
# qa_node = QANode()
# summarization_node = SummarizationNode()
cpa = ContentProcessorAgent()
# ---------------------- DOCUMENT HANDLING ----------------------
def load_document(file_path: str):
    """Load and return a document object."""
    return document_loader.load_document(file_path)

async def store_document(document):
    """Store document chunks in DB or vector store."""
    await chunk_store_node.process([document])
    return {"status": "success", "message": "Document stored successfully"}

# ---------------------- ROUTING & MODULE EXECUTION ----------------------
async def route_query(query: str) -> Dict[str, Any]:
    """Ask the router model to decide which node to use."""
    decision = await router_node(query)
    return decision

# async def run_qa(query: str, document):
#     """Run the QA module only."""
#     return await qa_node.process(query=query, documents=[document])

# async def run_summarization(query: str, document):
#     """Run the Summarization module only."""
#     return await summarization_node.process(query=query, documents=[document])

# ---------------------- Agents ----------------------
async def cpa_agent(query: str, document):
    """Run the Content Processor Agent (CPA) to handle complex queries."""
    result = await cpa.process(query=query, document=document)
    return result


# ---------------------- ORCHESTRATOR ----------------------
async def orchestrate() -> Dict[str, Any]:
    doc= load_document("/Users/maryamsaad/Documents/grad_data/ground_truth_files/fast_test_clean.json")
    await store_document(doc)
    query = "شخصيات"
    result= await cpa_agent(query, doc)
    print("CPA Result:", result)
    query="ما الأسباب التي تدفع الطفل إلى الكذب حسب ما ورد في النص"
    result= await cpa_agent(query, doc)
    print("CPA Result:", result)
    query="ما هي العوامل التي تؤثر على سلوك الطفل؟"
    result= await cpa_agent(query, doc)
    print("CPA Result:", result)
    query="ما المراحل التسع للّحْرَم التي ذكرها النص، وما خصائص كل مرحلة؟"
    result= await cpa_agent(query, doc)
    print("CPA Result:", result)

    # qa=await run_qa(query, doc)
    # summary=await run_summarization(query, doc)
    # print("QA Result:", qa)
    # print("Summary Result:", summary)

if __name__ == "__main__":
    import asyncio
    asyncio.run(orchestrate())
