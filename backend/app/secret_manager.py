from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


class SecretProvider:
    def __init__(self, name: str, provider_type: str = "generic"):
        self.name = name
        self.provider_type = provider_type

    def get_secret(self, key: str) -> Optional[str]:
        raise NotImplementedError


class LocalSecretProvider(SecretProvider):
    def __init__(self, name: str, values: Optional[Dict[str, str]] = None, provider_type: str = "local"):
        super().__init__(name, provider_type=provider_type)
        self.values = values or {}

    def get_secret(self, key: str) -> Optional[str]:
        return self.values.get(key)


class EnvSecretProvider(SecretProvider):
    def __init__(self, name: str = "env", prefix: Optional[str] = None):
        super().__init__(name, provider_type="environment")
        self.prefix = prefix or "LEAtTrace_"

    def get_secret(self, key: str) -> Optional[str]:
        env_key = f"{self.prefix}{key.replace('.', '_').upper()}"
        return os.getenv(env_key)


class FileSecretProvider(SecretProvider):
    def __init__(self, name: str, path: str, provider_type: str = "file"):
        super().__init__(name, provider_type=provider_type)
        self.path = Path(path)

    def get_secret(self, key: str) -> Optional[str]:
        if not self.path.exists():
            return None
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return None
        return data.get(key)


class SecretManagerRegistry:
    def __init__(self) -> None:
        self.providers: Dict[str, SecretProvider] = {}

    def register(self, provider: SecretProvider) -> None:
        self.providers[provider.name] = provider

    def get_provider(self, name: str) -> Optional[SecretProvider]:
        return self.providers.get(name)

    def resolve(self, provider_name: str, key: str) -> Optional[str]:
        provider = self.get_provider(provider_name)
        if provider is None:
            return None
        return provider.get_secret(key)

    def resolve_from_any(self, key: str) -> Dict[str, Optional[str]]:
        return {name: provider.get_secret(key) for name, provider in self.providers.items()}
