"""
Audio preprocessing and text cleaning utilities for Seamless.

Includes:
- Audio loading with strictness
- Mono conversion
- 16 kHz resampling (mandatory)
- Duration checking
- Normalization
- Arabic text cleaning
"""

import re
from pathlib import Path

import torch
import torchaudio
import numpy as np


def get_audio_info(audio_path: str) -> dict:
    """Get audio metadata without full loading."""
    waveform, sr = torchaudio.load(audio_path)
    duration_sec = waveform.shape[-1] / sr
    channels = waveform.shape[0]
    return {
        "sr": sr,
        "channels": channels,
        "duration_sec": duration_sec,
        "shape": tuple(waveform.shape),
    }


def load_audio_metadata(audio_path: str) -> tuple[dict, bool]:
    """
    Load audio metadata and check 30-second limit.
    
    Returns:
        (metadata_dict, is_valid_duration: bool)
    """
    info = get_audio_info(audio_path)
    is_valid = info["duration_sec"] <= 30.0
    return info, is_valid


def preprocess_audio_strict(
    audio_path: str,
    target_sr: int = 16000,
    max_duration_sec: float = 30.0,
) -> np.ndarray:
    """
    Strict preprocessing per SeamlessM4Tv2 paper.
    
    Steps:
    1. Load waveform
    2. Convert to mono
    3. Resample to 16 kHz
    4. Reject if >30s (one-shot only)
    5. Normalize amplitude to [-1, 1]
    
    Args:
        audio_path: Path to audio file
        target_sr: Target sample rate (fixed at 16000)
        max_duration_sec: Max allowed duration (fixed at 30.0)
        
    Returns:
        Preprocessed mono waveform (numpy, shape (n_samples,))
        
    Raises:
        ValueError: If validation fails
        RuntimeError: If audio loading fails
    """
    audio_path = str(Path(audio_path).resolve())
    
    if not Path(audio_path).exists():
        raise ValueError(f"Audio file not found: {audio_path}")

    try:
        # Load
        waveform, sr = torchaudio.load(audio_path)
        print(f"  ✓ Loaded: shape={tuple(waveform.shape)}, sr={sr}Hz")
    except Exception as e:
        raise RuntimeError(f"Failed to load audio: {e}")

    # Convert to mono
    if waveform.ndim > 1 and waveform.shape[0] > 1:
        print(f"  → Converting {waveform.shape[0]} channels to mono")
        waveform = torch.mean(waveform, dim=0, keepdim=True)

    # Resample to 16 kHz (mandatory per paper)
    if sr != target_sr:
        print(f"  → Resampling {sr}Hz → {target_sr}Hz")
        resampler = torchaudio.transforms.Resample(sr, target_sr)
        waveform = resampler(waveform)
        sr = target_sr

    # Check duration (enforce one-shot, reject long audio)
    duration_sec = waveform.shape[-1] / sr
    if duration_sec > max_duration_sec:
        raise ValueError(
            f"Audio too long ({duration_sec:.2f}s > {max_duration_sec}s). "
            f"SeamlessM4T v2 is optimized for one-shot inference. "
            f"Please use audio ≤30 seconds."
        )
    print(f"  ✓ Duration: {duration_sec:.2f}s (within limit)")

    # Normalize to [-1, 1]
    waveform = waveform.squeeze(0)  # Remove channel dimension
    max_val = waveform.abs().max()
    if max_val > 0:
        waveform = waveform / max_val
    print(f"  ✓ Normalized: range=[{waveform.min():.3f}, {waveform.max():.3f}]")

    return waveform.numpy()


def clean_arabic_text(text: str) -> str:
    """
    Clean Arabic text by:
    - Removing diacritics (tashkeel)
    - Normalizing alef variations (أ، إ، آ → ا)
    - Normalizing ya/alef maksura (ى → ي)
    - Removing hamza marks
    - Removing punctuation
    - Collapsing whitespace
    
    Args:
        text: Raw Arabic text
        
    Returns:
        Cleaned Arabic text
    """
    # Remove diacritics (tashkeel): FATHATAN, DAMMATAN, KASRATAN, FATHA, DAMMA, KASRA, SHADDA, SUKUN
    text = re.sub(r"[\u064B-\u0652]", "", text)

    # Normalize alef variations → ا
    text = re.sub(r"[إأآ]", "ا", text)

    # Normalize ya and alef maksura → ي
    text = re.sub(r"[ىۀ]", "ي", text)

    # Normalize hamza → و
    text = re.sub(r"[ؤ]", "و", text)

    # Normalize ta marbuta → ه
    text = re.sub(r"[ة]", "ه", text)

    # Remove common punctuation
    text = re.sub(r"[،؛؟!٫٪]", "", text)

    # Keep only Arabic characters and spaces
    text = re.sub(r"[^\u0600-\u06FF\s]", "", text)

    # Normalize whitespace (newlines, tabs → spaces, collapse multiple)
    text = re.sub(r"\s+", " ", text).strip()

    return text


def batch_clean_arabic(texts: list[str]) -> list[str]:
    """Clean multiple Arabic texts."""
    return [clean_arabic_text(t) for t in texts]


if __name__ == "__main__":
    # Test with dummy text
    test_text = "السلام عليكم ورحمة الله وبركاته"
    cleaned = clean_arabic_text(test_text)
    print(f"Original:  {test_text}")
    print(f"Cleaned:   {cleaned}")