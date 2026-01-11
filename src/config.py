"""
Application configuration.
"""
import os
from typing import Optional

# Load environment variables in local development
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # In Cloudflare Workers we don't need dotenv
    pass

class Settings:
    """Application settings."""
    
    # API Keys
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    MASTER_API_KEY: str = os.getenv("MASTER_API_KEY", "")
    
    # Claude Configuration
    CLAUDE_MODEL: str = "claude-haiku-4-5-20251001"
    MAX_TOKENS: int = 1024
    TEMPERATURE: float = 0.7
    
    # Data Configuration
    DATA_FILE_PATH: str = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "data",
        "tourism_data.json"
    )
    
    # CORS Configuration
    CORS_ORIGINS: list = ["*"]
    CORS_METHODS: list = ["*"]
    CORS_HEADERS: list = ["*"]
    
    # Rate Limiting (optional for future use)
    MAX_REQUESTS_PER_MINUTE: int = 60
    
    @classmethod
    def validate(cls) -> bool:
        """Validates that required settings are present."""
        if not cls.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY is not configured")
        if not cls.MASTER_API_KEY:
            raise ValueError("MASTER_API_KEY is not configured")
        return True


settings = Settings()
