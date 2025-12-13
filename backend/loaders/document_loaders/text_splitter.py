from langchain_text_splitters import RecursiveCharacterTextSplitter
import re

def document_chunk(text: str, chunk_size: int = 200, chunk_overlap: int = 30) -> list[str]:

    text = re.sub(r'\s+', ' ', text.strip())
    splitter = RecursiveCharacterTextSplitter(
        separators=[" ", "\n\n", "\n", ".", "،", "؟", ";", ","], 
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=lambda x: len(x.split(" ")), 
        is_separator_regex=False,
    )

    chunks = splitter.split_text(text)
    return chunks
