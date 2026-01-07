import asyncio
from typing import Dict, Any, List
from backend.database.db import NeonDatabase
from backend.database.repositories.chunk_repo import ChunkRepository
from backend.database.repositories.document_repo import DocumentRepository
from backend.database.db import NeonDatabase
from backend.utils.logger_config import get_logger
import os
import re
import io
import base64

logger = get_logger("NextSectionHandler")



async def next_section_handler(pdf_pages: List, current_page: int) -> Dict[str, Any]:
    """
    Handler for 'next_section' action.
    Increments page number and returns the next page as a base64 encoded image.
    """
    try:
        if not pdf_pages:
             return {
                "status": "error",
                "message": "No document loaded or pages available",
                "action": "next_section"
            }

        next_page = current_page + 1
        if next_page > len(pdf_pages):
            return {
                "status": "end_of_document",
                "message": "End of document reached",
                "action": "next_section"
            }

        page_image = pdf_pages[next_page - 1]
        
        # Convert PIL Image to Base64
        img_byte_arr = io.BytesIO()
        page_image.save(img_byte_arr, format='JPEG')
        img_byte_arr = img_byte_arr.getvalue()
        base64_encoded = base64.b64encode(img_byte_arr).decode('utf-8')

        logger.info(f"Next section for page {next_page} fetched successfully")
        return {
            "status": "success",
            "page_number": next_page,
            "image": base64_encoded,
            "action": "next_section"
        }
    except Exception as e:
        logger.error(f"Error fetching next section for page {current_page}: {str(e)}")
        return {
            "status": "error",
            "message": str(e),
            "action": "next_section"
        }

