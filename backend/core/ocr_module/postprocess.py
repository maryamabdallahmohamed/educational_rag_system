from bs4 import BeautifulSoup
import html
import re

def reconstruct_html_content(html_strings):
    """
    Cleans and reconstructs text from a list of OCR-generated HTML strings.
    - Decodes HTML entities (e.g., &quot;)
    - Strips tags using BeautifulSoup
    - Removes excessive blank lines
    """
    reconstructed_texts = []
    for content in html_strings:
        decoded = html.unescape(content)
        soup = BeautifulSoup(decoded, "html.parser")
        plain_text = soup.get_text(separator="\n")
        cleaned_text = "\n".join(
            [line.strip() for line in plain_text.splitlines() if line.strip()]
        )
        reconstructed_texts.append(cleaned_text)
    return reconstructed_texts


def merge_page_texts(ocr_results):
    """
    Merges OCR results (list of text snippets per page) into full-page text blocks.
    Returns a dict {page_idx: merged_text}.
    """
    merged_texts = {}
    for page_idx in sorted(ocr_results.keys()):
        ocr_texts = ocr_results[page_idx]
        merged = "\n".join(t.strip() for t in ocr_texts if t.strip())
        merged_texts[page_idx] = merged
    return merged_texts


def normalize_arabic(text):
    """
    Normalizes Arabic characters and removes OCR artifacts.
    """
    text = re.sub("[إأآا]", "ا", text)
    text = re.sub("ى", "ي", text)
    text = re.sub("ؤ", "و", text)
    text = re.sub("ئ", "ي", text)
    text = re.sub("ة", "ه", text)
    text = re.sub("[ًٌٍَُِّْ]", "", text)
    text = re.sub(r"[\|\)\(\:\-\;\\\/]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r'\b(\w+)\s+\1\b', r'\1', text)
    text = re.sub(r'[A-Za-z0-9]+', '', text)
    text=text.replace("[غير واضح]", "")
    return text.strip()


def postprocess_ocr_results(all_ocr_results):
    """
    End-to-end OCR postprocessing:
    1. Merge text boxes into full-page text.
    2. Clean HTML entities/tags.
    3. Normalize Arabic text.

    Args:
        all_ocr_results (dict[int, list[str]]): Raw OCR outputs per page.

    Returns:
        dict[int, str]: Cleaned, reconstructed text per page (keeps original page indices).
    """
    merged_pages = merge_page_texts(all_ocr_results)
    cleaned_pages = {}

    for idx in sorted(merged_pages.keys()):
        cleaned = reconstruct_html_content([merged_pages[idx]])[0]
        normalized = normalize_arabic(cleaned)
        cleaned_pages[idx] = normalized

    return cleaned_pages
