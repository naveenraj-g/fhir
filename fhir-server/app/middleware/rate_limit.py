import time
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import get_logger

logger = get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        read_limit: int = 100,
        write_limit: int = 20,
        window_seconds: int = 60,
    ):
        super().__init__(app)
        self.read_limit = read_limit
        self.write_limit = write_limit
        self.window = window_seconds

        self.EXCLUDED_PATHS = {"/", "/openapi.json"}
        self.EXCLUDED_PREFIXES = ("/docs", "/redoc")

    async def dispatch(self, request: Request, call_next):

        path = request.url.path

        # Skip public/system endpoints
        if path in self.EXCLUDED_PATHS or path.startswith(self.EXCLUDED_PREFIXES):
            return await call_next(request)

        redis = request.app.state.redis

        if not redis:
            logger.warning("Redis is not available, skipping rate limiting")
            return await call_next(request)

        # ----------------------------
        # Identify client
        # ----------------------------

        user = getattr(request.state, "user", None)

        if user:
            user_id = user.get("sub")
            roles = user.get("realm_access", {}).get("roles", [])
        else:
            # Fallback to IP-based rate limiting
            forwarded = request.headers.get("x-forwarded-for")
            user_id = (
                forwarded.split(",")[0].strip() if forwarded else request.client.host
            )
            roles = []

        # Admin bypass (optional)
        if "admin" in roles:
            return await call_next(request)

        # ----------------------------
        # Determine limit
        # ----------------------------

        is_read = request.method in ("GET", "HEAD", "OPTIONS")
        limit = self.read_limit if is_read else self.write_limit

        key = f"rate:{user_id}:{request.method}"
        now = int(time.time())
        window_start = now - self.window

        # ----------------------------
        # Sliding window logic
        # ----------------------------

        # Remove expired timestamps
        await redis.zremrangebyscore(key, 0, window_start)

        # Count current requests in window
        current_count = await redis.zcard(key)

        if current_count >= limit:
            # return JSONResponse(
            #     status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            #     content={"detail": "Rate limit exceeded"},
            # )
            logger.info(
                "Rate limit exceeded",
                extra={
                    "user_id": user_id,
                    "method": request.method,
                    "path": path,
                    "limit": limit,
                },
            )
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "resourceType": "OperationOutcome",
                    "issue": [
                        {
                            "severity": "error",
                            "code": "throttled",  # FHIR issue type
                            "diagnostics": "Rate limit exceeded",
                        }
                    ],
                },
                headers={
                    "Retry-After": str(self.window),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Window": str(self.window),
                },
            )

        # Add current request timestamp
        await redis.zadd(key, {str(now): now})
        await redis.expire(key, self.window)

        response = await call_next(request)

        # ----------------------------
        # Professional rate limit headers
        # ----------------------------

        remaining = max(limit - current_count - 1, 0)

        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Window"] = str(self.window)

        return response
