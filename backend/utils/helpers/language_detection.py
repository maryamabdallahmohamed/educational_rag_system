from langdetect import detect, DetectorFactory
import asyncio
DetectorFactory.seed = 0



async def returnlang(text: str) -> str:
    """Detect language of the input text."""
    try:
        detected = detect(text)
        lang_mapping = {
            "ar": "Arabic",
            "en": "English"
        }
        return lang_mapping.get(detected, "English")
    except Exception as e:
        print(f"Language detection failed: {e}. Defaulting to Arabic.")
        return "Arabic"
