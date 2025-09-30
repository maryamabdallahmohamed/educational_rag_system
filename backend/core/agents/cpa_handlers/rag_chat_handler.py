from langchain_core.tools import Tool
from backend.core.agents.base_handler import BaseHandler
from backend.core.rag.rag_orchestrator import RAGOrchestrator
class RAGChatHandler(BaseHandler):
    """
    Handles RAG-based conversational chat with documents only
    """

    def __init__(self, similarity_threshold: float = 0.3, use_json_output: bool = False, use_learning_unit: bool = False):
        super().__init__()
        self.rag_orchestrator = RAGOrchestrator(
            similarity_threshold=similarity_threshold,
            top_k=10,
            max_context_docs=5,
            max_content_length=1000,
            use_json_output=use_json_output,
            use_learning_unit=use_learning_unit
        )
    
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
            import asyncio
            return asyncio.run(self._process(query))
        except Exception as e:
            return self._handle_error(e, "rag_chat")
    
    async def _process(self, query: str) -> str:
        """Process RAG chat request using orchestrator"""
        try:
            # Use the orchestrator to handle the complete RAG pipeline
            response = await self.rag_orchestrator.process_query(query)

            # Update state
            self.current_state["rag_context_used"] = True
            self.logger.info(f"Processed RAG query: {query[:50]}...")

            return response

        except Exception as e:
            self.logger.error(f"Error in RAG chat processing: {e}")
            return f"I encountered an error while processing your question about the documents: {str(e)}"

    async def check_relevance(self, query: str) -> bool:
        """Check if query has relevant content"""
        return await self.rag_orchestrator.check_query_relevance(query)

    def get_pipeline_info(self) -> dict:
        """Get RAG pipeline configuration info"""
        return self.rag_orchestrator.get_pipeline_info()

    def update_configuration(self, **kwargs):
        """Update RAG pipeline configuration"""
        self.rag_orchestrator.update_configuration(**kwargs)

    def clear_memory(self):
        """Clear conversation memory"""
        self.rag_orchestrator.clear_conversation_history()
        self.logger.info("Conversation memory cleared")