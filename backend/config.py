import torch
from dotenv import load_dotenv
load_dotenv()
if torch.backends.mps.is_available():
    DEVICE = "mps" 
elif torch.cuda.is_available():
    DEVICE = "cuda"
else:
    DEVICE = "cpu"
CACHE_DIR = "cache/"
GLOBAL_K=5
