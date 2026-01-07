import re
from backend.database.repositories.note_repo import NoteRepository
from backend.utils.logger_config import get_logger
from backend.database.db import NeonDatabase

logger = get_logger("add_note")

def _extract_note_content(user_message: str) -> str:
    """
    Extracts the actual note content from the command using improved heuristics for speech.
    Handling: "Add note about X", "Add note that says X", "زود نوتة ان X", etc.
    """
    if not user_message:
        return "" 

    # 0. Normalize Arabic Digits for easier regex matching (١ -> 1)
    digits_map = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
    norm_message = user_message.translate(digits_map)
    param_match = re.search(r"[\(\"'](.*?)[\)\"']", user_message)
    if param_match:
        return param_match.group(1).strip()

    text = norm_message
    
    page_regex = r"(?:in\s+|on\s+|at\s+|في\s+|علي\s+)?(?:page|pg|p\.|صفحة|ص)\s*(?:number\s+|num\s+|rqm\s+|رقم\s+)?\d+"
    text = re.sub(page_regex, " ", text, flags=re.IGNORECASE)

    command_pattern = r"^(?:add\s+(?:a\s+)?(?:quick\s+)?(?:note|comment)|make\s+(?:a\s+)?(?:note|comment)|take\s+(?:a\s+)?(?:note|comment)|create\s+(?:a\s+)?(?:note|comment)|write\s+(?:a\s+)?(?:note|comment)|record\s+(?:a\s+)?(?:note|comment)|zod\s+not(?:a|e)|زود\s+(?:نوته|نوتة|ملحوظة)|اضف\s+(?:ملاحظة|تعليق)|سجل\s+(?:ملاحظة|تعليق)|اكتب\s+(?:ملاحظة|تعليق))"
    
    match = re.search(command_pattern, text, flags=re.IGNORECASE)
    if match:

        content = text[match.end():].strip()
        connector_pattern = r"^(?:that\s+says|that\s+is|that|about|saying|say|to|for|on|regarding|concerning|bta3t|3an|inn|in|bi|3ala|el|ly|عن|بأن|إن|ان|بخصوص|علي|بتقول|وهي|عبارة\s+عن)\s+"
        content = re.sub(connector_pattern, "", content, flags=re.IGNORECASE).strip()
        
        return content
    return text.strip()

async def add_note(payload):

    logger.info(f"[add_note] received payload: {payload}")
    arguments = payload.get("arguments", {})
    if isinstance(arguments, dict):
        note_text = arguments.get("note_text")
        doc_id = arguments.get("doc_id")
        page_arg = arguments.get("page_num")
        if page_arg:
            try:
                page_num = int(str(page_arg))
            except:
                page_num = None
        else:
            page_num = None
    else:
        note_text = None
        doc_id = None
        page_num = None

    if not note_text:
        note_text = payload.get("note_text") or payload.get("note") or payload.get("content")
    
    if not doc_id:
        doc_id = payload.get("doc_id")
        
    if not page_num:
        page_arg = payload.get("page_num") or payload.get("page") or payload.get("page_number")
        if page_arg:
             try:
                page_num = int(str(page_arg))
             except:
                pass

    if not note_text:
        raw_msg = payload.get("message", "")
        note_text = _extract_note_content(raw_msg)
        
        if not page_num:
             digits_map = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
             norm_msg = raw_msg.translate(digits_map)
             page_match = re.search(r"(?:page|p\.|صفحة|ص)\s*(\d+)", norm_msg, re.IGNORECASE)
             if page_match:
                 page_num = int(page_match.group(1))

    # Defaults
    if not note_text:
         note_text = "New Note"

    session_id = payload.get("session_id")

    # ---- Validation ----
    # Just ensure it's a string strip
    note_text = str(note_text).strip()

    logger.info(
        f"session={session_id}: {note_text}"
    )

    async with NeonDatabase.get_session() as session:
        note_repo = NoteRepository(session)

        try:
            note = await note_repo.add_note(
                note_text=note_text,
                page_num=page_num,
                session_id=session_id
            )

            logger.info("Note added successfully.")

            return {
                "status": "ok",
                "note": {
                    "id": str(note.id),
                    "note": note.note,
                    "session_id": str(note.session_id) if note.session_id else None,
                    "page_num": getattr(note, "page_num", None),
                    "created_at": note.created_at.isoformat() if note.created_at else None
                }
            }

        except Exception as e:
            logger.exception("Failed to add note")
            return {
                "status": "error",
                "message": str(e)
            }
