import asyncio
import json
from langchain.schema import Document

# Import your class
from backend.core.states.graph_states import RAGState
from backend.core.nodes.chunk_store import ChunkAndStoreNode

# Dummy state builder
def build_test_state():
    docs = [
        Document(
            page_content="This is a test document. It has multiple sentences. "
                         "We want to check if it chunks properly.",
            metadata={"title": "TestDoc1", "source": "unit_test"}
        ),
        Document(
            page_content="Second test doc. Let's see if embedding + chunking works fine.",
            metadata={"title": "TestDoc2"}
        ),
    ]
    return RAGState(documents=docs)

async def run_test():
    node = ChunkAndStoreNode()
    state = build_test_state()

    print("🚀 Starting process...")
    new_state = await node.process(state)

    print("\n✅ Process completed!")
    print("Inserted document IDs:", new_state.get("document_ids"))
    print("Inserted chunks:", len(new_state.get("chunks", [])))

    # Pretty print one of the chunks
    if new_state["chunks"]:
        first_chunk = new_state["chunks"][0]
        try:
            print("\nFirst chunk DTO (dict-like):")
            print(json.dumps(first_chunk.__dict__, indent=2, default=str))
        except Exception:
            print("\nFirst chunk:", first_chunk)

if __name__ == "__main__":
    asyncio.run(run_test())
