from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from backend.core.TTS.text_to_speech_stream import text_to_speech_iterator

router = APIRouter(
    prefix="/tts",
    tags=["Text to Speech"]
)

class TTSRequest(BaseModel):
    text: str

def _stream_audio_response(text_input: str):
    """Helper to generate the streaming response."""
    try:
        return StreamingResponse(
            text_to_speech_iterator(text_input),
            media_type="audio/mpeg"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/speak")
async def text_to_speech_get(text: str):
    """
    GET endpoint for TTS (Short texts).
    Usage: /tts/speak?text=Hello
    """
    if not text:
        raise HTTPException(status_code=400, detail="Text query parameter is required")
    return _stream_audio_response(text)

@router.post("/speak")
async def text_to_speech_post(request_body: TTSRequest):
    """
    POST endpoint for TTS (Longer texts).
    Usage: body = {"text": "Hello world..."}
    """
    if not request_body.text:
         raise HTTPException(status_code=400, detail="Text field is required in body")
    return _stream_audio_response(request_body.text)