from typing import List
from .base import BaseLLM
from dotenv import load_dotenv
import os
from langchain_ollama import ChatOllama

load_dotenv()
class OllamaLLM(BaseLLM):

    def __init__(
        self,
        model: str = 'gpt-oss:120b-cloud',
        temperature: float = 0,
        api_key: str = None,
        base_url: str = None,
        timeout: int = 120
    ):
        api_key = api_key or os.getenv("OLLAMA_API_KEY")
        base_url = os.getenv("OLLAMA_BASE_URL")

        self.llm = ChatOllama(
            model=model,
            temperature=temperature,
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
        )

    def invoke(self, messages: List[dict]) -> str:
        ai_msg = self.llm.invoke(messages)
        return ai_msg.content


if __name__ == "__main__":
    llm = OllamaLLM()
    response = llm.invoke([{"role": "user", "content": "Hello, how are you?"}])
    print(response) 
