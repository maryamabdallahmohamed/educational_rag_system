from dotenv import load_dotenv
from text_to_speech_stream import text_to_speech_stream

load_dotenv()


def main(text: str):
    audio_stream = text_to_speech_stream(text)
    # Return the audio stream (BytesIO) directly instead of uploading to S3
    return audio_stream