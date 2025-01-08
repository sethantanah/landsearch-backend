from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # API Settings
    API_VERSION: str = "v1"
    API_TITLE: str = "LandSearch"
    API_DESCRIPTION: str = "LandSearch Application"
    DEBUG: bool = False
    ENVIRONMENT: str = "PRODUCTION"

    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4
    RELOAD: bool = False

    # Security Settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS Settings
    ALLOWED_ORIGINS: list = ["*"]
    ALLOWED_METHODS: list = ["*"]
    ALLOWED_HEADERS: list = ["*"]

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60  # seconds

    # Application Configuration
    LOG_LEVEL: str = Field("INFO", description="Logging level")
    ENVIRONMENT: str = Field("production", description="Application environment")
    SENTRY_DSN: Optional[str] = Field(None, description="Sentry DSN")
    METRICS_PORT: int = Field(9090, description="Prometheus metrics port")
    ENABLE_METRICS: bool = Field(True, description="Enable Metrics")

    # Data Caching
    DOCUMENT_CACHE_SIZE: int = 20

    # Gemini API Setup
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-1.5-pro-latest"

    # OpenAI Setup
    OPENAI_API_KEY: str
    ANON_PUBLIC: str
    SECRET: str

    # Superbase
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_TABLE: str = "LandSearch"

    # Processing
    MAX_RETRIES: int = 1

    LOCALEPSG: str = "epsg:2136"
    GLOBALEPSG: str = "epsg:4326"

    class Config:
        env_file = ".env"
        frozen = True
        case_sensitive = True
        extra = "allow"
