import os
import logging
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.auth.middleware import AuthMiddleware
from app.api import chat, llm, mcp, auth, websocket

setup_logging()
logger = logging.getLogger(__name__)

# Global MCP service instances for cleanup
_global_mcp_services = []

def register_mcp_service(mcp_service):
    """Register an MCP service for global cleanup"""
    _global_mcp_services.append(mcp_service)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup")
    yield
    logger.info("Application shutdown")
    
    # Close MCP clients on shutdown
    try:
        for mcp_service in _global_mcp_services:
            await mcp_service.close_mcp_clients()
        logger.info("MCP clients cleanup completed")
    except Exception as e:
        logger.error(f"Error during MCP cleanup: {str(e)}")

# middlware for logging the request and route
async def log_request(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code}")
    return response

def create_app() -> FastAPI:
    settings = get_settings()
    
    app = FastAPI(
        title="LLM Frontend",
        description="A modular LLM frontend with MCP integration",
        version="1.0.0",
        lifespan=lifespan
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # middlware for logging the request and  route 
    app.middleware("http")(log_request)

    
    app.add_middleware(AuthMiddleware)
    
    app.include_router(auth.router, prefix="/auth", tags=["auth"])
    app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
    app.include_router(llm.router, prefix="/api/llm", tags=["llm"])
    app.include_router(mcp.router, prefix="/api/mcp", tags=["mcp"])
    app.include_router(websocket.router, tags=["websocket"])
    
    if os.path.exists("../frontend"):
        app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")
    
    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )