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

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup")
    yield
    logger.info("Application shutdown")

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