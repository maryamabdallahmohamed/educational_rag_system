import logging
import time
from backend.core.ASR.src.asr_infrence import transcribe

logger = logging.getLogger("ASR_Pipeline")

class TranscriptionService:
    """
    Service for handling audio transcription in single-pass mode.
    """
    def __init__(self):
        logger.info("Initializing TranscriptionService (single-pass)...")

    def process_audio(self, audio_path: str) -> str:
        """
        Transcribe the entire audio file without chunking and return text only.
        """
        logger.info(f"Transcribing file: {audio_path}")
        start_time = time.time()
        text = transcribe(audio_path)
        logger.info(f"Transcription complete in {time.time() - start_time:.2f}s")
        return text