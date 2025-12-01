from pdf2image import convert_from_path
from PyPDF2 import PdfReader
from backend.core.ocr_module.text_detector import preprocess_detected_texts
from backend.core.ocr_module.qari import  extract_text_from_images, load_ocr_model
from backend.core.ocr_module.postprocess import postprocess_ocr_results
from backend.utils.logger_config import get_logger
from PIL import Image
from tqdm import tqdm
import os
import time
import re
logger = get_logger("ocr_orchestrator")


def gibberish_detection(text):
    """
    Detects likely gibberish or invalid extracted text.
    """
    if not text.strip():
        return True
    if len(text.strip()) < 20:
        return True

    if re.search(r'[^\w\s\u0600-\u06FF.,!?؛،:()«»"-]', text):
        weird_ratio = len(re.findall(r'[^\w\s\u0600-\u06FF]', text)) / max(len(text), 1)
        if weird_ratio > 0.3:
            return True

    words = text.split()
    avg_word_len = sum(len(w) for w in words) / max(len(words), 1)
    if avg_word_len < 2:
        return True

    return False




def upload_document(pdf_path):
    start = time.time()
    reader = PdfReader(pdf_path)
    text = ""
    pages_dict = {}
    for i, page in enumerate(reader.pages):
        page_text = page.extract_text() or ""
        text += page_text
        pages_dict[str(i+1)] = page_text
    if text.strip():
        arabic_chars = re.findall(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]', text)
        arabic_ratio = len(arabic_chars) / max(len(text), 1)
        gibberish = gibberish_detection(text)

        if arabic_ratio > 0.1 or gibberish:
            reason = "Arabic" if arabic_ratio > 0.1 else "gibberish"
            logger.info(f"⚠️ Detected {reason} or unreadable text, switching to OCR.")
            texts, metadata = ocr_pdf(pdf_path)
            return texts, metadata

        metadata = {
            "file_name": os.path.basename(pdf_path),
            "num_pages": len(reader.pages),
            "method": "pdf_extract",
            "processing_time": round(time.time() - start, 2),
            "text_length": sum(len(t) for t in pages_dict.values()),
            "gibberish_detected": gibberish,
            "arabic_ratio": round(arabic_ratio, 3),
        }
        logger.info("✅ Extracted clean text directly from PDF.")
        return pages_dict, metadata
    logger.info("⚠️ Empty text detected, switching to OCR.")
    texts, metadata = ocr_pdf(pdf_path)
    return texts, metadata



def ocr_pdf(pdf_path, dpi=300):
    images = []
    if os.path.isfile(pdf_path):
        images.extend(convert_from_path(pdf_path, dpi=dpi))
    else:
        for pdf_file in tqdm(os.listdir(pdf_path), desc="Converting PDFs"):
            if pdf_file.lower().endswith('.pdf'):
                pdf_path = os.path.join(pdf_path, pdf_file)
                images.extend(convert_from_path(pdf_path, dpi=dpi))
    
    detected_texts = preprocess_detected_texts(images)
    start = time.time()
    model, processor, eos_id, pad_id = load_ocr_model()
    all_ocr_results = {}
    for page_idx in tqdm(sorted(detected_texts.keys()), desc="Performing OCR on pages"):
        textboxes = detected_texts[page_idx]
        pil_textboxes=[Image.fromarray(box) for box in textboxes]
        ocr_results = extract_text_from_images(pil_textboxes, model, processor, eos_id, pad_id)
        all_ocr_results[page_idx] = ocr_results
    logger.debug(all_ocr_results)
    print("OCR RESULTS:", all_ocr_results)
    texts = postprocess_ocr_results(all_ocr_results)
    metadata = {
        "file_name": os.path.basename(pdf_path),
        "num_pages": len(images),
        "method": "ocr",
        "processing_time": round(time.time() - start, 2),
        "dpi": dpi,
        "pages_processed": sorted(all_ocr_results.keys()),
        "text_length": sum(len(t) for t in texts.values()),}
    logger.info(f" OCR completed in {metadata['processing_time']}s for {metadata['num_pages']} pages.")

    return texts, metadata


