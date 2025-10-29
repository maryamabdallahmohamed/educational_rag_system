from langchain.schema import Document

class DocumentBuilder:
    def __init__(self):
        self._content = None
        self._metadata = {}

    def set_content(self, content: str):
        self._content = content
        return self

    def add_metadata(self, key: str, value):
        self._metadata[key] = value
        return self

    def set_metadata(self, metadata: dict):
        self._metadata.update(metadata)
        return self

    def build(self) -> Document:
        if not self._content:
            raise ValueError("Document content must be set before building.")
        return Document(page_content=self._content, metadata=self._metadata)
