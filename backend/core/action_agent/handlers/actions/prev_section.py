import asyncio
from typing import Dict, Any, List
from backend.database.db import NeonDatabase
from backend.database.repositories.chunk_repo import ChunkRepository
from backend.database.repositories.document_repo import DocumentRepository
from backend.database.db import NeonDatabase
from backend.utils.logger import logger
import os
import re
logger = logging.getLogger("PreviousSectionHandler")

async def _get_previous_section(doc_id: str, current_page: str):
    try:
        async with NeonDatabase.get_session() as session:
            chunk_repo = ChunkRepository(session)
            doc_repo = DocumentRepository(session)
            logger.info(f"Fetching previous section for document {doc_id} and page {current_page}")
            try:
                prev_page_num = int(current_page) - 1
                prev_page = str(prev_page_num)
            except ValueError:
                return None, None, "Invalid page number format"

            doc = await doc_repo.get(doc_id)
            logger.info(f"Document {doc_id} fetched successfully")
            if not doc:
                return None, None, "Document not found"
            
            max_page = max(int(k) for k in doc.content.keys())
            logger.info(f"Max page for document {doc_id} is {max_page}")
            if prev_page_num < 1:
                return None, str(max_page), "End of document reached"
            chunks = await chunk_repo.get_by_document_and_page(doc_id, prev_page)
            logger.info(f"Previous section for document {doc_id} and page {current_page} fetched successfully")
            return chunks, prev_page, None
    except Exception as e:
        logger.error(f"Error fetching previous section for document {doc_id} and page {current_page}: {str(e)}")
        return None, None, str(e)



def previous_section_handler(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler for 'previous_section' action.
    Decrements page number and fetches chunks for the previous page of the specified document.
    Ensures document-page coherence by filtering by both document_id and page.
    """
    doc_id = payload.get("document_id")
    current_page = payload.get("current_page")
    
    if not doc_id or current_page is None:
         return {
             "status": "error", 
             "message": "Missing document_id or current_page in payload",
             "action": "previous_section"
         }

    try:
        chunks, prev_page, error_msg = asyncio.run(_get_previous_section(doc_id, str(current_page)))
        
        if error_msg:
             return {
                "status": "error" if "End" not in error_msg else "limit_reached",
                "action": "previous_section",
                "message": error_msg,
                "document_id": doc_id,
                "page": prev_page 
            }

        if chunks:
            chunk_data = [{"id": str(c.id), "content": c.content} for c in chunks]
            return {
                "status": "ok",
                "action": "previous_section",
                "document_id": doc_id,
                "page": prev_page,
                "chunks": chunk_data
            }
        else:
            return {
                "status": "empty",
                "action": "previous_section",
                "message": "No chunks found for previous page.",
                "document_id": doc_id,
                "page": prev_page
            }
            
    except Exception as e:
        return {
            "status": "error",
            "action": "previous_section",
            "message": str(e)
        }
