from pydantic_settings import BaseSettings

# Release-specific constants (not environment variables)
PROJECT_NAME = "Kubera"
VERSION = "0.1.0"
API_V1_PREFIX = "/api/v1"


class Settings(BaseSettings):
    # CORS origins for development (frontend dev server cross-origin requests)
    # In production, frontend is served by FastAPI so no CORS needed
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative dev port
    ]

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost/kubera"
    DATABASE_ECHO: bool = False

    # JWT Authentication
    JWT_SECRET_KEY: str

    APP_DOMAIN: str = "localhost"
    API_DOMAIN: str = "localhost"
    WEBSITE_DOMAIN: str = "http://localhost:5173"

    # Environment: development, production, staging, etc.
    ENVIRONMENT: str = "development"

    # Frontend static files path (only used in production)
    FRONTEND_DIST_PATH: str = "/app/frontend/dist"

    class Config:
        env_file = ".env"


settings = Settings()
