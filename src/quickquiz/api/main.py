"""FastAPI main application for QuickQuiz-GPT."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ..core.config import settings
from ..core.exceptions import DocumentIngestionError, QuickQuizException
from .routes import evaluate, generate, ingest, questions

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting QuickQuiz-GPT API")
    yield
    # Shutdown
    logger.info("Shutting down QuickQuiz-GPT API")


app = FastAPI(
    title="QuickQuiz-GPT",
    description="AI-powered quiz question generation microservice",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=getattr(settings, "cors_origins", ["*"]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(DocumentIngestionError)
async def document_ingestion_exception_handler(
    request: Request, exc: DocumentIngestionError
):
    """Handle document ingestion errors."""
    return JSONResponse(
        status_code=422,
        content={"error": "Document Ingestion Error", "detail": str(exc)},
    )


@app.exception_handler(QuickQuizException)
async def quickquiz_exception_handler(request: Request, exc: QuickQuizException):
    """Handle general QuickQuiz errors."""
    return JSONResponse(
        status_code=500, content={"error": "QuickQuiz Error", "detail": str(exc)}
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "HTTP Error", "detail": exc.detail},
    )


# Include routers
app.include_router(ingest.router, prefix="/api/v1")
app.include_router(questions.router, prefix="/api/v1")
app.include_router(generate.router, prefix="/api/v1")
app.include_router(evaluate.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint for health check."""
    return {
        "message": "QuickQuiz-GPT API is running",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "QuickQuiz-GPT", "version": "1.0.0"}


@app.get("/api/v1/health")
async def api_health_check():
    """API health check endpoint."""
    try:
        # You can add database connectivity checks here
        return {
            "status": "healthy",
            "api_version": "v1",
            "components": {
                "api": "healthy",
                "database": "healthy",  # TODO: Add actual DB check
                "embedding_service": "healthy",  # TODO: Add actual service check
            },
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503, content={"status": "unhealthy", "error": str(e)}
        )
