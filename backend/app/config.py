"""
LEATrace Production Configuration Module.

Centralized Pydantic-based configuration management loading environment variables
with strict validation, production defaults, and security constraints.
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # System Info
    PROJECT_NAME: str = "LEATrace API"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "production"
    DEBUG: bool = False
    DEMO_DATA_ENABLED: bool = False

    # Security & Tokens
    SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "LEATrace_enterprise_production_secret_key_2026_x99_sec")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS Configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://leattrace.gov.in"
    ]

    # Database Settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./LEATrace.db")
    DB_POOL_SIZE: int = 15
    DB_MAX_OVERFLOW: int = 25
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800

    # Redis Caching & Rate Limiting
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD", None)

    # MongoDB Document Store
    MONGO_URL: str = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    MONGO_DB_NAME: str = os.getenv("MONGO_DB_NAME", "LEATrace_nosql")

    # Blockchain Provider API Keys & Gateways
    ETHERSCAN_API_KEY: Optional[str] = os.getenv("ETHERSCAN_API_KEY", "")
    BLOCKCHAIN_INFO_API_KEY: Optional[str] = os.getenv("BLOCKCHAIN_INFO_API_KEY", "")
    ALCHEMY_API_KEY: Optional[str] = os.getenv("ALCHEMY_API_KEY", "")
    INFURA_PROJECT_ID: Optional[str] = os.getenv("INFURA_PROJECT_ID", "")
    ETH_RPC_URL: str = os.getenv("ETH_RPC_URL", "https://eth-mainnet.g.alchemy.com/v2/demo")
    BTC_RPC_URL: str = os.getenv("BTC_RPC_URL", "https://blockstream.info/api")
    SOLANA_RPC_URL: str = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")

    # AI & Forensic Analysis Engine
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", "")
    AI_MODEL_NAME: str = "gemini-1.5-pro"
    XAI_EXPLAINABILITY_ENABLED: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
