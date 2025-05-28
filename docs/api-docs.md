# QuickQuiz-GPT API Documentation

## Overview

QuickQuiz-GPT is a FastAPI-based service that automatically generates quiz questions from documents and provides self-evaluation capabilities. The API supports document ingestion from PDFs and URLs, intelligent question generation using LLMs, and automated quality assessment.

## Base URL

```
Production: https://quickquiz-gpt.onrender.com/api/v1
Development: http://localhost:8000/api/v1
```

## Authentication

### API Key Authentication (Optional)

If authentication is enabled, include your API key in the request headers:

```
Authorization: Bearer YOUR_API_KEY
```

### Rate Limiting

- 100 requests per minute per IP address
- 1000 requests per hour per API key
- Rate limit headers are included in responses

## Error Handling

### Standard Error Response

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": "Additional error details",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

### HTTP Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `429` - Rate Limit Exceeded
- `500` - Internal Server Error
- `503` - Service Unavailable

## Document Management

### Upload Document

```http
POST /documents/upload
Content-Type: multipart/form-data
```

**Parameters:**
- `file` (file) - PDF file to upload
- `title` (string, optional) - Document title
- `tags` (array[string], optional) - Document tags

**Response:**
```json
{
  "document_id": "uuid",
  "title": "Document Title",
  "status": "processing",
  "upload_timestamp": "2024-01-15T10:30:00Z",
  "file_size": 1024,
  "page_count": 10
}
```

### Ingest from URL

```http
POST /documents/ingest-url
Content-Type: application/json
```

**Request Body:**
```json
{
  "url": "https://example.com/document.pdf",
  "title": "Optional Document Title",
  "tags": ["tag1", "tag2"]
}
```

**Response:**
```json
{
  "document_id": "uuid",
  "title": "Document Title",
  "status": "processing",
  "url": "https://example.com/document.pdf",
  "ingestion_timestamp": "2024-01-15T10:30:00Z"
}
```

### Get Document Status

```http
GET /documents/{document_id}/status
```

**Response:**
```json
{
  "document_id": "uuid",
  "status": "completed",
  "progress": 100,
  "chunks_created": 25,
  "embeddings_generated": 25,
  "error": null,
  "processing_time": 45.2
}
```

### List Documents

```http
GET /documents
```

**Query Parameters:**
- `limit` (int, default: 50) - Number of documents to return
- `offset` (int, default: 0) - Pagination offset
- `status` (string, optional) - Filter by status
- `tags` (array[string], optional) - Filter by tags

**Response:**
```json
{
  "documents": [
    {
      "document_id": "uuid",
      "title": "Document Title",
      "status": "completed",
      "upload_timestamp": "2024-01-15T10:30:00Z",
      "tags": ["tag1", "tag2"],
      "chunk_count": 25
    }
  ],
  "total": 100,
  "limit": 50,
  "offset": 0
}
```

### Delete Document

```http
DELETE /documents/{document_id}
```

**Response:**
```json
{
  "message": "Document deleted successfully",
  "document_id": "uuid"
}
```

## Question Generation

### Generate Questions

```http
POST /questions/generate
Content-Type: application/json
```

**Request Body:**
```json
{
  "document_id": "uuid",
  "question_types": ["multiple_choice", "true_false", "short_answer"],
  "difficulty_levels": ["easy", "medium", "hard"],
  "num_questions": 10,
  "topic_focus": "Optional topic to focus on",
  "custom_instructions": "Additional generation instructions"
}
```

**Response:**
```json
{
  "generation_id": "uuid",
  "status": "processing",
  "estimated_completion": "2024-01-15T10:35:00Z",
  "questions_requested": 10
}
```

### Get Generation Status

```http
GET /questions/generate/{generation_id}/status
```

**Response:**
```json
{
  "generation_id": "uuid",
  "status": "completed",
  "progress": 100,
  "questions_generated": 10,
  "questions_approved": 8,
  "processing_time": 120.5,
  "error": null
}
```

### Get Generated Questions

```http
GET /questions/generate/{generation_id}/questions
```

**Response:**
```json
{
  "generation_id": "uuid",
  "questions": [
    {
      "question_id": "uuid",
      "type": "multiple_choice",
      "difficulty": "medium",
      "question": "What is the main purpose of...",
      "options": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"],
      "correct_answer": "C",
      "explanation": "The correct answer is C because...",
      "source_chunks": ["chunk_id_1", "chunk_id_2"],
      "quality_score": 0.85,
      "metadata": {
        "topic": "Topic Name",
        "generated_at": "2024-01-15T10:30:00Z"
      }
    }
  ],
  "total_questions": 10,
  "quality_metrics": {
    "average_score": 0.82,
    "distribution": {
      "easy": 3,
      "medium": 5,
      "hard": 2
    }
  }
}
```

### Custom Question Generation

```http
POST /questions/custom-generate
Content-Type: application/json
```

**Request Body:**
```json
{
  "document_id": "uuid",
  "custom_prompt": "Generate questions about specific concepts...",
  "max_questions": 5,
  "response_format": "structured"
}
```

## Question Management

### List Questions

```http
GET /questions
```

**Query Parameters:**
- `document_id` (string, optional) - Filter by document
- `type` (string, optional) - Filter by question type
- `difficulty` (string, optional) - Filter by difficulty
- `quality_score_min` (float, optional) - Minimum quality score
- `limit` (int, default: 50) - Number of questions to return
- `offset` (int, default: 0) - Pagination offset

### Get Question Details

```http
GET /questions/{question_id}
```

**Response:**
```json
{
  "question_id": "uuid",
  "type": "multiple_choice",
  "difficulty": "medium",
  "question": "What is the main purpose of...",
  "options": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"],
  "correct_answer": "C",
  "explanation": "The correct answer is C because...",
  "source_chunks": ["chunk_id_1", "chunk_id_2"],
  "quality_score": 0.85,
  "evaluation_history": [
    {
      "timestamp": "2024-01-15T10:30:00Z",
      "score": 0.85,
      "criteria": {
        "clarity": 0.9,
        "accuracy": 0.8,
        "difficulty": 0.85
      }
    }
  ],
  "metadata": {
    "topic": "Topic Name",
    "generated_at": "2024-01-15T10:30:00Z",
    "last_evaluated": "2024-01-15T10:31:00Z"
  }
}
```

### Update Question

```http
PUT /questions/{question_id}
Content-Type: application/json
```

**Request Body:**
```json
{
  "question": "Updated question text",
  "options": ["A) Updated option 1", "B) Updated option 2"],
  "correct_answer": "A",
  "explanation": "Updated explanation"
}
```

### Delete Question

```http
DELETE /questions/{question_id}
```

## Evaluation System

### Evaluate Questions

```http
POST /evaluation/evaluate
Content-Type: application/json
```

**Request Body:**
```json
{
  "question_ids": ["uuid1", "uuid2", "uuid3"],
  "evaluation_criteria": {
    "clarity": true,
    "accuracy": true,
    "difficulty": true,
    "relevance": true
  },
  "evaluator_model": "gpt-4"
}
```

**Response:**
```json
{
  "evaluation_id": "uuid",
  "status": "processing",
  "questions_count": 3,
  "estimated_completion": "2024-01-15T10:35:00Z"
}
```

### Get Evaluation Results

```http
GET /evaluation/{evaluation_id}/results
```

**Response:**
```json
{
  "evaluation_id": "uuid",
  "status": "completed",
  "results": [
    {
      "question_id": "uuid",
      "overall_score": 0.85,
      "criteria_scores": {
        "clarity": 0.9,
        "accuracy": 0.8,
        "difficulty": 0.85,
        "relevance": 0.85
      },
      "feedback": "The question is well-structured and clear...",
      "suggestions": ["Consider simplifying the language", "Add more context"],
      "approved": true
    }
  ],
  "summary": {
    "average_score": 0.83,
    "approval_rate": 0.9,
    "top_issues": ["clarity", "accuracy"]
  }
}
```

### Manual Quality Override

```http
POST /evaluation/manual-override
Content-Type: application/json
```

**Request Body:**
```json
{
  "question_id": "uuid",
  "quality_score": 0.95,
  "approved": true,
  "feedback": "Manual review: Excellent question",
  "reviewer": "human_reviewer_id"
}
```

## Analytics and Metrics

### Get Generation Metrics

```http
GET /analytics/generation-metrics
```

**Query Parameters:**
- `start_date` (string) - ISO date format
- `end_date` (string) - ISO date format
- `document_id` (string, optional) - Filter by document

**Response:**
```json
{
  "period": {
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-01-15T23:59:59Z"
  },
  "metrics": {
    "total_questions_generated": 150,
    "average_quality_score": 0.82,
    "approval_rate": 0.88,
    "generation_time_avg": 45.2,
    "question_types": {
      "multiple_choice": 75,
      "true_false": 40,
      "short_answer": 35
    },
    "difficulty_distribution": {
      "easy": 45,
      "medium": 75,
      "hard": 30
    }
  }
}
```

### Get Quality Trends

```http
GET /analytics/quality-trends
```

**Response:**
```json
{
  "trends": [
    {
      "date": "2024-01-15",
      "average_score": 0.85,
      "questions_generated": 25,
      "approval_rate": 0.88
    }
  ],
  "improvement_rate": 0.15,
  "quality_factors": {
    "most_improved": "clarity",
    "needs_attention": "difficulty_calibration"
  }
}
```

## System Management

### Health Check

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "components": {
    "database": "healthy",
    "redis": "healthy",
    "openai_api": "healthy",
    "embedding_service": "healthy"
  },
  "metrics": {
    "uptime": 86400,
    "memory_usage": 0.65,
    "cpu_usage": 0.25,
    "active_connections": 12
  }
}
```

### System Status

```http
GET /system/status
```

**Response:**
```json
{
  "system_status": "operational",
  "active_generations": 3,
  "queue_size": 5,
  "cache_hit_rate": 0.85,
  "resource_usage": {
    "database_connections": 8,
    "redis_memory": "45MB",
    "background_tasks": 2
  }
}
```

## WebSocket Endpoints

### Real-time Generation Updates

```websocket
WS /ws/generation/{generation_id}
```

**Message Types:**

**Progress Update:**
```json
{
  "type": "progress_update",
  "generation_id": "uuid",
  "progress": 65,
  "current_question": 7,
  "total_questions": 10,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Question Generated:**
```json
{
  "type": "question_generated",
  "generation_id": "uuid",
  "question": {
    "question_id": "uuid",
    "type": "multiple_choice",
    "question": "What is...",
    "quality_score": 0.85
  }
}
```

**Generation Complete:**
```json
{
  "type": "generation_complete",
  "generation_id": "uuid",
  "total_questions": 10,
  "approved_questions": 8,
  "processing_time": 120.5
}
```

### Live Evaluation Feedback

```websocket
WS /ws/evaluation/{evaluation_id}
```

**Evaluation Progress:**
```json
{
  "type": "evaluation_progress",
  "evaluation_id": "uuid",
  "questions_evaluated": 3,
  "total_questions": 10,
  "current_average_score": 0.82
}
```

## Data Models

### Document Model

```json
{
  "document_id": "string (uuid)",
  "title": "string",
  "status": "string (enum: uploading, processing, completed, failed)",
  "url": "string (optional)",
  "file_path": "string (optional)",
  "upload_timestamp": "string (ISO datetime)",
  "file_size": "integer",
  "page_count": "integer (optional)",
  "chunk_count": "integer",
  "tags": ["string"],
  "metadata": "object"
}
```

### Question Model

```json
{
  "question_id": "string (uuid)",
  "document_id": "string (uuid)",
  "type": "string (enum: multiple_choice, true_false, short_answer, essay)",
  "difficulty": "string (enum: easy, medium, hard)",
  "question": "string",
  "options": ["string"] (optional),
  "correct_answer": "string",
  "explanation": "string",
  "source_chunks": ["string"],
  "quality_score": "number (0-1)",
  "approved": "boolean",
  "metadata": "object",
  "created_at": "string (ISO datetime)",
  "updated_at": "string (ISO datetime)"
}
```

### Generation Request Model

```json
{
  "document_id": "string (uuid)",
  "question_types": ["string"],
  "difficulty_levels": ["string"],
  "num_questions": "integer",
  "topic_focus": "string (optional)",
  "custom_instructions": "string (optional)"
}
```

### Evaluation Criteria Model

```json
{
  "clarity": "boolean",
  "accuracy": "boolean",
  "difficulty": "boolean",
  "relevance": "boolean",
  "engagement": "boolean (optional)",
  "bias_check": "boolean (optional)"
}
```

## SDK Examples

### Python SDK Usage

```python
from quickquiz_gpt import QuickQuizClient

client = QuickQuizClient(api_key="your_api_key", base_url="https://api.example.com")

# Upload document
document = client.documents.upload("path/to/document.pdf")

# Generate questions
generation = client.questions.generate(
    document_id=document.document_id,
    question_types=["multiple_choice", "true_false"],
    num_questions=10
)

# Wait for completion
questions = client.questions.wait_for_generation(generation.generation_id)

# Evaluate questions
evaluation = client.evaluation.evaluate(
    question_ids=[q.question_id for q in questions]
)
```

### JavaScript SDK Usage

```javascript
import { QuickQuizClient } from 'quickquiz-gpt-js';

const client = new QuickQuizClient({
  apiKey: 'your_api_key',
  baseUrl: 'https://api.example.com'
});

// Upload document
const document = await client.documents.upload(file);

// Generate questions
const generation = await client.questions.generate({
  documentId: document.documentId,
  questionTypes: ['multiple_choice', 'true_false'],
  numQuestions: 10
});

// Get questions
const questions = await client.questions.getGeneratedQuestions(generation.generationId);
```

## Changelog

### v1.0.0 (2024-01-15)
- Initial API release
- Document ingestion from PDF and URL
- Question generation with multiple types
- Self-evaluation system
- WebSocket support for real-time updates

### v1.1.0 (Planned)
- Bulk operations support
- Advanced filtering options
- Custom evaluation criteria
- Enhanced analytics dashboard
