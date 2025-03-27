from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "SimplifyChat"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/simplifychat")
    
    @property
    def SYNC_DATABASE_URL(self) -> str:
        """Convert async database URL to sync URL for Alembic."""
        return self.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    
    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your_secret_key_here")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Gemini AI
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    class Config:
        case_sensitive = True

settings = Settings() 