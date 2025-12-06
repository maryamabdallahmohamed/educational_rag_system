#!/bin/bash
# Example cURL requests for SeamlessM4Tv2 API

# Make sure server is running:
# uvicorn server:app --reload

echo "=== SeamlessM4Tv2 API Examples ==="

# 1. Health Check
echo -e "\n[1] Health Check"
curl -X GET http://localhost:8000/health | jq .

# 2. Transcribe MP3 (Egyptian Arabic)
echo -e "\n[2] Transcribe MP3 (Egyptian Arabic)"
curl -X POST http://localhost:8000/transcribe \
  -F "file=@test.mp3" \
  -F "tgt_lang=arb" \
  -F "clean=true" | jq .

# 3. Transcribe WAV (without cleaning)
echo -e "\n[3] Transcribe WAV (without cleaning)"
curl -X POST http://localhost:8000/transcribe \
  -F "file=@test.wav" \
  -F "tgt_lang=arb" \
  -F "clean=false" | jq .

# 4. Transcribe FLAC (English)
echo -e "\n[4] Transcribe FLAC (English)"
curl -X POST http://localhost:8000/transcribe \
  -F "file=@test.flac" \
  -F "tgt_lang=eng" | jq .

# 5. Error Test - Invalid Format
echo -e "\n[5] Error Test - Invalid Format (.txt)"
curl -X POST http://localhost:8000/transcribe \
  -F "file=@test.txt" \
  -F "tgt_lang=arb" | jq .

# 6. Error Test - Missing File
echo -e "\n[6] Error Test - Missing File"
curl -X POST http://localhost:8000/transcribe \
  -F "file=@nonexistent.mp3" \
  -F "tgt_lang=arb" 2>&1 | head -5

# Notes:
# - Replace test.mp3, test.wav, test.flac with actual files
# - Supported formats: .mp3, .wav, .flac, .ogg, .m4a, .aac, .opus
# - Language codes: arb (Arabic), eng (English), fra (French), etc.
# - First request takes longer (model loading)
# - jq is used for pretty JSON output (optional: `brew install jq` or `choco install jq`)
