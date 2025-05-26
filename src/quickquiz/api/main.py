"""FastAPI main application for QuickQuiz-GPT."""

from fastapi import FastAPI

app = FastAPI(
    title="QuickQuiz-GPT",
    description="AI-powered quiz question generation microservice",
    version="0.1.0"
)


@app.get("/")
async def root():
    """Root endpoint for health check."""
    return {"message": "QuickQuiz-GPT API is running"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
