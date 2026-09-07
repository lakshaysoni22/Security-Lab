"""
LEAtTrace AI Platform — Centralized Configuration.

All AI/ML settings are driven by environment variables with sensible defaults.
No API keys are hardcoded. Provider selection is fully configurable.
"""

import os
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class AIConfig:
    """Central configuration for all AI platform components."""

    # --- LLM Provider ---
    llm_provider: str = field(default_factory=lambda: os.getenv("AI_LLM_PROVIDER", "ollama"))
    llm_model: str = field(default_factory=lambda: os.getenv("AI_LLM_MODEL", "llama3"))
    llm_api_key: Optional[str] = field(default_factory=lambda: os.getenv("AI_LLM_API_KEY"))
    llm_api_base: str = field(default_factory=lambda: os.getenv("AI_LLM_API_BASE", "http://localhost:11434"))
    llm_temperature: float = field(default_factory=lambda: float(os.getenv("AI_LLM_TEMPERATURE", "0.3")))
    llm_max_tokens: int = field(default_factory=lambda: int(os.getenv("AI_LLM_MAX_TOKENS", "2048")))

    # --- Embedding Model ---
    embedding_model: str = field(default_factory=lambda: os.getenv("AI_EMBEDDING_MODEL", "all-MiniLM-L6-v2"))
    embedding_dimension: int = field(default_factory=lambda: int(os.getenv("AI_EMBEDDING_DIM", "384")))

    # --- Vector Database ---
    vector_backend: str = field(default_factory=lambda: os.getenv("AI_VECTOR_BACKEND", "faiss"))
    vector_index_path: str = field(default_factory=lambda: os.getenv("AI_VECTOR_INDEX_PATH", "models_registry/vector_indices"))
    qdrant_host: str = field(default_factory=lambda: os.getenv("AI_QDRANT_HOST", "localhost"))
    qdrant_port: int = field(default_factory=lambda: int(os.getenv("AI_QDRANT_PORT", "6333")))

    # --- Model Registry ---
    model_registry_path: str = field(default_factory=lambda: os.getenv("AI_MODEL_REGISTRY", "models_registry"))
    experiment_tracking_path: str = field(default_factory=lambda: os.getenv("AI_EXPERIMENT_PATH", "models_registry/experiments"))

    # --- Training ---
    training_batch_size: int = field(default_factory=lambda: int(os.getenv("AI_TRAIN_BATCH_SIZE", "32")))
    training_epochs: int = field(default_factory=lambda: int(os.getenv("AI_TRAIN_EPOCHS", "100")))
    cross_validation_folds: int = field(default_factory=lambda: int(os.getenv("AI_CV_FOLDS", "5")))
    test_split_ratio: float = field(default_factory=lambda: float(os.getenv("AI_TEST_SPLIT", "0.2")))

    # --- Inference ---
    inference_cache_ttl: int = field(default_factory=lambda: int(os.getenv("AI_CACHE_TTL", "300")))
    inference_max_batch: int = field(default_factory=lambda: int(os.getenv("AI_MAX_BATCH", "64")))
    inference_timeout: int = field(default_factory=lambda: int(os.getenv("AI_INFERENCE_TIMEOUT", "30")))

    # --- MLOps ---
    drift_check_interval_hours: int = field(default_factory=lambda: int(os.getenv("AI_DRIFT_INTERVAL", "24")))
    retrain_schedule_cron: str = field(default_factory=lambda: os.getenv("AI_RETRAIN_CRON", "0 2 * * 0"))
    min_accuracy_threshold: float = field(default_factory=lambda: float(os.getenv("AI_MIN_ACCURACY", "0.85")))

    # --- RAG ---
    rag_top_k: int = field(default_factory=lambda: int(os.getenv("AI_RAG_TOP_K", "5")))
    rag_min_relevance: float = field(default_factory=lambda: float(os.getenv("AI_RAG_MIN_RELEVANCE", "0.3")))
    rag_max_context_tokens: int = field(default_factory=lambda: int(os.getenv("AI_RAG_MAX_CONTEXT", "4096")))

    # --- Feature Flags ---
    enable_gpu: bool = field(default_factory=lambda: os.getenv("AI_ENABLE_GPU", "false").lower() == "true")
    enable_streaming: bool = field(default_factory=lambda: os.getenv("AI_ENABLE_STREAMING", "true").lower() == "true")
    enable_caching: bool = field(default_factory=lambda: os.getenv("AI_ENABLE_CACHING", "true").lower() == "true")


# Singleton configuration instance
ai_config = AIConfig()
