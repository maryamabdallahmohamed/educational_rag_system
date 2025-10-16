from langchain_core.tools import Tool
from backend.core.agents.base_handler import BaseHandler
from backend.core.rag.rag_orchestrator import RAGOrchestrator
from backend.database.repositories.cpa_repo import ContentProcessorAgentRepository
from backend.database.db import NeonDatabase
import time
import uuid
import asyncio
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
            func=self._process_wrapper,
            coroutine=self._process,
        )
    
    def _process_wrapper(self, query: str) -> str:
        """Wrapper for tool execution with error handling"""
        try:   
            # If already inside an event loop (e.g., FastAPI or async agent),
            # submit the coroutine to that loop and wait thread-safely.
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                # We're in an async context; schedule on this loop without creating a new one.
                future = asyncio.run_coroutine_threadsafe(self._process(query), loop)
                return future.result()
            else:
                # No running loop in this thread; safe to create one just for this call.
                return asyncio.run(self._process(query))
        except Exception as e:
            return self._handle_error(e, "rag_chat")
    
    async def _process(self, query: str) -> str:
        """Process RAG chat request using orchestrator with database tracking"""
        start_time = time.time()
        
        try:
            self.logger.info("Starting RAG query processing")

            # Use the orchestrator to handle the complete RAG pipeline
            # The orchestrator returns the response and internally handles retrieval
            response = await self.rag_orchestrator.process_query(query)

            # Get retrieval metadata from orchestrator if available
            retrieval_info = self.rag_orchestrator.get_last_retrieval_info()
            
            # Extract chunk information
            chunk_ids = retrieval_info.get("chunk_ids", [])
            similarity_scores = retrieval_info.get("similarity_scores", [])

            # Calculate processing time
            processing_time = int((time.time() - start_time) * 1000)

            # Save to database
            if chunk_ids: 
                await self._save_to_database(
                    query=query,
                    response=response,
                    chunk_ids=chunk_ids,
                    similarity_scores=similarity_scores,
                    processing_time=processing_time
                )

            # Update state
            self.current_state["rag_context_used"] = True
            self.logger.info(f"Processed RAG query in {processing_time}ms")

            return response

        except Exception as e:
            self.logger.error(f"Error in RAG chat processing: {e}")
            return f"I encountered an error while processing your question about the documents: {str(e)}"

    async def _save_to_database(
        self,
        query: str,
        response: str,
        chunk_ids: list,
        similarity_scores: list,
        processing_time: int
    ) -> uuid.UUID:
        """
        Save RAG operation to database
        Returns the CPA session ID
        """
        try:
            async with NeonDatabase.get_session() as session:
                cpa_repo = ContentProcessorAgentRepository(session=session)

                # Create CPA session record for RAG operation
                cpa_record = await cpa_repo.create(
                    query=query,
                    response=response,
                    tool_used="rag_chat",
                    chunks_used=chunk_ids,
                    similarity_scores=similarity_scores,
                    units_generated_count=None
                )

                self.logger.info(f"Saved RAG operation to database: {cpa_record.id}")
                
                # Store session ID in state for reference
                if self.current_state:
                    self.current_state["cpa_session_id"] = str(cpa_record.id)
                
                return cpa_record.id

        except Exception as e:
            self.logger.error(f"Error saving RAG operation to database: {e}")
            # Don't raise - we don't want DB errors to break the user response
            return None

    async def check_relevance(self, query: str) -> tuple:
        """
        Check if query has relevant content
        Returns: (has_relevant, similarity_scores, chunk_ids, tool_name)
        """
        try:
            # Use orchestrator to check relevance
            has_relevant = await self.rag_orchestrator.check_query_relevance(query)
            
            # Get retrieval info if available
            retrieval_info = self.rag_orchestrator.get_last_retrieval_info()
            chunk_ids = retrieval_info.get("chunk_ids", [])
            scores = retrieval_info.get("similarity_scores", [])
            
            return has_relevant, scores, chunk_ids, "rag_chat"
            
        except Exception as e:
            self.logger.error(f"Error checking relevance: {e}")
            return False, [], [], "rag_chat"

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