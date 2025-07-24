import logging
import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from pathlib import Path

log = logging.getLogger("uvicorn")

# Move up two directories from the current file location to find .env
ENV_PATH = Path(__file__).resolve().parents[2] / ".env"

# Load environment variables from the .env file
load_dotenv(dotenv_path=ENV_PATH)

print("This is the host name loaded")
print(str(os.getenv("POSTGRES_HOST")))

class Settings(BaseSettings):
    """Class for storing settings."""

    POSTGRES_DB: str = os.getenv("POSTGRES_DB")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", 5432))  # Ensure integer
    PGADMIN_DEFAULT_EMAIL: str = os.getenv("PGADMIN_DEFAULT_EMAIL")
    BE_BLOB_API_URL : str = os.getenv("BE_BLOB_API_URL", "")
    S3_IMAGES_FOLDER : str = os.getenv("S3_IMAGES_FOLDER", "")
    S3_DOCS_FOLDER : str = os.getenv("S3_DOCS_FOLDER", "")
    
    
    # POSTGRES_HOST: str = "localhost"

    # Database URL Construction
    DATABASE_URL: str = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"


    # Redis Configuration
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB: int = int(os.getenv("REDIS_DB", 0))
    
    # REDIS_HOST: str = "localhost"

    # Google Maps API Key
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "defaultapikey")
    BE_NOTIFICATION_API_URL: str = os.getenv("BE_NOTIFICATION_API_URL")
    BE_AUTH_API_URL: str = os.getenv("BE_AUTH_API_URL")

    BE_SERVICE_API_URL: str = os.getenv("BE_SERVICE_API_URL")
    BE_PROFILE_API_URL: str = os.getenv("BE_PROFILE_API_URL", "http://profile-service:8001")
    BE_SERVICE_API_URL: str = os.getenv("BE_SERVICE_API_URL", "http://service-management:8003")
    MINIO_URL : str = os.getenv("MINIO_URL", "")
    MINIO_ROOT_USER : str = os.getenv("MINIO_ROOT_USER", "")
    MINIO_ROOT_PASSWORD : str = os.getenv("MINIO_ROOT_PASSWORD", "")
    MINIO_ACCESS_KEY : str = os.getenv("MINIO_ACCESS_KEY", "")
    MINIO_SECRET_KEY : str = os.getenv("MINIO_SECRET_KEY", "")
    APP_NAME: str = os.getenv("APP_NAME", "")
    AWS_REGION: str = os.getenv("AWS_REGION", "")
    AWS_REGION: str = os.getenv("AWS_REGION", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    FROM_EMAIL: str = os.getenv("FROM_EMAIL", "")
    SES_ACCESS_KEY: str = os.getenv("SES_ACCESS_KEY", "")
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    SES_SECRET_KEY: str = os.getenv("SES_SECRET_KEY", "")
    

def get_settings() -> BaseSettings:
    """Get application settings usually stored as environment variables.

    Returns:
        Settings: Application settings.
    """
    log.info("🔧 Loading config settings from the environment...")
    return Settings()

settings = get_settings()

# Debugging: Print loaded configuration (optional, remove in production)
if __name__ == "__main__":
    print("✅ Loaded Configuration:")
    print(f"POSTGRES_DB: {settings.POSTGRES_DB}")
    print(f"POSTGRES_USER: {settings.POSTGRES_USER}")
    print(f"POSTGRES_PASSWORD: {settings.POSTGRES_PASSWORD}")  # Remove this in production
    print(f"POSTGRES_HOST: {settings.POSTGRES_HOST}")
    print(f"POSTGRES_PORT: {settings.POSTGRES_PORT}")
    print(f"DATABASE_URL: {settings.DATABASE_URL}")
    print(f"REDIS_HOST: {settings.REDIS_HOST}")
    print(f"REDIS_PORT: {settings.REDIS_PORT}")
    print(f"GOOGLE_API_KEY: {settings.GOOGLE_API_KEY}")
