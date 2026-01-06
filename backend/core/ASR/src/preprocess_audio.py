
import numpy as np
import torchaudio
import torch


class audio_utils:
    def __init__(self) -> None:
        # Single-pass mode: no chunking configuration needed
        pass

    def preprocess_audio(self, audio_path: str) -> np.ndarray:
  
        print(f"[audio] Loading: {audio_path}")
        waveform, sr = torchaudio.load(audio_path)
        print(f"[audio] Loaded: {waveform.shape}, sr={sr}Hz")
        if waveform.ndim > 1 and waveform.shape[0] > 1:
            print("[audio] Converting to mono...")
            waveform = torch.mean(waveform, dim=0, keepdim=True)
        if sr != 16000:
            print(f"[audio] Resampling {sr}Hz → 16000Hz...")
            resampler = torchaudio.transforms.Resample(sr, 16000)
            waveform = resampler(waveform)
            sr = 16000

        duration_sec = waveform.shape[-1] / sr
        print(f"[audio] Duration: {duration_sec:.2f}s")
        print("[audio] Normalizing amplitude...")
        waveform = waveform.squeeze(0)
        waveform = waveform / (waveform.abs().max() + 1e-8)
        print(f"[audio] ✓ Preprocessed: shape={waveform.shape}, range=[{waveform.min():.3f}, {waveform.max():.3f}]")
        return waveform.numpy()

    def chunk_audio(self, waveform: torch.Tensor, sr: int = 16000, overlap_sec: float = 0.0):
        """
        Deprecated: For compatibility, now returns a single full-length chunk.
        """
        return [waveform.numpy()]
