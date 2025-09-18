from typing import List
from langchain.schema import Document
from langchain_core.tools import Tool
from backend.core.agents.base_handler import BaseHandler
from backend.models.reranker_model.reranker import Reranker


class DocumentAnalysisHandler(BaseHandler):
    """
    Handler for analyzing document relevance and providing document insights
    """
    
    def __init__(self):
        super().__init__()
        self.reranker = Reranker()
        self.relevance_threshold = 0.7
    
    def tool(self) -> Tool:
        """Return configured LangChain Tool for document analysis"""
        return Tool(
            name="document_analysis",
            description="Analyze available documents and their relevance to a query. Use this to understand what documents are available and how relevant they are.",
            func=self._process_wrapper
        )
    
    def _process_wrapper(self, query: str) -> str:
        try:
            if not self._validate_state():
                return "No documents available for analysis."
            
            return self._process(query)
        except Exception as e:
            return self._handle_error(e, "document analysis")
    
    def _process(self, query: str) -> str:
        """Analyze documents and their relevance to the query"""
        try:
            documents = self.current_state.get("documents", [])
            # Combine all documents
            all_documents = documents
            
            if not all_documents:
                return "No documents available for analysis."
            
            # Analyze documents with reranker
            reranked_docs = self.reranker.rerank_chunks(query, all_documents)
            
            # Build analysis report
            analysis = self._build_analysis_report(query, all_documents, reranked_docs)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error in document analysis: {e}")
            return f"Error analyzing documents: {str(e)}"
    
    def _build_analysis_report(self, query: str, all_documents: List[Document], reranked_docs: List[Document]) -> str:
        """Build comprehensive document analysis report"""
        analysis_parts = []
        
        # Header
        analysis_parts.append("📊 Document Analysis Report")
        analysis_parts.append("=" * 40)
        
        # Basic statistics
        analysis_parts.append(f"📁 Total documents: {len(all_documents)}")
        analysis_parts.append(f"🎯 Query: '{query}'")
        analysis_parts.append(f"📏 Relevance threshold: {self.relevance_threshold}")
        
        if reranked_docs:
            top_score = reranked_docs[0].metadata.get('rerank_score', 0)
            analysis_parts.append(f"⭐ Highest relevance score: {top_score:.3f}")
            analysis_parts.append(f"✅ Documents meet threshold: {'Yes' if top_score >= self.relevance_threshold else 'No'}")
        
        analysis_parts.append("")
        
        # Document details
        analysis_parts.append("📋 Document Details:")
        analysis_parts.append("-" * 20)
        
        for i, doc in enumerate(reranked_docs[:5], 1):  # Top 5 documents
            score = doc.metadata.get('rerank_score', 0)
            source = doc.metadata.get('source', f'Document {i}')
            
            # Content preview
            content_preview = doc.page_content[:150].replace('\n', ' ')
            if len(doc.page_content) > 150:
                content_preview += "..."
            
            # Relevance indicator
            relevance_indicator = "🟢" if score >= self.relevance_threshold else "🟡" if score >= 0.5 else "🔴"
            
            analysis_parts.append(f"{relevance_indicator} Document {i}: {source}")
            analysis_parts.append(f"   Score: {score:.3f}")
            analysis_parts.append(f"   Preview: {content_preview}")
            analysis_parts.append("")
        
        # Recommendations
        analysis_parts.append("💡 Recommendations:")
        analysis_parts.append("-" * 20)
        
        if reranked_docs and reranked_docs[0].metadata.get('rerank_score', 0) >= self.relevance_threshold:
            analysis_parts.append("✅ Documents are relevant for RAG chat")
            analysis_parts.append("✅ You can ask specific questions about the content")
            analysis_parts.append("✅ Consider generating learning units from this content")
        else:
            analysis_parts.append("⚠️  Documents may not be highly relevant to your query")
            analysis_parts.append("💭 Try rephrasing your question")
            analysis_parts.append("📤 Consider uploading more relevant documents")
            analysis_parts.append("🤔 You can still ask general questions using my knowledge")
        
        return "\n".join(analysis_parts)