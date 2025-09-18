from abc import ABC, abstractmethod
from typing import Optional
from langchain_core.tools import Tool
from backend.core.states.graph_states import RAGState
from backend.utils.logger_config import get_logger


class BaseHandler(ABC):
    """
    Abstract base class for all content processing handlers.
    Provides consistent interface and state management for tool-based agents.
    """
    
    def __init__(self):
        self.current_state: Optional[RAGState] = None
        self.logger = get_logger(self.__class__.__name__)
    
    @abstractmethod
    def tool(self) -> Tool:
        """
        Return a LangChain Tool for this handler.
        Must be implemented by all handler subclasses.
        """
        pass
    
    def set_state(self, state: RAGState):
        """Set the current state for processing"""
        self.current_state = state
        self.logger.debug(f"State set for {self.__class__.__name__}")
    
    def get_state(self) -> Optional[RAGState]:
        """Get the current state"""
        return self.current_state
    
    def _handle_error(self, error: Exception, context: str = "") -> str:
        """
        Consistent error handling for all handlers.
        Returns user-friendly error message.
        """
        error_msg = f"Error in {self.__class__.__name__}"
        if context:
            error_msg += f" ({context})"
        error_msg += f": {str(error)}"
        
        self.logger.error(error_msg)
        
        # Return user-friendly message
        return f"I encountered an error while processing your request. Please try again or rephrase your question."
    
    def _validate_state(self) -> bool:
        """Validate that state is available and contains required data"""
        if not self.current_state:
            self.logger.error("No state available for processing")
            return False
        return True