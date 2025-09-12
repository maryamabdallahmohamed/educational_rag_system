from langchain_groq import ChatGroq
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from dotenv import load_dotenv
import os

from .base import BaseLLM


class GroqLLM(BaseLLM):
    """Groq-based LLM implementation using LangChain."""

    def __init__(self, model: str = "qwen/qwen3-32b",
                 temperature: float = 0,
                 max_tokens: int = None,
                 reasoning_format: str = "parsed",
                 timeout: int = None,
                 max_retries: int = 2):

        load_dotenv()
        api_key = os.getenv("grok_api")

        if not api_key:
            raise ValueError("❌ No Groq API key found. Set 'grok_api' in .env")

        self.llm = ChatGroq(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            reasoning_format=reasoning_format,
            timeout=timeout,
            max_retries=max_retries,
            api_key=api_key,
        )
    def invoke(self, messages) -> str:
        """
        Invoke Groq LLM with LangChain message objects.
        """
        ai_msg = self.llm.invoke(messages)
        return ai_msg.content

