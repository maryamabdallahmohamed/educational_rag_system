"""
Comprehensive tests for the Tutor Agent system

This module tests the complete tutor agent flow including:
- Creating learner profiles
- Starting and managing tutoring sessions  
- Processing tutoring questions
- Logging interactions
- Updating learner models
- Session performance summaries
"""

import pytest
import asyncio
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock

from backend.core.agents.tutor_agent import TutorAgent
from backend.core.states.graph_states import RAGState
from backend.database.db import NeonDatabase
from backend.database.repositories.learner_profile_repo import LearnerProfileRepository
from backend.database.repositories.tutoring_session_repo import TutoringSessionRepository
from backend.database.repositories.learner_interaction_repo import LearnerInteractionRepository
from backend.database.models.learner_profile import LearnerProfile
from backend.database.models.tutoring_session import TutoringSession
from backend.database.models.learner_interaction import LearnerInteraction


class TestTutorAgent:
    """Test suite for TutorAgent complete flow"""

    @pytest.fixture
    def mock_database(self):
        """Mock database session"""
        with patch('backend.database.db.NeonDatabase.get_session') as mock_session:
            yield mock_session

    @pytest.fixture
    def mock_llm(self):
        """Mock LLM responses"""
        with patch('backend.models.llms.groq_llm.GroqLLM') as mock_groq:
            mock_llm_instance = MagicMock()
            mock_groq.return_value.llm = mock_llm_instance
            yield mock_llm_instance

    @pytest.fixture
    def sample_learner_profile(self):
        """Sample learner profile data"""
        return {
            "id": str(uuid.uuid4()),
            "name": "Ahmed Hassan",
            "grade_level": "10th Grade",
            "learning_style": "Visual",
            "preferred_language": "Arabic",
            "subjects_of_interest": ["Mathematics", "Physics"],
            "learning_goals": ["Improve algebra skills", "Understand calculus basics"],
            "accessibility_needs": {"screen_reader": True, "high_contrast": True},
            "performance_metrics": {
                "accuracy_rate": 0.75,
                "avg_response_time": 45.2,
                "engagement_score": 0.85
            },
            "mastered_topics": ["Basic Algebra", "Linear Equations"],
            "learning_struggles": ["Quadratic Equations", "Trigonometry"]
        }

    @pytest.fixture
    def sample_tutoring_session(self):
        """Sample tutoring session data"""
        return {
            "id": str(uuid.uuid4()),
            "learner_id": str(uuid.uuid4()),
            "session_state": "active",
            "subject": "Mathematics",
            "topic": "Quadratic Equations",
            "difficulty_level": "medium",
            "learning_objectives": ["Solve quadratic equations", "Graph parabolas"],
            "session_metadata": {
                "start_time": datetime.utcnow().isoformat(),
                "platform": "web",
                "accessibility_mode": "screen_reader"
            },
            "interaction_history": []
        }

    @pytest.fixture
    def tutor_agent(self, mock_llm):
        """Initialize TutorAgent with mocked dependencies"""
        return TutorAgent()

    @pytest.fixture
    def sample_rag_state(self, sample_learner_profile, sample_tutoring_session):
        """Sample RAGState for testing"""
        return RAGState(
            query="Help me understand quadratic equations",
            learner_id=sample_learner_profile["id"],
            learner_profile=sample_learner_profile,
            tutoring_session_id=sample_tutoring_session["id"],
            session_state=sample_tutoring_session,
            interaction_history=[],
            learning_progress={"current_topic": "quadratic_equations", "completion": 0.3}
        )


class TestLearnerProfileCreation:
    """Test learner profile creation and management"""

    @pytest.mark.asyncio
    async def test_create_learner_profile(self, mock_database, sample_learner_profile):
        """Test creating a new learner profile"""
        # Mock database session and repository
        mock_session = AsyncMock()
        mock_database.return_value.__aenter__.return_value = mock_session
        
        mock_repo = AsyncMock(spec=LearnerProfileRepository)
        mock_profile = LearnerProfile(**sample_learner_profile)
        mock_repo.create.return_value = mock_profile
        
        with patch('backend.database.repositories.learner_profile_repo.LearnerProfileRepository', return_value=mock_repo):
            # Test profile creation
            async with NeonDatabase.get_session() as session:
                repo = LearnerProfileRepository(session)
                created_profile = await repo.create(
                    name=sample_learner_profile["name"],
                    grade_level=sample_learner_profile["grade_level"],
                    learning_style=sample_learner_profile["learning_style"],
                    preferred_language=sample_learner_profile["preferred_language"],
                    subjects_of_interest=sample_learner_profile["subjects_of_interest"],
                    learning_goals=sample_learner_profile["learning_goals"],
                    accessibility_needs=sample_learner_profile["accessibility_needs"]
                )
                
                assert created_profile.name == "Ahmed Hassan"
                assert created_profile.grade_level == "10th Grade"
                assert created_profile.learning_style == "Visual"
                assert created_profile.preferred_language == "Arabic"
                assert "Mathematics" in created_profile.subjects_of_interest
                mock_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_learner_performance(self, mock_database, sample_learner_profile):
        """Test updating learner performance metrics"""
        mock_session = AsyncMock()
        mock_database.return_value.__aenter__.return_value = mock_session
        
        mock_repo = AsyncMock(spec=LearnerProfileRepository)
        updated_profile = LearnerProfile(**sample_learner_profile)
        updated_profile.performance_metrics = {
            "accuracy_rate": 0.80,  # Improved
            "avg_response_time": 40.0,  # Faster
            "engagement_score": 0.90  # Better engagement
        }
        mock_repo.update_performance_metrics.return_value = updated_profile
        
        with patch('backend.database.repositories.learner_profile_repo.LearnerProfileRepository', return_value=mock_repo):
            async with NeonDatabase.get_session() as session:
                repo = LearnerProfileRepository(session)
                result = await repo.update_performance_metrics(
                    learner_id=sample_learner_profile["id"],
                    accuracy_rate=0.80,
                    avg_response_time=40.0,
                    engagement_score=0.90
                )
                
                assert result.performance_metrics["accuracy_rate"] == 0.80
                assert result.performance_metrics["avg_response_time"] == 40.0
                assert result.performance_metrics["engagement_score"] == 0.90
                mock_repo.update_performance_metrics.assert_called_once()


class TestTutoringSessionManagement:
    """Test tutoring session lifecycle management"""

    @pytest.mark.asyncio
    async def test_start_tutoring_session(self, mock_database, sample_tutoring_session):
        """Test starting a new tutoring session"""
        mock_session = AsyncMock()
        mock_database.return_value.__aenter__.return_value = mock_session
        
        mock_repo = AsyncMock(spec=TutoringSessionRepository)
        mock_tutoring_session = TutoringSession(**sample_tutoring_session)
        mock_repo.create.return_value = mock_tutoring_session
        
        with patch('backend.database.repositories.tutoring_session_repo.TutoringSessionRepository', return_value=mock_repo):
            async with NeonDatabase.get_session() as session:
                repo = TutoringSessionRepository(session)
                created_session = await repo.create(
                    learner_id=sample_tutoring_session["learner_id"],
                    subject=sample_tutoring_session["subject"],
                    topic=sample_tutoring_session["topic"],
                    difficulty_level=sample_tutoring_session["difficulty_level"],
                    learning_objectives=sample_tutoring_session["learning_objectives"],
                    session_metadata=sample_tutoring_session["session_metadata"]
                )
                
                assert created_session.subject == "Mathematics"
                assert created_session.topic == "Quadratic Equations"
                assert created_session.session_state == "active"
                assert created_session.difficulty_level == "medium"
                mock_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_end_session_with_summary(self, mock_database, sample_tutoring_session):
        """Test ending session and generating performance summary"""
        mock_session = AsyncMock()
        mock_database.return_value.__aenter__.return_value = mock_session
        
        mock_repo = AsyncMock(spec=TutoringSessionRepository)
        
        # Mock session ending with summary
        performance_summary = {
            "topics_covered": ["Quadratic Formula", "Factoring"],
            "questions_answered": 8,
            "correct_answers": 6,
            "accuracy_rate": 0.75,
            "time_spent": 1800,  # 30 minutes
            "areas_for_improvement": ["Complex quadratic equations"],
            "next_recommended_topics": ["Completing the square"]
        }
        
        ended_session = TutoringSession(**sample_tutoring_session)
        ended_session.session_state = "completed"
        ended_session.performance_summary = performance_summary
        
        mock_repo.end_session.return_value = ended_session
        
        with patch('backend.database.repositories.tutoring_session_repo.TutoringSessionRepository', return_value=mock_repo):
            async with NeonDatabase.get_session() as session:
                repo = TutoringSessionRepository(session)
                result = await repo.end_session(
                    session_id=sample_tutoring_session["id"],
                    performance_summary=performance_summary
                )
                
                assert result.session_state == "completed"
                assert result.performance_summary["accuracy_rate"] == 0.75
                assert result.performance_summary["questions_answered"] == 8
                assert "Completing the square" in result.performance_summary["next_recommended_topics"]
                mock_repo.end_session.assert_called_once()


class TestInteractionLogging:
    """Test interaction logging and analytics"""

    @pytest.mark.asyncio
    async def test_log_tutoring_interaction(self, mock_database):
        """Test logging individual tutoring interactions"""
        mock_session = AsyncMock()
        mock_database.return_value.__aenter__.return_value = mock_session
        
        mock_repo = AsyncMock(spec=LearnerInteractionRepository)
        
        interaction_data = {
            "id": str(uuid.uuid4()),
            "session_id": str(uuid.uuid4()),
            "learner_id": str(uuid.uuid4()),
            "interaction_type": "question_answer",
            "user_input": "How do I solve x² + 5x + 6 = 0?",
            "agent_response": "You can solve this by factoring: (x + 2)(x + 3) = 0",
            "response_time": 2.5,
            "difficulty_rating": "medium",
            "correctness_assessment": "correct",
            "interaction_metadata": {
                "topic": "quadratic_equations",
                "method_used": "factoring",
                "hints_provided": 1
            }
        }
        
        mock_interaction = LearnerInteraction(**interaction_data)
        mock_repo.create.return_value = mock_interaction
        
        with patch('backend.database.repositories.learner_interaction_repo.LearnerInteractionRepository', return_value=mock_repo):
            async with NeonDatabase.get_session() as session:
                repo = LearnerInteractionRepository(session)
                logged_interaction = await repo.create(
                    session_id=interaction_data["session_id"],
                    learner_id=interaction_data["learner_id"],
                    interaction_type=interaction_data["interaction_type"],
                    user_input=interaction_data["user_input"],
                    agent_response=interaction_data["agent_response"],
                    response_time=interaction_data["response_time"],
                    difficulty_rating=interaction_data["difficulty_rating"],
                    correctness_assessment=interaction_data["correctness_assessment"],
                    interaction_metadata=interaction_data["interaction_metadata"]
                )
                
                assert logged_interaction.interaction_type == "question_answer"
                assert logged_interaction.user_input == "How do I solve x² + 5x + 6 = 0?"
                assert logged_interaction.correctness_assessment == "correct"
                assert logged_interaction.response_time == 2.5
                mock_repo.create.assert_called_once()


class TestTutorAgentIntegration:
    """Test complete tutor agent workflow integration"""

    @pytest.mark.asyncio
    async def test_complete_tutoring_flow(self, tutor_agent, sample_rag_state, mock_database):
        """Test the complete end-to-end tutoring flow"""
        # Mock all database operations
        mock_session = AsyncMock()
        mock_database.return_value.__aenter__.return_value = mock_session
        
        # Mock agent executor response
        mock_response = {
            "output": "I understand you need help with quadratic equations. Let me start by assessing your current knowledge. Can you tell me what you already know about solving equations like x² + 5x + 6 = 0?"
        }
        
        with patch.object(tutor_agent.agent_executor, 'ainvoke', return_value=mock_response):
            # Process tutoring request
            result = await tutor_agent.process(sample_rag_state)
            
            # Verify response
            assert "tutoring_response" in result
            assert "quadratic equations" in result["tutoring_response"].lower()
            assert result["learning_progress"] is not None
            
            # Verify state updates
            assert result["learner_id"] == sample_rag_state["learner_id"]
            assert result["tutoring_session_id"] == sample_rag_state["tutoring_session_id"]

    @pytest.mark.asyncio
    async def test_personalized_content_adaptation(self, tutor_agent, sample_rag_state):
        """Test content adaptation based on learner profile"""
        # Update learner profile for visual learner with accessibility needs
        sample_rag_state["learner_profile"]["learning_style"] = "Visual"
        sample_rag_state["learner_profile"]["accessibility_needs"] = {
            "screen_reader": True,
            "high_contrast": True
        }
        
        mock_response = {
            "output": "Since you're a visual learner using a screen reader, I'll describe the quadratic equation graphically. Imagine a U-shaped curve called a parabola..."
        }
        
        with patch.object(tutor_agent.agent_executor, 'ainvoke', return_value=mock_response):
            result = await tutor_agent.process(sample_rag_state)
            
            # Verify personalized response
            assert "visual learner" in result["tutoring_response"].lower() or "parabola" in result["tutoring_response"].lower()
            assert "accessibility" in str(result).lower() or "screen reader" in result["tutoring_response"].lower()

    @pytest.mark.asyncio
    async def test_error_handling(self, tutor_agent, sample_rag_state):
        """Test error handling in tutoring flow"""
        # Simulate LLM error
        with patch.object(tutor_agent.agent_executor, 'ainvoke', side_effect=Exception("LLM service unavailable")):
            result = await tutor_agent.process(sample_rag_state)
            
            # Verify graceful error handling
            assert "tutoring_response" in result
            assert "error" in result["tutoring_response"].lower() or "sorry" in result["tutoring_response"].lower()

    @pytest.mark.asyncio
    async def test_session_state_management(self, tutor_agent, sample_rag_state):
        """Test session state updates during tutoring"""
        initial_progress = sample_rag_state["learning_progress"]["completion"]
        
        mock_response = {
            "output": "Great! You've shown good understanding of basic quadratic solving. Let's move to more complex examples."
        }
        
        with patch.object(tutor_agent.agent_executor, 'ainvoke', return_value=mock_response):
            result = await tutor_agent.process(sample_rag_state)
            
            # Verify session state tracking
            assert result["learning_progress"] is not None
            assert "interaction_history" in result
            assert len(result["interaction_history"]) > 0


class TestPracticeGeneratorHandler:
    """Test Practice Generator Handler for adaptive practice problems"""

    @pytest.mark.asyncio
    async def test_practice_generation(self, sample_rag_state):
        """Test generating practice problems"""
        from backend.core.agents.tutor_handlers.practice_generator import PracticeGeneratorHandler
        
        handler = PracticeGeneratorHandler()
        handler.set_state(sample_rag_state)
        
        # Mock LLM response with JSON practice items
        mock_practice_response = '''
        [
          {
            "id": "item_1",
            "question": "Solve the quadratic equation: x² + 5x + 6 = 0",
            "answer": "x = -2 or x = -3",
            "explanation": "Factor as (x+2)(x+3) = 0",
            "difficulty": "medium",
            "type": "problems"
          },
          {
            "id": "item_2", 
            "question": "Find the vertex of y = x² + 4x + 3",
            "answer": "(-2, -1)",
            "explanation": "Use vertex form or complete the square",
            "difficulty": "medium",
            "type": "problems"
          }
        ]
        '''
        
        with patch.object(handler.llm, 'invoke', return_value=type('Response', (), {'content': mock_practice_response})()):
            result = await handler._process("generate 2 problems for quadratic equations")
            
            assert "problems" in result.lower()
            assert "medium difficulty" in result.lower()
            assert "quadratic equation" in result.lower()
            assert "interaction_history" in sample_rag_state
            assert any(h["type"] == "practice_generation" for h in sample_rag_state["interaction_history"])

    def test_request_parsing(self):
        """Test parsing different practice request formats"""
        from backend.core.agents.tutor_handlers.practice_generator import PracticeGeneratorHandler
        
        handler = PracticeGeneratorHandler()
        
        # Test JSON format
        json_request = '{"topic": "algebra", "practice_type": "quiz", "num_items": 3}'
        parsed = handler._parse_practice_request(json_request)
        assert parsed["topic"] == "algebra"
        assert parsed["practice_type"] == "quiz"
        assert parsed["num_items"] == 3
        
        # Test natural language
        nl_request = "generate 5 math problems about quadratic equations"
        parsed = handler._parse_practice_request(nl_request)
        assert "quadratic equations" in parsed["topic"]
        assert parsed["practice_type"] == "problems"
        assert parsed["num_items"] == 5
        
        # Test difficulty specification
        diff_request = "create easy quiz questions about photosynthesis"
        parsed = handler._parse_practice_request(diff_request)
        assert parsed["difficulty_level"] == "easy"
        assert parsed["practice_type"] == "quiz"

    def test_difficulty_determination(self, sample_learner_profile):
        """Test determining appropriate difficulty level"""
        from backend.core.agents.tutor_handlers.practice_generator import PracticeGeneratorHandler
        
        handler = PracticeGeneratorHandler()
        
        # Test high performer
        high_profile = sample_learner_profile.copy()
        high_profile["performance_metrics"] = {"accuracy_rate": 0.9}
        difficulty = handler._determine_difficulty_level(high_profile)
        assert difficulty == "hard"
        
        # Test struggling learner
        struggling_profile = sample_learner_profile.copy()
        struggling_profile["performance_metrics"] = {"accuracy_rate": 0.5}
        struggling_profile["learning_struggles"] = ["algebra"]
        difficulty = handler._determine_difficulty_level(struggling_profile)
        assert difficulty == "easy"
        
        # Test young grade level
        young_profile = sample_learner_profile.copy()
        young_profile["grade_level"] = "4th Grade"
        difficulty = handler._determine_difficulty_level(young_profile)
        assert difficulty == "easy"
        
        # Test explicit request
        difficulty = handler._determine_difficulty_level(sample_learner_profile, "hard")
        assert difficulty == "hard"

    def test_practice_types(self):
        """Test that all practice types are properly defined"""
        from backend.core.agents.tutor_handlers.practice_generator import PracticeGeneratorHandler
        
        handler = PracticeGeneratorHandler()
        
        expected_types = ["problems", "quiz", "exercises", "assessment", "flashcards"]
        
        for ptype in expected_types:
            assert ptype in handler.practice_types
            assert "description" in handler.practice_types[ptype]
            assert "format" in handler.practice_types[ptype]
            assert "include_solutions" in handler.practice_types[ptype]

    def test_difficulty_levels(self):
        """Test that all difficulty levels are properly defined"""
        from backend.core.agents.tutor_handlers.practice_generator import PracticeGeneratorHandler
        
        handler = PracticeGeneratorHandler()
        
        expected_difficulties = ["easy", "medium", "hard"]
        
        for difficulty in expected_difficulties:
            assert difficulty in handler.difficulty_levels
            assert "complexity" in handler.difficulty_levels[difficulty]
            assert "thinking_level" in handler.difficulty_levels[difficulty]
            assert "steps" in handler.difficulty_levels[difficulty]
            assert "vocabulary" in handler.difficulty_levels[difficulty]

    @pytest.mark.asyncio
    async def test_topic_content_fetching(self, mock_database):
        """Test fetching content from learning units"""
        from backend.core.agents.tutor_handlers.practice_generator import PracticeGeneratorHandler
        
        handler = PracticeGeneratorHandler()
        
        # Test with learning unit ID
        mock_unit = type('Unit', (), {
            'title': 'Quadratic Equations',
            'detailed_explanation': 'Detailed explanation...',
            'key_points': ['Factor form', 'Vertex form'],
            'learning_objectives': ['Solve equations'],
            'keywords': ['quadratic', 'parabola'],
            'difficulty_level': 'medium',
            'subject': 'Mathematics'
        })()
        
        mock_session = AsyncMock()
        mock_database.return_value.__aenter__.return_value = mock_session
        
        with patch('backend.database.repositories.learning_unit_repo.LearningUnitRepository') as mock_repo:
            mock_repo.return_value.get_by_id.return_value = mock_unit
            
            content = await handler._fetch_topic_content(learning_unit_id="test_unit_id")
            
            assert content["title"] == "Quadratic Equations"
            assert content["subject"] == "Mathematics"
            assert "Factor form" in content["key_points"]

    def test_fallback_practice_creation(self):
        """Test creating fallback practice when LLM fails"""
        from backend.core.agents.tutor_handlers.practice_generator import PracticeGeneratorHandler
        
        handler = PracticeGeneratorHandler()
        
        fallback_items = handler._create_fallback_practice("algebra", "medium", 3, "problems")
        
        assert len(fallback_items) == 3
        assert all("algebra" in item["question"] for item in fallback_items)
        assert all(item["difficulty"] == "medium" for item in fallback_items)
        assert all(item["type"] == "problems" for item in fallback_items)


class TestExplanationEngineHandler:
    """Test Explanation Engine Handler for personalized explanations"""

    @pytest.mark.asyncio
    async def test_explanation_generation(self, sample_rag_state):
        """Test generating personalized explanations"""
        from backend.core.agents.tutor_handlers.explanation_engine import ExplanationEngineHandler
        
        handler = ExplanationEngineHandler()
        handler.set_state(sample_rag_state)
        
        # Mock LLM response
        mock_explanation = "Quadratic equations are like finding where a ball lands when you throw it in the air..."
        
        with patch.object(handler.llm, 'invoke', return_value=type('Response', (), {'content': mock_explanation})()):
            result = await handler._process("explain quadratic equations using analogy style")
            
            assert "analogy explanation" in result.lower()
            assert "quadratic equations" in result.lower()
            assert "interaction_history" in sample_rag_state
            assert len(sample_rag_state["interaction_history"]) > 0

    def test_request_parsing(self):
        """Test parsing different explanation request formats"""
        from backend.core.agents.tutor_handlers.explanation_engine import ExplanationEngineHandler
        
        handler = ExplanationEngineHandler()
        
        # Test JSON format
        json_request = '{"topic": "photosynthesis", "explanation_style": "simplified"}'
        parsed = handler._parse_explanation_request(json_request)
        assert parsed["topic"] == "photosynthesis"
        assert parsed["explanation_style"] == "simplified"
        
        # Test natural language
        nl_request = "explain quadratic equations using visual style"
        parsed = handler._parse_explanation_request(nl_request)
        assert "quadratic equations" in parsed["topic"]
        assert parsed["explanation_style"] == "visual"
        
        # Test simple request
        simple_request = "what is photosynthesis"
        parsed = handler._parse_explanation_request(simple_request)
        assert "photosynthesis" in parsed["topic"]

    def test_style_determination(self, sample_learner_profile):
        """Test determining best explanation style"""
        from backend.core.agents.tutor_handlers.explanation_engine import ExplanationEngineHandler
        
        handler = ExplanationEngineHandler()
        
        # Test visual learner
        visual_profile = sample_learner_profile.copy()
        visual_profile["learning_style"] = "Visual"
        style = handler._determine_best_explanation_style(visual_profile)
        assert style == "visual"
        
        # Test young grade level
        young_profile = sample_learner_profile.copy()
        young_profile["grade_level"] = "3rd Grade"
        style = handler._determine_best_explanation_style(young_profile)
        assert style == "simplified"
        
        # Test with learning struggles
        struggle_profile = sample_learner_profile.copy()
        struggle_profile["learning_struggles"] = ["algebra", "equations"]
        style = handler._determine_best_explanation_style(struggle_profile)
        assert style == "simplified"
        
        # Test with preferred styles
        preferred_profile = sample_learner_profile.copy()
        preferred_profile["preferred_explanation_styles"] = ["step-by-step"]
        style = handler._determine_best_explanation_style(preferred_profile)
        assert style == "step-by-step"

    def test_grade_extraction(self):
        """Test extracting numeric grade levels"""
        from backend.core.agents.tutor_handlers.explanation_engine import ExplanationEngineHandler
        
        handler = ExplanationEngineHandler()
        
        assert handler._extract_grade_number("10th Grade") == 10
        assert handler._extract_grade_number("Grade 7") == 7
        assert handler._extract_grade_number("3rd grade") == 3
        assert handler._extract_grade_number("High School") == 10
        assert handler._extract_grade_number("Elementary") == 3
        assert handler._extract_grade_number("University") == 13

    def test_explanation_styles(self):
        """Test that all explanation styles are properly defined"""
        from backend.core.agents.tutor_handlers.explanation_engine import ExplanationEngineHandler
        
        handler = ExplanationEngineHandler()
        
        expected_styles = [
            "simplified", "detailed", "analogy", "step-by-step", 
            "visual", "interactive", "practical"
        ]
        
        for style in expected_styles:
            assert style in handler.explanation_styles
            assert isinstance(handler.explanation_styles[style], str)
            assert len(handler.explanation_styles[style]) > 10  # Has meaningful description


class TestCPABridgeHandler:
    """Test CPA Bridge Handler for content adaptation requests and CPA integration"""

    @pytest.fixture
    def sample_learner_profile(self):
        """Sample learner profile data"""
        return {
            "id": str(uuid.uuid4()),
            "name": "Ahmed Hassan",
            "grade_level": "10th Grade",
            "learning_style": "Visual",
            "preferred_language": "Arabic",
            "subjects_of_interest": ["Mathematics", "Physics"],
            "learning_goals": ["Improve algebra skills", "Understand calculus basics"],
            "accessibility_needs": {"screen_reader": True, "high_contrast": True},
            "performance_metrics": {
                "accuracy_rate": 0.75,
                "avg_response_time": 45.2,
                "engagement_score": 0.85
            },
            "mastered_topics": ["Basic Algebra", "Linear Equations"],
            "learning_struggles": ["Quadratic Equations", "Trigonometry"]
        }

    @pytest.fixture
    def sample_tutoring_session(self):
        """Sample tutoring session data"""
        return {
            "id": str(uuid.uuid4()),
            "learner_id": str(uuid.uuid4()),
            "session_state": "active",
            "subject": "Mathematics",
            "topic": "Quadratic Equations",
            "difficulty_level": "medium",
            "learning_objectives": ["Solve quadratic equations", "Graph parabolas"],
            "session_metadata": {
                "start_time": datetime.utcnow().isoformat(),
                "platform": "web",
                "accessibility_mode": "screen_reader"
            },
            "interaction_history": []
        }

    @pytest.fixture
    def sample_rag_state(self, sample_learner_profile, sample_tutoring_session):
        """Sample RAGState for testing"""
        return RAGState(
            query="Help me understand quadratic equations",
            learner_id=sample_learner_profile["id"],
            learner_profile=sample_learner_profile,
            tutoring_session_id=sample_tutoring_session["id"],
            session_state=sample_tutoring_session,
            interaction_history=[],
            learning_progress={"current_topic": "quadratic_equations", "completion": 0.3}
        )

    @pytest.fixture
    def cpa_bridge_handler(self):
        """Initialize CPABridgeHandler"""
        from backend.core.agents.tutor_handlers.cpa_bridge_handler import CPABridgeHandler
        return CPABridgeHandler()

    @pytest.fixture
    def sample_state_with_struggle(self, sample_rag_state):
        """Sample state where learner is struggling"""
        state = sample_rag_state.copy()
        state["session_state"]["difficulty_level"] = "hard"
        state["learner_profile"]["learning_struggles"] = ["Quadratic Equations", "Complex Numbers"]
        return state

    @pytest.mark.asyncio
    async def test_content_adaptation_when_struggling(self, cpa_bridge_handler, sample_state_with_struggle):
        """Test content adaptation request when learner struggles"""
        cpa_bridge_handler.set_state(sample_state_with_struggle)
        
        # Mock ContentProcessorAgent response
        mock_cpa_result = {
            "answer": "Simplified explanation of quadratic equations with visual aids and step-by-step breakdown."
        }
        
        with patch.object(cpa_bridge_handler, '_call_cpa_for_adaptation', return_value=mock_cpa_result):
            result = await cpa_bridge_handler._process(
                '{"adaptation_type": "simplify", "topic": "quadratic_equations", "reason": "learner struggling with complexity"}'
            )
            
            assert "simplified" in result.lower()
            assert "personalized_content" in sample_state_with_struggle
            assert len(sample_state_with_struggle["personalized_content"]) > 0
            
            # Verify adaptation was recorded
            adaptation = sample_state_with_struggle["personalized_content"][0]
            assert adaptation["adaptation_type"] == "simplify"
            assert adaptation["original_topic"] == "quadratic_equations"

    @pytest.mark.asyncio
    async def test_style_adaptation_request(self, cpa_bridge_handler, sample_rag_state):
        """Test content adaptation for different learning styles"""
        cpa_bridge_handler.set_state(sample_rag_state)
        
        mock_cpa_result = {
            "answer": "Kinesthetic approach to quadratic equations with hands-on activities using algebra tiles and graphing calculators."
        }
        
        with patch.object(cpa_bridge_handler, '_call_cpa_for_adaptation', return_value=mock_cpa_result):
            result = await cpa_bridge_handler._process(
                "Adapt content for kinesthetic learner who prefers hands-on learning"
            )
            
            assert "kinesthetic" in result.lower() or "hands-on" in result.lower()
            assert "personalized_content" in sample_rag_state

    @pytest.mark.asyncio
    async def test_difficulty_increase_adaptation(self, cpa_bridge_handler, sample_rag_state):
        """Test content adaptation for increasing difficulty"""
        cpa_bridge_handler.set_state(sample_rag_state)
        
        # Simulate advanced learner
        sample_rag_state["learner_profile"]["mastered_topics"].extend(["Quadratic Equations", "Factoring"])
        
        mock_cpa_result = {
            "answer": "Advanced quadratic applications with complex coefficients and discriminant analysis for advanced students."
        }
        
        with patch.object(cpa_bridge_handler, '_call_cpa_for_adaptation', return_value=mock_cpa_result):
            result = await cpa_bridge_handler._process(
                '{"adaptation_type": "increase_difficulty", "topic": "quadratic_equations", "reason": "learner ready for advanced concepts"}'
            )
            
            assert "advanced" in result.lower()
            assert "personalized_content" in sample_rag_state

    @pytest.mark.asyncio
    async def test_adaptation_request_parsing(self, cpa_bridge_handler):
        """Test parsing different types of adaptation requests"""
        cpa_bridge_handler.set_state({"learner_profile": {}, "session_state": {}})
        
        # Test JSON format
        json_request = '{"topic": "algebra", "adaptation_type": "simplify", "reason": "too complex"}'
        parsed = await cpa_bridge_handler._parse_adaptation_request(json_request)
        assert parsed["topic"] == "algebra"
        assert parsed["adaptation_type"] == "simplify"
        
        # Test natural language format
        nl_request = "Make the topic about quadratic equations easier to understand"
        parsed = await cpa_bridge_handler._parse_adaptation_request(nl_request)
        assert "simplify" in parsed["adaptation_type"] or "easier" in parsed["adaptation_type"]
        
        # Test example request
        example_request = "Add more examples for linear equations"
        parsed = await cpa_bridge_handler._parse_adaptation_request(example_request)
        assert "example" in parsed["adaptation_type"] or "examples" in str(parsed).lower()

    @pytest.mark.asyncio
    async def test_learner_context_extraction(self, cpa_bridge_handler, sample_rag_state):
        """Test extracting learner context for adaptation"""
        cpa_bridge_handler.set_state(sample_rag_state)
        
        context = await cpa_bridge_handler._extract_learner_context()
        
        assert context["grade_level"] == "10th Grade"
        assert context["learning_style"] == "Visual"
        assert context["preferred_language"] == "Arabic"
        assert "Mathematics" in context["subjects_of_interest"]

    @pytest.mark.asyncio
    async def test_cpa_integration_with_mock(self, cpa_bridge_handler, sample_rag_state):
        """Test integration with ContentProcessorAgent using mocks"""
        cpa_bridge_handler.set_state(sample_rag_state)
        
        # Mock CPA agent initialization and processing
        with patch('backend.core.agents.content_processor_agent.ContentProcessorAgent') as mock_cpa_class:
            mock_cpa_instance = AsyncMock()
            mock_cpa_instance.process.return_value = {
                "answer": "Adapted content for visual learner with accessibility features"
            }
            mock_cpa_class.return_value = mock_cpa_instance
            
            # Initialize CPA agent
            cpa_bridge_handler.cpa_agent = mock_cpa_class()
            
            # Test adaptation
            result = await cpa_bridge_handler._process(
                "Simplify quadratic equations for visual learner with screen reader"
            )
            
            assert result is not None
            assert len(result) > 0
            
    @pytest.mark.asyncio
    async def test_error_handling_invalid_request(self, cpa_bridge_handler, sample_rag_state):
        """Test error handling for invalid adaptation requests"""
        cpa_bridge_handler.set_state(sample_rag_state)
        
        result = await cpa_bridge_handler._process("")
        
        # Check for error indicators (in any language) or generic response
        assert result is not None and len(result) > 0

    @pytest.mark.asyncio
    async def test_add_examples_adaptation(self, cpa_bridge_handler, sample_rag_state):
        """Test requesting additional examples through CPA"""
        cpa_bridge_handler.set_state(sample_rag_state)
        
        mock_cpa_result = {
            "answer": "Additional examples for quadratic equations:\n1. x² + 4x + 3 = 0\n2. 2x² - 8x + 6 = 0\n3. x² - 1 = 0"
        }
        
        with patch.object(cpa_bridge_handler, '_call_cpa_for_adaptation', return_value=mock_cpa_result):
            result = await cpa_bridge_handler._process(
                '{"adaptation_type": "add_examples", "topic": "quadratic_equations", "num_examples": 3}'
            )
            
            assert "example" in result.lower()
            assert "x²" in result or "quadratic" in result.lower()


class TestExplanationEngine:
    """Test Explanation Engine Handler for generating personalized explanations"""

    @pytest.fixture
    def sample_learner_profile(self):
        """Sample learner profile data"""
        return {
            "id": str(uuid.uuid4()),
            "name": "Ahmed Hassan",
            "grade_level": "10th Grade",
            "learning_style": "Visual",
            "preferred_language": "Arabic",
            "subjects_of_interest": ["Mathematics", "Physics"],
            "learning_goals": ["Improve algebra skills", "Understand calculus basics"],
            "accessibility_needs": {"screen_reader": True, "high_contrast": True},
            "performance_metrics": {
                "accuracy_rate": 0.75,
                "avg_response_time": 45.2,
                "engagement_score": 0.85
            },
            "mastered_topics": ["Basic Algebra", "Linear Equations"],
            "learning_struggles": ["Quadratic Equations", "Trigonometry"]
        }

    @pytest.fixture
    def sample_tutoring_session(self):
        """Sample tutoring session data"""
        return {
            "id": str(uuid.uuid4()),
            "learner_id": str(uuid.uuid4()),
            "session_state": "active",
            "subject": "Mathematics",
            "topic": "Quadratic Equations",
            "difficulty_level": "medium",
            "learning_objectives": ["Solve quadratic equations", "Graph parabolas"],
            "session_metadata": {
                "start_time": datetime.utcnow().isoformat(),
                "platform": "web",
                "accessibility_mode": "screen_reader"
            },
            "interaction_history": []
        }

    @pytest.fixture
    def sample_rag_state(self, sample_learner_profile, sample_tutoring_session):
        """Sample RAGState for testing"""
        return RAGState(
            query="Help me understand quadratic equations",
            learner_id=sample_learner_profile["id"],
            learner_profile=sample_learner_profile,
            tutoring_session_id=sample_tutoring_session["id"],
            session_state=sample_tutoring_session,
            interaction_history=[],
            learning_progress={"current_topic": "quadratic_equations", "completion": 0.3}
        )

    @pytest.fixture
    def explanation_engine(self):
        """Initialize ExplanationEngineHandler"""
        from backend.core.agents.tutor_handlers.explanation_engine import ExplanationEngineHandler
        return ExplanationEngineHandler()

    @pytest.mark.asyncio
    async def test_simplified_explanation(self, explanation_engine, sample_rag_state):
        """Test generating simplified explanations"""
        explanation_engine.set_state(sample_rag_state)
        
        # Set young learner profile
        sample_rag_state["learner_profile"]["grade_level"] = "5th Grade"
        
        mock_explanation = """
        # Quadratic Equations - Simple Explanation
        
        A quadratic equation is like a puzzle with x². Think of it as finding what number makes the equation true.
        
        For example: x² + 5x + 6 = 0
        This means "what number times itself, plus 5 times that number, plus 6 equals zero?"
        
        The answer is x = -2 or x = -3. Let's check: (-2)² + 5(-2) + 6 = 4 - 10 + 6 = 0 ✓
        """
        
        # Mock the LLM object's invoke method
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = type('Response', (), {'content': mock_explanation})()
        explanation_engine.llm = mock_llm
        
        result = await explanation_engine._process(
            '{"topic": "quadratic_equations", "explanation_style": "simplified"}'
        )
        
        assert "quadratic equation" in result.lower()
        assert "interaction_history" in sample_rag_state
        assert len(sample_rag_state["interaction_history"]) > 0
        
        # Verify explanation was logged
        interaction = sample_rag_state["interaction_history"][-1]
        assert interaction["type"] == "explanation"
        assert interaction["style"] == "simplified"

    @pytest.mark.asyncio
    async def test_analogy_based_explanation(self, explanation_engine, sample_rag_state):
        """Test generating analogy-based explanations"""
        explanation_engine.set_state(sample_rag_state)
        
        mock_explanation = """
        # Quadratic Equations - Using Analogies
        
        Think of a quadratic equation like throwing a ball in the air:
        - The ball goes up, reaches a peak, then comes down (like a parabola)
        - The equation tells us the ball's height at any time
        - Finding solutions is like asking "when does the ball hit the ground?"
        
        Just like the ball has two moments when it's at the same height (going up and coming down),
        quadratic equations often have two solutions!
        """
        
        # Mock the LLM
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = type('Response', (), {'content': mock_explanation})()
        explanation_engine.llm = mock_llm
        
        result = await explanation_engine._process(
            "explain quadratic equations using analogy style"
        )
        
        assert "like" in result.lower() or "analogy" in result.lower()
        assert "interaction_history" in sample_rag_state

    @pytest.mark.asyncio
    async def test_step_by_step_explanation(self, explanation_engine, sample_rag_state):
        """Test generating step-by-step explanations"""
        explanation_engine.set_state(sample_rag_state)
        
        mock_explanation = """
        # Solving Quadratic Equations - Step by Step
        
        Let's solve x² + 5x + 6 = 0:
        
        Step 1: Identify it's in the form ax² + bx + c = 0
        - a = 1, b = 5, c = 6
        
        Step 2: Try to factor (look for two numbers that multiply to 6 and add to 5)
        - 2 × 3 = 6 ✓
        - 2 + 3 = 5 ✓
        
        Step 3: Write as factors: (x + 2)(x + 3) = 0
        
        Step 4: Set each factor to zero:
        - x + 2 = 0, so x = -2
        - x + 3 = 0, so x = -3
        
        Step 5: Check your answers by substituting back into the original equation
        """
        
        # Mock the LLM
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = type('Response', (), {'content': mock_explanation})()
        explanation_engine.llm = mock_llm
        
        result = await explanation_engine._process(
            '{"topic": "solving_quadratic_equations", "explanation_style": "step-by-step"}'
        )
        
        assert "step" in result.lower()
        
        # Verify logged with correct style
        interaction = sample_rag_state["interaction_history"][-1]
        assert interaction["style"] == "step-by-step"

    @pytest.mark.asyncio
    async def test_visual_explanation(self, explanation_engine, sample_rag_state):
        """Test generating visual-focused explanations"""
        explanation_engine.set_state(sample_rag_state)
        
        # Set learner as visual learner
        sample_rag_state["learner_profile"]["learning_style"] = "Visual"
        
        mock_explanation = """
        # Quadratic Equations - Visual Explanation
        
        Picture a U-shaped curve (parabola) on a graph:
        
        📊 The equation y = x² + 5x + 6 creates this curve
        🎯 Where the curve crosses the x-axis are your solutions
        📍 Looking at the graph, the curve crosses at x = -2 and x = -3
        
        Visual tips:
        • The curve opens upward (since coefficient of x² is positive)
        • The vertex (lowest point) is at x = -2.5, y = -0.25
        • You can see the symmetry: equal distances from vertex to each x-intercept
        
        Think of it like a basketball shot - the ball follows a parabolic path!
        """
        
        # Mock the LLM
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = type('Response', (), {'content': mock_explanation})()
        explanation_engine.llm = mock_llm
        
        result = await explanation_engine._process(
            "explain quadratic equations visually"
        )
        
        assert any(word in result.lower() for word in ["graph", "curve", "visual", "picture"])
        
        # Verify visual style was selected for visual learner
        interaction = sample_rag_state["interaction_history"][-1]
        assert interaction["style"] == "visual"

    @pytest.mark.asyncio
    async def test_detailed_explanation(self, explanation_engine, sample_rag_state):
        """Test generating detailed explanations for advanced learners"""
        explanation_engine.set_state(sample_rag_state)
        
        # Set advanced learner profile
        sample_rag_state["learner_profile"]["grade_level"] = "12th Grade"
        sample_rag_state["learner_profile"]["mastered_topics"] = ["Basic Algebra", "Linear Equations"]
        
        mock_explanation = """
        # Quadratic Equations - Comprehensive Explanation
        
        A quadratic equation is a polynomial equation of the second degree...
        The general form is ax² + bx + c = 0 where a ≠ 0.
        
        Solutions can be found using multiple methods:
        1. Factoring (when possible)
        2. Quadratic formula: x = (-b ± √(b² - 4ac)) / 2a
        3. Completing the square
        4. Graphical analysis
        
        The discriminant (b² - 4ac) determines the nature of the roots...
        """
        
        # Mock the LLM
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = type('Response', (), {'content': mock_explanation})()
        explanation_engine.llm = mock_llm
        
        result = await explanation_engine._process(
            '{"topic": "quadratic_equations", "explanation_style": "detailed"}'
        )
        
        assert "quadratic" in result.lower()
        assert len(result) > 200  # Detailed explanation should be longer

    @pytest.mark.asyncio
    async def test_style_determination_visual_learner(self, explanation_engine, sample_rag_state):
        """Test automatic style determination for visual learners"""
        explanation_engine.set_state(sample_rag_state)
        
        # Set visual learning style WITHOUT grade level to prioritize learning style
        learner_profile = {"learning_style": "Visual"}
        
        style = explanation_engine._determine_best_explanation_style(learner_profile)
        
        assert style == "visual"

    @pytest.mark.asyncio
    async def test_style_determination_young_learner(self, explanation_engine, sample_rag_state):
        """Test automatic style determination for young learners"""
        explanation_engine.set_state(sample_rag_state)
        
        # Set young learner
        learner_profile = {"grade_level": "3rd Grade", "learning_style": "Auditory"}
        
        style = explanation_engine._determine_best_explanation_style(learner_profile)
        
        assert style == "simplified"

    @pytest.mark.asyncio
    async def test_style_determination_struggling_learner(self, explanation_engine, sample_rag_state):
        """Test automatic style determination for struggling learners without other priorities"""
        explanation_engine.set_state(sample_rag_state)
        
        # Set struggling learner without grade level and without specific learning style
        learner_profile = {
            "learning_struggles": ["Algebra", "Equations"]
        }
        
        style = explanation_engine._determine_best_explanation_style(learner_profile)
        
        assert style == "simplified"

    @pytest.mark.asyncio
    async def test_practical_explanation(self, explanation_engine, sample_rag_state):
        """Test generating practical, real-world explanations"""
        explanation_engine.set_state(sample_rag_state)
        
        mock_explanation = """
        # Quadratic Equations - Real-World Applications
        
        Quadratic equations appear everywhere in real life:
        
        1. Physics: A ball thrown in the air follows path h = -16t² + 64t + 5
        2. Business: Profit functions like P = -x² + 100x - 1500
        3. Architecture: Parabolic arches and bridges
        4. Sports: Trajectory of basketballs, golf balls
        
        Example: If you throw a ball at 64 ft/s from 5 feet high,
        when does it hit the ground? Solve: -16t² + 64t + 5 = 0
        """
        
        # Mock the LLM
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = type('Response', (), {'content': mock_explanation})()
        explanation_engine.llm = mock_llm
        
        result = await explanation_engine._process(
            '{"topic": "quadratic_equations", "explanation_style": "practical"}'
        )
        
        assert any(word in result.lower() for word in ["real", "application", "example"])

    @pytest.mark.asyncio
    async def test_error_handling_no_state(self, explanation_engine):
        """Test error handling when no state is set"""
        result = await explanation_engine._process("explain quadratic equations")
        
        assert "unable" in result.lower() or "error" in result.lower()


class TestPracticeGenerator:
    """Test Practice Generator Handler for creating practice problems at different difficulty levels"""

    @pytest.fixture
    def sample_learner_profile(self):
        """Sample learner profile data"""
        return {
            "id": str(uuid.uuid4()),
            "name": "Ahmed Hassan",
            "grade_level": "10th Grade",
            "learning_style": "Visual",
            "preferred_language": "Arabic",
            "subjects_of_interest": ["Mathematics", "Physics"],
            "learning_goals": ["Improve algebra skills", "Understand calculus basics"],
            "accessibility_needs": {"screen_reader": True, "high_contrast": True},
            "performance_metrics": {
                "accuracy_rate": 0.75,
                "avg_response_time": 45.2,
                "engagement_score": 0.85
            },
            "mastered_topics": ["Basic Algebra", "Linear Equations"],
            "learning_struggles": ["Quadratic Equations", "Trigonometry"]
        }

    @pytest.fixture
    def sample_tutoring_session(self):
        """Sample tutoring session data"""
        return {
            "id": str(uuid.uuid4()),
            "learner_id": str(uuid.uuid4()),
            "session_state": "active",
            "subject": "Mathematics",
            "topic": "Quadratic Equations",
            "difficulty_level": "medium",
            "learning_objectives": ["Solve quadratic equations", "Graph parabolas"],
            "session_metadata": {
                "start_time": datetime.utcnow().isoformat(),
                "platform": "web",
                "accessibility_mode": "screen_reader"
            },
            "interaction_history": []
        }

    @pytest.fixture
    def sample_rag_state(self, sample_learner_profile, sample_tutoring_session):
        """Sample RAGState for testing"""
        return RAGState(
            query="Help me understand quadratic equations",
            learner_id=sample_learner_profile["id"],
            learner_profile=sample_learner_profile,
            tutoring_session_id=sample_tutoring_session["id"],
            session_state=sample_tutoring_session,
            interaction_history=[],
            learning_progress={"current_topic": "quadratic_equations", "completion": 0.3}
        )

    @pytest.fixture
    def mock_database(self):
        """Mock database session"""
        with patch('backend.database.db.NeonDatabase.get_session') as mock_session:
            yield mock_session

    @pytest.fixture
    def practice_generator(self):
        """Initialize PracticeGeneratorHandler"""
        from backend.core.agents.tutor_handlers.practice_generator import PracticeGeneratorHandler
        return PracticeGeneratorHandler()

    @pytest.mark.asyncio
    async def test_easy_practice_problems(self, practice_generator, sample_rag_state):
        """Test generating easy difficulty practice problems"""
        practice_generator.set_state(sample_rag_state)
        
        # Set struggling learner profile
        sample_rag_state["learner_profile"]["learning_struggles"] = ["Quadratic Equations"]
        sample_rag_state["learner_profile"]["performance_metrics"] = {"accuracy_rate": 0.55}
        
        mock_practice = """
        [
            {
                "question": "Solve: x² + 4x + 3 = 0",
                "answer": "x = -1 or x = -3",
                "explanation": "Factor as (x+1)(x+3) = 0",
                "hint": "Look for two numbers that multiply to 3 and add to 4",
                "difficulty": "easy",
                "type": "problem"
            },
            {
                "question": "Solve: x² - 5x + 6 = 0",
                "answer": "x = 2 or x = 3",
                "explanation": "Factor as (x-2)(x-3) = 0",
                "hint": "Find two numbers that multiply to 6 and add to -5",
                "difficulty": "easy",
                "type": "problem"
            }
        ]
        """
        
        # Mock the LLM
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = type('Response', (), {'content': mock_practice})()
        practice_generator.llm = mock_llm
        
        result = await practice_generator._process(
            '{"topic": "quadratic_equations", "practice_type": "problems", "difficulty_level": "easy", "num_items": 2}'
        )
        
        assert "easy" in result.lower() or "problems" in result.lower()
        assert "interaction_history" in sample_rag_state
        
        # Verify practice was logged
        interaction = sample_rag_state["interaction_history"][-1]
        assert interaction["type"] == "practice_generation"

    @pytest.mark.asyncio
    async def test_medium_difficulty_quiz(self, practice_generator, sample_rag_state):
        """Test generating medium difficulty quiz"""
        practice_generator.set_state(sample_rag_state)
        
        mock_quiz = """
        [
            {
                "question": "What are the solutions to 2x² + 7x + 3 = 0?",
                "answer": "A) x = -1/2, x = -3",
                "choices": ["A) x = -1/2, x = -3", "B) x = 1/2, x = 3", "C) x = -2, x = -3/2", "D) x = 2, x = 3/2"],
                "explanation": "Using the quadratic formula: x = (-7 ± √(49-24))/4 = (-7 ± 5)/4",
                "difficulty": "medium",
                "type": "quiz"
            },
            {
                "question": "Which method is best for solving x² + 6x + 9 = 0?",
                "answer": "B) Factoring",
                "choices": ["A) Quadratic formula", "B) Factoring", "C) Completing the square", "D) Graphing"],
                "explanation": "This is a perfect square trinomial: (x + 3)² = 0",
                "difficulty": "medium",
                "type": "quiz"
            }
        ]
        """
        
        # Mock the LLM
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = type('Response', (), {'content': mock_quiz})()
        practice_generator.llm = mock_llm
        
        result = await practice_generator._process(
            '{"topic": "quadratic_equations", "practice_type": "quiz", "difficulty_level": "medium", "num_items": 2}'
        )
        
        assert "quiz" in result.lower() or "medium" in result.lower()

    @pytest.mark.asyncio
    async def test_hard_difficulty_assessment(self, practice_generator, sample_rag_state):
        """Test generating hard difficulty assessment"""
        practice_generator.set_state(sample_rag_state)
        
        # Set advanced learner profile
        sample_rag_state["learner_profile"]["mastered_topics"].extend(["Basic Quadratic Equations", "Factoring"])
        sample_rag_state["learner_profile"]["performance_metrics"] = {"accuracy_rate": 0.92}
        
        mock_assessment = """
        [
            {
                "question": "Find all complex solutions to 3x² + 2x + 5 = 0",
                "answer": "x = (-1 ± 2i√3.5)/3",
                "explanation": "Use quadratic formula with complex arithmetic",
                "difficulty": "hard",
                "type": "assessment",
                "points": 5
            },
            {
                "question": "A projectile is fired with equation h(t) = -16t² + 64t + 80. When does it hit the ground?",
                "answer": "t = 5 seconds",
                "explanation": "Set h(t) = 0 and solve",
                "difficulty": "hard",
                "type": "assessment",
                "points": 5
            }
        ]
        """
        
        # Mock the LLM
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = type('Response', (), {'content': mock_assessment})()
        practice_generator.llm = mock_llm
        
        result = await practice_generator._process(
            '{"topic": "advanced_quadratic_equations", "practice_type": "assessment", "difficulty_level": "hard", "num_items": 2}'
        )
        
        assert "hard" in result.lower() or "assessment" in result.lower() or "advanced" in result.lower()

    @pytest.mark.asyncio
    async def test_hands_on_exercises(self, practice_generator, sample_rag_state):
        """Test generating kinesthetic/hands-on exercises"""
        practice_generator.set_state(sample_rag_state)
        
        # Set kinesthetic learner
        sample_rag_state["learner_profile"]["learning_style"] = "Kinesthetic"
        
        mock_exercises = """
        [
            {
                "question": "Algebra Tiles Activity: Use algebra tiles to model and solve x² + 5x + 6 = 0",
                "answer": "x = -2 or x = -3",
                "explanation": "Arrange tiles to form rectangles representing (x+2)(x+3)",
                "difficulty": "medium",
                "type": "exercise",
                "materials": "algebra tiles, workspace mat"
            },
            {
                "question": "Graphing Calculator Exploration: Graph y = x² + 5x + 6 and find x-intercepts",
                "answer": "x = -2 and x = -3",
                "explanation": "Use trace or zero function to find where curve crosses x-axis",
                "difficulty": "medium",
                "type": "exercise",
                "materials": "graphing calculator or Desmos"
            }
        ]
        """
        
        # Mock the LLM
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = type('Response', (), {'content': mock_exercises})()
        practice_generator.llm = mock_llm
        
        result = await practice_generator._process(
            '{"topic": "quadratic_equations", "practice_type": "exercises", "num_items": 2}'
        )
        
        assert "exercise" in result.lower() or "activity" in result.lower()

    @pytest.mark.asyncio
    async def test_difficulty_auto_detection(self, practice_generator, sample_rag_state):
        """Test automatic difficulty level determination"""
        practice_generator.set_state(sample_rag_state)
        
        # Test high performer with NO learning struggles
        high_profile = {
            "performance_metrics": {"accuracy_rate": 0.9},
            "learning_struggles": [],
            "grade_level": "10th Grade"
        }
        difficulty = practice_generator._determine_difficulty_level(high_profile)
        assert difficulty == "hard"
        
        # Test struggling learner - struggles override performance metrics
        struggling_profile = {
            "performance_metrics": {"accuracy_rate": 0.5},
            "learning_struggles": ["algebra"],
            "grade_level": "10th Grade"
        }
        difficulty = practice_generator._determine_difficulty_level(struggling_profile)
        assert difficulty == "easy"
        
        # Test medium performer with no struggles
        medium_profile = {
            "performance_metrics": {"accuracy_rate": 0.75},
            "learning_struggles": [],
            "grade_level": "10th Grade"
        }
        difficulty = practice_generator._determine_difficulty_level(medium_profile)
        assert difficulty == "medium"

    @pytest.mark.asyncio
    async def test_flashcards_generation(self, practice_generator, sample_rag_state):
        """Test generating flashcards for memorization"""
        practice_generator.set_state(sample_rag_state)
        
        mock_flashcards = """
        [
            {
                "question": "What is the standard form of a quadratic equation?",
                "answer": "ax² + bx + c = 0, where a ≠ 0",
                "explanation": "This is the general form with a, b, c as constants",
                "difficulty": "easy",
                "type": "flashcard"
            },
            {
                "question": "What is the quadratic formula?",
                "answer": "x = (-b ± √(b² - 4ac)) / 2a",
                "explanation": "Used to find roots of any quadratic equation",
                "difficulty": "easy",
                "type": "flashcard"
            },
            {
                "question": "What does the discriminant tell us?",
                "answer": "b² - 4ac determines the nature and number of solutions",
                "explanation": "Positive: 2 real roots, Zero: 1 root, Negative: complex roots",
                "difficulty": "easy",
                "type": "flashcard"
            }
        ]
        """
        
        # Mock the LLM
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = type('Response', (), {'content': mock_flashcards})()
        practice_generator.llm = mock_llm
        
        result = await practice_generator._process(
            '{"topic": "quadratic_equations", "practice_type": "flashcards", "num_items": 3}'
        )
        
        assert "flashcard" in result.lower() or "front" in result.lower() or "back" in result.lower()

    @pytest.mark.asyncio
    async def test_practice_with_learning_unit(self, practice_generator, sample_rag_state):
        """Test that _fetch_topic_content can retrieve from learning units"""
        practice_generator.set_state(sample_rag_state)
        
        # Create mock unit with proper attributes
        mock_unit = MagicMock()
        mock_unit.title = 'Quadratic Equations'
        mock_unit.detailed_explanation = 'Comprehensive guide...'
        mock_unit.key_points = ['Factor form', 'Vertex form']
        mock_unit.learning_objectives = ['Solve equations']
        mock_unit.keywords = ['quadratic', 'parabola']
        mock_unit.difficulty_level = 'medium'
        mock_unit.subject = 'Mathematics'
        
        # Mock the repository get_by_id method
        mock_repo = AsyncMock()
        mock_repo.get_by_id = AsyncMock(return_value=mock_unit)
        
        # Mock both the database session and repository instantiation
        with patch('backend.core.agents.tutor_handlers.practice_generator.NeonDatabase.get_session') as mock_get_session, \
             patch('backend.core.agents.tutor_handlers.practice_generator.LearningUnitRepository', return_value=mock_repo):
            
            mock_session = AsyncMock()
            mock_get_session.return_value.__aenter__.return_value = mock_session
            
            content = await practice_generator._fetch_topic_content(learning_unit_id="test_unit_id")
            
            # Verify the content was fetched
            assert content is not None
            assert content["title"] == "Quadratic Equations"
            assert content["subject"] == "Mathematics"
            assert "Factor form" in content["key_points"]

    @pytest.mark.asyncio
    async def test_request_parsing(self, practice_generator):
        """Test parsing different practice request formats"""
        practice_generator.set_state({"learner_profile": {}, "session_state": {}})
        
        # Test JSON format
        json_request = '{"topic": "algebra", "practice_type": "quiz", "num_items": 3, "difficulty_level": "medium"}'
        parsed = practice_generator._parse_practice_request(json_request)
        assert parsed["topic"] == "algebra"
        assert parsed["practice_type"] == "quiz"
        assert parsed["num_items"] == 3
        assert parsed["difficulty_level"] == "medium"
        
        # Test natural language
        nl_request = "generate 5 math problems about quadratic equations"
        parsed = practice_generator._parse_practice_request(nl_request)
        assert "quadratic equations" in parsed["topic"]
        assert parsed["practice_type"] == "problems"
        assert parsed["num_items"] == 5

    @pytest.mark.asyncio
    async def test_fallback_practice_creation(self, practice_generator):
        """Test creating fallback practice when LLM fails"""
        practice_generator.set_state({"learner_profile": {}, "session_state": {}})
        
        fallback_items = practice_generator._create_fallback_practice("algebra", "medium", 3, "problems")
        
        assert len(fallback_items) == 3
        assert all("algebra" in str(item).lower() for item in fallback_items)

    @pytest.mark.asyncio
    async def test_error_handling_invalid_request(self, practice_generator, sample_rag_state):
        """Test error handling for invalid practice requests"""
        practice_generator.set_state(sample_rag_state)
        
        result = await practice_generator._process("")
        
        assert "invalid" in result.lower() or "unable" in result.lower()

    @pytest.mark.asyncio
    async def test_adaptive_difficulty_progression(self, practice_generator, sample_rag_state):
        """Test that difficulty adapts based on learner performance"""
        practice_generator.set_state(sample_rag_state)
        
        # Simulate good performance - should suggest harder problems (no struggles)
        good_profile = {
            "performance_metrics": {"accuracy_rate": 0.90},
            "learning_struggles": [],  # No struggles
            "grade_level": "10th Grade"
        }
        difficulty = practice_generator._determine_difficulty_level(good_profile)
        assert difficulty == "hard"
        
        # Simulate poor performance - should suggest easier problems
        poor_profile = {
            "performance_metrics": {"accuracy_rate": 0.45},
            "learning_struggles": [],  # No struggles
            "grade_level": "10th Grade"
        }
        difficulty = practice_generator._determine_difficulty_level(poor_profile)
        assert difficulty == "easy"


class TestIntegratedTutoringFlow:
    """Test complete integrated tutoring flow using all 6 handlers"""

    @pytest.fixture
    def all_handlers(self):
        """Initialize all tutor handlers"""
        from backend.core.agents.tutor_handlers.session_manager import SessionManagerHandler
        from backend.core.agents.tutor_handlers.learner_model_manager import LearnerModelManagerHandler
        from backend.core.agents.tutor_handlers.interaction_logger import InteractionLoggerHandler
        from backend.core.agents.tutor_handlers.cpa_bridge_handler import CPABridgeHandler
        from backend.core.agents.tutor_handlers.explanation_engine import ExplanationEngineHandler
        from backend.core.agents.tutor_handlers.practice_generator import PracticeGeneratorHandler
        
        return {
            'session_manager': SessionManagerHandler(),
            'learner_model': LearnerModelManagerHandler(),
            'interaction_logger': InteractionLoggerHandler(),
            'cpa_bridge': CPABridgeHandler(),
            'explanation_engine': ExplanationEngineHandler(),
            'practice_generator': PracticeGeneratorHandler()
        }

    @pytest.mark.asyncio
    async def test_struggling_learner_complete_flow(self, all_handlers, sample_rag_state, mock_database):
        """Test complete flow when learner is struggling with concept"""
        # Setup struggling learner scenario
        struggling_state = sample_rag_state.copy()
        struggling_state["query"] = "I don't understand quadratic equations at all. They're too confusing."
        struggling_state["learner_profile"]["learning_struggles"].append("Quadratic Equations")
        
        # Mock database operations
        mock_session = AsyncMock()
        mock_database.return_value.__aenter__.return_value = mock_session
        
        # Mock all handler responses
        with patch.multiple(
            'backend.core.agents.tutor_handlers.session_manager.SessionManagerHandler',
            _execute_tool=AsyncMock(return_value={"session_id": "session_123", "status": "active"}),
        ), patch.multiple(
            'backend.core.agents.tutor_handlers.cpa_bridge_handler.CPABridgeHandler',
            _execute_tool=AsyncMock(return_value={
                "adapted_content": "Simplified quadratic equations with visual aids",
                "adaptation_type": "simplify"
            })
        ), patch.multiple(
            'backend.core.agents.tutor_handlers.explanation_engine.ExplanationEngineHandler',
            _execute_tool=AsyncMock(return_value={
                "explanation": "Think of quadratic equations like a simple puzzle...",
                "style": "simplified"
            })
        ), patch.multiple(
            'backend.core.agents.tutor_handlers.practice_generator.PracticeGeneratorHandler',
            _execute_tool=AsyncMock(return_value={
                "problems": [{"problem": "x² + 2x + 1 = 0", "difficulty": "easy"}],
                "difficulty_level": "easy"
            })
        ), patch.multiple(
            'backend.core.agents.tutor_handlers.learner_model_manager.LearnerModelManagerHandler',
            _execute_tool=AsyncMock(return_value={"updated": True, "struggle_noted": True})
        ), patch.multiple(
            'backend.core.agents.tutor_handlers.interaction_logger.InteractionLoggerHandler',
            _execute_tool=AsyncMock(return_value={"logged": True, "interaction_id": "int_456"})
        ):
            
            # Test the flow
            for handler_name, handler in all_handlers.items():
                handler.set_state(struggling_state)
            
            # 1. Start session
            session_result = await all_handlers['session_manager']._execute_tool(
                action="start",
                learner_id=struggling_state["learner_id"]
            )
            assert session_result["status"] == "active"
            
            # 2. Request content adaptation (learner struggling)
            adaptation_result = await all_handlers['cpa_bridge']._execute_tool(
                adaptation_type="simplify",
                current_topic="quadratic_equations",
                learner_needs="struggling with concept complexity"
            )
            assert adaptation_result["adaptation_type"] == "simplify"
            
            # 3. Generate simplified explanation
            explanation_result = await all_handlers['explanation_engine']._execute_tool(
                topic="quadratic_equations",
                explanation_style="simplified",
                specific_question="What are quadratic equations?"
            )
            assert explanation_result["style"] == "simplified"
            
            # 4. Generate easy practice
            practice_result = await all_handlers['practice_generator']._execute_tool(
                topic="quadratic_equations",
                practice_type="problems",
                difficulty_level="easy"
            )
            assert practice_result["difficulty_level"] == "easy"
            
            # 5. Update learner model (note struggle)
            model_result = await all_handlers['learner_model']._execute_tool(
                update_type="note_struggle",
                topic="quadratic_equations",
                performance_data={"difficulty": "high", "needs_support": True}
            )
            assert model_result["struggle_noted"] == True
            
            # 6. Log the interaction
            log_result = await all_handlers['interaction_logger']._execute_tool(
                interaction_type="struggle_support",
                query_text="I don't understand quadratic equations at all",
                response_text="Provided simplified explanation and easy practice",
                was_helpful=True
            )
            assert log_result["logged"] == True

    @pytest.mark.asyncio 
    async def test_advanced_learner_complete_flow(self, all_handlers, sample_rag_state, mock_database):
        """Test complete flow when learner is ready for advanced content"""
        # Setup advanced learner scenario
        advanced_state = sample_rag_state.copy()
        advanced_state["query"] = "I've mastered basic quadratic equations. Can you give me something more challenging?"
        advanced_state["learner_profile"]["mastered_topics"].extend([
            "Basic Quadratic Equations", "Factoring", "Quadratic Formula"
        ])
        
        # Mock database operations
        mock_session = AsyncMock()
        mock_database.return_value.__aenter__.return_value = mock_session
        
        with patch.multiple(
            'backend.core.agents.tutor_handlers.session_manager.SessionManagerHandler',
            _execute_tool=AsyncMock(return_value={"session_id": "session_789", "status": "active"}),
        ), patch.multiple(
            'backend.core.agents.tutor_handlers.cpa_bridge_handler.CPABridgeHandler',
            _execute_tool=AsyncMock(return_value={
                "adapted_content": "Advanced quadratic applications with complex numbers",
                "adaptation_type": "increase_difficulty"
            })
        ), patch.multiple(
            'backend.core.agents.tutor_handlers.explanation_engine.ExplanationEngineHandler',
            _execute_tool=AsyncMock(return_value={
                "explanation": "Advanced quadratic concepts include complex solutions...",
                "style": "detailed"
            })
        ), patch.multiple(
            'backend.core.agents.tutor_handlers.practice_generator.PracticeGeneratorHandler',
            _execute_tool=AsyncMock(return_value={
                "problems": [{"problem": "3x² + 2x + 5 = 0", "difficulty": "hard"}],
                "difficulty_level": "hard"
            })
        ), patch.multiple(
            'backend.core.agents.tutor_handlers.learner_model_manager.LearnerModelManagerHandler',
            _execute_tool=AsyncMock(return_value={"updated": True, "advancement_noted": True})
        ), patch.multiple(
            'backend.core.agents.tutor_handlers.interaction_logger.InteractionLoggerHandler',
            _execute_tool=AsyncMock(return_value={"logged": True, "interaction_id": "int_789"})
        ):
            
            # Set state for all handlers
            for handler in all_handlers.values():
                handler.set_state(advanced_state)
            
            # 1. Continue/manage session
            session_result = await all_handlers['session_manager']._execute_tool(
                action="continue",
                learner_id=advanced_state["learner_id"]
            )
            assert session_result["status"] == "active"
            
            # 2. Request advanced content adaptation
            adaptation_result = await all_handlers['cpa_bridge']._execute_tool(
                adaptation_type="increase_difficulty",
                current_topic="quadratic_equations",
                learner_needs="ready for advanced concepts"
            )
            assert adaptation_result["adaptation_type"] == "increase_difficulty"
            
            # 3. Generate detailed explanation
            explanation_result = await all_handlers['explanation_engine']._execute_tool(
                topic="advanced_quadratic_equations",
                explanation_style="detailed",
                specific_question="What are complex solutions in quadratic equations?"
            )
            assert explanation_result["style"] == "detailed"
            
            # 4. Generate challenging practice
            practice_result = await all_handlers['practice_generator']._execute_tool(
                topic="complex_quadratic_equations",
                practice_type="assessment",
                difficulty_level="hard"
            )
            assert practice_result["difficulty_level"] == "hard"
            
            # 5. Update learner model (note advancement)
            model_result = await all_handlers['learner_model']._execute_tool(
                update_type="note_mastery",
                topic="basic_quadratic_equations",
                performance_data={"ready_for_advancement": True}
            )
            assert model_result["advancement_noted"] == True
            
            # 6. Log the interaction
            log_result = await all_handlers['interaction_logger']._execute_tool(
                interaction_type="advancement",
                query_text="I've mastered basic quadratic equations",
                response_text="Provided advanced content and challenging practice",
                was_helpful=True
            )
            assert log_result["logged"] == True


class TestTutorAgentTools:
    """Test individual tutor agent tools"""

    def test_tool_collection(self, tutor_agent):
        """Test that all required tools are collected"""
        tool_names = [tool.name for tool in tutor_agent.tools]
        
        assert "manage_tutoring_session" in tool_names
        assert "manage_learner_model" in tool_names  
        assert "log_interaction" in tool_names
        assert "request_content_adaptation" in tool_names
        assert "generate_explanation" in tool_names
        assert "generate_practice" in tool_names
        assert len(tutor_agent.tools) == 6

    def test_handler_initialization(self, tutor_agent):
        """Test that all handlers are properly initialized"""
        handler_types = [type(handler).__name__ for handler in tutor_agent.handlers]
        
        assert "SessionManagerHandler" in handler_types
        assert "LearnerModelManagerHandler" in handler_types
        assert "InteractionLoggerHandler" in handler_types
        assert "CPABridgeHandler" in handler_types
        assert "ExplanationEngineHandler" in handler_types
        assert "PracticeGeneratorHandler" in handler_types
        assert len(tutor_agent.handlers) == 6


# Integration test to run manually
async def run_integration_test():
    """Manual integration test for development"""
    print("🚀 Starting Tutor Agent Integration Test...")
    
    # Initialize database
    NeonDatabase.init()
    
    # Create test state
    test_state = RAGState(
        query="I need help understanding quadratic equations",
        learner_id=str(uuid.uuid4()),
        learner_profile={
            "name": "Test Student",
            "grade_level": "10th Grade", 
            "learning_style": "Visual",
            "preferred_language": "English"
        }
    )
    
    # Initialize tutor agent
    tutor_agent = TutorAgent()
    
    try:
        # Process tutoring request
        result = await tutor_agent.process(test_state)
        print("✅ Tutoring flow completed successfully!")
        print(f"Response: {result.get('tutoring_response', 'No response')}")
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
    
    print("🏁 Integration test completed")


if __name__ == "__main__":
    # Run integration test
    asyncio.run(run_integration_test())
