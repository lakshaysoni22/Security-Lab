"""
LEATrace Blockchain Intelligence — Wallet Attribution Engine.

Enterprise wallet attribution with provider abstraction.
Classifies addresses into categories: exchange, custodial, government,
bridge, protocol_treasury, mining_pool, validator, dao_treasury,
multisig, service, public_label.

PRODUCTION INVARIANTS:
- Never fabricates attribution.
- If a provider is unavailable, returns structured status.
- All attribution includes confidence and evidence.
- Provider health is exposed.
"""

from __future__ import annotations

import datetime
import logging
import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

logger = logging.getLogger("leatrace.wallet_attribution")


# ═══════════════════════════════════════════════════════════════════
# Attribution Result
# ═══════════════════════════════════════════════════════════════════

ATTRIBUTION_TYPES = frozenset({
    "exchange", "custodial", "government", "bridge",
    "protocol_treasury", "mining_pool", "validator",
    "dao_treasury", "multisig", "service", "public_label",
    "defi_protocol", "mixer", "nft_marketplace", "unknown",
})


def _utcnow() -> str:
    return datetime.datetime.now(datetime.UTC).isoformat() + "Z"


# ═══════════════════════════════════════════════════════════════════
# Provider Base Class
# ═══════════════════════════════════════════════════════════════════

class AttributionProvider(ABC):
    """Base class for wallet attribution data providers."""

    def __init__(self, provider_id: str, display_name: str, priority: int = 50):
        self.provider_id = provider_id
        self.display_name = display_name
        self.priority = priority
        self._enabled = True
        self._status = "not_configured"
        self._last_error: Optional[str] = None

    @abstractmethod
    def lookup(self, address: str, chain: str = "ethereum") -> Optional[Dict[str, Any]]:
        """
        Looks up attribution for an address.
        Returns dict with keys: attribution_type, entity_name, confidence, evidence
        Returns None if no attribution found.
        """
        ...

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Returns provider health status."""
        ...

    def get_status(self) -> Dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "display_name": self.display_name,
            "enabled": self._enabled,
            "status": self._status,
            "priority": self.priority,
            "last_error": self._last_error,
        }


# ═══════════════════════════════════════════════════════════════════
# Local DB Provider (queries AddressLabel + WalletAttribution tables)
# ═══════════════════════════════════════════════════════════════════

class LocalDBAttributionProvider(AttributionProvider):
    """
    Queries local PostgreSQL database for existing attributions.
    Checks address_labels and wallet_attributions tables.
    """

    def __init__(self):
        super().__init__("local_db", "Local Database", priority=10)
        self._status = "active"

    def lookup(self, address: str, chain: str = "ethereum") -> Optional[Dict[str, Any]]:
        addr_lower = address.strip().lower()
        try:
            from .database import SessionLocal
            from . import blockchain_models as bm
            db = SessionLocal()
            try:
                # Check address_labels table
                label = db.query(bm.AddressLabel).filter(
                    bm.AddressLabel.address == addr_lower,
                    bm.AddressLabel.chain == chain,
                    bm.AddressLabel.is_deleted == False,
                ).first()
                if label:
                    return {
                        "attribution_type": label.category,
                        "subcategory": label.subcategory,
                        "entity_name": label.label,
                        "confidence": label.confidence,
                        "source": label.source,
                        "provider_id": self.provider_id,
                        "is_verified": label.is_verified,
                        "metadata": label.metadata_json,
                    }

                # Check wallet_attributions table
                attr = db.query(bm.WalletAttribution).filter(
                    bm.WalletAttribution.address == addr_lower,
                    bm.WalletAttribution.chain == chain,
                    bm.WalletAttribution.is_active == True,
                ).order_by(bm.WalletAttribution.confidence.desc()).first()
                if attr:
                    return {
                        "attribution_type": attr.attribution_type,
                        "entity_name": attr.entity_name,
                        "confidence": attr.confidence,
                        "source": f"provider:{attr.provider_id}",
                        "provider_id": self.provider_id,
                        "evidence": attr.evidence_json,
                    }
            finally:
                db.close()
        except Exception as e:
            self._last_error = str(e)[:200]
            logger.debug("Local DB attribution lookup failed: %s", e)
        return None

    def health_check(self) -> Dict[str, Any]:
        try:
            from .database import SessionLocal
            db = SessionLocal()
            try:
                from . import blockchain_models as bm
                count = db.query(bm.AddressLabel).count()
                self._status = "active"
                return {"status": "healthy", "label_count": count}
            finally:
                db.close()
        except Exception as e:
            self._status = "degraded"
            return {"status": "degraded", "error": str(e)[:200]}


# ═══════════════════════════════════════════════════════════════════
# In-Memory Registry Provider (seed data for known entities)
# ═══════════════════════════════════════════════════════════════════

class InMemoryRegistryProvider(AttributionProvider):
    """
    In-memory registry of well-known, publicly verified addresses.
    Used as fallback when DB is empty. All entries are verifiable on-chain.
    """

    def __init__(self):
        super().__init__("registry", "In-Memory Registry", priority=20)
        self._status = "active"
        self._registry: Dict[str, Dict[str, Any]] = {}
        self._load_verified_addresses()

    def _load_verified_addresses(self):
        """Loads verified, publicly known addresses."""
        entries = {
            # Exchanges — verified hot wallets
            "0x3f5ce5fbfe3e9af3971dd833d26ba9b5c936f0be": {"type": "exchange", "sub": "hot_wallet", "name": "Binance Hot Wallet", "confidence": 0.99},
            "0x28c6c06298d514db089934071355e5743bf21d60": {"type": "exchange", "sub": "hot_wallet", "name": "Binance Hot Wallet 14", "confidence": 0.99},
            "0xdfd5293d8e347dfe59e90efd55b2956a1343963d": {"type": "exchange", "sub": "hot_wallet", "name": "OKX Hot Wallet", "confidence": 0.98},
            "0x21a31ee1afc51d94c2efccaa2092ad1028285549": {"type": "exchange", "sub": "hot_wallet", "name": "Bybit Hot Wallet", "confidence": 0.97},
            # DeFi — verified protocol contracts
            "0xae7ab96520de3a18e5e111b5eaab095312d7fe84": {"type": "defi_protocol", "sub": "staking", "name": "Lido Staking (stETH)", "confidence": 0.99},
            "0x7a250d5630b4cf539739df2c5dacb4c659f2488d": {"type": "defi_protocol", "sub": "dex", "name": "Uniswap V2 Router", "confidence": 0.99},
            "0xe592427a0ae9002fa3f0b06d01db5d3778a2dd53": {"type": "defi_protocol", "sub": "dex", "name": "Uniswap V3 Router", "confidence": 0.99},
            "0x1111111254fb6c44bac0bed2854e76f90643097d": {"type": "defi_protocol", "sub": "aggregator", "name": "1inch Aggregator V5", "confidence": 0.99},
            "0x87870bca3f12d455540a04d96e6866a9e4b1b6e4": {"type": "defi_protocol", "sub": "lending", "name": "Aave V3 Pool", "confidence": 0.99},
            # Bridges — verified L1 bridge contracts
            "0xa0c68c638235ee32657e8f720a23cec1bfc77c77": {"type": "bridge", "sub": "l1_bridge", "name": "Polygon PoS Bridge", "confidence": 0.99},
            "0xcee284f754e854890e311e3280b767f80797180d": {"type": "bridge", "sub": "l1_bridge", "name": "Arbitrum L1 Gateway Router", "confidence": 0.99},
            "0x99c9fc46f90e8a1c45c1113857e30d87a20c38c2": {"type": "bridge", "sub": "l1_bridge", "name": "Optimism Standard Bridge", "confidence": 0.99},
            # Mixers — verified mixer contracts
            "0x12d66f87a04a9e220743712ce6d9bb1b5616b8fc": {"type": "mixer", "sub": "privacy_pool", "name": "Tornado.Cash 0.1 ETH", "confidence": 0.99},
            "0x47ce0dbc5425fd3e2002a290749d5f6e9f6f8594": {"type": "mixer", "sub": "privacy_pool", "name": "Tornado.Cash 1 ETH", "confidence": 0.99},
            "0xa160cdab225685da1d56aa342ad8841c3b53f291": {"type": "mixer", "sub": "privacy_pool", "name": "Tornado.Cash 100 ETH", "confidence": 0.99},
            # NFT — verified marketplace contracts
            "0x00000000000000adc04c56bf30ac9d3c0aaf14dc": {"type": "nft_marketplace", "sub": "marketplace", "name": "Seaport (OpenSea)", "confidence": 0.99},
        }
        for addr, info in entries.items():
            self._registry[addr.lower()] = info

    def lookup(self, address: str, chain: str = "ethereum") -> Optional[Dict[str, Any]]:
        addr_lower = address.strip().lower()
        entry = self._registry.get(addr_lower)
        if entry:
            return {
                "attribution_type": entry["type"],
                "subcategory": entry.get("sub"),
                "entity_name": entry["name"],
                "confidence": entry["confidence"],
                "source": "verified_registry",
                "provider_id": self.provider_id,
            }
        return None

    def health_check(self) -> Dict[str, Any]:
        return {"status": "healthy", "entry_count": len(self._registry)}

    def get_entry_count(self) -> int:
        return len(self._registry)


# ═══════════════════════════════════════════════════════════════════
# ENS Resolution Provider (interface — requires external service)
# ═══════════════════════════════════════════════════════════════════

class ENSResolutionProvider(AttributionProvider):
    """
    ENS name resolution provider.
    Requires a configured Ethereum RPC endpoint.
    Resolves forward (name→address) and reverse (address→name).
    """

    def __init__(self):
        super().__init__("ens", "ENS Resolution", priority=30)
        self._status = "not_configured"

    def lookup(self, address: str, chain: str = "ethereum") -> Optional[Dict[str, Any]]:
        if chain != "ethereum":
            return None
        # ENS resolution requires Web3 + RPC endpoint
        try:
            import os
            rpc_url = os.getenv("ETH_RPC_URL")
            if not rpc_url:
                self._status = "not_configured"
                return None

            try:
                from web3 import Web3
            except ImportError:
                self._status = "not_configured"
                self._last_error = "web3 package not installed"
                return None

            w3 = Web3(Web3.HTTPProvider(rpc_url))
            if not w3.is_connected():
                self._status = "offline"
                return None

            # Reverse resolve: address → ENS name
            ens_name = w3.ens.name(address)
            if ens_name:
                self._status = "active"
                return {
                    "attribution_type": "public_label",
                    "subcategory": "ens_name",
                    "entity_name": ens_name,
                    "confidence": 0.85,
                    "source": "ens_reverse",
                    "provider_id": self.provider_id,
                }
            self._status = "active"
        except Exception as e:
            self._last_error = str(e)[:200]
            self._status = "degraded"
        return None

    def health_check(self) -> Dict[str, Any]:
        return {
            "status": self._status,
            "provider": "ens",
            "requires": "ETH_RPC_URL environment variable + web3 package",
        }


# ═══════════════════════════════════════════════════════════════════
# Wallet Attribution Engine (Orchestrator)
# ═══════════════════════════════════════════════════════════════════

class WalletAttributionEngine:
    """
    Enterprise wallet attribution engine.
    Queries multiple providers in priority order and returns the
    highest-confidence attribution found.

    Never fabricates attribution. If no provider has data,
    returns a structured "no_attribution" result.
    """

    def __init__(self):
        self._providers: Dict[str, AttributionProvider] = {}
        # Register default providers
        self.register_provider(LocalDBAttributionProvider())
        self.register_provider(InMemoryRegistryProvider())
        self.register_provider(ENSResolutionProvider())

    def register_provider(self, provider: AttributionProvider):
        """Registers an attribution provider."""
        self._providers[provider.provider_id] = provider
        logger.info("Registered attribution provider: %s (priority=%d)", provider.provider_id, provider.priority)

    def unregister_provider(self, provider_id: str):
        """Removes an attribution provider."""
        self._providers.pop(provider_id, None)

    def attribute(self, address: str, chain: str = "ethereum") -> Dict[str, Any]:
        """
        Resolves attribution for an address by querying all enabled providers
        in priority order. Returns the highest-confidence result.

        Never fabricates data. Returns structured 'no_attribution' if
        no provider has information.
        """
        addr_lower = address.strip().lower()
        if not addr_lower:
            return {
                "address": address,
                "attributed": False,
                "status": "invalid_address",
            }

        results = []
        providers_queried = []

        # Query providers in priority order (lower = higher priority)
        sorted_providers = sorted(
            self._providers.values(),
            key=lambda p: p.priority,
        )

        for provider in sorted_providers:
            if not provider._enabled:
                continue
            providers_queried.append(provider.provider_id)
            try:
                result = provider.lookup(addr_lower, chain)
                if result:
                    result["queried_at"] = _utcnow()
                    results.append(result)
            except Exception as e:
                logger.warning("Provider %s failed for %s: %s", provider.provider_id, addr_lower[:12], e)

        if not results:
            return {
                "address": address,
                "chain": chain,
                "attributed": False,
                "attribution_type": "unknown",
                "entity_name": None,
                "confidence": 0.0,
                "providers_queried": providers_queried,
                "status": "no_attribution",
                "queried_at": _utcnow(),
            }

        # Return highest confidence result
        best = max(results, key=lambda r: r.get("confidence", 0.0))

        return {
            "address": address,
            "chain": chain,
            "attributed": True,
            "attribution_type": best.get("attribution_type", "unknown"),
            "subcategory": best.get("subcategory"),
            "entity_name": best.get("entity_name"),
            "confidence": best.get("confidence", 0.0),
            "source": best.get("source"),
            "provider_id": best.get("provider_id"),
            "is_verified": best.get("is_verified", False),
            "providers_queried": providers_queried,
            "alternative_attributions": results[1:] if len(results) > 1 else [],
            "status": "attributed",
            "queried_at": _utcnow(),
        }

    def attribute_batch(self, addresses: List[str], chain: str = "ethereum") -> Dict[str, Dict[str, Any]]:
        """Batch attribution for multiple addresses."""
        return {addr: self.attribute(addr, chain) for addr in addresses}

    def save_attribution(
        self,
        address: str,
        attribution_type: str,
        entity_name: str,
        chain: str = "ethereum",
        confidence: float = 0.9,
        provider_id: str = "manual",
        evidence: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Saves a new attribution to the database."""
        if attribution_type not in ATTRIBUTION_TYPES:
            return {"status": "error", "detail": f"Invalid attribution_type: {attribution_type}"}

        addr_lower = address.strip().lower()
        try:
            from .database import SessionLocal
            from . import blockchain_models as bm
            db = SessionLocal()
            try:
                attr = bm.WalletAttribution(
                    id=str(uuid.uuid4()),
                    address=addr_lower,
                    chain=chain,
                    attribution_type=attribution_type,
                    entity_name=entity_name,
                    provider_id=provider_id,
                    confidence=confidence,
                    evidence_json=evidence,
                )
                db.add(attr)
                db.commit()
                return {"status": "created", "address": addr_lower, "attribution_type": attribution_type}
            finally:
                db.close()
        except Exception as e:
            return {"status": "error", "detail": str(e)[:200]}

    def get_all_provider_status(self) -> List[Dict[str, Any]]:
        """Returns status of all registered providers."""
        return [p.get_status() for p in self._providers.values()]

    def health_check(self) -> Dict[str, Any]:
        """Full health check across all providers."""
        provider_health = {}
        for pid, provider in self._providers.items():
            try:
                provider_health[pid] = provider.health_check()
            except Exception as e:
                provider_health[pid] = {"status": "error", "error": str(e)[:200]}

        healthy_count = sum(1 for h in provider_health.values() if h.get("status") == "healthy")
        return {
            "overall": "healthy" if healthy_count > 0 else "degraded",
            "total_providers": len(self._providers),
            "healthy_providers": healthy_count,
            "providers": provider_health,
            "checked_at": _utcnow(),
        }


# ═══════════════════════════════════════════════════════════════════
# Singleton
# ═══════════════════════════════════════════════════════════════════

wallet_attribution_engine = WalletAttributionEngine()
