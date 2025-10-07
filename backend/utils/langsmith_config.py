"""
LangSmith Configuration and Utilities

Handles LangSmith setup, configuration, and helper functions for tracing.
Works gracefully even when LangSmith is not configured.
"""
import os
from typing import Optional
from backend.utils.logger_config import get_logger

logger = get_logger("langsmith_config")


def is_langsmith_enabled() -> bool:
    """
    Check if LangSmith tracing is enabled.
    
    Returns:
        bool: True if LangSmith is properly configured, False otherwise
    """
    api_key = os.getenv("LANGSMITH_API_KEY", "").strip()
    tracing_enabled = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
    
    return bool(api_key) and tracing_enabled


def get_langsmith_project() -> Optional[str]:
    """
    Get the LangSmith project name from environment.
    
    Returns:
        Optional[str]: Project name or None if not configured
    """
    return os.getenv("LANGCHAIN_PROJECT", "educational-rag-system")


def get_langsmith_endpoint() -> str:
    """
    Get the LangSmith API endpoint.
    
    Returns:
        str: LangSmith API endpoint URL
    """
    return os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")


def setup_langsmith() -> None:
    """
    Setup and validate LangSmith configuration.
    Prints status information about LangSmith availability.
    """
    if is_langsmith_enabled():
        project = get_langsmith_project()
        endpoint = get_langsmith_endpoint()
        
        logger.info("=" * 70)
        logger.info("🔍 LangSmith Tracing ENABLED")
        logger.info(f"   Project: {project}")
        logger.info(f"   Endpoint: {endpoint}")
        logger.info(f"   View traces at: https://smith.langchain.com")
        logger.info("=" * 70)
        
        # Set environment variables for LangChain components
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_PROJECT"] = project
        os.environ["LANGCHAIN_ENDPOINT"] = endpoint
    else:
        logger.info("=" * 70)
        logger.info("ℹ️  LangSmith Tracing DISABLED")
        logger.info("   Agents will work normally without tracing")
        logger.info("   To enable: Set LANGSMITH_API_KEY and LANGCHAIN_TRACING_V2=true")
        logger.info("=" * 70)


def get_langsmith_url(run_id: str) -> str:
    """
    Generate LangSmith URL for a specific run.
    
    Args:
        run_id: The LangSmith run ID
        
    Returns:
        str: Full URL to view the run in LangSmith
    """
    if not run_id:
        return "https://smith.langchain.com"
    
    project = get_langsmith_project()
    # URL format: https://smith.langchain.com/o/{org}/projects/p/{project}/r/{run_id}
    # Simplified version
    return f"https://smith.langchain.com/public/{run_id}/r"


def get_run_metadata(state: dict) -> dict:
    """
    Extract useful metadata from state for LangSmith traces.
    
    Args:
        state: The current RAG state
        
    Returns:
        dict: Metadata dictionary for tracing
    """
    metadata = {
        "query_length": len(state.get("query", "")),
        "has_documents": bool(state.get("documents")),
        "has_learner_profile": bool(state.get("learner_profile")),
    }
    
    # Add learner-specific metadata if available
    learner_profile = state.get("learner_profile", {})
    if learner_profile:
        metadata.update({
            "learner_id": state.get("learner_id", "unknown"),
            "grade_level": learner_profile.get("grade_level", "unknown"),
            "learning_style": learner_profile.get("learning_style", "unknown"),
            "accuracy_rate": learner_profile.get("accuracy_rate", 0.0),
            "difficulty_preference": learner_profile.get("difficulty_preference", "medium"),
        })
    
    # Add session info if available
    if state.get("tutoring_session_id"):
        metadata["session_id"] = state.get("tutoring_session_id")
    
    return metadata


# Auto-setup on import
setup_langsmith()
