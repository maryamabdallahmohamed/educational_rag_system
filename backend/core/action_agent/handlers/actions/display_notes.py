#append note in db
#input is page num doc id  and text input 
from backend.database.repositories.note_repo import NoteRepository
from backend.utils.logger_config import get_logger
from backend.database.db import NeonDatabase

logger = get_logger("Display Notes")

async def display_note(payload):
    doc_id = payload.get("doc_id")
    session_id = payload.get("session_id")
    logger.info(f"Displaying notes for doc_id: {doc_id} and session_id: {session_id}")
    async with NeonDatabase.get_session() as session:
        note_repo = NoteRepository(session)
        notes = await note_repo.get_notes_by_session(session_id)
        logger.info(f"Notes retrieved successfully.")
    return await notes



