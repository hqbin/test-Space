"""
全局限流中间件
基于滑动窗口算法，按IP和用户维度限制请求频率
"""
import time
import threading
from jose import jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from config import settings


class RateLimitStore:
    """内存限流存储（滑动窗口）"""
    def __init__(self):
        self._requests = {}
        self._lock = threading.Lock()

    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> bool:
        now = time.time()
        with self._lock:
            if key not in self._requests:
                self._requests[key] = []
            self._requests[key] = [
                t for t in self._requests[key]
                if now - t < window_seconds
            ]
            if len(self._requests[key]) >= max_requests:
                return False
            self._requests[key].append(now)
            return True

    def get_remaining(self, key: str, max_requests: int, window_seconds: int) -> int:
        now = time.time()
        with self._lock:
            if key not in self._requests:
                return max_requests
            valid = [t for t in self._requests[key] if now - t < window_seconds]
            return max(0, max_requests - len(valid))

    def cleanup(self):
        now = time.time()
        with self._lock:
            keys_to_delete = []
            for key in self._requests:
                self._requests[key] = [
                    t for t in self._requests[key]
                    if now - t < 3600
                ]
                if not self._requests[key]:
                    keys_to_delete.append(key)
            for key in keys_to_delete:
                del self._requests[key]


store = RateLimitStore()


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    return request.client.host if request.client else "unknown"


def get_user_id_from_token(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return ""
    token = auth[7:]
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username = payload.get("sub")
        return username or ""
    except Exception:
        return ""


SENSITIVE_PATHS = [
    "/api/testcases",
    "/api/testplans",
    "/api/reports",
    "/api/executions",
    "/api/analytics",
    "/api/dashboard",
]


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, default_limit=60, login_limit=20):
        super().__init__(app)
        self.default_limit = default_limit
        self.login_limit = login_limit

    async def dispatch(self, request: Request, call_next):
        client_ip = get_client_ip(request)
        path = request.url.path

        if path.startswith("/api/auth/login"):
            limit = self.login_limit
            key = f"{client_ip}:login"
        elif path.startswith("/api/auth/register"):
            limit = self.login_limit
            key = f"{client_ip}:register"
        elif path.startswith("/api/captcha"):
            limit = 60
            key = f"{client_ip}:captcha"
        elif any(path.startswith(sp) for sp in SENSITIVE_PATHS):
            user_id = get_user_id_from_token(request)
            if user_id:
                limit = 300
                key = f"user:{user_id}:data"
            else:
                limit = 30
                key = f"{client_ip}:data"
        else:
            limit = self.default_limit
            key = f"{client_ip}:global"

        if not store.is_allowed(key, limit, 60):
            return JSONResponse(
                status_code=429,
                content={"detail": "请求过于频繁，请稍后再试"}
            )

        response = await call_next(request)
        remaining = store.get_remaining(key, limit, 60)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
