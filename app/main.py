import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.config import get_settings
from app.database import init_db
from app.services.scheduler_service import shutdown_scheduler, start_scheduler
from app.services.sourcing.client import HttpClient

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing database schema...")
    await init_db()
    logger.info("Database schema initialized")

    if settings.ENABLE_SCHEDULER:
        start_scheduler()

    yield

    # Shutdown
    logger.info("Shutting down background services...")
    if settings.ENABLE_SCHEDULER:
        shutdown_scheduler()
    await HttpClient.close()
    logger.info("Application shutdown complete")


app = FastAPI(
    title="LeetCode Contest Analytics & Rating Predictor",
    description="High-performance backend API for LeetCode contests, submissions, real-time analytics, and FFT Elo rating predictions.",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Attach API routes
app.include_router(api_router)


@app.get("/", tags=["Health"])
async def root():
    return {"message": "LeetCode Contest Analytics & Rating Predictor API is running", "version": "1.0.0"}


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server error on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "An unexpected internal server error occurred"},
    )


if __name__ == "__main__":
    import sys
    from pathlib import Path
    import uvicorn

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)

