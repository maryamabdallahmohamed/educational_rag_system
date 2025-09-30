from typing import Dict, Any, Union
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser, PydanticOutputParser
from langchain.memory import ConversationBufferWindowMemory
from backend.models.llms.groq_llm import GroqLLM
from backend.loaders.prompt_loaders.prompt_loader import PromptLoader
from backend.core.states.graph_states import LearningUnit
import logging


class RAGResponseGenerator:
    """Handles response generation using LLM with context"""

    def __init__(self, use_json_output: bool = False, use_learning_unit: bool = False):
        self.llm_wrapper = GroqLLM()
        self.llm = self.llm_wrapper.llm
        self.logger = logging.getLogger(__name__)
        self.use_json_output = use_json_output
        self.use_learning_unit = use_learning_unit

        # Memory for conversation history
        self.memory = ConversationBufferWindowMemory(
            k=50,
            return_messages=True
        )

        # Load and setup RAG prompt
        self._setup_prompt_chain()

    def _setup_prompt_chain(self):
        """Setup the prompt chain for RAG"""
        try:
            rag_chat_template = PromptLoader.load_system_prompt("prompts/rag_chat.yaml")

            # Choose output parser and modify prompt based on configuration
            if self.use_learning_unit:
                # Use Pydantic output parser for LearningUnit
                output_parser = PydanticOutputParser(pydantic_object=LearningUnit)
                rag_chat_template += "\n\nFormat your response as a structured learning unit with the following JSON schema:\n"
                rag_chat_template += output_parser.get_format_instructions()
            elif self.use_json_output:
                # Use basic JSON output parser
                output_parser = JsonOutputParser()
                rag_chat_template += "\n\nFormat your response as JSON with this structure:\n"
                rag_chat_template += '{"response": "your answer here", "sources_referenced": ["source1", "source2"], "confidence": "high/medium/low"}'
            else:
                # Use string output parser
                output_parser = StrOutputParser()

            self.rag_chat_prompt = ChatPromptTemplate.from_messages([
                ("system", rag_chat_template),
                ("human", "{query}")
            ])

            self.rag_chain = self.rag_chat_prompt | self.llm | output_parser

            parser_type = "LearningUnit" if self.use_learning_unit else ("JSON" if self.use_json_output else "String")
            self.logger.info(f"RAG prompt chain setup successfully with {parser_type} output parser")

        except Exception as e:
            self.logger.error(f"Error setting up prompt chain: {e}")
            # Fallback to simple prompt
            system_prompt = "Answer the user's question based on the provided context."

            if self.use_learning_unit:
                output_parser = PydanticOutputParser(pydantic_object=LearningUnit)
                system_prompt += f"\n\nFormat as LearningUnit JSON:\n{output_parser.get_format_instructions()}"
            elif self.use_json_output:
                output_parser = JsonOutputParser()
                system_prompt += ' Format your response as JSON: {"response": "your answer", "confidence": "high/medium/low"}'
            else:
                output_parser = StrOutputParser()

            self.rag_chat_prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("human", "{query}")
            ])

            self.rag_chain = self.rag_chat_prompt | self.llm | output_parser

    def generate_response(self, query: str, context: str, conversation_history: str = None) -> Union[str, Dict[str, Any], LearningUnit]:
        """Generate response using RAG chain"""
        try:
            chain_input = {
                "query": query,
                "context": context,
                "conversation_history": conversation_history or "No previous conversation."
            }

            response = self.rag_chain.invoke(chain_input)

            # Extract text for memory update
            if isinstance(response, LearningUnit):
                response_text = f"{response.title}: {response.detailed_explanation}"
            elif isinstance(response, str):
                response_text = response
            else:
                response_text = response.get("response", str(response))

            self.update_memory(query, response_text)

            self.logger.info(f"Generated response for query: {query[:50]}...")
            return response

        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            error_msg = f"I'm sorry, I encountered an error while processing your question: {str(e)}"

            if self.use_learning_unit:
                return LearningUnit(
                    title="Error in Processing",
                    subtopics=["Error handling"],
                    detailed_explanation=error_msg,
                    key_points=[error_msg],
                    difficulty_level="easy",
                    learning_objectives=["Understand error occurred"],
                    keywords=["error"]
                )
            elif self.use_json_output:
                return {
                    "response": error_msg,
                    "sources_referenced": [],
                    "confidence": "low"
                }
            else:
                return error_msg

    def generate_structured_response(self, query: str, structured_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate structured response with metadata"""
        try:
            context = structured_context.get("context", "")
            sources = structured_context.get("sources", [])

            conversation_history = self.get_conversation_history()
            response_text = self.generate_response(query, context, conversation_history)

            return {
                "response": response_text,
                "sources_used": sources,
                "total_sources": len(sources),
                "context_length": len(context)
            }

        except Exception as e:
            self.logger.error(f"Error generating structured response: {e}")
            return {
                "response": f"Error generating response: {str(e)}",
                "sources_used": [],
                "total_sources": 0,
                "context_length": 0
            }

    def get_conversation_history(self) -> str:
        """Get formatted conversation history"""
        try:
            history = self.memory.chat_memory.messages
            if not history:
                return "No previous conversation."

            # Format last 6 messages (3 exchanges)
            formatted_history = []
            for message in history[-6:]:
                role = "Human" if message.type == "human" else "Assistant"
                formatted_history.append(f"{role}: {message.content}")

            return "\n".join(formatted_history)

        except Exception as e:
            self.logger.error(f"Error getting conversation history: {e}")
            return "No conversation history available."

    def update_memory(self, query: str, response: str):
        """Update conversation memory"""
        try:
            self.memory.chat_memory.add_user_message(query)
            self.memory.chat_memory.add_ai_message(response)
        except Exception as e:
            self.logger.error(f"Error updating memory: {e}")

    def clear_memory(self):
        """Clear conversation memory"""
        self.memory.clear()
        self.logger.info("Conversation memory cleared")