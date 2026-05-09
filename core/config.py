from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List

class Settings(BaseSettings):
    """Application settings loaded from environment."""
    
    # Firebase
    firebase_service_account: str = Field(..., env="FIREBASE_SERVICE_ACCOUNT")
    
    # Security
    api_secret: str = Field(..., env="API_SECRET")
    
    # AI
    gemini_api_key: str = Field(..., env="GEMINI_API_KEY")
    
    # CORS
    cors_origins: List[str] = Field(default=["http://localhost:3000"], env="CORS_ORIGINS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Parse CORS_ORIGINS if it's a comma-separated string
        if isinstance(self.cors_origins, str):
            self.cors_origins = [origin.strip() for origin in self.cors_origins.split(",")]

settings = Settings()
