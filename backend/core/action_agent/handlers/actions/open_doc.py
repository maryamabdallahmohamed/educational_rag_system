from typing import Dict, Any
import io
import base64

def open_doc_handler(pdf_pages: list) -> Dict[str, Any]:
    if not pdf_pages:
         return {
            "action": "open_doc",
            "status": "error",
            "details": "No pages to display."
        }
        
    encoded_images = []
    try:
        for page in pdf_pages:
            # Convert PIL Image to Bytes
            img_byte_arr = io.BytesIO()
            page.save(img_byte_arr, format='JPEG')
            img_byte_arr = img_byte_arr.getvalue()
            # Encode to Base64
            base64_encoded = base64.b64encode(img_byte_arr).decode('utf-8')
            encoded_images.append(base64_encoded)
            
        return {
            "action": "open_doc",
            "status": "success",
            "details": f"Opened {len(pdf_pages)} pages.",
            "images": encoded_images # List of base64 strings
        }
    except Exception as e:
         return {
            "action": "open_doc",
            "status": "error",
            "details": f"Failed to process images: {str(e)}"
        }