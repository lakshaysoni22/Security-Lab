import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "LEAtTrace Backend Ecosystem"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./LEAtTrace_micro.db")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "super-secret-key-12345-cpos-singularity")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Service URLs
    AUTH_SERVICE_URL: str = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")
    CPOS_SERVICE_URL: str = os.getenv("CPOS_SERVICE_URL", "http://localhost:8002")
    RIIL_SERVICE_URL: str = os.getenv("RIIL_SERVICE_URL", "http://localhost:8003")
    NGEL_SERVICE_URL: str = os.getenv("NGEL_SERVICE_URL", "http://localhost:8004")
    QCAL_SERVICE_URL: str = os.getenv("QCAL_SERVICE_URL", "http://localhost:8005")
    ARNS_SERVICE_URL: str = os.getenv("ARNS_SERVICE_URL", "http://localhost:8006")
    BLOCKCHAIN_SERVICE_URL: str = os.getenv("BLOCKCHAIN_SERVICE_URL", "http://localhost:8007")
    INVESTIGATION_SERVICE_URL: str = os.getenv("INVESTIGATION_SERVICE_URL", "http://localhost:8008")

    class Config:
        case_sensitive = True

settings = Settings()
