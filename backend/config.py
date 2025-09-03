import torch

if torch.backends.mps.is_available():
    DEVICE = "mps"   # Apple Silicon
elif torch.cuda.is_available():
    DEVICE = "cuda"  # NVIDIA GPU
else:
    DEVICE = "cpu"   # Default fallback

CACHE_DIR = "cache/"

GLOBAL_K=5