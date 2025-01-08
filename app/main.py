from datetime import datetime
from typing import Optional, Dict
import time
import uuid

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, RedirectResponse

from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
import sentry_sdk

from app.api import document_processing, document_retrieval
from app.utils.logging import setup_logging
from app.utils.monitoring import MetricsManager
from app.config.settings import Settings

# Create a global metrics manager instance
metrics_manager = MetricsManager()

# Initialize settings
settings = Settings()

logger = setup_logging(app_name=__name__)


# Custom middleware for request ID and timing
class RequestMiddleware:
    """Middleware to add request ID and timing information."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        start_time = time.time()
        request_id = str(uuid.uuid4())

        async def wrapped_send(message):
            if message["type"] == "http.response.start":
                headers = message.get("headers", [])
                headers.append((b"X-Request-ID", str(request_id).encode()))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, wrapped_send)

        # Log request timing
        if scope["type"] == "http":
            duration = time.time() - start_time
            logger.info(f"Request {request_id} completed in {duration:.3f}s")


# Custom exception handler
class APIException(Exception):
    """Base exception for API errors."""

    def __init__(
        self,
        status_code: int,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict] = None,
    ):
        self.status_code = status_code
        self.message = message
        self.error_code = error_code or "ERROR"
        self.details = details
        super().__init__(message)


async def api_exception_handler(request: Request, exc: APIException):
    """Handle API exceptions and return structured response."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
                "timestamp": datetime.now().isoformat(),
                "request_id": request.state.request_id,
            }
        },
    )


# Initialize FastAPI application
def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title=settings.API_TITLE,
        description=settings.API_DESCRIPTION,
        version=settings.API_VERSION,
        debug=settings.DEBUG,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=settings.ALLOWED_METHODS,
        allow_headers=settings.ALLOWED_HEADERS,
    )

    # Add Gzip compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Add request middleware
    app.add_middleware(RequestMiddleware)

    # Configure Sentry if DSN is provided
    if settings.SENTRY_DSN and settings.ENVIRONMENT == "PRODUCTION":
        sentry_sdk.init(dsn=settings.SENTRY_DSN, traces_sample_rate=1.0)
        app.add_middleware(SentryAsgiMiddleware)

    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next):
        """Middleware to track request metrics."""
        start_time = time.time()

        try:
            response = await call_next(request)

            # Record metrics after request is processed
            duration = time.time() - start_time
            metrics_manager.increment_request_count(
                method=request.method,
                endpoint=request.url.path,
                status=str(response.status_code),
            )
            metrics_manager.observe_request_latency(
                method=request.method, endpoint=request.url.path, duration=duration
            )

            return response

        except Exception as e:
            metrics_manager.increment_error_count(error_type=type(e).__name__)
            raise

    # Add exception handlers
    app.add_exception_handler(APIException, api_exception_handler)

    # Add routes
    add_routes(app)

    return app


# Route handlers
def add_routes(app: FastAPI):
    """Add routes to the application."""

    # FastAPI EntryPoint
    @app.get("/")
    async def index():
        return RedirectResponse("/docs")

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": settings.API_VERSION,
        }

    # FastAPI route for metrics endpoint
    @app.get("/metrics")
    async def metrics():
        """Endpoint to expose Prometheus metrics."""
        return Response(content=metrics_manager.get_metrics(), media_type="text/plain")

    # Other Routes
    app.include_router(document_processing.router, prefix="/api")
    app.include_router(document_retrieval.router, prefix="/api")


# Application factory
def get_application() -> FastAPI:
    """Application factory function."""
    app = create_app()
    return app


# Server startup
app = get_application()

# uvicorn app.main:app --port 8000 --log-level=info  --workers 4 --reload