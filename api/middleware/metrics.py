"""
Prometheus metrics middleware
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
import time
from services.logger import get_logger

logger = get_logger(__name__)

# Define metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)

REQUEST_IN_PROGRESS = Gauge(
    'http_requests_in_progress',
    'Number of HTTP requests in progress',
    ['method', 'endpoint']
)

ANALYSIS_DURATION = Histogram(
    'document_analysis_duration_seconds',
    'Document analysis duration in seconds',
    ['document_type'],
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0]
)

CHAT_MESSAGES = Counter(
    'chat_messages_total',
    'Total chat messages processed',
    ['source']
)

EVALUATION_COUNT = Counter(
    'evaluations_total',
    'Total proposal evaluations',
    ['organization_id']
)

LLM_CALLS = Counter(
    'llm_calls_total',
    'Total LLM API calls',
    ['provider', 'model']
)

LLM_TOKENS = Counter(
    'llm_tokens_total',
    'Total tokens used by LLM',
    ['provider', 'model', 'type']  # type: prompt/completion
)

DATABASE_OPERATIONS = Counter(
    'database_operations_total',
    'Total database operations',
    ['operation', 'table']
)

DATABASE_ERRORS = Counter(
    'database_errors_total',
    'Total database errors',
    ['operation', 'table']
)

CACHE_HITS = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_type']
)

CACHE_MISSES = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_type']
)


class PrometheusMetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect Prometheus metrics"""
    
    async def dispatch(self, request: Request, call_next):
        """Process request and collect metrics"""
        # Skip metrics endpoint itself
        if request.url.path == "/metrics":
            return await call_next(request)
        
        # Extract endpoint pattern
        endpoint = self._get_endpoint_pattern(request.url.path)
        method = request.method
        
        # Track request in progress
        REQUEST_IN_PROGRESS.labels(method=method, endpoint=endpoint).inc()
        
        # Start timer
        start_time = time.time()
        
        try:
            # Process request
            response = await call_next(request)
            status_code = response.status_code
            
        except Exception as e:
            logger.error("request_processing_error", error=str(e))
            status_code = 500
            raise
        
        finally:
            # Calculate duration
            duration = time.time() - start_time
            
            # Record metrics
            REQUEST_COUNT.labels(
                method=method,
                endpoint=endpoint,
                status=status_code
            ).inc()
            
            REQUEST_DURATION.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
            REQUEST_IN_PROGRESS.labels(method=method, endpoint=endpoint).dec()
            
            logger.info(
                "request_metrics_recorded",
                method=method,
                endpoint=endpoint,
                status=status_code,
                duration=duration
            )
        
        return response
    
    def _get_endpoint_pattern(self, path: str) -> str:
        """
        Extract endpoint pattern from path
        
        Replaces dynamic IDs with placeholders to reduce cardinality
        """
        # Replace UUIDs and numeric IDs
        import re
        
        # Replace UUID patterns
        path = re.sub(
            r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
            '/{id}',
            path,
            flags=re.IGNORECASE
        )
        
        # Replace numeric IDs
        path = re.sub(r'/\d+', '/{id}', path)
        
        # Replace session IDs
        path = re.sub(r'/session-[^/]+', '/session-{id}', path)
        
        return path


def setup_metrics(app):
    """Setup Prometheus metrics middleware"""
    try:
        # Add middleware
        app.add_middleware(PrometheusMetricsMiddleware)
        
        # Add metrics endpoint
        @app.get("/metrics")
        async def metrics():
            """Expose Prometheus metrics"""
            return Response(
                content=generate_latest(),
                media_type=CONTENT_TYPE_LATEST
            )
        
        logger.info("prometheus_metrics_enabled")
        
    except Exception as e:
        logger.error("metrics_setup_failed", error=str(e))
        # Continue without metrics
        pass


# Utility functions for custom metrics
def record_analysis_duration(document_type: str, duration: float):
    """Record document analysis duration"""
    ANALYSIS_DURATION.labels(document_type=document_type).observe(duration)


def record_chat_message(source: str = "web"):
    """Record chat message"""
    CHAT_MESSAGES.labels(source=source).inc()


def record_evaluation(organization_id: str = "unknown"):
    """Record proposal evaluation"""
    EVALUATION_COUNT.labels(organization_id=organization_id).inc()


def record_llm_call(provider: str, model: str, prompt_tokens: int, completion_tokens: int):
    """Record LLM API call and token usage"""
    LLM_CALLS.labels(provider=provider, model=model).inc()
    LLM_TOKENS.labels(provider=provider, model=model, type="prompt").inc(prompt_tokens)
    LLM_TOKENS.labels(provider=provider, model=model, type="completion").inc(completion_tokens)


def record_database_operation(operation: str, table: str, success: bool = True):
    """Record database operation"""
    DATABASE_OPERATIONS.labels(operation=operation, table=table).inc()
    if not success:
        DATABASE_ERRORS.labels(operation=operation, table=table).inc()


def record_cache_access(cache_type: str, hit: bool):
    """Record cache hit/miss"""
    if hit:
        CACHE_HITS.labels(cache_type=cache_type).inc()
    else:
        CACHE_MISSES.labels(cache_type=cache_type).inc()
