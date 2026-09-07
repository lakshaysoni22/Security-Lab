"""
LEATrace Production Archival Node Manager.

Provides multi-client RPC abstraction, automatic node health detection,
sync monitoring, archive depth verification, and automatic failover for:
- Ethereum Geth
- Erigon (Archive & Tracing)
- Nethermind
- Bitcoin Core
"""

import json
import time
import logging
import urllib.request
import urllib.parse
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("leatrace.nodes.archive")


class ArchiveNodeManager:
    """
    Production RPC Node Abstraction Layer.
    Monitors latency, syncing state, and archive depth for EVM & Bitcoin RPC nodes.
    Automatically routes requests to the healthiest node.
    """

    def __init__(self):
        self.node_registry: Dict[str, List[Dict[str, Any]]] = {
            "ethereum": [
                {"name": "Erigon-Local", "url": "http://localhost:8545", "client_type": "erigon", "is_archive": True},
                {"name": "Geth-Local", "url": "http://localhost:8546", "client_type": "geth", "is_archive": False},
                {"name": "Nethermind-Local", "url": "http://localhost:8547", "client_type": "nethermind", "is_archive": True},
                {"name": "Alchemy-Fallback", "url": "https://eth-mainnet.g.alchemy.com/v2/demo", "client_type": "remote", "is_archive": True},
            ],
            "bitcoin": [
                {"name": "Bitcoin-Core-Local", "url": "http://localhost:8332", "client_type": "bitcoind", "is_archive": True},
                {"name": "Blockstream-Fallback", "url": "https://blockstream.info/api", "client_type": "remote_rest", "is_archive": True},
            ],
        }
        self.node_health_cache: Dict[str, Dict[str, Any]] = {}
        self.refresh_health_status()

    def _rpc_call(self, url: str, method: str, params: List[Any], timeout: float = 3.0) -> Tuple[bool, Any, float]:
        """Executes a standard JSON-RPC 2.0 request and measures latency in ms."""
        start_time = time.perf_counter()
        payload = json.dumps({"jsonrpc": "2.0", "method": method, "params": params, "id": 1}).encode("utf-8")
        headers = {"Content-Type": "application/json"}

        try:
            req = urllib.request.Request(url, data=payload, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as response:
                result = json.loads(response.read().decode("utf-8"))
                latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
                if "error" in result:
                    return False, result["error"], latency_ms
                return True, result.get("result"), latency_ms
        except Exception as e:
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return False, str(e), latency_ms

    def check_node_health(self, node: Dict[str, Any], chain: str = "ethereum") -> Dict[str, Any]:
        """Inspects syncing status, current block height, and archive depth."""
        url = node["url"]
        client_type = node["client_type"]

        if chain == "bitcoin":
            success, res, latency = self._rpc_call(url, "getblockchaininfo", [])
            if success and isinstance(res, dict):
                return {
                    "name": node["name"],
                    "status": "healthy",
                    "latency_ms": latency,
                    "block_height": res.get("blocks", 0),
                    "is_syncing": res.get("initialblockdownload", False),
                    "is_archive": not res.get("pruned", False),
                    "client_type": client_type,
                }
            return {"name": node["name"], "status": "unhealthy", "error": str(res), "latency_ms": latency}

        # EVM Chains (Geth / Erigon / Nethermind)
        success, block_res, latency = self._rpc_call(url, "eth_blockNumber", [])
        if not success:
            return {"name": node["name"], "status": "unhealthy", "error": str(block_res), "latency_ms": latency}

        block_height = int(block_res, 16) if isinstance(block_res, str) else 0

        # Check sync status
        _, sync_res, _ = self._rpc_call(url, "eth_syncing", [])
        is_syncing = bool(sync_res) if isinstance(sync_res, (dict, bool)) else False

        # Verify archive depth by checking historical balance at Genesis block #1
        is_archive = node.get("is_archive", False)
        if success:
            _, arch_res, _ = self._rpc_call(url, "eth_getBalance", ["0x0000000000000000000000000000000000000000", "0x1"])
            if isinstance(arch_res, str):
                is_archive = True

        return {
            "name": node["name"],
            "status": "healthy",
            "latency_ms": latency,
            "block_height": block_height,
            "is_syncing": is_syncing,
            "is_archive": is_archive,
            "client_type": client_type,
        }

    def refresh_health_status(self):
        """Scans all registered node endpoints and updates cached metrics."""
        for chain, nodes in self.node_registry.items():
            for node in nodes:
                health = self.check_node_health(node, chain=chain)
                self.node_health_cache[node["name"]] = health
                logger.info(f"Node '{node['name']}' health: {health['status']} ({health.get('latency_ms', 0)}ms)")

    def get_best_node(self, chain: str = "ethereum", require_archive: bool = False) -> Dict[str, Any]:
        """
        Returns the optimal RPC node based on health status, lowest latency,
        and archive capability requirements.
        """
        nodes = self.node_registry.get(chain, [])
        healthy_nodes = []

        for node in nodes:
            name = node["name"]
            health = self.node_health_cache.get(name, {})
            if health.get("status") == "healthy" and not health.get("is_syncing", True):
                if require_archive and not health.get("is_archive", False):
                    continue
                healthy_nodes.append((node, health.get("latency_ms", 9999)))

        if healthy_nodes:
            # Sort by lowest latency
            healthy_nodes.sort(key=lambda x: x[1])
            return healthy_nodes[0][0]

        # Return fallback remote node if all local nodes are syncing or offline
        return nodes[-1] if nodes else {"name": "Default-Fallback", "url": "https://eth-mainnet.g.alchemy.com/v2/demo"}


archive_node_manager = ArchiveNodeManager()
