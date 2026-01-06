import os
import re
from io import BytesIO
from typing import IO

from dotenv import load_dotenv
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs

load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

if not ELEVENLABS_API_KEY:
    raise ValueError("ELEVENLABS_API_KEY environment variable not set")

client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

EGYPTIAN_VOICE_ID = "DWMVT5WflKt0P8OPpIrY"  # replace with an Egyptian / Arabic voice if you have one


def clean_text_for_speech(text: str) -> str:
    """
    Removes Markdown formatting and other artifacts that shouldn't be read aloud.
    """
    if not text:
        return ""
    
    # Remove Bold/Italic markers (* or **)
    text = re.sub(r'\*+', '', text)
    
    # Remove Headers (#)
    text = re.sub(r'#+\s', '', text)
    
    # Remove Links [text](url) -> text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    
    # Remove raw URLs
    text = re.sub(r'http[s]?://\S+', '', text)
    
    # Replace Hyphens with comma (better for Arabic pausing)
    text = text.replace("-", "،")
    
    # Remove Code blocks
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'`[^`]*`', '', text)
    
    # Clean extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def text_to_speech_stream(text: str) -> IO[bytes]:
    """
    Converts text to speech using ElevenLabs and returns a BytesIO stream.
    """
    clean_text = clean_text_for_speech(text)

    response = client.text_to_speech.convert(
        voice_id=EGYPTIAN_VOICE_ID,
        optimize_streaming_latency="0",
        output_format="mp3_22050_32",
        text=clean_text,
        model_id="eleven_multilingual_v2",  # important for Arabic / dialects [web:12][web:13]
        voice_settings=VoiceSettings(
            stability=0.5,
            similarity_boost=0.5,
            style=0.5,
            use_speaker_boost=True,
        ),
    )

    audio_stream = BytesIO()
    for chunk in response:
        if chunk:
            audio_stream.write(chunk)

    audio_stream.seek(0)
    return audio_stream


def text_to_speech_iterator(text: str):
    """
    Generator that yields chunks of audio data from ElevenLabs.
    """
    clean_text = clean_text_for_speech(text)
    
    response = client.text_to_speech.convert(
        voice_id=EGYPTIAN_VOICE_ID,
        optimize_streaming_latency="0",
        output_format="mp3_22050_32",
        text=clean_text,
        model_id="eleven_multilingual_v2",  # same model here [web:12][web:13]
        voice_settings=VoiceSettings(
            stability=0.0,
            similarity_boost=1.0,
            style=0.0,
            use_speaker_boost=True,
        ),
    )

    for chunk in response:
        if chunk:
            yield chunk


if __name__ == "__main__":
    # Simple Egyptian Arabic test sentence
    text = "إزيك يا مروان؟ عامل إيه النهارده - الجو تحفة - والصوت ده مصري على الآخر."
    stream = text_to_speech_stream(text)
    with open("output_stream_egyptian.mp3", "wb") as f:
        f.write(stream.read())
    print(f"Saved audio for '{text}' to output_stream_egyptian.mp3")