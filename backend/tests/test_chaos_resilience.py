import pytest
from typing import Dict, Any

# Local state representation for testing fallback logic
NEO4J_STATUS = {"active": True}
REDIS_STATUS = {"active": True}

class ResilientGraphService:
    def get_transaction_graph(self, wallet: str) -> Dict[str, Any]:
        """Fetches graph nodes; falls back dynamically if Neo4j is offline."""
        if not NEO4J_STATUS["active"]:
            # Local NetworkX fallback response
            return {
                "engine": "NetworkX fallback",
                "nodes": [{"id": wallet, "label": "Target"}],
                "edges": []
            }
        return {
            "engine": "Neo4j Production",
            "nodes": [{"id": wallet, "label": "Target"}],
            "edges": []
        }

class ResilientCacheService:
    def get_cached_rpc(self, request_hash: str) -> str:
        """Reads JSON-RPC cache; falls back to Direct RPC Provider if Redis is down."""
        if not REDIS_STATUS["active"]:
            # Local SQLite database or Direct RPC Provider fallback
            return "direct_provider_rpc_response"
        return "redis_cached_rpc_response"

def test_neo4j_outage_fallback():
    service = ResilientGraphService()
    
    # 1. Normal state (Neo4j active)
    res_normal = service.get_transaction_graph("0x123")
    assert res_normal["engine"] == "Neo4j Production"
    
    # 2. Outage state (Neo4j down)
    NEO4J_STATUS["active"] = False
    res_fallback = service.get_transaction_graph("0x123")
    assert res_fallback["engine"] == "NetworkX fallback"
    
    # Restore status
    NEO4J_STATUS["active"] = True

def test_redis_outage_fallback():
    service = ResilientCacheService()
    
    # 1. Normal state (Redis active)
    res_normal = service.get_cached_rpc("hash_101")
    assert res_normal == "redis_cached_rpc_response"
    
    # 2. Outage state (Redis down)
    REDIS_STATUS["active"] = False
    res_fallback = service.get_cached_rpc("hash_101")
    assert res_fallback == "direct_provider_rpc_response"
    
    # Restore status
    REDIS_STATUS["active"] = True
