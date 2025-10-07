# Tests

## 📚 Test Structure

### Unit Tests
- `test_tutor_agent.py` - Comprehensive unit tests for TutorAgent handlers
- `conftest.py` - Shared pytest fixtures and configuration
- `chunk_test.py` - Document chunking tests
- `test_repo.py` - Repository tests

### Manual Testing
- `manual_test_tutor.py` - Interactive test scenarios for TutorAgent with LangSmith tracing

## 🧪 Running Tests

### Unit Tests

```bash
# Run all unit tests
pytest tests/test_tutor_agent.py -v

# Run specific handler tests
pytest tests/test_tutor_agent.py::TestSessionManager -v
pytest tests/test_tutor_agent.py::TestLearnerModelManager -v
pytest tests/test_tutor_agent.py::TestInteractionLogger -v
pytest tests/test_tutor_agent.py::TestCPABridgeHandler -v
pytest tests/test_tutor_agent.py::TestExplanationEngine -v
pytest tests/test_tutor_agent.py::TestPracticeGenerator -v

# Run with coverage
pytest tests/test_tutor_agent.py --cov=backend.core.agents.tutor_handlers -v
```

### Manual Testing with LangSmith

The manual test script provides 6 real-world tutoring scenarios:

```bash
# Run all scenarios
python tests/manual_test_tutor.py

# Run specific scenario (1-6)
python tests/manual_test_tutor.py 1

# Show help
python tests/manual_test_tutor.py --help
```

#### Test Scenarios

1. **Visual Learner - Photosynthesis**
   - Tests personalized explanation for visual learning style
   - Verifies adaptation to grade level and preferences

2. **Struggling Learner - Fractions**
   - Tests content simplification for struggling learners
   - Verifies difficulty adjustment and supportive language

3. **Advanced Learner - Calculus**
   - Tests advanced content delivery
   - Verifies challenging material for high performers

4. **Practice Generation - Quadratic Equations**
   - Tests practice problem generation
   - Verifies difficulty calibration and variety

5. **Step-by-Step Explanation**
   - Tests detailed problem-solving guidance
   - Verifies sequential explanation style

6. **Content Adaptation - Simplification**
   - Tests on-the-fly content adaptation
   - Verifies response to explicit adaptation requests

## 🔍 LangSmith Tracing

### Setup

1. Sign up at [https://smith.langchain.com](https://smith.langchain.com)
2. Get your API key
3. Update `.env`:
   ```env
   LANGCHAIN_TRACING_V2=true
   LANGSMITH_API_KEY=your_key_here
   LANGCHAIN_PROJECT=educational-rag-system
   ```

### Viewing Traces

When LangSmith is enabled, all manual tests are traced:

1. Run any manual test scenario
2. Go to [https://smith.langchain.com](https://smith.langchain.com)
3. Navigate to your project
4. View the trace for each scenario

### What to Check in Traces

✅ **Agent Flow**
- Agent reasoning steps
- Tool selection (which handlers were called)
- LLM interactions

✅ **Personalization**
- Learner profile metadata visible
- Content adapted correctly
- Appropriate difficulty level

✅ **Performance**
- Total response time
- Handler execution times
- Token usage and costs

✅ **Error Handling**
- Graceful failure handling
- Error metadata captured
- Fallback responses

## 🎯 Testing Strategy

### Unit Tests ✅
- **Purpose**: Validate individual handler logic in isolation
- **Approach**: Mock all dependencies (repositories, models, LLMs)
- **Coverage**: All 6 handlers with comprehensive test cases
- **Status**: Maintained for regression testing

### Manual Testing with LangSmith 🚀
- **Purpose**: Validate real-world tutoring workflows
- **Approach**: End-to-end testing with actual LLMs and tracing
- **Benefits**:
  - Test complete agent workflows
  - Trace full conversation flows
  - Monitor LLM performance
  - Debug production-like issues
  - No complex database mocking needed

### Production Monitoring 📊
- **Tool**: LangSmith production tracing
- **Tracks**:
  - Real user interactions
  - Agent decisions and reasoning
  - Performance metrics over time
  - Error rates and patterns
  - Personalization effectiveness

## 📈 Best Practices

### Before Committing Code

1. ✅ Run unit tests: `pytest tests/test_tutor_agent.py -v`
2. ✅ Run at least 2 manual scenarios
3. ✅ Check traces in LangSmith
4. ✅ Verify metadata is captured correctly
5. ✅ Check for regressions in performance

### When Adding Features

1. Add unit tests for new handlers
2. Create manual test scenario if needed
3. Test with LangSmith tracing enabled
4. Document new metadata being traced
5. Update this README if needed

### Debugging Issues

1. **Unit test failing?**
   - Check handler logic
   - Verify mock setup
   - Check assertions

2. **Manual test failing?**
   - Check LangSmith trace
   - Review agent reasoning
   - Check tool selection
   - Verify LLM responses

3. **Production issue?**
   - Find trace in LangSmith
   - Compare with passing traces
   - Check metadata differences
   - Review error patterns

## 🔧 Test Configuration

### Environment Variables

Tests respect these environment variables:

```env
# Database
DATABASE_URL=postgresql://...
SUPABASE_URL=postgresql://...

# LLM
grok_api=your_groq_api_key

# LangSmith (optional)
LANGCHAIN_TRACING_V2=true
LANGSMITH_API_KEY=your_key
LANGCHAIN_PROJECT=educational-rag-system
```

### Test Data

Manual tests use synthetic learner profiles:
- No real student data
- Predefined scenarios
- Consistent test cases
- Safe for development

## 📚 Additional Resources

- [LangSmith Integration Guide](../LANGSMITH_INTEGRATION.md) - Detailed tracing documentation
- [TutorAgent Documentation](../backend/core/agents/tutor_agent.py) - Agent implementation
- [Handler Documentation](../backend/core/agents/tutor_handlers/) - Individual handler docs

## 🆘 Troubleshooting

### Tests Won't Run

```bash
# Check Python environment
python --version  # Should be 3.13+

# Install dependencies
pip install -r requirements.txt

# Check imports
python -c "from backend.core.agents.tutor_agent import TutorAgent"
```

### LangSmith Not Tracing

1. Check `LANGCHAIN_TRACING_V2=true` in `.env`
2. Verify API key is valid
3. Check internet connectivity
4. Look for errors in console output

### Database Connection Issues

1. Check `.env` has correct credentials
2. Verify network access to database
3. Check database is running
4. Review connection logs

---

## Summary

- ✅ **Unit Tests**: Fast, isolated handler testing
- ✅ **Manual Tests**: Real-world scenario validation  
- ✅ **LangSmith**: Production-grade tracing and monitoring
- ✅ **Documentation**: Clear guides for all testing approaches

Happy testing! 🎉
