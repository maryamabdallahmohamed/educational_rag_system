from abc import ABC, abstractmethod
from typing import List, Union
import numpy as np

class BaseEmbedder(ABC):
    """Abstract base class for all embedders."""

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> Union[List[List[float]], np.ndarray]:
        """
        Convert a list of texts into embeddings.

        Args:
            texts (List[str]): List of strings to embed.

        Returns:
            Union[List[List[float]], np.ndarray]: Embedding vectors.
        """
        pass

    @abstractmethod
    def embed_query(self, emb1: Union[List[float], np.ndarray],emb2: Union[List[float], np.ndarray]) -> float:
        pass
