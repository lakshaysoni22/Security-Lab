import asyncio
import json
import urllib.request
import datetime
import time
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from .database import SessionLocal
from . import models

try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False

RPC_PROVIDERS = {
    "ethereum": ["https://cloudflare-eth.com", "https://eth.llamarpc.com"],
    "polygon": ["https://polygon-rpc.com", "https://polygon.llamarpc.com"],
    "bnb": ["https://bsc-dataseed.binance.org", "https://binance.llamarpc.com"],
    "avalanche": ["https://api.avax.network/ext/bc/C/rpc", "https://avax.llamarpc.com"],
    "arbitrum": ["https://arb1.arbitrum.io/rpc", "https://arbitrum.llamarpc.com"],
    "optimism": ["https://mainnet.optimism.io", "https://optimism.llamarpc.com"]
}

WSS_PROVIDERS = {
    "ethereum": "wss://ethereum-rpc.publicnode.com",
    "polygon": "wss://polygon-bor-rpc.publicnode.com",
    "bnb": "wss://bsc-rpc.publicnode.com",
    "avalanche": "wss://avalanche-c-chain-rpc.publicnode.com",
    "arbitrum": "wss://arbitrum-one-rpc.publicnode.com",
    "optimism": "wss://optimism-rpc.publicnode.com"
}

block_cache = set()

class BlockchainIndexer:
    def __init__(self):
        self.active_provider_idx = {chain: 0 for chain in RPC_PROVIDERS.keys()}
        self.circuit_breakers = {chain: {"failures": 0, "last_failure": None} for chain in RPC_PROVIDERS.keys()}
        self.websocket_active = {chain: False for chain in RPC_PROVIDERS.keys()}

    def _get_active_rpc(self, chain: str) -> str:
        providers = RPC_PROVIDERS.get(chain, ["https://cloudflare-eth.com"])
        idx = self.active_provider_idx.get(chain, 0)
        return providers[idx % len(providers)]

    def _failover_rpc(self, chain: str):
        providers = RPC_PROVIDERS.get(chain, [])
        if len(providers) > 1:
            self.active_provider_idx[chain] = (self.active_provider_idx[chain] + 1) % len(providers)
            print(f"[INDEXER] RPC Failover triggered for {chain}. New endpoint: {self._get_active_rpc(chain)}")

    def _rpc_request(self, chain: str, method: str, params: list, retries: int = 3) -> Optional[Any]:
        url = self._get_active_rpc(chain)
        payload = json.dumps({"jsonrpc": "2.0", "method": method, "params": params, "id": 1}).encode("utf-8")
        
        for attempt in range(retries):
            try:
                req = urllib.request.Request(
                    url,
                    data=payload,
                    headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
                )
                with urllib.request.urlopen(req, timeout=4) as res:
                    response = json.loads(res.read().decode("utf-8"))
                    self.circuit_breakers[chain]["failures"] = 0
                    return response.get("result")
            except Exception as e:
                self.circuit_breakers[chain]["failures"] += 1
                if self.circuit_breakers[chain]["failures"] >= 2:
                    self._failover_rpc(chain)
                    url = self._get_active_rpc(chain)
                time.sleep(0.5 * (attempt + 1))
        return None

    def get_latest_block_number(self, chain: str) -> Optional[int]:
        result = self._rpc_request(chain, "eth_blockNumber", [])
        if result:
            return int(result, 16)
        return None

    def fetch_block(self, chain: str, block_num: int) -> Optional[Dict[str, Any]]:
        block_hex = hex(block_num)
        return self._rpc_request(chain, "eth_getBlockByNumber", [block_hex, True])

    def index_chain_incrementally(self, chain: str, target_block: Optional[int] = None):
        """Indexes blocks incrementally up to target block height."""
        db: Session = SessionLocal()
        try:
            checkpoint = db.query(models.BlockIndexCheckpoint).filter(models.BlockIndexCheckpoint.chain == chain).first()
            latest_head = target_block or self.get_latest_block_number(chain)
            
            if not latest_head:
                return

            if not checkpoint:
                start_block = latest_head - 5
                checkpoint = models.BlockIndexCheckpoint(
                    id=chain + "_checkpoint",
                    chain=chain,
                    block_number=start_block
                )
                db.add(checkpoint)
                db.commit()
            
            current_block = checkpoint.block_number + 1
            max_sync_per_loop = min(current_block + 5, latest_head + 1)
            
            while current_block < max_sync_per_loop:
                if current_block > latest_head:
                    break
                    
                cache_key = f"{chain}_{current_block}"
                if cache_key in block_cache:
                    current_block += 1
                    continue
                
                block_data = self.fetch_block(chain, current_block)
                if not block_data:
                    break
                
                db.query(models.IndexedTransaction).filter(
                    models.IndexedTransaction.chain == chain,
                    models.IndexedTransaction.block_number == current_block
                ).delete()
                
                transactions = block_data.get("transactions", [])
                timestamp_sec = int(block_data.get("timestamp", "0x0"), 16)
                block_time = datetime.datetime.utcfromtimestamp(timestamp_sec)
                
                for tx in transactions:
                    val_eth = int(tx.get("value", "0x0"), 16) / (10**18)
                    gas_used = int(tx.get("gas", "0x0"), 16) * int(tx.get("gasPrice", "0x0"), 16) / (10**18)
                    tx_hash = tx.get("hash")
                    
                    if not tx_hash:
                        continue
                        
                    db_tx = models.IndexedTransaction(
                        id=tx_hash,
                        chain=chain,
                        tx_hash=tx_hash,
                        block_number=current_block,
                        from_address=tx.get("from", "").lower(),
                        to_address=tx.get("to", "0x0").lower() if tx.get("to") else "0x0",
                        value=val_eth,
                        gas_used=gas_used,
                        timestamp=block_time
                    )
                    db.add(db_tx)
                    
                    # Log Token Transfers
                    input_data = tx.get("input", "0x")
                    if input_data.startswith("0xa9059cbb"):
                        try:
                            to_addr = "0x" + input_data[34:74].lower()
                            val_token = int(input_data[74:], 16) / (10**18)
                            db_token = models.IndexedTokenTransfer(
                                id=tx_hash + "_token",
                                chain=chain,
                                tx_hash=tx_hash,
                                contract_address=tx.get("to", "").lower(),
                                from_address=tx.get("from", "").lower(),
                                to_address=to_addr,
                                value=val_token,
                                token_type="ERC-20",
                                symbol="USDT" if "d261" in tx.get("to", "") else "USDC" if "a0b8" in tx.get("to", "") else "TOKEN",
                                timestamp=block_time
                            )
                            db.add(db_token)
                        except Exception:
                            pass
                
                checkpoint.block_number = current_block
                db.commit()
                block_cache.add(cache_key)
                
                if len(block_cache) > 200:
                    block_cache.pop()
                    
                current_block += 1
                
        except Exception as e:
            print(f"[INDEXER] Sync loop error for {chain}: {e}")
        finally:
            db.close()

indexer = BlockchainIndexer()

async def listen_blockchain_websocket(chain: str):
    """Subscribes to block headers via WebSocket. Fallback triggers polling on connection drops."""
    if not WEBSOCKETS_AVAILABLE:
        print(f"[INDEXER] WSS unavailable for {chain}. Running HTTP Polling fallback.")
        return

    wss_url = WSS_PROVIDERS.get(chain)
    if not wss_url:
        return

    while True:
        try:
            print(f"[INDEXER] Connecting WSS block subscriber to {chain} node...")
            async with websockets.connect(wss_url, ping_interval=20, ping_timeout=10) as ws:
                indexer.websocket_active[chain] = True
                
                # Send subscribe subscription payload
                sub_payload = {"jsonrpc": "2.0", "id": 1, "method": "eth_subscribe", "params": ["newHeads"]}
                await ws.send(json.dumps(sub_payload))
                
                # Receive confirmation
                await ws.recv()
                print(f"[INDEXER] WSS subscription active for {chain} block heads.")
                
                while True:
                    msg = await ws.recv()
                    data = json.loads(msg)
                    params = data.get("params", {})
                    result = params.get("result", {})
                    block_hex = result.get("number")
                    
                    if block_hex:
                        block_num = int(block_hex, 16)
                        # Index the new block immediately
                        await asyncio.to_thread(indexer.index_chain_incrementally, chain, block_num)
                        
        except Exception as e:
            indexer.websocket_active[chain] = False
            print(f"[INDEXER] WSS subscription dropped for {chain}: {e}. Retrying in 10s...")
            await asyncio.sleep(10)

async def run_multi_chain_indexer():
    """Background parallel sync worker running constantly inside FastAPI lifecycle."""
    print("[INDEXER] Initializing Multi-Chain Indexer Core...")
    
    # 1. Start WebSocket Listeners in the background
    for chain in WSS_PROVIDERS.keys():
        asyncio.create_task(listen_blockchain_websocket(chain))
        
    while True:
        # 2. Polling loop: If WSS is degraded/offline, polling fills in block gaps
        tasks = []
        for chain in RPC_PROVIDERS.keys():
            if not indexer.websocket_active[chain]:
                # WSS offline: trigger HTTP polling sync
                tasks.append(asyncio.to_thread(indexer.index_chain_incrementally, chain))
                
        if tasks:
            await asyncio.gather(*tasks)
            
        await asyncio.sleep(8)
