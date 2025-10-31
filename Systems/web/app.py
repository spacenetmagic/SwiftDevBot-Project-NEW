"""
FastAPI application for web panel.
"""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from Systems.core.logger import get_logger
from Systems.core.utils.config import Config
from Systems.web.api import admin, modules, settings, users
from Systems.web.auth import routes as auth_routes
from Systems.web.websocket import notifications

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown.
    
    Handles graceful startup and shutdown of the web panel.
    
    Args:
        app: FastAPI application
        
    Example:
        ```python
        app = FastAPI(lifespan=lifespan)
        ```
    """
    # Startup
    logger.info("Starting web panel...")
    
    # Subscribe to events for WebSocket notifications
    try:
        await notifications.subscribe_to_events()
        logger.info("Subscribed to event bus")
    except Exception as e:
        logger.error(f"Failed to subscribe to events: {e}", exc_info=True)
    
    yield
    
    # Shutdown
    logger.info("Shutting down web panel...")
    
    try:
        # Unsubscribe from events
        await notifications.unsubscribe_from_events()
        logger.info("Unsubscribed from event bus")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}", exc_info=True)
    
    logger.info("Web panel shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="SwiftDevBot Web Panel",
    description="Web panel for SwiftDevBot administration",
    version="1.0.0",
    lifespan=lifespan,
)

# Load config
config = Config()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle validation errors."""
    logger.warning(f"Validation error: {exc.errors()}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next: Any) -> Any:
    """Log all API requests."""
    logger.info(f"{request.method} {request.url.path}")
    
    response = await call_next(request)
    
    logger.debug(f"{request.method} {request.url.path} - {response.status_code}")
    
    return response


# Include routers
app.include_router(auth_routes.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router)
app.include_router(modules.router)
app.include_router(settings.router)
app.include_router(admin.router)
app.include_router(notifications.router)


# Health check
@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """
    Health check endpoint.
    
    Returns:
        Health status
        
    Example:
        ```python
        GET /health
        ```
    """
    return {"status": "ok"}


# Static files (for frontend)
static_path = Path("web/static")
if static_path.exists():
    app.mount("/static", StaticFiles(directory=static_path), name="static")


# Root endpoint
@app.get("/", tags=["root"])
async def root() -> dict[str, str]:
    """
    Root endpoint.
    
    Returns:
        API information
        
    Example:
        ```python
        GET /
        ```
    """
    return {
        "name": "SwiftDevBot Web Panel API",
        "version": "1.0.0",
        "docs": "/docs",
    }

