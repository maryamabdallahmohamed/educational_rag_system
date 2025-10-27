# ===============================
# Stage 1: Builder
# ===============================
# Build: docker build -t educational-rag-backend:latest .
# Run:   docker run -p 8000:8000 --env-file .env educational-rag-backend:latest
# Or:    docker run -p 8000:8000 -e grok_api=YOUR_KEY -e DATABASE_URL=YOUR_DB educational-rag-backend:latest
FROM python:3.11-slim AS builder

# Set working directory
WORKDIR /app

# Install system dependencies for building packages like psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better Docker caching)
COPY requirements.txt .

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# ===============================
# Stage 2: Runtime
# ===============================
FROM python:3.11-slim
WORKDIR /app

# Install runtime dependencies (lightweight)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEVICE=cpu \
    CACHE_DIR=/app/cache \
    GLOBAL_K=5 \
    API_HOST=0.0.0.0 \
    API_PORT=8000

# Copy all application code
COPY . .

# Copy .env file if it exists (optional, can be overridden at runtime)
COPY .env* ./

# Ensure cache directory exists
RUN mkdir -p /app/cache

# Expose FastAPI port
EXPOSE 8000

# Healthcheck endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the FastAPI app
CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
