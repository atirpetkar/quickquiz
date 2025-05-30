"""Main entry point for QuickQuiz-GPT API server."""

import uvicorn

from quickquiz.core.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "quickquiz.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        access_log=True,
    )
