import os
import json
import urllib.request
from typing import Dict, Any, Optional

ABI_CACHE_FILE = os.path.join(os.path.dirname(__file__), "..", "abi_cache.json")

# Preseeded famous function selectors (4-byte signatures)
PRESEEDED_SELECTORS = {
    "0xa9059cbb": "transfer(address,uint256)",
    "0x095ea7b3": "approve(address,uint256)",
    "0x23b872dd": "transferFrom(address,address,uint256)",
    "0x70a08231": "balanceOf(address)",
    "0x313ce567": "decimals()",
    "0x06fdde03": "name()",
    "0x95d89b41": "symbol()",
    "0xa22cb465": "setApprovalForAll(address,bool)",
    "0x2e1a7d4d": "withdraw(uint256)",
    "0xd0e30db0": "deposit()",
    "0x5c1112de": "swapExactTokensForTokens(uint256,uint256,address[],address,uint256)"
}

class ABIIntelligenceEngine:
    def __init__(self):
        self.cache = PRESEEDED_SELECTORS.copy()
        self._load_cache()

    def _load_cache(self):
        if os.path.exists(ABI_CACHE_FILE):
            try:
                with open(ABI_CACHE_FILE, "r") as f:
                    data = json.load(f)
                    self.cache.update(data)
            except Exception:
                pass

    def _save_cache(self):
        try:
            with open(ABI_CACHE_FILE, "w") as f:
                json.dump(self.cache, f, indent=2)
        except Exception:
            pass

    def resolve_selector(self, selector: str) -> str:
        """Resolves a 4-byte hexadecimal function selector to its signature definition."""
        sel_clean = selector.strip().lower()
        if not sel_clean.startswith("0x"):
            sel_clean = "0x" + sel_clean
        
        # Only take first 10 characters (0x + 8 hex chars)
        sel_key = sel_clean[:10]
        
        if sel_key in self.cache:
            return self.cache[sel_key]

        # Fetch signature from public directory API dynamically
        try:
            url = f"https://www.4byte.directory/api/v1/signatures/?hex_signature={sel_key}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=3) as res:
                response = json.loads(res.read().decode("utf-8"))
                results = response.get("results", [])
                if results:
                    signature = results[0].get("text_signature", "")
                    if signature:
                        self.cache[sel_key] = signature
                        self._save_cache()
                        return signature
        except Exception:
            pass

        return f"unknown_function_{sel_key}"

    def detect_proxy_contract(self, address: str, rpc_url: str) -> Optional[str]:
        """Detects if an address is an EIP-1967 proxy and retrieves its implementation address."""
        # EIP-1967 Implementation Slot
        EIP1967_SLOT = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
        
        payload = json.dumps({
            "jsonrpc": "2.0",
            "method": "eth_getStorageAt",
            "params": [address, EIP1967_SLOT, "latest"],
            "id": 1
        }).encode("utf-8")
        
        try:
            req = urllib.request.Request(rpc_url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=3) as res:
                response = json.loads(res.read().decode("utf-8"))
                result = response.get("result", "")
                if result and result != "0x" + "0"*64:
                    # Target address is stored in the last 40 hex characters
                    target_addr = "0x" + result[-40:]
                    return target_addr
        except Exception:
            pass
        return None

abi_engine = ABIIntelligenceEngine()
