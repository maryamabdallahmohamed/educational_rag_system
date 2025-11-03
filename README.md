# Content Processing Agent System

A sophisticated AI-powered content processing system built with LangGraph that provides document analysis, RAG-based chat, and educational content generation capabilities.

## 🚀 Features

- **Document Analysis**: Upload and analyze various document formats
- **RAG Chat**: Intelligent question-answering based on uploaded documents
- **General Chat**: AI assistant for general queries when no documents are available
- **Explainable Learning Units**: Generate structured educational content from documents
- **Personalized Tutoring**: Adaptive AI tutor with learner profiling and personalized explanations
- **Multi-language Support**: Supports both English and Arabic
- **Modular Architecture**: Handler-based system for easy extensibility
- **🔍 LangSmith Tracing**: Production monitoring, debugging, and performance analysis

## 📁 Project Structure

```
├── backend/                    # Core backend application
│   ├── core/                  # Main application logic
│   │   ├── agents/           # AI agents and handlers
│   │   │   ├── cpa_handlers/ # Content processor agent handlers
│   │   │   │   ├── document_analysis_handler.py
│   │   │   │   ├── explainable_units_handler.py
│   │   │   │   └── rag_chat_handler.py
│   │   │   ├── tutor_handlers/ # Tutor agent handlers (integrated with CPA)
│   │   │   │   ├── session_manager.py
│   │   │   │   ├── learner_model_manager.py
│   │   │   │   ├── interaction_logger.py
│   │   │   │   ├── cpa_bridge.py
│   │   │   │   ├── explanation_engine.py
│   │   │   │   └── practice_generator.py
│   │   │   ├── base_handler.py
│   │   │   ├── content_processor_agent.py # Main agent with integrated tutoring
│   │   │   └── tutor_agent.py          # Sub-agent for personalized learning
│   │   ├── nodes/            # LangGraph workflow nodes
│   │   ├── states/           # State management
│   │   ├── utils/            # Core utilities
│   │   └── graph.py          # Main LangGraph workflow
│   ├── db/                   # Database connections
│   ├── loaders/              # Document and prompt loaders
│   │   ├── document_loaders/
│   │   └── prompt_loaders/
│   ├── models/               # AI model integrations
│   │   ├── embedders/        # Text embedding models
│   │   ├── llms/            # Language models (Groq)
│   │   └── reranker_model/  # Document reranking
│   └── utils/               # Utility functions
├── frontend/                 # Frontend application (if applicable)
├── logs/                    # Application logs
├── .env                     # Environment variables (not in repo)
├── example.env              # Environment variables template
├── requirements.txt         # Python dependencies
└── langgraph.json          # LangGraph configuration
```

## 🛠️ Installation

### Prerequisites

- Python 3.8+
- PostgreSQL database (or Supabase)
- Groq API key

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd content-processing-agent
   ```

2. **Create virtual environment**
   ```bash
   python -m venv myenv
   source myenv/bin/activate  # On Windows: myenv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   ```bash
   cp example.env .env
   # Edit .env with your actual credentials
   ```

5. **Required Environment Variables**
   ```env
   # Groq API Configuration
   grok_api=your_groq_api_key_here
   
   # Database Configuration
   user=your_db_user
   password=your_db_password
   host=your_db_host
   port=your_db_port
   dbname=your_db_name
   
   # Optional: Supabase Configuration
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   
   # Optional: LangSmith for tracing
   LANGSMITH_API_KEY=your_langsmith_key
   ```

## 🚀 Usage

### Running the Application

The application is built on LangGraph and can be run using the LangGraph CLI:

```bash
# Start the LangGraph server
langgraph up
```

The application will be available at the configured endpoint.

### Core Components

#### 1. Content Processor Agent (Main Orchestrator)
The main agent that handles all requests and intelligently delegates to appropriate handlers:

```python
from backend.core.agents.content_processor_agent import ContentProcessorAgent

agent = ContentProcessorAgent()
result = await agent.process(state)
```

**Key Features:**
- **Intelligent Routing**: Automatically detects tutoring requests and delegates to integrated TutorAgent
- **Document Processing**: Handles file uploads, analysis, and structured content creation
- **RAG Operations**: Manages document-based question answering and conversations
- **General Chat**: Provides conversational AI capabilities

#### 2. Integrated Tutor Agent (Sub-Agent)
The TutorAgent now works as a specialized sub-agent within the ContentProcessorAgent:

```python
# TutorAgent is automatically invoked for educational queries like:
# "Explain photosynthesis", "Help me with algebra", "I need practice problems"
```

**Tutoring Capabilities:**
- **Personalized Learning**: Adapts to individual learner profiles and styles
- **Session Management**: Maintains learning context across interactions
- **Practice Generation**: Creates customized exercises and assessments
- **Progress Tracking**: Monitors learning outcomes and adjusts difficulty
- **Multi-Modal Support**: Provides visual, auditory, and kinesthetic learning approaches

#### 3. Router Intelligence
The system intelligently routes requests through a 3-tier architecture:

1. **Router Node**: Classifies requests into `qa`, `summarization`, or `content_processor_agent`
2. **Content Processor Agent**: Further analyzes requests and delegates tutoring queries to TutorAgent
3. **Specialized Processing**: Handles the request with the most appropriate agent/handler

#### 4. Document Analysis Handler
Analyzes uploaded documents and extracts metadata:

- Supports multiple document formats
- Extracts key information and structure
- Provides document summaries

#### 3. RAG Chat Handler
Provides intelligent chat capabilities:

- **RAG Mode**: Uses uploaded documents as context
- **General Mode**: Fallback for general questions
- **Relevance Scoring**: Automatically determines when to use documents

#### 4. Explainable Units Handler
Generates structured educational content:

- Creates learning units from documents
- Supports adaptation instructions
- Multilingual content generation

### API Usage Examples

#### Document Upload and Analysis
```python
state = {
    "query": "Analyze this document",
    "documents": [uploaded_documents],
    "operation": "document_analysis"
}
result = await agent.process(state)
```

#### RAG-based Question Answering
```python
state = {
    "query": "What are the main points in the document?",
    "documents": [uploaded_documents]
}
result = await agent.process(state)
```

#### General Chat
```python
state = {
    "query": "What is machine learning?",
    "documents": []  # No documents - will use general chat
}
result = await agent.process(state)
```

#### Generate Learning Units
```python
state = {
    "query": "Create learning units from this content",
    "documents": [uploaded_documents],
    "adaptation_instruction": "Focus on beginner level"
}
result = await agent.process(state)
```

## 🔧 Configuration

### Model Configuration
The system uses Groq LLMs by default. Configure in `backend/models/llms/groq_llm.py`:

```python
GroqLLM(
    model="qwen/qwen3-32b",  # Model selection
    temperature=0,           # Creativity level
    max_tokens=None,        # Response length
    max_retries=2           # Error handling
)
```

### Prompt Customization
Prompts are stored in YAML files under `backend/loaders/prompt_loaders/prompts/`:

- `content_processor_agent.yaml` - Main agent prompt
- `rag_chat.yaml` - RAG chat prompt
- `general_chat.yaml` - General chat prompt

### Handler Extension
To add new functionality, create a new handler:

```python
from backend.core.agents.base_handler import BaseHandler

class CustomHandler(BaseHandler):
    def tool(self):
        return Tool(
            name="custom_tool",
            description="Custom functionality",
            func=self._process_wrapper
        )
    
    def _process(self, query: str) -> str:
        # Your custom logic here
        return "Custom response"
```

## 📊 Monitoring and Logging

- **Logs**: Application logs are stored in `logs/app.log`
- **LangSmith**: Optional integration for request tracing and production monitoring
- **Error Handling**: Comprehensive error handling with fallback responses

### LangSmith Integration

This system includes production-grade tracing with LangSmith for:
- Real-time monitoring of agent workflows
- Debugging personalized tutoring sessions
- Performance analysis and optimization
- Cost tracking (token usage)

To enable LangSmith tracing:
1. Sign up at [https://smith.langchain.com](https://smith.langchain.com)
2. Get your API key
3. Update `.env`:
   ```env
   LANGCHAIN_TRACING_V2=true
   LANGSMITH_API_KEY=your_key_here
   LANGCHAIN_PROJECT=educational-rag-system
   ```

**See [LANGSMITH_INTEGRATION.md](LANGSMITH_INTEGRATION.md) for detailed documentation.**

## 🧪 Testing

### Unit Tests
```bash
# Run all tests
pytest tests/test_tutor_agent.py -v

# Run specific handler tests
pytest tests/test_tutor_agent.py::TestSessionManager -v
```

### Manual Testing with LangSmith
```bash
# Run all tutoring scenarios
python tests/manual_test_tutor.py

# Run specific scenario (1-6)
python tests/manual_test_tutor.py 1
```

The manual test script provides 6 real-world tutoring scenarios:
1. Visual Learner - Photosynthesis
2. Struggling Learner - Fractions
3. Advanced Learner - Calculus
4. Practice Generation - Quadratic Equations
5. Step-by-Step Explanation
6. Content Adaptation - Simplification

**See [tests/README.md](tests/README.md) for complete testing documentation.**

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

[Add your license information here]

## 🆘 Troubleshooting

### Common Issues

1. **API Key Errors**
   - Ensure your Groq API key is correctly set in `.env`
   - Check API key permissions and quotas

2. **Database Connection Issues**
   - Verify database credentials in `.env`
   - Ensure database is accessible from your network

3. **Import Errors**
   - Activate your virtual environment
   - Install all requirements: `pip install -r requirements.txt`

4. **Document Processing Errors**
   - Check document format compatibility
   - Verify file size limits

### Getting Help

- Check the logs in `logs/app.log` for detailed error information
- Ensure all environment variables are properly configured
- Verify that all required services (database, APIs) are accessible

## 🔮 Future Enhancements

- Support for additional document formats
- Enhanced multilingual capabilities
- Advanced analytics and reporting
- Integration with more LLM providers
- Real-time collaboration features