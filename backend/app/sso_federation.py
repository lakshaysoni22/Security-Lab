from __future__ import annotations

import os
from typing import Any, Dict, Optional


class SSOProvider:
    def __init__(self, name: str, provider_type: str = "generic"):
        self.name = name
        self.provider_type = provider_type

    def authenticate(self, username: str, password: str) -> bool:
        raise NotImplementedError

    def get_provider_info(self) -> Dict[str, Any]:
        return {"name": self.name, "type": self.provider_type}

    def create_session_claims(self, username: str) -> Dict[str, Any]:
        return {
            "sub": username,
            "iss": os.getenv("SSO_ISSUER", "https://local.LEAtTrace"),
            "provider": self.name,
            "provider_type": self.provider_type,
        }


class LocalSSOProvider(SSOProvider):
    def __init__(self, name: str, users: Optional[Dict[str, str]] = None, provider_type: str = "local"):
        super().__init__(name, provider_type=provider_type)
        self.users = users or {}

    def authenticate(self, username: str, password: str) -> bool:
        if not username or not password:
            return False
        stored = self.users.get(username)
        if isinstance(stored, dict):
            return stored.get("password") == password
        return stored == password


class LDAPProviderAdapter(SSOProvider):
    def __init__(self, name: str, server: str, base_dn: str, bind_dn: Optional[str] = None):
        super().__init__(name, provider_type="ldap")
        self.server = server
        self.base_dn = base_dn
        self.bind_dn = bind_dn

    def authenticate(self, username: str, password: str) -> bool:
        if not self.server or not self.base_dn:
            return False
        return bool(username and password)


class OIDCProviderAdapter(SSOProvider):
    def __init__(self, name: str, issuer: str, client_id: str):
        super().__init__(name, provider_type="oidc")
        self.issuer = issuer or os.getenv("OIDC_ISSUER", "https://example.com")
        self.client_id = client_id

    def authenticate(self, username: str, password: str) -> bool:
        return bool(username and password and self.client_id)


class SSOProviderRegistry:
    def __init__(self) -> None:
        self.providers: Dict[str, SSOProvider] = {}

    def register(self, provider: SSOProvider) -> None:
        self.providers[provider.name] = provider

    def get_provider(self, name: str) -> Optional[SSOProvider]:
        return self.providers.get(name)

    def authenticate(self, provider_name: str, username: str, password: str) -> bool:
        provider = self.get_provider(provider_name)
        if provider is None:
            return False
        return provider.authenticate(username, password)

    def get_provider_claims(self, provider_name: str, username: str) -> Optional[Dict[str, Any]]:
        provider = self.get_provider(provider_name)
        if provider is None:
            return None
        return provider.create_session_claims(username)
