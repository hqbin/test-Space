"""
UA过滤中间件
拦截已知爬虫和异常User-Agent
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

KNOWN_BOTS = [
    'python-requests',
    'scrapy',
    'httpclient',
    'go-http-client',
    'java/',
    'apache-httpclient',
    'curl',
    'wget',
    'bot',
    'spider',
    'crawler',
    'scraper',
    'selenium',
    'headless',
    'phantomjs',
    'mechanize',
    'webharvest',
    'nutch',
    'mj12bot',
    'ahrefbot',
    'semrushbot',
    'dotbot',
    'blexbot',
    'bytespider',
    'gptbot',
    'chatgpt-user',
    'ccbot',
    'claudebot',
]

WHITELIST_PATHS = [
    '/ws/',
    '/api/health',
    '/api/auth/login',
    '/api/database',
    '/docs',
    '/redoc',
    '/openapi.json',
]


class AntiBotMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        for wp in WHITELIST_PATHS:
            if path.startswith(wp):
                return await call_next(request)

        user_agent = (request.headers.get("user-agent") or "").lower()

        if not user_agent:
            client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip() \
                        or request.headers.get("X-Real-IP") \
                        or (request.client.host if request.client else "unknown")
            return JSONResponse(
                status_code=403,
                content={"detail": "请使用浏览器访问"}
            )

        for bot in KNOWN_BOTS:
            if bot in user_agent:
                return JSONResponse(
                    status_code=403,
                    content={"detail": "不允许的访问方式"}
                )

        return await call_next(request)
