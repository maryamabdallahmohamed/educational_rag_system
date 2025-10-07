# LangSmith Integration

The Educational RAG System is integrated with LangSmith for comprehensive tracing, monitoring, and debugging of agent interactions.

## 🎯 What is LangSmith?

LangSmith is LangChain's observability platform that provides:
- **Real-time tracing** of agent execution
- **Performance monitoring** and analytics
- **Debug tools** for troubleshooting
- **Production monitoring** for live systems
- **Cost tracking** for LLM usage

## 🔧 Setup

### 1. Sign Up for LangSmith

Visit [https://smith.langchain.com](https://smith.langchain.com) and create a free account.

### 2. Get Your API Key

1. Go to Settings → API Keys
2. Create a new API key
3. Copy the key

### 3. Configure Environment Variables

Update your `.env` file (copy from `example.env`):

```env
# Enable LangSmith Tracing
LANGCHAIN_TRACING_V2=true
LANGSMITH_API_KEY=your_langsmith_api_key_here
LANGCHAIN_PROJECT=educational-rag-system
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

## 📊 What Gets Traced?

### TutorAgent Traces Include:
- **Learner Information**: ID, grade level, learning style, accuracy rate
- **Session Details**: Session ID, active status
- **Query Processing**: Input query, detected language
- **Handler Calls**: Which tools were invoked (session manager, explanation engine, practice generator, etc.)
- **LLM Interactions**: Prompts sent, responses received, token usage
- **Performance Metrics**: Response time, success/failure status
- **Personalization**: How content was adapted for the learner

### ContentProcessorAgent Traces Include:
- **Query Details**: Query text, language detection
- **RAG Operations**: Document retrieval, relevance scoring
- **Document Processing**: Chunks analyzed, similarity scores
- **Handler Calls**: RAG chat, explainable units generation
- **Performance**: Processing time, success status

## 🚀 Running Tests with Tracing

### Manual Testing

Run the manual test scenarios:

```bash
# Run all 6 test scenarios
python tests/manual_test_tutor.py

# Run specific scenario (1-6)
python tests/manual_test_tutor.py 1
python tests/manual_test_tutor.py 4

# Show help
python tests/manual_test_tutor.py --help
```

### Test Scenarios

1. **Visual Learner - Photosynthesis**: Tests personalized explanation
2. **Struggling Learner - Fractions**: Tests content simplification
3. **Advanced Learner - Calculus**: Tests advanced content delivery
4. **Practice Generation**: Tests practice problem creation
5. **Step-by-Step Explanation**: Tests detailed problem solving
6. **Content Adaptation**: Tests on-the-fly adaptation

## 🔍 Viewing Traces

### Access Your Traces

1. Go to [https://smith.langchain.com](https://smith.langchain.com)
2. Navigate to your project (e.g., "educational-rag-system")
3. View the traces list

### Understanding Trace Structure

Each trace shows:

```
tutor_agent_process (or content_processor_agent_process)
├── Agent Execution
│   ├── LLM Call 1: Reasoning
│   ├── Tool Call: manage_tutoring_session
│   ├── Tool Call: generate_explanation
│   ├── LLM Call 2: Final Response
│   └── ...
└── Metadata
    ├── learner_id
    ├── grade_level
    ├── learning_style
    ├── session_id
    ├── success: true
    └── response_length: 450
```

### Key Metrics to Monitor

- **Latency**: How long each request takes
- **Token Usage**: LLM cost tracking
- **Success Rate**: Percentage of successful requests
- **Error Patterns**: Common failure points
- **Handler Usage**: Which tools are used most

## 🐛 Debugging with LangSmith

### Finding Issues

1. **Filter by Status**: Show only failed runs
2. **Search by Metadata**: Find specific learner or session
3. **Timeline View**: See execution flow
4. **Token Analysis**: Identify expensive calls

### Common Debug Scenarios

**Problem**: Learner not getting personalized content
- **Check**: Metadata shows correct learner_profile?
- **Check**: Was LearnerModelManager tool called?
- **Check**: What context was passed to LLM?

**Problem**: Slow responses
- **Check**: Latency breakdown by component
- **Check**: Token counts in LLM calls
- **Check**: Handler execution times

**Problem**: Incorrect answers
- **Check**: Input preprocessing (language detection)
- **Check**: Tool selection and parameters
- **Check**: LLM prompt and response

## 📈 Production Monitoring

### Real-World Usage

With LangSmith enabled in production:
- Monitor actual user interactions
- Track performance over time
- Identify edge cases
- Measure improvement from updates

### Dashboards

Create custom dashboards to track:
- Average response time by agent
- Success rate trends
- Most common queries
- Handler usage patterns
- Cost per interaction

### Alerts (LangSmith Pro)

Set up alerts for:
- Error rate spikes
- Latency increases
- Unusual token usage
- Specific error patterns

## 🔒 Privacy & Security

### Data Handling

LangSmith traces include:
- Query text
- Generated responses
- Learner metadata (IDs, preferences)
- System performance metrics

**Note**: Ensure compliance with your privacy policy and data protection regulations.

### Disabling Tracing

To disable tracing (e.g., for sensitive data):

```env
LANGCHAIN_TRACING_V2=false
```

The system works perfectly without tracing enabled.

## 💡 Best Practices

### Development

1. **Enable tracing** for all development work
2. **Review traces** before committing changes
3. **Test edge cases** and check traces
4. **Document issues** found via traces

### Testing

1. **Run manual tests** with tracing enabled
2. **Check trace metadata** is meaningful
3. **Verify handler calls** are correct
4. **Monitor performance** of new features

### Production

1. **Start with sampling** (trace 10% of requests)
2. **Monitor key metrics** daily
3. **Set up alerts** for critical issues
4. **Review traces weekly** for insights

## 🤝 Integration with CI/CD

### Pre-Deployment Checks

Add to your CI/CD pipeline:

```bash
# Run tests with tracing
LANGCHAIN_TRACING_V2=true python tests/manual_test_tutor.py

# Check for regressions in trace data
# (Custom scripts can analyze trace metrics)
```

### Deployment Validation

After deployment:
1. Check first 10 traces manually
2. Compare metrics to baseline
3. Monitor error rates
4. Verify personalization working

## 📚 Resources

- [LangSmith Documentation](https://docs.smith.langchain.com/)
- [LangSmith Python SDK](https://github.com/langchain-ai/langsmith-sdk)
- [LangChain Tracing Guide](https://python.langchain.com/docs/langsmith/)
- [Project Dashboard](https://smith.langchain.com)

## 🆘 Troubleshooting

### Traces Not Appearing

1. Check `LANGCHAIN_TRACING_V2=true`
2. Verify `LANGSMITH_API_KEY` is valid
3. Check internet connectivity
4. Look for errors in logs

### Missing Metadata

1. Verify state has expected fields
2. Check `get_run_metadata()` logic
3. Ensure handlers are setting state
4. Review trace decorator parameters

### Performance Issues

1. Tracing adds ~50-100ms overhead
2. Consider sampling in production
3. Check LangSmith service status
4. Verify network latency

---

## Summary

LangSmith provides powerful observability for our educational agents:
- ✅ Trace every interaction
- ✅ Debug issues quickly
- ✅ Monitor production
- ✅ Improve performance
- ✅ Track costs

Enable it for development, testing, and production monitoring!
