
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "iWonder"
    SQLALCHEMY_DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/iwonder"
    SECRET_KEY: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Email Settings
    MAIL_USERNAME: str = "your_email@gmail.com"
    MAIL_PASSWORD: str = "your_app_password"
    MAIL_FROM: str = "your_email@gmail.com"
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = True

    R2_ENDPOINT_URL: Optional[str] = None
    R2_ACCESS_KEY_ID: Optional[str] = None
    R2_SECRET_ACCESS_KEY: Optional[str] = None
    R2_BUCKET: Optional[str] = None
    R2_PUBLIC_BASE_URL: Optional[str] = None
    R2_PRESIGN_EXPIRES_SECONDS: int = 600
    R2_MAX_UPLOAD_BYTES: int = 5000000
    R2_REGION: str = "auto"

    REDIS_URL: Optional[str] = None

    class Config:
        env_file = ".env"

settings = Settings()