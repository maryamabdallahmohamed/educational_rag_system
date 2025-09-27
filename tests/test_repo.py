# backend/database/test_repos.py
import asyncio

from backend.database.db import NeonDatabase
from backend.database.repositories.document_repo import DocumentRepository

async def test_repositories():
    NeonDatabase.init()
    session_factory = NeonDatabase.get_session_factory()

    async with session_factory() as session:
        repo = DocumentRepository(session)
        doc = await repo.add("Test Doc", "Some content", {"source": "test"})
        print(doc)

if __name__ == "__main__":
    asyncio.run(test_repositories())
