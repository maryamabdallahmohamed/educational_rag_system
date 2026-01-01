import torch
from backend.core.ASR.src.preprocess_audio import audio_utils
from backend.core.ASR.src.load_model import LoadSeamlessModel
from dotenv import load_dotenv
import time

load_dotenv()
utils = audio_utils()
ASR = LoadSeamlessModel()
processor, model = ASR.load()


def calculate_confidence_scores(scores, logits_shape):
    """Calculate confidence scores from model output scores with tracing."""
    logits = torch.stack(scores)    
    probs = torch.softmax(logits, dim=-1)         
    log_probs = torch.log_softmax(logits, dim=-1) 
    entropy = -(probs * log_probs).sum(dim=-1)
    entropy = entropy.cpu()

    # Normalize entropy into confidence (0 to 1)
    max_entropy = torch.log(torch.tensor(logits.size(-1)))
    confidence = 1.0 - (entropy / max_entropy)
    confidence = confidence.tolist()

    # Flatten confidence scores
    flat_confidence = [c for sublist in confidence for c in (sublist if isinstance(sublist, list) else [sublist])]
    avg_conf = sum(flat_confidence) / len(flat_confidence) if flat_confidence else 0.0
    
    # Add metadata to current trace
    from langsmith import get_current_run_tree
    current_run = get_current_run_tree()
    if current_run:
        current_run.extra = current_run.extra or {}
        current_run.extra.update({
            "entropy_values": entropy.tolist()[:10], 
            "max_entropy": max_entropy.item(),
            "avg_confidence": avg_conf,
            "confidence_method": "entropy_normalization",
            "vocab_size": logits_shape[-1],
            "sequence_length": len(flat_confidence)
        })
    
    return flat_confidence, avg_conf


def process_audio_chunk(chunk, chunk_index, total_chunks, sr, tgt_lang, device):
    """Process a single audio chunk with tracing."""
    start_time = time.time()
    
    print(f"[chunk {chunk_index}/{total_chunks}] Processing...")
    
    # Convert audio chunk to model inputs
    inputs = processor(
        audio=chunk.astype(float),
        sampling_rate=sr,
        return_tensors="pt"
    ).to(device)

    with torch.no_grad():
        output = model.generate(
            **inputs,
            tgt_lang=tgt_lang,
            max_new_tokens=256,
            return_dict_in_generate=True,
            output_scores=True
        )

    # Extract decoded token ids
    token_ids = output.sequences[0]
    token_ids = torch.tensor(token_ids, dtype=torch.long).unsqueeze(0)

    # Decode text
    text = processor.batch_decode(token_ids, skip_special_tokens=True)[0]

    # Compute per-token confidence using traceable function
    scores = output.scores
    logits_shape = torch.stack(scores).shape
    flat_confidence, avg_conf = calculate_confidence_scores(scores, logits_shape)
    
    processing_time = time.time() - start_time
    
    # Add metadata to current trace
    from langsmith import get_current_run_tree
    current_run = get_current_run_tree()
    if current_run:
        current_run.extra = current_run.extra or {}
        current_run.extra.update({
            "chunk_index": chunk_index,
            "total_chunks": total_chunks,
            "chunk_duration": len(chunk) / sr,
            "avg_confidence": avg_conf,
            "token_count": len(token_ids[0]),
            "processing_time_seconds": processing_time,
            "text_length": len(text),
            "confidence_scores": flat_confidence[:10]  
        })
    
    print(f"[chunk {chunk_index}] Text: {text}")
    print(f"[chunk {chunk_index}] Avg confidence: {avg_conf:.3f}")
    
    return {
        "text": text,
        "token_confidence": flat_confidence,
        "avg_confidence": avg_conf,
        "processing_time": processing_time
    }


def transcribe(audio_path: str, tgt_lang: str = "arb") -> str:
    """
    Single-pass transcription: process the full audio and return text only.
    """
    print(f"\n[inference] Starting single-pass transcription (lang={tgt_lang})...")
    waveform = utils.preprocess_audio(audio_path)
    sr = 16000

    device = torch.device(ASR.device)
    inputs = processor(
        audio=waveform.astype(float),
        sampling_rate=sr,
        return_tensors="pt"
    ).to(device)

    with torch.no_grad():
        output = model.generate(
            **inputs,
            tgt_lang=tgt_lang,
            max_new_tokens=512,
            return_dict_in_generate=True,
            output_scores=True
        )

    token_ids = output.sequences[0]
    token_ids = torch.tensor(token_ids, dtype=torch.long).unsqueeze(0)
    text = processor.batch_decode(token_ids, skip_special_tokens=True)[0]
    print(f"[single-pass] Text: {text}")
    
    if device.type == "mps":
        torch.mps.empty_cache()
        print("[cleanup] MPS cache cleared")

    return text.strip()
            
