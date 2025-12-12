#append note in db
#input is page num doc id  and text input 
from backend.database.repositories.note_repo import NoteRepository
from backend.utils.logger_config import get_logger
from backend.database.db import NeonDatabase

logger = get_logger("add_note")

async def add_note(doc_id, note_text, session_id):
    logger.info(f"Adding note: {note_text} to doc_id: {doc_id} for session_id: {session_id}")
    async with NeonDatabase.get_session() as session:
        note_repo = NoteRepository(session)
        note_repo.add_note(note_text, document_id=doc_id, session_id=session_id)
        logger.info(f"Note added successfully.")
    return note_repo.get_notes_by_session(session_id)



