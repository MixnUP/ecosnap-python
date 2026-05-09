from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """Application settings loaded from environment."""
    
    # Firebase
    firebase_service_account: str = Field(..., env="FIREBASE_SERVICE_ACCOUNT")
    
    # Security
    api_secret: str = Field(..., env="API_SECRET")
    
    # AI
    gemini_api_key: str = Field(..., env="GEMINI_API_KEY")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
