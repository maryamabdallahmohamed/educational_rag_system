from typing import List, Dict, Any
from langchain.schema import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.tools import Tool
from langchain.memory import ConversationBufferWindowMemory
from backend.core.agents.base_handler import BaseHandler
from backend.models.llms.groq_llm import GroqLLM
from backend.models.reranker_model.reranker import Reranker
from backend.loaders.prompt_loaders.prompt_loader import PromptLoader


class RAGChatHandler(BaseHandler):
    """
    Handles RAG-based conversational chat with documents only
    """
    
    def __init__(self):
        super().__init__()
        self.llm_wrapper = GroqLLM()
        self.llm = self.llm_wrapper.llm
        self.reranker = Reranker()
        self.relevance_threshold = 0.5 
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
        
        self.rag_chain = self.rag_chat_prompt | self.llm | StrOutputParser()
    
    def tool(self) -> Tool:
        """Return configured LangChain Tool for RAG chat"""
        return Tool(
            name="rag_chat",
            description="Answer questions about uploaded documents using RAG (Retrieval-Augmented Generation). Requires documents to be available.",
            func=self._process_wrapper
        )
    
    def _process_wrapper(self, query: str) -> str:
        """Wrapper for tool execution with error handling"""
        try:
            return self._process(query)
        except Exception as e:
            return self._handle_error(e, "rag_chat")
    
    def _process(self, query: str) -> str:
        """Process RAG chat request"""
        try:
            documents = self.current_state.get('documents', [])
            
            # Check if documents are available
            if not documents:
                return "I don't have any documents to reference. Please upload documents first before asking questions about their content."
            
            # Check document relevance
            if not self._has_relevant_content(query, documents):
                return "I couldn't find relevant information in the uploaded documents to answer your question. Please try rephrasing your question or check if the documents contain the information you're looking for."
            
            conversation_history = self._get_conversation_history()
            context = self._prepare_context(documents, query)
            response = self._generate_rag_response(query, context, conversation_history)
            
            # Update state and memory
            self.current_state["rag_context_used"] = True
            self._update_memory(query, response)
            
            self.logger.info(f"Processed RAG query: {query[:50]}...")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error in RAG chat processing: {e}")
            return f"I encountered an error while processing your question about the documents: {str(e)}"
    
    def _has_relevant_content(self, query: str, documents: List[Document]) -> bool:
        """Check if documents have relevant content for the query"""
        try:
            # Use reranker to check relevance
            reranked_docs = self.reranker.rerank_chunks(query, documents)
            
            # If no reranked docs or relevance is too low, return False
            if not reranked_docs:
                return False
                
            best_score = reranked_docs[0].metadata.get("rerank_score", 0)
            
            # Check if relevance score meets threshold
            return best_score >= self.relevance_threshold
            
        except Exception as e:
            self.logger.error(f"Error checking content relevance: {e}")
            # Default to True to allow processing, let the RAG chain handle it
            return True
    
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