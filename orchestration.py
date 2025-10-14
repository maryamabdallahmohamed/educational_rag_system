import asyncio
from typing import Optional, Dict, Any
from backend.core.nodes.loader import LoadDocuments
from backend.core.nodes.chunk_store import ChunkAndStoreNode
from backend.core.nodes.router import router_runnable, router_node
from backend.core.nodes.qa_node import QANode
from backend.core.nodes.summarizer import SummarizationNode


# Module instantiation
document_loader = LoadDocuments()
chunk_store_node = ChunkAndStoreNode()
qa_node = QANode()
summarization_node = SummarizationNode()


async def store_document(document) -> None:
    await chunk_store_node.process([document])
    print(f"✓ Document stored successfully")


async def route_query(query: str) -> Dict[str, Any]:
    routing_result = await router_node(query)
    print(f"Router decision: {routing_result}")
    return routing_result


async def process_qa(query: str, document) -> str:
    result = await qa_node.process(query=query, documents=[document])
    return result


async def process_summarization(query: str, document) -> str:
    result = await summarization_node.process(query=query, documents=[document])
    return result


async def process_query(query: str, document) -> str:
    routing_result = await route_query(query)
    
    # Extract the route type from routing result
    route_type = routing_result.get('route', '').lower()
    
    if 'qa' in route_type or 'question' in route_type:
        print("\n→ Routing to QA Node")
        return await process_qa(query, document)
    elif 'summar' in route_type:
        print("\n→ Routing to Summarization Node")
        return await process_summarization(query, document)
    else:
        print(f"\n⚠ Unknown route type: {route_type}")
        print("→ Defaulting to QA Node")
        return await process_qa(query, document)


def load_document(file_path: str):
    return document_loader.load_document(file_path)


async def main():
    """Main execution function for testing the orchestration."""
    
    # Load document
    print("=" * 80)
    print("LOADING DOCUMENT")
    print("=" * 80)
    document_path = "/Users/maryamsaad/Documents/grad_data/ground_truth_files/fast_test_clean.json"
    document = load_document(document_path)
    
    print(f"\nDocument preview: {document.page_content[:100]}...")
    print(f"Metadata: {document.metadata}")
    print(f"Language: {document.metadata.get('language', 'N/A')}")
    
    # Store document
    print("\n" + "=" * 80)
    print("STORING DOCUMENT")
    print("=" * 80)
    await store_document(document)
    
    # Test queries
    test_queries = [
        "generate questions and answers from the document",
        "what are the main points in this document?",
        "summarize the key findings"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print("\n" + "=" * 80)
        print(f"PROCESSING QUERY {i}: {query}")
        print("=" * 80)
        
        result = await process_query(query, document)
        print(f"\nResult:\n{result}\n")


if __name__ == "__main__":
    asyncio.run(main())