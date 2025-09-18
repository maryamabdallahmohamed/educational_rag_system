from abc import ABC, abstractmethod
from typing import List


class BaseLLM(ABC):
    """Abstract base class for all LLMs."""

    @abstractmethod
    def invoke(self, messages: List[dict]) -> str:
        """
        Invoke the LLM with a sequence of messages.

        Args:
            messages (List[dict]): Conversation history in role-content format.
                Example: [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]

        Returns:
            str: The LLM's response text.
        """
        pass
