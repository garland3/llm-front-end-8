import os
import logging
from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"
    
    # Model Configuration
    models_config_path: str = "models.yml"
    
    # MCP Configuration
    mcp_config_path: str = "mcp/config.json"
    
    # API Keys
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_deployment_name: str = ""
    
    # Security
    secret_key: str = "development-secret-key"
    allowed_hosts: str = "localhost,127.0.0.1"
    
    # Logging
    log_to_file: bool = True
    log_rotation_size: int = 10485760
    log_backup_count: int = 5
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        logger = logging.getLogger(__name__)
        logger.info(f"Settings initialized with debug={self.debug}")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

def get_project_root() -> Path:
    """Get the project root directory"""
    return Path(__file__).parent.parent.parent.parent