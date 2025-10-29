import cv2
import numpy as np
from tqdm import tqdm
from surya.foundation import FoundationPredictor
from surya.recognition import RecognitionPredictor
from surya.detection import DetectionPredictor
from backend.config import DEVICE

# ==============================
# Text Detection and Preprocessing
# ==============================

def detect_text_regions(pages, conf_threshold=0.65, padding_y=20):
    """
    Detects text regions in PDF pages and crops them into individual images.

    Args:
        pages (list[PIL.Image]): List of PDF pages as PIL images.
        conf_threshold (float): Minimum confidence to keep detected boxes.
        padding_y (int): Vertical padding around bounding boxes.

    Returns:
        dict[int, list[PIL.Image]]: Dictionary mapping page index to cropped text region images.
    """
    foundation = FoundationPredictor()
    detection = DetectionPredictor(device=DEVICE)

    cropped_pages = {}

    for idx, image in enumerate(tqdm(pages, desc="Detecting text regions")):
        results = detection([image])[0]

        # Filter boxes by confidence
        boxes = [b for b in results.bboxes if b.confidence >= conf_threshold]

        cropped_regions = []
        for box in boxes:
            x1, y1, x2, y2 = map(int, box.bbox)
            y1 = max(0, y1 - padding_y)
            y2 = min(image.height, y2 + padding_y)
            cropped_region = image.crop((x1, y1, x2, y2))
            cropped_regions.append(cropped_region)

        cropped_pages[idx] = cropped_regions

    return cropped_pages


def preprocess_image(image, target_height=120):
    """
    Preprocesses a text region image for OCR or recognition.

    Steps:
    - Convert to grayscale
    - Denoise
    - Adaptive thresholding
    - Resize and dilate

    Args:
        image (PIL.Image): Cropped text region.
        target_height (int): Desired height for normalization.

    Returns:
        np.ndarray: Preprocessed binary image.
    """
    sample = np.array(image)
    gray = cv2.cvtColor(sample, cv2.COLOR_BGR2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    binary = cv2.adaptiveThreshold(
        denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    scale = target_height / binary.shape[0]
    resized = cv2.resize(binary, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    kernel = np.ones((1, 1), np.uint8)
    processed = cv2.dilate(resized, kernel, iterations=1)
    return processed


def preprocess_detected_texts(pages):
    """
    Runs text detection and preprocessing on all pages.

    Args:
        pages (list[PIL.Image]): List of page images.

    Returns:
        dict[int, list[np.ndarray]]: Dictionary mapping page index to preprocessed text regions.
    """
    detected_regions = detect_text_regions(pages)
    preprocessed_pages = {}

    for idx in sorted(detected_regions.keys()):
        regions = detected_regions[idx]
        preprocessed_pages[idx] = [preprocess_image(region) for region in regions]

    return preprocessed_pages
