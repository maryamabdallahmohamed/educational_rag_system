"""
Arabic Data Ingestion Script

This script converts the Arabic JSON learning unit into a formatted text file
and uploads it to the RAG system for indexing.

Run with: python ingest_ar_data.py
Requires the server to be running: uvicorn backend.api.main:app --port 8000
"""

import json
import requests
import os

# Configuration
API_URL = "http://localhost:8000/api"
JSON_FILE = "photosynthesis_unit_ar.json"


def ingest_data():
    """Ingest Arabic educational content into the RAG system."""
    
    print("=" * 60)
    print("  ARABIC CONTENT INGESTION")
    print("  Ingesting: عملية البناء الضوئي (Photosynthesis)")
    print("=" * 60)
    
    # Step 1: Read JSON file
    print(f"\n--- 1. Reading {JSON_FILE} ---")
    try:
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"✅ Loaded: {data['title']}")
    except FileNotFoundError:
        print(f"❌ File not found: {JSON_FILE}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}")
        return None

    # Step 2: Format text content for RAG (Arabic Context)
    print("\n--- 2. Formatting Arabic Content ---")
    
    text_content = f"""الموضوع: {data['title']}
المستوى: {data['difficulty']}

الملخص:
{data['summary']}

المفاهيم الأساسية:
"""
    for i, point in enumerate(data['key_points'], 1):
        text_content += f"{i}. {point}\n"
    
    text_content += "\nأسئلة وأجوبة شائعة:\n"
    for pair in data['qa_pairs']:
        text_content += f"\nسؤال: {pair['q']}\n"
        text_content += f"جواب: {pair['a']}\n"
    
    print("✅ Content formatted successfully")
    print(f"   Content length: {len(text_content)} characters")

    # Step 3: Save as temporary file
    temp_filename = "photosynthesis_ar_export.txt"
    with open(temp_filename, "w", encoding="utf-8") as f:
        f.write(text_content)
    print(f"✅ Saved temporary file: {temp_filename}")

    # Step 4: Upload to RAG System
    print("\n--- 3. Uploading to RAG System ---")
    
    try:
        with open(temp_filename, "rb") as f:
            files = {"file": (temp_filename, f, "text/plain; charset=utf-8")}
            response = requests.post(f"{API_URL}/upload", files=files, timeout=120)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Successfully ingested!")
                print(f"   Response: {json.dumps(result, ensure_ascii=False, indent=2)}")
                return data['title']
            else:
                print(f"❌ Upload failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return None
                
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Is it running?")
        print("   Run: uvicorn backend.api.main:app --port 8000")
        return None
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return None
    finally:
        # Cleanup temporary file
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
            print(f"✅ Cleaned up temporary file")


def verify_ingestion():
    """Verify the Arabic content was indexed correctly."""
    print("\n--- 4. Verifying Ingestion ---")
    
    try:
        # Try a simple search to verify Arabic content is indexed
        # This depends on your API structure
        response = requests.get(f"{API_URL}/documents", timeout=10)
        if response.status_code == 200:
            docs = response.json()
            print(f"✅ Documents in system: {len(docs) if isinstance(docs, list) else docs}")
        else:
            print(f"⚠️ Could not verify documents: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Verification skipped: {e}")


if __name__ == "__main__":
    title = ingest_data()
    
    if title:
        verify_ingestion()
        print("\n" + "=" * 60)
        print("  INGESTION COMPLETE")
        print(f"  Topic: {title}")
        print("  Next: Run test_tutor_ar.py to test Arabic interactions")
        print("=" * 60)
    else:
        print("\n❌ Ingestion failed. Check errors above.")
