#!/usr/bin/env python
"""
Test API with MP3 file

Usage:
    python test_api_mp3.py <mp3_file_path>
    
Example:
    python test_api_mp3.py test.mp3
    python test_api_mp3.py path/to/audio.mp3
"""

import sys
import requests
import json
from pathlib import Path

def test_api(audio_file: str):
    """Test the API with an MP3 file."""
    
    audio_path = Path(audio_file)
    
    # 1. Validate file exists
    if not audio_path.exists():
        print(f"❌ Error: File not found: {audio_file}")
        return
    
    file_ext = audio_path.suffix.lower()
    print(f"✓ File found: {audio_file} ({file_ext})")
    print(f"✓ Size: {audio_path.stat().st_size / 1024 / 1024:.1f}MB")
    
    # 2. Test health check
    print("\n[1/3] Testing health check...")
    try:
        response = requests.get("http://localhost:8000/health")
        print(f"✓ Status: {response.status_code}")
        health = response.json()
        print(f"✓ Model loaded: {health['model_loaded']}")
        print(f"✓ Supported formats: {', '.join(health['supported_formats'])}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        print("   Make sure server is running: uvicorn server_mp3_ready:app --reload")
        return
    
    # 3. Upload and transcribe
    print("\n[2/3] Uploading and transcribing...")
    try:
        with open(audio_path, "rb") as f:
            files = {"file": (audio_path.name, f, "audio/mpeg")}
            data = {
                "tgt_lang": "arb",
                "clean": "true",
            }
            
            print(f"  Sending to: POST /transcribe")
            print(f"  Language: arb (Arabic)")
            print(f"  Clean: true")
            
            response = requests.post(
                "http://localhost:8000/transcribe",
                files=files,
                data=data,
                timeout=300  # 5 min timeout
            )
        
        print(f"✓ Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Error: {response.json()}")
            return
        
        result = response.json()
        print(f"✓ Status: {result['status']}")
        
    except Exception as e:
        print(f"❌ Transcription failed: {e}")
        return
    
    # 4. Display results
    print("\n[3/3] Results:")
    print("=" * 70)
    print(f"File: {result['file']}")
    print(f"Format: {result['file_format']}")
    print(f"Duration: {result['duration_sec']:.2f}s")
    print(f"Language: {result['language']}")
    print(f"Cleaned: {result['cleaned']}")
    print("=" * 70)
    print("\n📝 TRANSCRIPT:")
    print("-" * 70)
    print(result['text'])
    print("-" * 70)
    print("\n✅ API Test Successful!")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_api_mp3.py <audio_file>")
        print("Example: python test_api_mp3.py test.mp3")
        sys.exit(1)
    
    audio_file = sys.argv[1]
    test_api(audio_file)
