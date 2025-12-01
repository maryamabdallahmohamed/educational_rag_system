#append note in db
#input is page num doc id  and text input 
from backend.database.repositories.note_repo import NoteRepository

def add_note(doc_id, note_text, session_id):
    async with NeonDatabase.get_session() as session:
        note_repo = NoteRepository(session)
        note_repo.add_note(note_text, document_id=doc_id, session_id=session_id)
    return note_repo.get_notes_by_session(session_id)




