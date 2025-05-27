# QuickQuiz-GPT 🧠✨

[![CI](https://github.com/atirpetkar/quickquiz/actions/workflows/ci.yml/badge.svg)](https://github.com/atirpetkar/quickquiz/actions/workflows/ci.yml)
[![Deploy](https://github.com/atirpetkar/quickquiz/actions/workflows/deploy.yml/badge.svg)](https://github.com/atirpetkar/quickquiz/actions/workflows/deploy.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An AI-powered microservice that transforms any instructional content (PDFs, URLs, text) into high-quality, difficulty-ranked quiz questions with automatic evaluation and caching.

## 🚀 Features

- **Smart Content Ingestion**: Extract and process text from PDFs, URLs, and documents
- **AI-Powered Question Generation**: Create MCQs with explanations, difficulty levels, and Bloom's taxonomy classification
- **Self-Evaluation System**: Built-in quality assessment using LLM-as-judge methodology
- **Vector Search**: Semantic search through content using pgvector embeddings
- **REST & WebSocket APIs**: Clean, documented APIs with OpenAPI specifications
- **Intelligent Caching**: Redis-backed caching to avoid regenerating identical content
- **Docker Ready**: Fully containerized for easy deployment
- **Production Ready**: Comprehensive testing, CI/CD, and monitoring

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Content       │    │   QuickQuiz     │    │   Vector        │
│   Sources       │───▶│   Processor     │───▶│   Database      │
│ (PDF/URL/Text)  │    │                 │    │  (pgvector)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    Question     │    │   AI Question   │    │    Quality      │
│    Database     │◀───│   Generator     │───▶│   Evaluator     │
│   (PostgreSQL)  │    │   (LLM Chain)   │    │ (LLM-as-Judge)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                      ┌─────────────────┐
                      │   REST API      │
                      │   (FastAPI)     │
                      └─────────────────┘
```

## 📋 Prerequisites

- Python 3.11+
- PostgreSQL with pgvector extension
- Redis (optional, for caching)
- OpenAI API key or compatible LLM endpoint

## 🛠️ Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/atirpetkar/quickquiz.git
cd quickquiz
```

### 2. Environment Setup

Create a `.env` file in the project root:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/quickquiz
REDIS_URL=redis://localhost:6379/0

# AI Models
OPENAI_API_KEY=your_openai_api_key_here
GENERATION_MODEL=gpt-4
EVALUATION_MODEL=gpt-3.5-turbo

# API Configuration
API_KEY=your_secret_api_key
DEBUG=true
```

### 3. Using Docker (Recommended)

```bash
# Development environment
docker-compose -f docker/docker-compose.dev.yml up

# Production environment
docker-compose -f docker/docker-compose.yml up
```

### 4. Manual Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup database
python scripts/setup_db.py

# Run development server
python scripts/run_dev.py
```

## 📚 API Usage

### Ingest Content

```bash
# Ingest PDF from URL
curl -X POST "http://localhost:8000/api/v1/ingest" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "source_url": "https://example.com/document.pdf",
    "source_type": "pdf",
    "title": "Physics Chapter 1"
  }'
```

### Generate Quiz Questions

```bash
# Generate questions on a specific topic
curl -X POST "http://localhost:8000/api/v1/generate" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Newton's Laws of Motion",
    "difficulty": "medium",
    "count": 5,
    "question_type": "multiple_choice"
  }'
```

### Evaluate Custom Questions

```bash
# Evaluate question quality
curl -X POST "http://localhost:8000/api/v1/evaluate" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is Newton's first law?",
    "options": ["A law about motion", "Law of inertia", "F=ma", "Action-reaction"],
    "correct_answer": "Law of inertia",
    "explanation": "Newton's first law states that an object at rest stays at rest..."
  }'
```

### Retrieve Questions

```bash
# Get question by ID
curl -X GET "http://localhost:8000/api/v1/questions/123" \
  -H "X-API-Key: your_api_key"

# Search questions
curl -X GET "http://localhost:8000/api/v1/questions?topic=physics&difficulty=easy" \
  -H "X-API-Key: your_api_key"
```

## 🧪 Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/quickquiz --cov-report=html

# Run specific test suite
pytest tests/test_services/
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Add new table"

# Apply migrations
alembic upgrade head
```

## 📊 API Documentation

Once the server is running, visit:

- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## 🔧 Configuration

Key configuration options in `src/quickquiz/core/config.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| `GENERATION_MODEL` | `gpt-4` | Model for question generation |
| `EVALUATION_MODEL` | `gpt-3.5-turbo` | Model for quality evaluation |
| `MIN_QUALITY_SCORE` | `0.9` | Minimum acceptable quality score |
| `CACHE_TTL` | `3600` | Cache time-to-live in seconds |
| `MAX_QUESTIONS_PER_REQUEST` | `20` | Maximum questions per generation request |

## 🚀 Deployment

### Using Docker

```bash
# Build production image
docker build -f docker/Dockerfile -t quickquiz-gpt .

# Run container
docker run -p 8000:8000 --env-file .env quickquiz-gpt
```

### Using Render

1. Connect your GitHub repository to Render
2. Set environment variables in Render dashboard
3. Deploy using the provided `render.yaml` configuration

### Using Railway/Heroku

The application includes a `Procfile` and is ready for deployment on platforms like Railway or Heroku.

## 📈 Monitoring & Observability

- **Health Checks**: `/health` endpoint for container health
- **Metrics**: Prometheus-compatible metrics at `/metrics`
- **Logging**: Structured JSON logging with configurable levels
- **Tracing**: OpenTelemetry integration for distributed tracing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Write tests for new features
- Update documentation as needed
- Ensure all CI checks pass

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI for providing powerful language models
- FastAPI for the excellent web framework
- pgvector for efficient vector operations
- The open-source community for inspiration and tools

## 📞 Support

- **Documentation**: [Full documentation](docs/)
- **Issues**: [GitHub Issues](https://github.com/atirpetkar/quickquiz/issues)
- **Discussions**: [GitHub Discussions](https://github.com/atirpetkar/quickquiz/discussions)

---

**Built with ❤️ for educators and developers**
