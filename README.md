# Content Processing Agent System

A sophisticated AI-powered content processing system built with LangGraph that provides document analysis, RAG-based chat, and educational content generation capabilities.

## 🚀 Features

- **Document Analysis**: Upload and analyze various document formats
- **RAG Chat**: Intelligent question-answering based on uploaded documents
- **General Chat**: AI assistant for general queries when no documents are available
- **Explainable Learning Units**: Generate structured educational content from documents
- **Multi-language Support**: Supports both English and Arabic
- **Modular Architecture**: Handler-based system for easy extensibility

## 📁 Project Structure

```
├── backend/                    # Core backend application
│   ├── core/                  # Main application logic
│   │   ├── agents/           # AI agents and handlers
│   │   │   ├── cpa_handlers/ # Content processor agent handlers
│   │   │   │   ├── document_analysis_handler.py
│   │   │   │   ├── explainable_units_handler.py
│   │   │   │   └── rag_chat_handler.py
│   │   │   ├── base_handler.py
│   │   │   └── content_processor_agent.py
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
   DATABASE_URL=DB_URL

   ```

## 🚀 Usage

### Running the Application

The application is built on LangGraph and can be run using the LangGraph CLI:

```bash
# Start the LangGraph server
langgraph up
```

The application will be available at the configured endpoint.

### FastAPI Service

A lightweight FastAPI service is available for testing the core nodes through tools such as Postman:

```bash
uvicorn backend.api.main:app --reload
```

Available endpoints:

- `GET /health` – basic health check
- `POST /api/upload` – upload and store a document:
   ```bash
   # Using curl with multipart/form-data
   curl -X POST http://localhost:8000/api/upload \
     -F "file=@document.pdf"
   ```
   Response: `{"status": "uploaded", "filename": "document.pdf"}`

- `POST /api/router` – route a query to determine the operation type:
   ```bash
   curl -X POST http://localhost:8000/api/router \
     -F "query=What is in this document?"
   ```
   Response: `{"decision": "qa"}` or `{"decision": "summarize"}`

- `POST /api/qa` – answer questions using the latest uploaded document:
   ```bash
   curl -X POST http://localhost:8000/api/qa \
     -F "query=What are the main points?"
   ```
   Response: `{"query": "What are the main points?", "result": "...answer..."}`

- `POST /api/summarize` – summarize the latest uploaded document:
   ```bash
   curl -X POST http://localhost:8000/api/summarize \
     -F "query=Summarize this document"
   ```
   Response: `{"query": "Summarize this document", "result": "...summary..."}`

- `POST /api/cpa_agent` – run the Content Processor Agent on the latest uploaded document:
   ```bash
   curl -X POST http://localhost:8000/api/cpa_agent \
     -F "query=Analyze and process this content"
   ```
   Response: `{"query": "Analyze and process this content", "result": "...analysis..."}`

**Note**: The service uses an in-memory document store. Upload a document first using `/api/upload`, then use the other endpoints to process it.

### 🐳 Docker Deployment

#### Prerequisites

- Docker installed on your system
- Docker Desktop or Docker Engine running

#### Building the Docker Image

```bash
# Build the image
docker build -t educational-rag-backend:latest .

# Build with specific tag (recommended for versioning)
docker build -t educational-rag-backend:v1.0 .
```

#### Running the Container

**Option 1: Using environment file (Recommended)**
```bash
docker run -p 8000:8000 \
  --env-file .env \
  educational-rag-backend:latest
```

**Option 2: Using individual environment variables**
```bash
docker run -p 8000:8000 \
  -e grok_api=your_groq_api_key \
  -e DATABASE_URL=postgresql://user:password@host:port/dbname \
  -e LANGSMITH_API_KEY=your_langsmith_key \
  -e API_HOST=0.0.0.0 \
  -e API_PORT=8000 \
  educational-rag-backend:latest
```

**Option 3: Running in detached mode (Background)**
```bash
docker run -d \
  -p 8000:8000 \
  --name rag-backend \
  --env-file .env \
  educational-rag-backend:latest

# View logs
docker logs -f rag-backend

# Stop container
docker stop rag-backend
```

#### Docker Compose (Production Recommended)

Create a `docker-compose.yml` file:

```yaml
version: '3.8'

services:
  backend:
    build: .
    image: educational-rag-backend:latest
    container_name: educational-rag-backend
    ports:
      - "8000:8000"
    env_file: .env
    volumes:
      - ./cache:/app/cache
      - ./logs:/app/logs
    environment:
      - PYTHONUNBUFFERED=1
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

volumes:
  cache:
  logs:
```

Then run:
```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

#### Docker Environment Variables

The following environment variables should be set in your `.env` file:

```env
# Groq API Configuration
grok_api=your_groq_api_key_here

# Database Configuration
DATABASE_URL=postgresql://username:password@host:port/database

# LangSmith Configuration (optional)
LANGSMITH_API_KEY=your_langsmith_key_here

# API Server Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=false

# Application Configuration
DEVICE=cpu
CACHE_DIR=/app/cache
GLOBAL_K=5
```

#### Accessing the Application

Once running, the API will be available at:
- **API Base URL**: `http://localhost:8000`
- **Health Check**: `http://localhost:8000/health`
- **API Documentation**: `http://localhost:8000/docs` (Swagger UI)
- **Alternative Documentation**: `http://localhost:8000/redoc` (ReDoc)

#### GPU Support (Optional)

If you have an NVIDIA GPU and want to use it:

```bash
# Install NVIDIA Container Runtime
# For Docker Desktop, enable GPU support in preferences

# Run with GPU support
docker run --gpus all \
  -p 8000:8000 \
  --env-file .env \
  -e DEVICE=cuda \
  educational-rag-backend:latest
```

#### Docker Image Optimization

The Dockerfile uses multi-stage builds to optimize image size:
- **Builder stage**: Installs build dependencies and compiles packages
- **Runtime stage**: Contains only runtime dependencies

Final image size is significantly reduced by excluding build tools.

#### Troubleshooting Docker

**Issue: Container exits immediately**
```bash
# Check logs
docker logs container_name

# Run with interactive terminal
docker run -it --env-file .env educational-rag-backend:latest
```

**Issue: Port already in use**
```bash
# Use a different port
docker run -p 8001:8000 --env-file .env educational-rag-backend:latest
```

**Issue: Environment variables not loaded**
```bash
# Verify .env file exists
ls -la .env

# Check environment variables in container
docker run -it --env-file .env educational-rag-backend:latest env | grep -E "(grok_api|DATABASE_URL)"
```

**Issue: Database connection refused**
```bash
# Ensure database is accessible
# For local postgres: use host.docker.internal instead of localhost
DATABASE_URL=postgresql://user:password@host.docker.internal:5432/dbname
```

### Core Components

#### 1. Content Processor Agent
The main orchestrator that routes requests to appropriate handlers:

```python
from backend.core.agents.content_processor_agent import ContentProcessorAgent

agent = ContentProcessorAgent()
result = await agent.process(state)
```

#### 2. Document Analysis Handler
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
- **LangSmith**: Optional integration for request tracing
- **Error Handling**: Comprehensive error handling with fallback responses

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