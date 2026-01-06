import asyncio
from typing import Dict, Any, List
from backend.database.db import NeonDatabase
from backend.database.repositories.chunk_repo import ChunkRepository
from backend.database.repositories.document_repo import DocumentRepository
from backend.database.db import NeonDatabase
from backend.utils.logger_config import get_logger
import os
import re
logger = get_logger("NextSectionHandler")



async def _get_next_section(doc_id: str, current_page: str):
    try:
        async with NeonDatabase.get_session() as session:
            chunk_repo = ChunkRepository(session)
            doc_repo = DocumentRepository(session)
            logger.info(f"Fetching next section for document {doc_id} and page {current_page}")
            try:
                next_page_num = int(current_page) + 1
                next_page = str(next_page_num)
            except ValueError:
                return None, None, "Invalid page number format"

            doc = await doc_repo.get(doc_id)
            logger.info(f"Document {doc_id} fetched successfully")
            if not doc:
                return None, None, "Document not found"
            
            max_page = max(int(k) for k in doc.content.keys())
            logger.info(f"Max page for document {doc_id} is {max_page}")
            if next_page_num > max_page:
                return None, str(max_page), "End of document reached"
            chunks = await chunk_repo.get_by_document_and_page(doc_id, next_page)
            logger.info(f"Next section for document {doc_id} and page {current_page} fetched successfully")
            return chunks, next_page, None
    except Exception as e:
        logger.error(f"Error fetching next section: {e}")
        return None, None, str(e)


async def next_section_handler(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler for 'next_section' action.
    Increments page number and fetches chunks for the next page of the specified document.
    Ensures document-page coherence by filtering by both document_id and page.
    """
    doc_id = payload.get("document_id")
    current_page = payload.get("current_page")
    session_id = payload.get("session_id")
    current_page = payload.get("current_page")
    
    if not doc_id or current_page is None:
         return {
             "status": "error", 
             "message": "Missing document_id or current_page in payload",
             "action": "next_section"
         }

    try:
        chunks, next_page, error_msg = await _get_next_section(doc_id, str(current_page))
        
        if error_msg:
             return {
                "status": "error" if "End" not in error_msg else "limit_reached",
                "action": "next_section",
                "message": error_msg,
                "document_id": doc_id,
                "page": next_page,
                "session_id": session_id
            }

        if chunks:
            chunk_data = [{"id": str(c.id), "content": c.content} for c in chunks]
            return {
                "status": "ok",
                "action": "next_section",
                "document_id": doc_id,
                "page": next_page,
                "chunks": chunk_data,
                "session_id": session_id
            }
        else:
            return {
                "status": "empty",
                "action": "next_section",
                "message": "No chunks found for next page.",
                "document_id": doc_id,
                "page": next_page,
                "session_id": session_id
            }
            
    except Exception as e:
        return {
            "status": "error",
            "action": "next_section",
            "message": str(e),
            "session_id": session_id
        }
