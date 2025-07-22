import logging
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def auth_page(request: Request):
    """
    Authentication endpoint handled by reverse proxy.
    This is a placeholder that should never be reached in production.
    """
    logger.warning("Auth endpoint reached - should be handled by reverse proxy")
    
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Authentication Required</title>
    </head>
    <body>
        <h1>Authentication Required</h1>
        <p>This application requires authentication via reverse proxy.</p>
        <p>Please contact your administrator to configure proper authentication.</p>
    </body>
    </html>
    """)