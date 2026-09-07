"""
LEAtTrace Blockchain Intelligence — Risk API Router.

Production API for blockchain risk scoring: wallet, transaction, entity,
bridge, batch scoring, and risk pattern analysis.
"""

from fastapi import APIRouter, HTTPException, Query, Body
from typing import List, Optional
from pydantic import BaseModel as PydanticModel

from ..risk_engine import risk_engine
from ..risk_patterns import risk_pattern_engine
from ..blockchain_service import BlockchainService
from ..mixer_detector import mixer_detector
from ..laundering_engine import laundering_engine
from ..entity_resolution import entity_resolution


router = APIRouter(prefix="/api/blockchain/risk", tags=["Blockchain Risk Intelligence"])

_blockchain = BlockchainService()


class WalletRiskRequest(PydanticModel):
    address: str
    chain: str = "ethereum"

class BatchRiskRequest(PydanticModel):
    addresses: List[str]
    chain: str = "ethereum"

class TransactionRiskRequest(PydanticModel):
    tx_hash: str
    value_eth: float = 0.0
    sender_risk: int = 0
    receiver_risk: int = 0
    is_to_mixer: bool = False
    is_to_bridge: bool = False


@router.get("/wallet/{address}")
def get_wallet_risk(
    address: str,
    chain: str = Query("ethereum", description="Blockchain network"),
):
    """Comprehensive wallet risk assessment with 12-dimension scoring."""
    # Fetch real data
    txs = _blockchain.fetch_real_transactions(address, chain)
    threat = _blockchain.get_threat_intelligence(address)
    mixer_data = _blockchain.check_mixer_exposure(address)
    bridge_data = _blockchain.trace_cross_chain_bridges(address)

    # Extract metrics
    incoming = sum(1 for tx in txs if tx.get("to", "").lower() == address.lower())
    outgoing = len(txs) - incoming
    total_value = sum(tx.get("value", 0.0) for tx in txs)
    unique_cps = len(set(tx.get("from", "") for tx in txs) | set(tx.get("to", "") for tx in txs))
    is_contract = _blockchain.check_smart_contract(address, chain)

    # Entity check
    entity = entity_resolution.resolve_entity(address)
    is_exchange = entity_resolution.is_exchange(address)

    # Peel chain check
    peel = laundering_engine.detect_peel_chain(txs, address)

    result = risk_engine.score_wallet(
        address=address,
        tx_count=len(txs),
        total_volume_eth=total_value,
        incoming_count=incoming,
        outgoing_count=outgoing,
        unique_counterparties=unique_cps,
        is_contract=is_contract,
        age_days=180 if len(txs) > 5 else 7,
        mixer_exposure_pct=mixer_data.get("mixer_exposure_percent", 0.0),
        is_sanctioned=threat.get("is_sanctioned", False),
        counterparty_avg_risk=0.0,
        has_bridge_activity=bridge_data.get("bridging_activity_detected", False),
        has_defi_activity=len(_blockchain.get_defi_interactions(address)) > 0,
        peel_chain_detected=peel.get("is_peel_chain_active", False),
        is_exchange_wallet=is_exchange,
    )

    result["chain"] = chain
    result["entity"] = entity["entity_name"] if entity else "Unknown"
    result["threat_intel"] = threat
    return result


@router.post("/wallet")
def score_wallet_custom(req: WalletRiskRequest):
    """Scores a wallet with auto-fetched blockchain data."""
    return get_wallet_risk(req.address, req.chain)


@router.post("/transaction")
def score_transaction(req: TransactionRiskRequest):
    """Scores an individual transaction for risk."""
    return risk_engine.score_transaction(
        tx_hash=req.tx_hash,
        value_eth=req.value_eth,
        sender_risk=req.sender_risk,
        receiver_risk=req.receiver_risk,
        is_to_mixer=req.is_to_mixer,
        is_to_bridge=req.is_to_bridge,
    )


@router.post("/batch")
def score_batch(req: BatchRiskRequest):
    """Batch risk scoring for multiple addresses."""
    results = []
    for addr in req.addresses[:20]:  # Limit batch size
        try:
            txs = _blockchain.fetch_real_transactions(addr, req.chain)
            threat = _blockchain.get_threat_intelligence(addr)
            score = risk_engine.score_wallet(
                address=addr,
                tx_count=len(txs),
                is_sanctioned=threat.get("is_sanctioned", False),
            )
            results.append({"address": addr, "risk_score": score["overall_risk_score"], "risk_tier": score["risk_tier"]})
        except Exception:
            results.append({"address": addr, "risk_score": 0, "risk_tier": "error"})

    return {"batch_size": len(results), "results": results}


@router.get("/entity/{entity_name}")
def get_entity_risk(entity_name: str):
    """Aggregates risk across all wallets belonging to an entity."""
    entities = entity_resolution.search_entities(entity_name)
    if not entities:
        raise HTTPException(status_code=404, detail="Entity not found")

    wallet_risks = []
    for ent in entities[:10]:
        addr = ent.get("address", "")
        threat = _blockchain.get_threat_intelligence(addr)
        score = risk_engine.score_wallet(
            address=addr,
            is_sanctioned=threat.get("is_sanctioned", False),
        )
        wallet_risks.append(score["overall_risk_score"])

    return risk_engine.score_entity(entity_name, wallet_risks)


@router.get("/patterns")
def list_risk_patterns():
    """Lists all known blockchain risk/laundering patterns."""
    return {"patterns": risk_pattern_engine.get_all_patterns()}


@router.get("/aml/{address}")
def get_aml_analysis(address: str, chain: str = Query("ethereum")):
    """Full anti-money laundering analysis for an address."""
    txs = _blockchain.fetch_real_transactions(address, chain)
    return laundering_engine.full_aml_analysis(txs, address)


@router.get("/obfuscation/{address}")
def get_obfuscation_analysis(address: str, chain: str = Query("ethereum")):
    """Full obfuscation/mixer analysis for an address."""
    txs = _blockchain.fetch_real_transactions(address, chain)
    return mixer_detector.analyze_address_obfuscation(address, txs)
