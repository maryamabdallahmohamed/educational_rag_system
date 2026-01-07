#append note in db
#input is page num doc id  and text input 
from backend.database.repositories.note_repo import NoteRepository
from backend.utils.logger_config import get_logger
from backend.database.db import NeonDatabase
import re
logger = get_logger("Display Notes")

async def display_note(payload):
    session_id = payload.get("session_id")
    user_action = payload.get("message", "") or payload.get("user_message", "")

    page_num = payload.get("page_num", None)
    if page_num is None and user_action:
        digits_map = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
        norm_msg = user_action.translate(digits_map)
        match = re.search(r'\d+', norm_msg)
        if match:
            try:
                page_num = int(match.group())
            except ValueError:
                pass

    logger.info(f"Displaying notes session_id: {session_id}, page: {page_num}")
    async with NeonDatabase.get_session() as session:
        if page_num is not None:
            note_repo = NoteRepository(session)
            notes = await note_repo.get_notes_by_session_and_page(session_id, page_num)
            logger.info(f"Notes for page {page_num} retrieved successfully.")
        else:
            note_repo = NoteRepository(session)
            notes = await note_repo.get_notes_by_session(session_id)
            logger.info(f"Notes retrieved successfully.")
        
        # Serialize notes to list of dicts
        notes_list = []
        for n in notes:
            notes_list.append({
                "id": str(n.id),
                "note": n.note,
                "session_id": str(n.session_id) if n.session_id else None,
                "page_num": getattr(n, "page_num", None),
                "created_at": n.created_at.isoformat() if n.created_at else None
            })
            
    return notes_list



