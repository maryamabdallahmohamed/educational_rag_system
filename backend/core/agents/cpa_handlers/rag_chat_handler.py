from typing import List, Dict, Any
from langchain.schema import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.tools import Tool
from langchain.memory import ConversationBufferWindowMemory
from backend.core.agents.base_handler import BaseHandler
from backend.core.states.graph_states import RAGState
from backend.models.llms.groq_llm import GroqLLM
from backend.models.reranker_model.reranker import Reranker
from backend.loaders.prompt_loaders.prompt_loader import PromptLoader


class RAGChatHandler(BaseHandler):
    """
    Handles both RAG-based conversational chat with documents and general chat
    """
    
    def __init__(self):
        super().__init__()
        self.llm_wrapper = GroqLLM()
        self.llm = self.llm_wrapper.llm
        self.reranker = Reranker()
        self.relevance_threshold = 0.5  # Lowered threshold for better flexibility
        self.memory = ConversationBufferWindowMemory(
            k=50,  
            return_messages=True
        )
        
        # Load RAG prompt
        rag_chat_template = PromptLoader.load_system_prompt("prompts/rag_chat.yaml")
        self.rag_chat_prompt = ChatPromptTemplate.from_messages([
            ("system", rag_chat_template),
            ("human", "{query}")
        ])
        
        # Load general chat prompt
        general_chat_template = PromptLoader.load_system_prompt("prompts/general_chat.yaml")
        self.general_chat_prompt = ChatPromptTemplate.from_messages([
            ("system", general_chat_template),
            ("human", "{query}")
        ])
        
        self.rag_chain = self.rag_chat_prompt | self.llm | StrOutputParser()
        self.general_chain = self.general_chat_prompt | self.llm | StrOutputParser()
    
    def tool(self) -> Tool:
        """Return configured LangChain Tool for chat (both RAG and general)"""
        return Tool(
            name="chat",
            description="Answer questions and engage in conversation. Can use uploaded documents when relevant, or provide general assistance for any topic.",
            func=self._process_wrapper
        )
    
    def _process_wrapper(self, query: str) -> str:
        """Wrapper for tool execution with error handling"""
        try:
            return self._process(query)
        except Exception as e:
            return self._handle_error(e, "chat")
    
    def _process(self, query: str) -> str:
        """Process chat request - either RAG-based or general chat"""
        try:
            documents = self.current_state.get('documents', [])
            conversation_history = self._get_conversation_history()
            
            # Determine if we should use RAG or general chat
            use_rag = self._should_use_rag(query, documents)
            
            if use_rag:
                # RAG mode: use documents
                context = self._prepare_context(documents, query)
                response = self._generate_rag_response(query, context, conversation_history)
                self.current_state["rag_context_used"] = True
                self.logger.info(f"Used RAG mode for query: {query[:50]}...")
            else:
                # General chat mode: no documents
                response = self._generate_general_response(query, conversation_history)
                self.current_state["rag_context_used"] = False
                self.logger.info(f"Used general chat mode for query: {query[:50]}...")
            
            # Update conversation memory
            self._update_memory(query, response)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error in chat processing: {e}")
            return f"I encountered an error while processing your question: {str(e)}"
    
    def _should_use_rag(self, query: str, documents: List[Document]) -> bool:
        """Determine if we should use RAG based on document availability and relevance"""
        try:
            # No documents available - use general chat
            if not documents:
                return False
            
            # Use reranker to check relevance
            reranked_docs = self.reranker.rerank_chunks(query, documents)
            
            # If no reranked docs or relevance is too low, use general chat
            if not reranked_docs:
                return False
                
            best_score = reranked_docs[0].metadata.get("rerank_score", 0)
            
            # Use RAG if relevance score meets threshold
            return best_score >= self.relevance_threshold
            
        except Exception as e:
            self.logger.error(f"Error determining RAG usage: {e}")
            # Default to general chat on error
            return False
    
    def _generate_general_response(self, query: str, history: str) -> str:
        """Generate general chat response without document context"""
        try:
            chain_input = {
                "query": query,
                "conversation_history": history
            }
            
            response = self.general_chain.invoke(chain_input)
            return response
            
        except Exception as e:
            self.logger.error(f"Error generating general response: {e}")
            return f"I'm sorry, I encountered an error while processing your question: {str(e)}"
    
    def _prepare_context(self, documents: List[Document], query: str) -> str:
        """Prepare context from documents for RAG using reranker"""
        try:
            # Use reranker to score and sort documents by relevance
            reranked_docs = self.reranker.rerank_chunks(query, documents)
            
            # Take top 3 most relevant documents
            top_docs = reranked_docs[:3]
            
            # Combine context
            context_parts = []
            for i, doc in enumerate(top_docs, 1):
                # Limit content length
                content = doc.page_content[:1000] + "..." if len(doc.page_content) > 1000 else doc.page_content
                
                # Add metadata if available
                source = doc.metadata.get("source", f"Document {i}")
                rerank_score = doc.metadata.get("rerank_score", 0.0)
                
                context_parts.append(f"Source: {source} (Relevance: {rerank_score:.3f})\nContent: {content}")
            
            return "\n\n---\n\n".join(context_parts)
            
        except Exception as e:
            self.logger.error(f"Error preparing context with reranker: {e}")
            # Fallback: use first few documents without reranking
            return "\n\n".join([doc.page_content[:500] for doc in documents[:2]])
    
    def _get_conversation_history(self) -> str:
        """Get conversation history from memory"""
        try:
            # Get conversation history from memory
            history = self.memory.chat_memory.messages
            if not history:
                return "No previous conversation."
            
            # Format history
            formatted_history = []
            for message in history[-6:]:  # Last 3 exchanges
                role = "Human" if message.type == "human" else "Assistant"
                formatted_history.append(f"{role}: {message.content}")
            
            return "\n".join(formatted_history)
            
        except Exception as e:
            self.logger.error(f"Error getting conversation history: {e}")
            return "No conversation history available."
    
    def _generate_rag_response(self, query: str, context: str, history: str) -> str:
        """Generate RAG-based response"""
        try:
            chain_input = {
                "query": query,
                "context": context,
                "conversation_history": history
            }
            
            response = self.rag_chain.invoke(chain_input)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error generating RAG response: {e}")
            return f"I'm sorry, I encountered an error while processing your question about the document: {str(e)}"
    
    def _update_memory(self, query: str, response: str):
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