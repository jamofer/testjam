from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Swagger UI and ReDoc bundles are loaded from jsDelivr by FastAPI's defaults.
SWAGGER_CDN = "https://cdn.jsdelivr.net"

DEFAULT_CSP = (
    f"default-src 'self'; "
    f"img-src 'self' data: https:; "
    f"style-src 'self' 'unsafe-inline' {SWAGGER_CDN}; "
    f"script-src 'self' {SWAGGER_CDN}; "
    f"font-src 'self' data: {SWAGGER_CDN}; "
    f"connect-src 'self'; "
    f"frame-ancestors 'none'"
)

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Content-Security-Policy": DEFAULT_CSP,
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        for header, value in SECURITY_HEADERS.items():
            response.headers.setdefault(header, value)
        return response
