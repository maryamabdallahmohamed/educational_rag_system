import re
import torch
from tqdm import tqdm
from PIL import Image
from transformers import AutoProcessor, Qwen2VLForConditionalGeneration
from backend.config import DEVICE
from backend.utils.logger_config import get_logger
logger = get_logger("qari_ocr")

# ==============================
# Model & Processor Initialization
# ==============================

MODEL_ID = "NAMAA-Space/Qari-OCR-v0.3-VL-2B-Instruct"
PROCESSOR_ID = "Qwen/Qwen2-VL-2B-Instruct"


def load_ocr_model():
    """
    Loads the Qari OCR model and processor.
    Returns:
        model: Qwen2VLForConditionalGeneration model.
        processor: AutoProcessor object.
        eos_id, pad_id: Token IDs for generation.
        bad_words_ids: Filtered token sequences to suppress noise.
    """
    model = Qwen2VLForConditionalGeneration.from_pretrained(
        MODEL_ID,
        torch_dtype=torch.float16,
        trust_remote_code=True,
        cache_dir="backend/core/ocr_module/Qari_model_cache"
    ).to(DEVICE)

    processor = AutoProcessor.from_pretrained(
        PROCESSOR_ID,
        trust_remote_code=True,
        cache_dir="backend/core/ocr_module/Qwen_processor_cache"
    )
    logger.info(" Qari OCR model and processor loaded.")
    tokenizer = processor.tokenizer
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    eos_id = tokenizer.eos_token_id
    pad_id = tokenizer.pad_token_id

    noise_strings = [
        "br", "<br>", "</br>", "p", "<p>", "</p>", "div", "<div>", "</div>",
        "span", "<span>", "</span>", "document", "pdivdocument", "hbrh",
        "ipbrh", "ipbrp", "bold", "italic", "underline", "http", "https",
        "Global", "Trends", "The", "To", "Brown", "Cities"
    ]

    bad_words_ids = []
    for s in noise_strings:
        ids = tokenizer(s, add_special_tokens=False).input_ids
        if ids:
            bad_words_ids.append(ids)

    print(f"✅ OCR model loaded on {DEVICE}")
    return model, processor, eos_id, pad_id


# ==============================
# OCR Inference Logic
# ==============================

def get_ocr_prompt() -> str:
    """Returns the OCR instruction prompt for Arabic text extraction."""
    return (
        "You are an Arabic OCR specialist designed to extract text from images containing Arabic content. "
        "When processing images:\n"
        "1. Read Arabic text right-to-left, top-to-bottom.\n"
        "2. Do not hallucinate missing or decorative text.\n"
        "3. Mark unclear text as [غير واضح].\n"
        "4. Focus on visible text only — prioritize accuracy.\n"
        "5. Ignore watermarks, stamps, or background noise.\n"
        "6. Preserve line breaks and spacing.\n"
        "7. Avoid adding punctuation or diacritics.\n"
        "Return the extracted text only."
    )


def extract_text_from_images(images, model, processor, eos_id, pad_id, max_size=(1024, 1024), show_progress=True):
    """
    Extracts text from a list of images using the Qari OCR model.

    Args:
        images (list[PIL.Image]): List of PIL images.
        model: Loaded Qwen2VLForConditionalGeneration model.
        processor: Loaded AutoProcessor.
        eos_id (int): End-of-sequence token ID.
        pad_id (int): Padding token ID.
        max_size (tuple): Maximum (width, height) for resizing images.
        show_progress (bool): Whether to show progress bar.

    Returns:
        list[str]: Extracted text for each image.
    """
    results = []
    iterator = tqdm(images, desc="Extracting text", disable=not show_progress)

    for img in iterator:
        # Resize overly large images
        if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
            img = img.copy()
            img.thumbnail(max_size, Image.Resampling.LANCZOS)

        # Build prompt
        messages = [
            {"role": "system", "content": [{"type": "text", "text": get_ocr_prompt()}]},
            {"role": "user", "content": [{"type": "image", "image": img}]},
        ]
        prompt_text = processor.apply_chat_template(messages, add_generation_prompt=True, tokenize=False)

        # Prepare inputs
        inputs = processor(
            text=prompt_text,
            images=img,
            return_tensors="pt",
            padding=True,
        ).to(model.device)

        # Generate output
        with torch.inference_mode():
            generated_ids = model.generate(
                **inputs,
                max_new_tokens=256,
                do_sample=False,
                temperature=0.0,
                repetition_penalty=1.2,
                no_repeat_ngram_size=6,
                eos_token_id=eos_id,
                pad_token_id=pad_id,
                use_cache=True,
            )

        # Extract only the generated portion
        input_len = (
            int(inputs["attention_mask"].sum().item())
            if "attention_mask" in inputs
            else inputs["input_ids"].shape[-1]
        )
        gen_only = generated_ids[0, input_len:]

        text = processor.decode(gen_only, skip_special_tokens=True, clean_up_tokenization_spaces=False).strip()

        # Remove leaked role markers
        text = re.sub(r"^(system|user|assistant)\s*:?\s*", "", text, flags=re.I).strip()

        results.append(text)
    
    return results
