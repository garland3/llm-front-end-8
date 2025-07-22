import os
import logging
import traceback
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.core.config import get_settings, get_project_root

def setup_logging():
    settings = get_settings()
    project_root = get_project_root()
    
    logs_dir = project_root / "logs"
    os.makedirs(logs_dir, exist_ok=True)
    
    log_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
    
    if settings.log_to_file:
        file_handler = RotatingFileHandler(
            logs_dir / "app.log",
            maxBytes=settings.log_rotation_size,
            backupCount=settings.log_backup_count
        )
        file_handler.setFormatter(log_format)
        root_logger.addHandler(file_handler)
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)
    root_logger.addHandler(console_handler)

def log_exception(logger, exc: Exception, context: str = ""):
    error_msg = f"Exception in {context}: {str(exc)}\n{traceback.format_exc()}"
    logger.error(error_msg)