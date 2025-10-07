"""
Shared pytest configuration and fixtures for the educational RAG system tests
"""

import pytest
import asyncio
import uuid
from unittest.mock import AsyncMock, patch

from backend.database.db import NeonDatabase


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Mock database initialization for testing"""
    with patch('backend.database.db.NeonDatabase.init') as mock_init:
        mock_init.return_value = None
        yield
    # Cleanup code can go here if needed


@pytest.fixture
def mock_database_session():
    """Mock database session for testing"""
    with patch('backend.database.db.NeonDatabase.get_session') as mock_session:
        async_mock = AsyncMock()
        mock_session.return_value.__aenter__.return_value = async_mock
        yield async_mock


@pytest.fixture
def sample_learner_id():
    """Generate a sample learner ID"""
    return str(uuid.uuid4())


@pytest.fixture
def sample_session_id():
    """Generate a sample session ID"""
    return str(uuid.uuid4())


@pytest.fixture
def sample_learner_data():
    """Sample learner profile data for testing"""
    return {
        "name": "Test Learner",
        "grade_level": "10th Grade",
        "learning_style": "Visual",
        "preferred_language": "English",
        "subjects_of_interest": ["Mathematics", "Physics"],
        "learning_goals": ["Improve problem solving"],
        "accessibility_needs": {"screen_reader": True}
    }


@pytest.fixture
def sample_session_data(sample_learner_id):
    """Sample tutoring session data for testing"""
    return {
        "learner_id": sample_learner_id,
        "subject": "Mathematics",
        "topic": "Quadratic Equations",
        "difficulty_level": "medium",
        "learning_objectives": ["Solve quadratic equations"],
        "session_metadata": {"platform": "test"}
    }


@pytest.fixture
def sample_interaction_data(sample_session_id, sample_learner_id):
    """Sample interaction data for testing"""
    return {
        "session_id": sample_session_id,
        "learner_id": sample_learner_id,
        "interaction_type": "question_answer",
        "user_input": "How do I solve x² + 5x + 6 = 0?",
        "agent_response": "Factor as (x + 2)(x + 3) = 0",
        "response_time": 2.5,
        "difficulty_rating": "medium",
        "correctness_assessment": "correct",
        "interaction_metadata": {"method": "factoring"}
    }
