from backend.database.repositories.note_repo import NoteRepository
from backend.utils.logger_config import get_logger
from backend.database.db import NeonDatabase

logger = get_logger("add_note")


async def add_note(payload):

    logger.info(f"[add_note] received payload: {payload}")

    note_text = payload.get("note_text") or payload.get("note") or payload.get("content")
    page_num = payload.get("page_num") or payload.get("page") or payload.get("page_number")
    session_id = payload.get("session_id")

    # ---- Validation ----

    if not note_text or not str(note_text).strip():
        return {
            "status": "error",
            "message": "note_text cannot be empty."
        }

    note_text = note_text.strip()

    logger.info(
        f"session={session_id}: {note_text}"
    )

    async with NeonDatabase.get_session() as session:
        note_repo = NoteRepository(session)

        try:
            note = await note_repo.add_note(
                note_text=note_text,
                page_num=page_num,
                session_id=session_id,
            )

            logger.info("Note added successfully.")

            return {
                "status": "ok",
                "note": note
            }

        except Exception as e:
            logger.exception("Failed to add note")
            return {
                "status": "error",
                "message": str(e)
            }
