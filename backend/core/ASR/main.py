import logging
import sys
from ASR.src.pipeline import TranscriptionService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)


def main():    
    audio_file = '/Users/maryamsaad/Downloads/summ.mp3'
    
    service = TranscriptionService()
    
    try:
        text = service.process_audio(audio_file)

        print("\n--- Transcription ---")
        print(text)

    except FileNotFoundError:
        logging.error("Audio file not found.")
    except Exception as e:
        logging.error(f"Fatal error: {e}")

if __name__ == "__main__":
    main()