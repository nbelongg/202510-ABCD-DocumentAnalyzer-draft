"""Main FastAPI application with rate limiting and metrics"""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
from config.settings import settings
from services.logger import get_logger
from services.exceptions import DocumentAnalyzerException
from schemas.common import ErrorResponse, HealthCheckResponse
from api.routes import analyzer, evaluator, chatbot, admin, admin_guidelines, admin_csv_sync, admin_prompts_bulk
from api.dependencies import verify_api_key
from db.connection import initialize_pool

# Import new middleware
from api.middleware.rate_limiting import setup_rate_limiting
from api.middleware.metrics import setup_metrics

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown"""
    # Startup
    logger.info("application_starting", version=settings.APP_VERSION)
    initialize_pool()
    yield
    # Shutdown
    logger.info("application_shutting_down")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production-ready Document Analyzer with monitoring and rate limiting",
    lifespan=lifespan
)

# Setup rate limiting (must be before other middleware)
setup_rate_limiting(app)

# Setup Prometheus metrics
setup_metrics(app)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request, call_next):
    """Add processing time to response headers"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}"
    logger.info(
        "request_completed",
        path=request.url.path,
        method=request.method,
        duration=process_time
    )
    return response


# Global exception handler
@app.exception_handler(DocumentAnalyzerException)
async def analyzer_exception_handler(request, exc: DocumentAnalyzerException):
    """Handle custom exceptions"""
    logger.error(
        "application_error",
        error_code=exc.error_code,
        error=exc.message,
        path=request.url.path
    )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorResponse(
            error_code=exc.error_code,
            error_message=exc.message
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(
        "unexpected_error",
        error=str(exc),
        path=request.url.path,
        exc_info=True
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error_code="INTERNAL_ERROR",
            error_message="An unexpected error occurred"
        ).dict()
    )


# Health check
@app.get("/health", response_model=HealthCheckResponse, tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return HealthCheckResponse(
        status="healthy",
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        database="connected",
        services={
            "llm": "operational",
            "pinecone": "operational",
            "s3": "operational"
        }
    )


# Include routers
app.include_router(
    analyzer.router,
    prefix="/api/v1/analyzer",
    tags=["Analyzer"],
    dependencies=[Depends(verify_api_key)]
)

app.include_router(
    evaluator.router,
    prefix="/api/v1/evaluator",
    tags=["Evaluator"],
    dependencies=[Depends(verify_api_key)]
)

app.include_router(
    chatbot.router,
    prefix="/api/v1/chatbot",
    tags=["Chatbot"],
    dependencies=[Depends(verify_api_key)]
)

app.include_router(
    admin.router,
    prefix="/api/v1/admin",
    tags=["Admin"],
    dependencies=[Depends(verify_api_key)]
)

# Admin guideline management
app.include_router(
    admin_guidelines.router,
    prefix="/api/v1/admin/guidelines",
    tags=["Admin - Guideline Management"],
    dependencies=[Depends(verify_api_key)]
)

# CSV sync for guideline configuration
app.include_router(
    admin_csv_sync.router,
    prefix="/api/v1/admin/csv-sync",
    tags=["Admin - CSV Sync"],
    dependencies=[Depends(verify_api_key)]
)

# Bulk prompt operations (backwards compatible with legacy Colab script)
app.include_router(
    admin_prompts_bulk.router,
    prefix="",  # No prefix for backwards compatibility
    tags=["Admin - Bulk Prompts (Legacy Compatible)"],
    dependencies=[Depends(verify_api_key)]
)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )

