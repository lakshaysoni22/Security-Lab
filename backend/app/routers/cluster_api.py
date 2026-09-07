"""
LEAtTrace Blockchain Intelligence — Advanced Cluster & Investigation API.

Production API with live blockchain data: wallet clustering, cross-chain tracing,
bridge detection, DeFi decoding, mixer analysis, entity resolution, risk scoring,
and relationship analysis. No mock data.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional

from ..blockchain_service import BlockchainService
from ..wallet_cluster_engine import wallet_cluster
from ..wallet_reputation import wallet_reputation
from ..cross_chain_service import cross_chain_service
from ..bridge_detector import bridge_detector
from ..defi_decoder import defi_decoder
from ..mixer_detector import mixer_detector
from ..threat_feed_manager import threat_feed_manager
from ..risk_engine import risk_engine
from ..entity_resolution import entity_resolution
from ..relationship_engine import relationship_engine
from ..laundering_engine import laundering_engine
from ..risk_patterns import risk_pattern_engine

router = APIRouter(prefix="/api", tags=["Advanced Blockchain Intelligence"])

_blockchain = BlockchainService()


@router.get("/wallet/cluster")
def get_wallet_cluster(
    address: str = Query(..., description="Target wallet address to analyze co-spending clusters."),
    chain: str = Query("ethereum", description="Blockchain network."),
):
    """Enterprise wallet clustering with 6 heuristics using live blockchain data."""
    txs = _blockchain.fetch_real_transactions(address, chain)
    return wallet_cluster.cluster_address_network(address, txs)


@router.get("/wallet/reputation")
def get_wallet_reputation(
    address: str = Query(..., description="Target wallet address."),
    chain: str = Query("ethereum", description="Blockchain network."),
):
    """Wallet reputation score calculated from live transaction data."""
    txs = _blockchain.fetch_real_transactions(address, chain)
    threat = _blockchain.get_threat_intelligence(address)
    sanction_exposure = 90.0 if threat.get("is_sanctioned") else 0.0
    return wallet_reputation.calculate_reputation(address, len(txs), sanction_exposure)


@router.get("/wallet/relationships")
def get_wallet_relationships(
    address: str = Query(..., description="Target wallet address."),
    chain: str = Query("ethereum", description="Blockchain network."),
):
    """Analyzes all counterparty relationships for a wallet."""
    txs = _blockchain.fetch_real_transactions(address, chain)
    return relationship_engine.analyze_relationships(address, txs)


@router.get("/crosschain/trace")
def trace_crosschain_flow(
    address: str = Query(..., description="Target address."),
    chain: str = Query("ethereum", description="Source blockchain."),
):
    """Cross-chain fund tracing with bridge detection and timeline."""
    txs = _blockchain.fetch_real_transactions(address, chain)
    return cross_chain_service.trace_cross_chain_movements(txs, address)


@router.get("/crosschain/multichain")
def track_multichain(address: str = Query(..., description="Target address.")):
    """Tracks wallet activity across all supported chains."""
    return cross_chain_service.track_wallet_across_chains(address, _blockchain)


@router.get("/bridge/detect")
def detect_bridge(to_address: str = Query(..., description="Target bridge contract address.")):
    """Identifies a bridge contract and returns metadata."""
    res = bridge_detector.identify_bridge(to_address)
    if not res:
        raise HTTPException(status_code=404, detail="Bridge contract not found in registry")
    return res


@router.get("/bridge/analyze")
def analyze_bridge_tx(
    to_address: str = Query(..., description="Bridge contract address."),
    value_eth: float = Query(0.0, description="ETH value sent."),
    sender_address: str = Query("0x0", description="Sender address."),
):
    """Full bridge transaction analysis with risk scoring."""
    sender_risk = 0
    threat = _blockchain.get_threat_intelligence(sender_address)
    if threat.get("is_sanctioned"):
        sender_risk = 90
    return bridge_detector.analyze_bridge_transaction(to_address, value_eth, sender_address, sender_risk)


@router.get("/bridge/list")
def list_bridges(chain: Optional[str] = Query(None, description="Filter by target chain.")):
    """Lists all known bridge contracts with metadata."""
    if chain:
        return {"bridges": bridge_detector.get_bridges_by_chain(chain)}
    return {"bridges": bridge_detector.get_all_bridges()}


@router.get("/defi/decode")
def decode_defi_call(
    to_address: str = Query(..., description="Smart contract target address."),
    input_data: str = Query("0x", description="Method input data in hex."),
    value_eth: float = Query(0.0, description="ETH value sent."),
):
    """Decodes DeFi transaction with protocol identification and action classification."""
    return defi_decoder.decode_defi_transaction(to_address, input_data, value_eth)


@router.get("/defi/protocols")
def list_protocols(protocol_type: Optional[str] = Query(None, description="Filter by protocol type.")):
    """Lists all known DeFi protocols."""
    from ..protocol_registry import protocol_registry
    if protocol_type:
        return {"protocols": protocol_registry.get_by_type(protocol_type)}
    return {"protocols": protocol_registry.get_all()}


@router.get("/mixer/analyze")
def analyze_mixer_obfuscation(
    address: str = Query(..., description="Target wallet address."),
    chain: str = Query("ethereum", description="Blockchain network."),
):
    """Full mixer/obfuscation analysis with pattern detection and confidence scoring."""
    txs = _blockchain.fetch_real_transactions(address, chain)
    result = mixer_detector.analyze_address_obfuscation(address, txs)

    # Match risk patterns
    matched = risk_pattern_engine.match_patterns(result)
    result["matched_risk_patterns"] = matched
    result["combined_pattern_risk"] = risk_pattern_engine.calculate_combined_risk(matched)

    return result


@router.get("/threat/intelligence")
def check_threat_intelligence(address: str = Query(..., description="Target wallet address.")):
    """Checks address against threat intelligence feeds and sanctions lists."""
    return threat_feed_manager.verify_address_threat(address)


@router.get("/risk/score")
def get_risk_score(
    exposure_percent: float = Query(0.0, description="Direct mixer exposure."),
    has_peel_chain: bool = Query(False, description="Presence of active peel chains."),
):
    """Legacy risk scoring endpoint (backward compatible)."""
    return {"risk_score": risk_engine.evaluate_risk(exposure_percent, has_peel_chain)}


@router.get("/entity/resolve")
def resolve_entity_name(address: str = Query(..., description="Target address to resolve.")):
    """Resolves address to known entity with metadata."""
    res = entity_resolution.resolve_entity(address)
    if not res:
        raise HTTPException(status_code=404, detail="Entity not matched in registry")
    return res


@router.get("/entity/search")
def search_entities(
    query: str = Query(..., description="Entity name search query."),
    category: Optional[str] = Query(None, description="Filter by category."),
):
    """Searches entity registry by name or category."""
    return {"results": entity_resolution.search_entities(query, category)}


@router.post("/entity/tag")
def tag_address(
    address: str = Query(..., description="Wallet address to tag."),
    label: str = Query(..., description="Entity label."),
    category: str = Query("unknown", description="Entity category."),
):
    """Tags an address with an entity label in the database."""
    return entity_resolution.tag_address(address, label, category)


@router.get("/aml/analyze")
def aml_analysis(
    address: str = Query(..., description="Target address."),
    chain: str = Query("ethereum", description="Blockchain network."),
):
    """Full anti-money laundering pattern analysis."""
    txs = _blockchain.fetch_real_transactions(address, chain)
    return laundering_engine.full_aml_analysis(txs, address)
