import logging
from fastapi import Request
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import get_settings

logger = logging.getLogger(__name__)

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        settings = get_settings()
        
        if request.url.path.startswith("/auth"):
            return await call_next(request)
        
        if settings.debug:
            request.state.user_email = "test@test.com"
            logger.debug("Debug mode: bypassing auth, user set to test@test.com")
            return await call_next(request)
        
        user_email = request.headers.get("x-email-header")
        if not user_email:
            logger.warning(f"Missing x-email-header for {request.url.path}")
            return RedirectResponse(url="/auth")
        
        request.state.user_email = user_email
        logger.debug(f"Authenticated user: {user_email}")
        
        return await call_next(request)