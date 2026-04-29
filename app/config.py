from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    database_url: str = "sqlite:///data/novelforge.db"
    app_host: str = "0.0.0.0"
    app_port: int = 8788
    request_timeout_seconds: int = 120
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()