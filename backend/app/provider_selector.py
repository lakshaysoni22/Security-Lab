from typing import List, Dict, Any
from .provider_health import health_monitor

class ProviderSelector:
    def select_best_provider(self, providers: List[str]) -> str:
        """Selects the provider with the lowest latency from a list of RPC endpoints."""
        best_provider = providers[0]
        min_latency = 99999.0
        
        for url in providers:
            health = health_monitor.ping_provider(url)
            if health["is_healthy"] and health["latency_ms"] < min_latency:
                min_latency = health["latency_ms"]
                best_provider = url
                
        return best_provider

provider_selector = ProviderSelector()
