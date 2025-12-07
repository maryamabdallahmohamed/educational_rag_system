"""
SeamlessM4Tv2 inference wrapper with paper-recommended preprocessing.

Per Seamless paper best practices:
- Mono conversion for consistency
- 16 kHz resampling (strict)
- 30-second max (rejects longer without chunking)
- Amplitude normalization [-1, 1]
- One-shot inference (no chunking)
- Progress messages for UX
"""

import torch
import torchaudio
import numpy as np
from typing import TYPE_CHECKING
from backend.config import DEVICE
if TYPE_CHECKING:
    from transformers import AutoProcessor, SeamlessM4Tv2Model

from transformers import AutoProcessor, SeamlessM4Tv2Model
from huggingface_hub import snapshot_download

def ensure_model_downloaded(
    model_name: str, cache_dir: str | None = None
) -> str:
    """Download model with progress via huggingface_hub."""
    print(f"[model] Ensuring model {model_name} is available locally...")
    repo_dir = snapshot_download(repo_id=model_name, cache_dir=cache_dir)
    print(f"[model] ✓ Model available at: {repo_dir}")
    return repo_dir


class SeamlessModel:
    """One-shot SeamlessM4Tv2 transcriber with strict preprocessing."""

    def __init__(
        self,
        model_name: str = "facebook/seamless-m4t-v2-large",
        device: int = -1,
        cache_dir: str | None = None,
    ):
        """
        Initialize the model.
        
        Args:
            model_name: HuggingFace model ID
            device: -1 for CPU, >=0 for GPU device ID
            cache_dir: Optional HF cache directory
        """
        print("[Seamless] Loading SeamlessM4T v2 model...")
        self.model_name = model_name
        self.device = DEVICE
        self.cache_dir = cache_dir
        self.loaded = False
        self.processor = None
        self.model = None

        self._load()

    def _load(self) -> None:
        """Load model with progress."""
        ensure_model_downloaded(self.model_name, cache_dir=self.cache_dir)


        print(f"[model] Loading processor & model (device={DEVICE})...")

        self.processor = AutoProcessor.from_pretrained(
            self.model_name, cache_dir=self.cache_dir, use_fast=False
        )
        self.model = SeamlessM4Tv2Model.from_pretrained(
            self.model_name, cache_dir=self.cache_dir
        )
        self.model.to(self.device)
        self.loaded = True
        print("[Seamless] ✓ Model loaded successfully.")

    def maybe_reload(self, model_name: str) -> None:
        """Reload model if name changed."""
        if model_name and model_name != self.model_name:
            print(f"[model] Reloading to {model_name}...")
            self.model_name = model_name
            self._load()

    def preprocess_audio(
        self,
        audio_path: str,
        max_duration_sec: float = 30.0,
    ) -> np.ndarray:
        """
        Preprocess audio per Seamless paper recommendations.
        
        Steps:
        1. Load waveform
        2. Convert to mono
        3. Resample to 16 kHz (strict)
        4. Reject if >30s (enforce one-shot)
        5. Normalize amplitude to [-1, 1]
        
        Args:
            audio_path: Path to audio file
            max_duration_sec: Max allowed duration
            
        Returns:
            Preprocessed waveform (mono, 16kHz, normalized)
            
        Raises:
            ValueError: If audio exceeds max_duration_sec
        """
        print(f"[audio] Loading: {audio_path}")

        # Step 1: Load
        waveform, sr = torchaudio.load(audio_path)
        print(f"[audio] Loaded: {waveform.shape}, sr={sr}Hz")

        # Step 2: Convert to mono
        if waveform.ndim > 1 and waveform.shape[0] > 1:
            print("[audio] Converting to mono...")
            waveform = torch.mean(waveform, dim=0, keepdim=True)

        # Step 3: Resample to 16 kHz (strict requirement per paper)
        if sr != 16000:
            print(f"[audio] Resampling {sr}Hz → 16000Hz...")
            resampler = torchaudio.transforms.Resample(sr, 16000)
            waveform = resampler(waveform)
            sr = 16000

        # Step 4: Check duration (enforce one-shot, no chunking)
        duration_sec = waveform.shape[-1] / sr
        print(f"[audio] Duration: {duration_sec:.2f}s (max: {max_duration_sec}s)")

        if duration_sec > max_duration_sec:
            raise ValueError(
                f"Audio too long ({duration_sec:.1f}s exceeds {max_duration_sec}s). "
                f"SeamlessM4T v2 is designed for one-shot inference. "
                f"Please provide shorter audio."
            )

        # Step 5: Normalize amplitude
        print("[audio] Normalizing amplitude...")
        waveform = waveform.squeeze(0)  # Remove channel dim
        waveform = waveform / (waveform.abs().max() + 1e-8)  # Avoid division by zero

        print(f"[audio] ✓ Preprocessed: shape={waveform.shape}, range=[{waveform.min():.3f}, {waveform.max():.3f}]")

        return waveform.numpy()

    def transcribe(
        self,
        audio_path: str,
        tgt_lang: str = "arb",
        max_duration_sec: float = 30.0,
    ) -> dict:
        """
        Transcribe audio (one-shot, no chunking).
        
        Args:
            audio_path: Path to audio file
            tgt_lang: Target language code (e.g., 'arb', 'eng', 'fra')
            max_duration_sec: Max allowed duration
            
        Returns:
            Dict with keys:
                - 'text': Transcribed text
                - 'language': Target language
                - 'duration_sec': Audio duration
        """
        print(f"\n[inference] Starting transcription (lang={tgt_lang})...")

        # Preprocess with all checks
        waveform = self.preprocess_audio(audio_path, max_duration_sec)
        duration_sec = len(waveform) / 16000

        # Prepare for inference
        print("[inference] Preparing inputs...")
        inputs = self.processor(  # type: ignore
            audios=waveform,
            sampling_rate=16000,
            return_tensors="pt",
        )

        # Move to device
        device_obj = torch.device(self.device)
        inputs = inputs.to(device_obj)

        # One-shot inference
        print("[inference] Running model (one-shot)...")
        with torch.no_grad():
            output = self.model.generate(**inputs, tgt_lang=tgt_lang)  # type: ignore

        # Decode
        print(f"[inference] Output shape: {output}")
        # SeamlessM4T returns a GenerateOutput object or tuple-like structure
        token_ids = output.sequences if hasattr(output, "sequences") else output[0]
        text = self.processor.batch_decode( token_ids, skip_special_tokens=True)[0]

        print(f"[inference] ✓ Complete. Result length: {len(text)} chars")

        return {
            "text": text,
            "language": tgt_lang,
            "duration_sec": duration_sec,
        }


if __name__ == "__main__":
    # Quick test
    model = SeamlessModel(device=-1)
    print("\n✓ Model initialized successfully!")