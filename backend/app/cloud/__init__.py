"""
LEATrace Multi-Cloud Integration Package.
"""
from .storage_adapter import CloudStorageAdapter, cloud_storage_adapter
from .secret_adapter import CloudSecretAdapter, cloud_secret_adapter

__all__ = [
    "CloudStorageAdapter",
    "cloud_storage_adapter",
    "CloudSecretAdapter",
    "cloud_secret_adapter",
]
