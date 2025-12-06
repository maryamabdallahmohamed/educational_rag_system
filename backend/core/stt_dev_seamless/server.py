"""
FastAPI server for SeamlessM4Tv2 transcription with MP3 support.

Features:
- Accepts MP3, WAV, FLAC, OGG (any audio format)
- Validates file type
- Returns proper error messages
- Includes health check
"""

import tempfile
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.seamless_model import SeamlessModel
from app.utils import clean_arabic_text

app = FastAPI(title="SeamlessM4Tv2 Transcriber with MP3 Support")

# CORS for frontend testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supported audio formats
SUPPORTED_FORMATS = {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac", ".opus"}

# Global model instance
stt: SeamlessModel | None = None


@app.on_event("startup")
async def startup_event():
    """Initialize model on startup."""
    global stt
    print("\n[startup] Initializing SeamlessM4Tv2 model...")
    stt = SeamlessModel(
        model_name="facebook/seamless-m4t-v2-large",
        device=-1,  # CPU by default
    )
    print("[startup] ✓ Ready to accept requests\n")


@app.get("/health")
async def health() -> dict:
    """Health check endpoint."""
    return {
        "status": "ok",
        "model_loaded": stt is not None and stt.loaded,
        "model_name": stt.model_name if stt else None,
        "supported_formats": list(SUPPORTED_FORMATS),
    }


@app.post("/transcribe")
async def transcribe(
    file: UploadFile = File(..., description="Audio file (MP3, WAV, FLAC, OGG, etc.)"),
    tgt_lang: str = Form("arb", description="Target language code"),
    clean: bool = Form(False, description="Apply Arabic text cleaning"),
    model_name: str | None = Form(
        None, description="Override model (triggers reload)"
    ),
    max_duration_sec: float = Form(
        30.0, description="Max audio duration in seconds"
    ),
) -> dict:
    """
    Transcribe audio file with SeamlessM4Tv2.
    
    **Supported Formats:**
    - MP3 (recommended for storage)
    - WAV (lossless)
    - FLAC (compressed lossless)
    - OGG (Vorbis)
    - M4A/AAC
    - OPUS
    
    **Features:**
    - Automatic mono conversion
    - Automatic resampling to 16 kHz
    - Duration validation (max 30s)
    - Amplitude normalization
    - Optional Arabic text cleaning
    
    **Parameters:**
    - `file`: Audio file (required)
    - `tgt_lang`: Target language (default: "arb" for Arabic)
    - `clean`: Apply Arabic cleaning (default: false)
    - `model_name`: Override model (optional)
    - `max_duration_sec`: Max duration in seconds (default: 30)
    """
    global stt

    if stt is None:
        raise HTTPException(status_code=500, detail="Model not initialized")

    try:
        # 1. Validate file format
        file_ext = Path(file.filename).suffix.lower() if file.filename else ""
        
        if not file_ext:
            raise HTTPException(
                status_code=400,
                detail=f"File has no extension. Supported formats: {', '.join(SUPPORTED_FORMATS)}"
            )
        
        if file_ext not in SUPPORTED_FORMATS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported format: {file_ext}. Supported: {', '.join(SUPPORTED_FORMATS)}"
            )

        print(f"\n[server] ✓ File format validated: {file_ext}")

        # 2. Reload model if requested
        if model_name:
            stt.maybe_reload(model_name)

        # 3. Save uploaded file to temp
        suffix = file_ext if file_ext else ".mp3"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = tmp.name

        print(f"[server] Processing: {file.filename} ({len(contents) / 1024 / 1024:.1f}MB)")

        # 4. Transcribe (preprocess + inference all in one)
        result = stt.transcribe(
            tmp_path,
            tgt_lang=tgt_lang,
            max_duration_sec=max_duration_sec,
        )

        text = result["text"]

        # 5. Optional Arabic cleaning
        if clean:
            print("[server] Applying Arabic text cleaning...")
            text = clean_arabic_text(text)

        print(f"[server] ✓ Transcription complete\n")

        # 6. Clean up
        Path(tmp_path).unlink(missing_ok=True)

        return {
            "status": "success",
            "text": text,
            "language": tgt_lang,
            "duration_sec": result["duration_sec"],
            "file": file.filename,
            "file_format": file_ext,
            "cleaned": clean,
        }

    except ValueError as e:
        # Audio too long / invalid
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"[server] ERROR: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)