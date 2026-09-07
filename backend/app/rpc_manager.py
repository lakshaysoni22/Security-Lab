"""
LEATrace Blockchain Intelligence — Enterprise RPC Manager.

Production-grade RPC management with 9-chain support, weighted load balancing,
rate limiting, failover, httpx connection pooling, WebSocket support, and metrics.

PRODUCTION INVARIANTS:
- Uses httpx connection pool (replaces urllib.request).
- Three-state circuit breaker per provider.
- No fabricated fallback data on RPC failure.
- Batch JSON-RPC support for multi-call optimization.
"""

import os
import json
import time
import logging
from typing import Dict, List, Any, Optional

from .provider_health import health_monitor
from .connection_pool import connection_pool
from .rpc_metrics import rpc_metrics

logger = logging.getLogger("leatrace.rpc_manager")

# ===================================================================
# 9-Chain Provider Registry (env-configurable, no hardcoded creds)
# ===================================================================

PROVIDER_ENDPOINTS = {
    "ethereum": [
        os.getenv("ETH_RPC_1", "https://cloudflare-eth.com"),
        os.getenv("ETH_RPC_2", "https://eth.llamarpc.com"),
        os.getenv("ETH_RPC_3", "https://api.ankr.com/public/eth"),
    ],
    "polygon": [
        os.getenv("POLYGON_RPC_1", "https://polygon-rpc.com"),
        os.getenv("POLYGON_RPC_2", "https://polygon.llamarpc.com"),
        os.getenv("POLYGON_RPC_3", "https://api.ankr.com/public/polygon"),
    ],
    "bnb": [
        os.getenv("BNB_RPC_1", "https://bsc-dataseed.binance.org"),
        os.getenv("BNB_RPC_2", "https://binance.llamarpc.com"),
        os.getenv("BNB_RPC_3", "https://api.ankr.com/public/bsc"),
    ],
    "avalanche": [
        os.getenv("AVAX_RPC_1", "https://api.avax.network/ext/bc/C/rpc"),
        os.getenv("AVAX_RPC_2", "https://avax.llamarpc.com"),
        os.getenv("AVAX_RPC_3", "https://api.ankr.com/public/avax"),
    ],
    "arbitrum": [
        os.getenv("ARB_RPC_1", "https://arb1.arbitrum.io/rpc"),
        os.getenv("ARB_RPC_2", "https://arbitrum.llamarpc.com"),
        os.getenv("ARB_RPC_3", "https://api.ankr.com/public/arbitrum"),
    ],
    "optimism": [
        os.getenv("OP_RPC_1", "https://mainnet.optimism.io"),
        os.getenv("OP_RPC_2", "https://optimism.llamarpc.com"),
        os.getenv("OP_RPC_3", "https://api.ankr.com/public/optimism"),
    ],
    "base": [
        os.getenv("BASE_RPC_1", "https://mainnet.base.org"),
        os.getenv("BASE_RPC_2", "https://base.llamarpc.com"),
        os.getenv("BASE_RPC_3", "https://api.ankr.com/public/base"),
    ],
    "tron": [
        os.getenv("TRON_RPC_1", "https://api.trongrid.io"),
        os.getenv("TRON_RPC_2", "https://api.tronstack.io"),
    ],
    "bitcoin": [
        os.getenv("BTC_API_1", "https://blockstream.info/api"),
        os.getenv("BTC_API_2", "https://mempool.space/api"),
    ],
}

# WebSocket providers for real-time block subscription
WSS_PROVIDERS = {
    "ethereum": os.getenv("ETH_WSS", "wss://ethereum-rpc.publicnode.com"),
    "polygon": os.getenv("POLYGON_WSS", "wss://polygon-bor-rpc.publicnode.com"),
    "bnb": os.getenv("BNB_WSS", "wss://bsc-rpc.publicnode.com"),
    "avalanche": os.getenv("AVAX_WSS", "wss://avalanche-c-chain-rpc.publicnode.com"),
    "arbitrum": os.getenv("ARB_WSS", "wss://arbitrum-one-rpc.publicnode.com"),
    "optimism": os.getenv("OP_WSS", "wss://optimism-rpc.publicnode.com"),
    "base": os.getenv("BASE_WSS", "wss://base-rpc.publicnode.com"),
}

# Rate limits per provider domain (requests per second)
RATE_LIMITS = {
    "cloudflare-eth.com": 25,
    "llamarpc.com": 20,
    "ankr.com": 30,
    "trongrid.io": 15,
    "blockstream.info": 10,
    "mempool.space": 10,
    "base.org": 20,
    "default": 15,
}


class RPCManager:
    """Enterprise RPC manager with 9-chain support, failover, rate limiting, and metrics."""

    def __init__(self):
        self.endpoints = PROVIDER_ENDPOINTS
        self.wss_providers = WSS_PROVIDERS
        self._request_timestamps: Dict[str, List[float]] = {}
        self._provider_latencies: Dict[str, List[float]] = {}
        self._cache: Dict[str, Any] = {}
        self._cache_ttl: Dict[str, float] = {}
        self._cache_default_ttl = 12.0  # seconds
        self._cache_max_size = 1000

    def get_supported_chains(self) -> List[str]:
        """Returns all supported blockchain chains."""
        return list(self.endpoints.keys())

    def get_healthy_provider(self, chain: str) -> str:
        """Finds the fastest available, non-tripped, non-rate-limited RPC provider."""
        urls = self.endpoints.get(chain, [])
        if not urls:
            return self.endpoints.get("ethereum", ["https://cloudflare-eth.com"])[0]

        # Sort by latency (fastest first), filter tripped and rate-limited
        candidates = []
        for url in urls:
            if not rpc_metrics.is_allowed(url):
                continue
            if self._is_rate_limited(url):
                continue
            # Use cached health if available, else check
            health = health_monitor.health_history.get(url)
            if health and health.get("is_healthy"):
                latency = health.get("latency_ms", 9999)
                candidates.append((url, latency))
            elif health is None:
                # Unknown health — allow with high latency penalty
                candidates.append((url, 5000))

        if candidates:
            candidates.sort(key=lambda x: x[1])
            return candidates[0][0]

        # Fallback: return first endpoint even if tripped
        return urls[0]

    def execute_rpc(self, chain: str, method: str, params: List[Any], cache_ttl: Optional[float] = None) -> Optional[Any]:
        """Executes JSON-RPC with failover, rate limiting, caching, and metrics tracking."""
        # Check cache
        cache_key = f"{chain}:{method}:{json.dumps(params, sort_keys=True, default=str)}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        # Special handling for non-EVM chains
        if chain == "bitcoin":
            result = self._execute_bitcoin_api(method, params)
            if result is not None:
                self._set_cached(cache_key, result, cache_ttl)
            return result
        if chain == "tron":
            result = self._execute_tron_api(method, params)
            if result is not None:
                self._set_cached(cache_key, result, cache_ttl)
            return result

        url = self.get_healthy_provider(chain)
        payload = {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}

        # Try primary provider
        result = self._try_rpc_request(url, payload)
        if result is not None:
            self._set_cached(cache_key, result, cache_ttl)
            return result

        # Failover: try alternate providers
        for alt_url in self.endpoints.get(chain, []):
            if alt_url != url and rpc_metrics.is_allowed(alt_url):
                result = self._try_rpc_request(alt_url, payload)
                if result is not None:
                    self._set_cached(cache_key, result, cache_ttl)
                    return result

        return None

    def execute_batch_rpc(self, chain: str, calls: List[dict], cache_ttl: Optional[float] = None) -> Optional[List[Any]]:
        """
        Executes a batch of JSON-RPC calls in a single request.
        Each call should be {"method": "...", "params": [...]}.
        Returns list of results in the same order as calls.
        """
        if chain in ("bitcoin", "tron"):
            # Non-EVM chains don't support batch JSON-RPC
            return [self.execute_rpc(chain, c["method"], c.get("params", [])) for c in calls]

        url = self.get_healthy_provider(chain)
        batch_payload = [
            {"jsonrpc": "2.0", "method": c["method"], "params": c.get("params", []), "id": i + 1}
            for i, c in enumerate(calls)
        ]

        start = time.time()
        try:
            self._record_rate(url)
            rpc_metrics.record_request(url)

            response = connection_pool.post_json(url, batch_payload, timeout=10)
            if response is None:
                rpc_metrics.record_failure(url)
                return None

            latency = (time.time() - start) * 1000
            rpc_metrics.record_success(url, latency)

            # Sort by id to maintain order
            if isinstance(response, list):
                response.sort(key=lambda r: r.get("id", 0))
                return [r.get("result") for r in response]
            return None
        except Exception:
            rpc_metrics.record_failure(url)
            return None

    def _try_rpc_request(self, url: str, payload: dict) -> Optional[Any]:
        """Attempts a single RPC request using httpx connection pool."""
        start = time.time()
        try:
            self._record_rate(url)
            rpc_metrics.record_request(url)

            response = connection_pool.post_json(url, payload, timeout=5)
            if response is None:
                rpc_metrics.record_failure(url)
                return None

            latency = (time.time() - start) * 1000
            rpc_metrics.record_success(url, latency)
            self._record_latency(url, latency)

            return response.get("result")
        except Exception:
            rpc_metrics.record_failure(url)
            return None

    def _execute_bitcoin_api(self, method: str, params: List[Any]) -> Optional[Any]:
        """Bitcoin REST API adapter (read-only investigation support)."""
        urls = self.endpoints.get("bitcoin", [])
        if not urls:
            return None

        for base_url in urls:
            try:
                if method == "address_info" and params:
                    api_url = f"{base_url}/address/{params[0]}"
                elif method == "address_txs" and params:
                    api_url = f"{base_url}/address/{params[0]}/txs"
                elif method == "tx_info" and params:
                    api_url = f"{base_url}/tx/{params[0]}"
                elif method == "block_height":
                    api_url = f"{base_url}/blocks/tip/height"
                else:
                    return None

                result = connection_pool.get_json(api_url, timeout=8)
                if result is not None:
                    # get_json returns {"text": "..."} for plain text
                    if "text" in result and len(result) == 1:
                        return result["text"]
                    return result
            except Exception:
                continue
        return None

    def _execute_tron_api(self, method: str, params: List[Any]) -> Optional[Any]:
        """Tron HTTP API adapter."""
        urls = self.endpoints.get("tron", [])
        if not urls:
            return None

        tron_key = os.getenv("TRON_API_KEY")
        extra_headers = {}
        if tron_key:
            extra_headers["TRON-PRO-API-KEY"] = tron_key

        for base_url in urls:
            try:
                if method == "getaccount" and params:
                    api_url = f"{base_url}/v1/accounts/{params[0]}"
                elif method == "gettransactions" and params:
                    api_url = f"{base_url}/v1/accounts/{params[0]}/transactions"
                elif method == "getblock":
                    api_url = f"{base_url}/wallet/getnowblock"
                else:
                    return None

                result = connection_pool.get_json(api_url, timeout=8, extra_headers=extra_headers)
                return result
            except Exception:
                continue
        return None

    def _is_rate_limited(self, url: str) -> bool:
        """Checks if a provider has exceeded its rate limit."""
        now = time.time()
        timestamps = self._request_timestamps.get(url, [])
        # Clean old timestamps (older than 1 second)
        timestamps = [t for t in timestamps if now - t < 1.0]
        self._request_timestamps[url] = timestamps

        # Determine limit
        limit = RATE_LIMITS.get("default", 15)
        for domain, lim in RATE_LIMITS.items():
            if domain in url:
                limit = lim
                break

        return len(timestamps) >= limit

    def _record_rate(self, url: str):
        """Records a request timestamp for rate limiting."""
        if url not in self._request_timestamps:
            self._request_timestamps[url] = []
        self._request_timestamps[url].append(time.time())

    def _record_latency(self, url: str, latency_ms: float):
        """Records latency for priority sorting."""
        if url not in self._provider_latencies:
            self._provider_latencies[url] = []
        self._provider_latencies[url].append(latency_ms)
        # Keep last 50
        if len(self._provider_latencies[url]) > 50:
            self._provider_latencies[url] = self._provider_latencies[url][-50:]

    def _get_cached(self, key: str) -> Optional[Any]:
        """Returns cached value if within TTL."""
        if key in self._cache and key in self._cache_ttl:
            if time.time() < self._cache_ttl[key]:
                return self._cache[key]
            else:
                del self._cache[key]
                del self._cache_ttl[key]
        return None

    def _set_cached(self, key: str, value: Any, ttl: Optional[float] = None):
        """Caches a value with TTL."""
        self._cache[key] = value
        self._cache_ttl[key] = time.time() + (ttl or self._cache_default_ttl)
        # Evict oldest entries if cache too large
        while len(self._cache) > self._cache_max_size:
            oldest_key = min(self._cache_ttl, key=self._cache_ttl.get)
            self._cache.pop(oldest_key, None)
            self._cache_ttl.pop(oldest_key, None)

    def get_rpc_status(self) -> Dict[str, Any]:
        """Returns comprehensive RPC health dashboard."""
        chain_status = {}
        for chain, urls in self.endpoints.items():
            providers = []
            for url in urls:
                health = health_monitor.health_history.get(url, {})
                avg_latency = 0.0
                latencies = self._provider_latencies.get(url, [])
                if latencies:
                    avg_latency = sum(latencies) / len(latencies)
                providers.append({
                    "url": url[:50] + "..." if len(url) > 50 else url,
                    "healthy": health.get("is_healthy", False),
                    "latency_ms": round(health.get("latency_ms", 0), 1),
                    "avg_latency_ms": round(avg_latency, 1),
                    "circuit_state": rpc_metrics._get_breaker(url).state.value,
                    "success_rate": rpc_metrics.get_success_rate(url),
                    "rate_limited": self._is_rate_limited(url),
                })
            chain_status[chain] = {
                "provider_count": len(urls),
                "healthy_count": sum(1 for p in providers if p["healthy"]),
                "has_wss": chain in self.wss_providers,
                "providers": providers,
            }

        return {
            "supported_chains": self.get_supported_chains(),
            "total_chains": len(self.endpoints),
            "cache_size": len(self._cache),
            "chains": chain_status,
            "circuit_breaker_metrics": rpc_metrics.get_all_metrics(),
        }


rpc_manager = RPCManager()
