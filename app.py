"""Professional Finvo AI FastAPI application with LangChain integration."""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager

from src.finvo_ai.api.routes import router
from src.finvo_ai.utils.logger import get_logger, configure_logging
from config.settings import settings


# Configure logging
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    logger.info(
        "Starting Finvo AI application",
        version=settings.app_version,
        environment=settings.environment,
        debug=settings.debug
    )
    
    yield
    
    # Shutdown
    logger.info("Shutting down Finvo AI application")


# Create FastAPI application
app = FastAPI(
    title="Finvo AI - Professional Invoice Extractor",
    description="LangChain-powered AI service for financial document processing",
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware for production
if settings.environment == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # Configure appropriately for production
    )

# Include API routes
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "Finvo AI",
        "version": settings.app_version,
        "description": "Professional LangChain-powered invoice extraction service",
        "environment": settings.environment,
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Detailed health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "model": settings.openai_model,
        "debug": settings.debug
    }


if __name__ == "__main__":
    import uvicorn
    
    logger.info(
        "Starting server",
        host=settings.host,
        port=settings.port,
        reload=settings.reload
    )
    
    uvicorn.run(
        "app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower()
    )
