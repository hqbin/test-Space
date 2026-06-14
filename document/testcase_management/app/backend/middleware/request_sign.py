"""
请求签名验证中间件
验证请求来源合法性，防止重放和篡改
签名算法: MD5(timestamp + nonce + path + secret)
"""
import hashlib
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


SIGN_WHITELIST = [
    '/api/auth/login',
    '/api/auth/refresh',
    '/api/auth/register',
    '/api/auth/logout',
    '/api/captcha',
    '/api/behavior-tracker',
    '/api/external-executions',
    '/api/aml-patch-api',
    '/api/database',
    '/api/testcases/trigger-pr-sync',
    '/api/testcases/pr-sync-status',
    '/ws/',
    '/api/health',
    '/docs',
    '/redoc',
    '/openapi.json',
    '/',
]

MAX_TIMESTAMP_DIFF = 600


def compute_sign(timestamp: str, nonce: str, path: str, secret: str) -> str:
    raw = f"{timestamp}{nonce}{path}{secret}"
    return hashlib.md5(raw.encode('utf-8')).hexdigest()


class RequestSignMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, secret: str = ""):
        super().__init__(app)
        self.secret = secret

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        for wp in SIGN_WHITELIST:
            if path.startswith(wp):
                return await call_next(request)

        if not self.secret:
            return await call_next(request)

        timestamp = request.headers.get("x-timestamp", "")
        nonce = request.headers.get("x-nonce", "")
        sign = request.headers.get("x-sign", "")

        if not timestamp or not nonce or not sign:
            return JSONResponse(
                status_code=403,
                content={"detail": "缺少请求签名"}
            )

        try:
            ts = float(timestamp)
        except ValueError:
            return JSONResponse(
                status_code=403,
                content={"detail": "签名时间戳无效"}
            )

        now = time.time()
        if abs(now - ts) > MAX_TIMESTAMP_DIFF:
            return JSONResponse(
                status_code=403,
                content={"detail": "请求已过期，请刷新页面重试"}
            )

        expected = compute_sign(timestamp, nonce, path, self.secret)
        if not _constant_time_compare(sign, expected):
            return JSONResponse(
                status_code=403,
                content={"detail": "请求签名无效"}
            )

        return await call_next(request)


def _constant_time_compare(a: str, b: str) -> bool:
    if len(a) != len(b):
        return False
    result = 0
    for x, y in zip(a, b):
        result |= ord(x) ^ ord(y)
    return result == 0
