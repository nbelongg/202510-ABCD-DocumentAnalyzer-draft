"""
Rate limiting middleware using Redis backend
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import redis
import time
from typing import Optional
from config.settings import settings
from services.logger import get_logger

logger = get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware with Redis backend
    
    Implements token bucket algorithm for rate limiting.
    """
    
    def __init__(self, app, redis_client: Optional[redis.Redis] = None):
        super().__init__(app)
        self.redis_client = redis_client or self._create_redis_client()
        
        # Rate limit settings (requests per time window)
        self.limits = {
            "default": {"requests": 100, "window": 60},  # 100 req/min
            "analyze": {"requests": 20, "window": 60},   # 20 req/min
            "chat": {"requests": 50, "window": 60},      # 50 req/min
            "evaluate": {"requests": 10, "window": 60},  # 10 req/min
        }
    
    def _create_redis_client(self) -> redis.Redis:
        """Create Redis client"""
        try:
            redis_host = getattr(settings, 'REDIS_HOST', 'localhost')
            redis_port = getattr(settings, 'REDIS_PORT', 6379)
            
            client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=0,
                decode_responses=True,
                socket_connect_timeout=5
            )
            
            # Test connection
            client.ping()
            logger.info("redis_connected", host=redis_host, port=redis_port)
            
            return client
            
        except Exception as e:
            logger.error("redis_connection_failed", error=str(e))
            # Return None to disable rate limiting if Redis unavailable
            return None
    
    def _get_limit_config(self, path: str) -> dict:
        """Get rate limit config for path"""
        if "/analyze" in path:
            return self.limits["analyze"]
        elif "/chat" in path:
            return self.limits["chat"]
        elif "/evaluate" in path:
            return self.limits["evaluate"]
        else:
            return self.limits["default"]
    
    def _get_client_identifier(self, request: Request) -> str:
        """Get client identifier for rate limiting"""
        # Try to get user_id from request (if authenticated)
        user_id = request.headers.get("X-User-ID")
        if user_id:
            return f"user:{user_id}"
        
        # Fall back to API key
        api_key = request.headers.get("api-key")
        if api_key:
            return f"api_key:{api_key}"
        
        # Fall back to IP address
        client_ip = request.client.host
        return f"ip:{client_ip}"
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting"""
        # Skip rate limiting for health check
        if request.url.path == "/health":
            return await call_next(request)
        
        # Skip if Redis not available
        if self.redis_client is None:
            logger.warning("rate_limiting_disabled", reason="redis_unavailable")
            return await call_next(request)
        
        try:
            # Get rate limit config
            limit_config = self._get_limit_config(request.url.path)
            max_requests = limit_config["requests"]
            window_seconds = limit_config["window"]
            
            # Get client identifier
            client_id = self._get_client_identifier(request)
            redis_key = f"rate_limit:{client_id}:{request.url.path}"
            
            # Check current request count
            current_count = self.redis_client.get(redis_key)
            
            if current_count is None:
                # First request in window
                self.redis_client.setex(redis_key, window_seconds, 1)
                remaining = max_requests - 1
            else:
                current_count = int(current_count)
                
                if current_count >= max_requests:
                    # Rate limit exceeded
                    ttl = self.redis_client.ttl(redis_key)
                    
                    logger.warning(
                        "rate_limit_exceeded",
                        client_id=client_id,
                        path=request.url.path,
                        limit=max_requests,
                        window=window_seconds
                    )
                    
                    return JSONResponse(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        content={
                            "error": "Rate limit exceeded",
                            "message": f"Too many requests. Try again in {ttl} seconds.",
                            "retry_after": ttl,
                            "limit": max_requests,
                            "window": window_seconds
                        },
                        headers={
                            "X-RateLimit-Limit": str(max_requests),
                            "X-RateLimit-Remaining": "0",
                            "X-RateLimit-Reset": str(int(time.time()) + ttl),
                            "Retry-After": str(ttl)
                        }
                    )
                
                # Increment counter
                self.redis_client.incr(redis_key)
                remaining = max_requests - current_count - 1
            
            # Process request
            response = await call_next(request)
            
            # Add rate limit headers
            response.headers["X-RateLimit-Limit"] = str(max_requests)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Window"] = str(window_seconds)
            
            return response
            
        except redis.RedisError as e:
            logger.error("rate_limiting_error", error=str(e))
            # Allow request to proceed if Redis fails
            return await call_next(request)
        
        except Exception as e:
            logger.error("rate_limiting_unexpected_error", error=str(e), exc_info=True)
            return await call_next(request)


def setup_rate_limiting(app):
    """Setup rate limiting middleware"""
    try:
        app.add_middleware(RateLimitMiddleware)
        logger.info("rate_limiting_enabled")
    except Exception as e:
        logger.error("rate_limiting_setup_failed", error=str(e))
        # Continue without rate limiting
        pass
