"""
LEATrace Blockchain Intelligence — Database Models.

Production database models for blockchain intelligence:
- Address labels (consolidated, versioned)
- Wallet attribution (provider-tracked)
- Exchange wallet classification
- AML cases, alerts, decisions
- NFT collections, wash trading
- DeFi protocol interactions
- Investigation sessions

PRODUCTION INVARIANTS:
- No fabricated seed data.
- All models support audit trails via timestamps.
- Soft delete support on critical tables.
"""

from __future__ import annotations

import datetime
import uuid
from typing import Optional

from sqlalchemy import (
    Column, String, Float, Integer, Boolean, Text, DateTime,
    ForeignKey, Index, Enum as SAEnum, JSON,
)
from sqlalchemy.orm import relationship

from .database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime.datetime:
    return datetime.datetime.now(datetime.UTC)


# ═══════════════════════════════════════════════════════════════════
# Address Label Registry (consolidated from 5+ inline registries)
# ═══════════════════════════════════════════════════════════════════

class AddressLabel(Base):
    """
    Consolidated address label — single source of truth for all address
    classification (exchange, DeFi, bridge, mixer, sanctioned, etc.).
    Replaces the scattered KNOWN_ENTITIES, KNOWN_BRIDGES, MIXER_POOLS,
    PROTOCOL_DB, EXCHANGE_HOT_WALLETS dictionaries.
    """
    __tablename__ = "address_labels"

    id = Column(String, primary_key=True, default=_uuid)
    address = Column(String(128), nullable=False, index=True)
    chain = Column(String(32), nullable=False, default="ethereum")
    label = Column(String(256), nullable=False)
    category = Column(String(64), nullable=False)  # exchange, defi, bridge, mixer, sanctioned, nft, government, mining_pool, validator, dao, multisig, service
    subcategory = Column(String(64), nullable=True)  # hot_wallet, cold_wallet, deposit, withdrawal, router, pool, etc.
    source = Column(String(128), nullable=False, default="registry")  # registry, provider:<name>, manual, ofac, eu_consolidated
    provider_name = Column(String(128), nullable=True)  # External provider that supplied this label
    confidence = Column(Float, nullable=False, default=0.5)
    is_verified = Column(Boolean, default=False)
    metadata_json = Column(JSON, nullable=True)  # Additional metadata (audit status, TVL tier, risk_level, etc.)
    first_seen_at = Column(DateTime, default=_utcnow)
    last_updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    expires_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_address_labels_address_chain", "address", "chain"),
        Index("ix_address_labels_category", "category"),
        Index("ix_address_labels_source", "source"),
    )


class AddressLabelHistory(Base):
    """Audit trail for address label changes."""
    __tablename__ = "address_label_history"

    id = Column(String, primary_key=True, default=_uuid)
    label_id = Column(String, ForeignKey("address_labels.id"), nullable=False, index=True)
    field_changed = Column(String(64), nullable=False)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    changed_by = Column(String(128), nullable=False, default="system")
    changed_at = Column(DateTime, default=_utcnow)


# ═══════════════════════════════════════════════════════════════════
# Wallet Attribution
# ═══════════════════════════════════════════════════════════════════

class WalletAttribution(Base):
    """
    Provider-tracked wallet attribution.
    Records which provider attributed this wallet and with what confidence.
    """
    __tablename__ = "wallet_attributions"

    id = Column(String, primary_key=True, default=_uuid)
    address = Column(String(128), nullable=False, index=True)
    chain = Column(String(32), nullable=False, default="ethereum")
    attribution_type = Column(String(64), nullable=False)  # exchange, custodial, government, bridge, protocol_treasury, mining_pool, validator, dao_treasury, multisig, service, public_label
    entity_name = Column(String(256), nullable=True)
    provider_id = Column(String(128), nullable=False)  # Which provider supplied this
    confidence = Column(Float, nullable=False, default=0.0)
    evidence_json = Column(JSON, nullable=True)  # Supporting evidence
    first_seen_at = Column(DateTime, default=_utcnow)
    last_verified_at = Column(DateTime, default=_utcnow)
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        Index("ix_wallet_attr_address_chain", "address", "chain"),
        Index("ix_wallet_attr_type", "attribution_type"),
        Index("ix_wallet_attr_provider", "provider_id"),
    )


# ═══════════════════════════════════════════════════════════════════
# Exchange Intelligence
# ═══════════════════════════════════════════════════════════════════

class ExchangeWallet(Base):
    """Classified exchange wallet with type and confidence."""
    __tablename__ = "exchange_wallets"

    id = Column(String, primary_key=True, default=_uuid)
    address = Column(String(128), nullable=False, index=True)
    chain = Column(String(32), nullable=False, default="ethereum")
    exchange_name = Column(String(128), nullable=False)
    wallet_type = Column(String(64), nullable=False)  # deposit, hot_wallet, cold_wallet, treasury, withdrawal
    confidence = Column(Float, nullable=False, default=0.0)
    provider_id = Column(String(128), nullable=True)
    first_seen_at = Column(DateTime, default=_utcnow)
    last_activity_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    metadata_json = Column(JSON, nullable=True)

    __table_args__ = (
        Index("ix_exchange_wallet_address", "address", "chain"),
        Index("ix_exchange_wallet_name", "exchange_name"),
    )


# ═══════════════════════════════════════════════════════════════════
# AML Cases, Alerts, Decisions
# ═══════════════════════════════════════════════════════════════════

class AMLCase(Base):
    """AML investigation case with state machine lifecycle."""
    __tablename__ = "aml_cases"

    id = Column(String, primary_key=True, default=_uuid)
    case_number = Column(String(64), unique=True, nullable=False)
    title = Column(String(512), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(32), nullable=False, default="open")  # open, under_review, escalated, closed, archived
    priority = Column(String(32), nullable=False, default="medium")  # low, medium, high, critical
    risk_score = Column(Integer, nullable=True)
    assigned_analyst = Column(String(128), nullable=True)
    subject_address = Column(String(128), nullable=True)  # Primary address under investigation
    subject_entity = Column(String(256), nullable=True)
    patterns_detected = Column(JSON, nullable=True)  # List of detected AML patterns
    evidence_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    escalated_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    created_by = Column(String(128), nullable=False, default="system")

    # Relationships
    alerts = relationship("AMLAlert", back_populates="case")
    decisions = relationship("AMLDecision", back_populates="case")

    __table_args__ = (
        Index("ix_aml_case_status", "status"),
        Index("ix_aml_case_priority", "priority"),
        Index("ix_aml_case_subject", "subject_address"),
    )


class AMLAlert(Base):
    """AML alert generated by automated screening or rule engine."""
    __tablename__ = "aml_alerts"

    id = Column(String, primary_key=True, default=_uuid)
    case_id = Column(String, ForeignKey("aml_cases.id"), nullable=True, index=True)
    alert_type = Column(String(64), nullable=False)  # peel_chain, smurfing, layering, structuring, mixer_usage, sanctions_hit, velocity, high_risk_counterparty
    severity = Column(String(32), nullable=False, default="medium")  # low, medium, high, critical
    address = Column(String(128), nullable=False, index=True)
    chain = Column(String(32), nullable=False, default="ethereum")
    rule_id = Column(String(64), nullable=True)  # Which rule triggered this
    description = Column(Text, nullable=True)
    evidence_json = Column(JSON, nullable=True)
    risk_score = Column(Integer, nullable=True)
    status = Column(String(32), nullable=False, default="new")  # new, acknowledged, investigating, resolved, false_positive
    created_at = Column(DateTime, default=_utcnow)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(128), nullable=True)

    case = relationship("AMLCase", back_populates="alerts")

    __table_args__ = (
        Index("ix_aml_alert_type", "alert_type"),
        Index("ix_aml_alert_status", "status"),
        Index("ix_aml_alert_severity", "severity"),
    )


class AMLDecision(Base):
    """Analyst decision on an AML case — fully auditable."""
    __tablename__ = "aml_decisions"

    id = Column(String, primary_key=True, default=_uuid)
    case_id = Column(String, ForeignKey("aml_cases.id"), nullable=False, index=True)
    decision = Column(String(64), nullable=False)  # file_sar, escalate, close_no_action, close_false_positive, request_information
    rationale = Column(Text, nullable=False)
    analyst = Column(String(128), nullable=False)
    risk_assessment = Column(String(32), nullable=True)  # low, medium, high, critical
    evidence_references = Column(JSON, nullable=True)
    decided_at = Column(DateTime, default=_utcnow)

    case = relationship("AMLCase", back_populates="decisions")


# ═══════════════════════════════════════════════════════════════════
# AML Rules
# ═══════════════════════════════════════════════════════════════════

class AMLRule(Base):
    """Configurable AML detection rule."""
    __tablename__ = "aml_rules"

    id = Column(String, primary_key=True, default=_uuid)
    rule_id = Column(String(64), unique=True, nullable=False)
    name = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(64), nullable=False)  # velocity, structuring, layering, counterparty, pattern
    severity = Column(String(32), nullable=False, default="medium")
    is_enabled = Column(Boolean, default=True)
    parameters_json = Column(JSON, nullable=True)  # Configurable thresholds
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)


# ═══════════════════════════════════════════════════════════════════
# NFT Intelligence
# ═══════════════════════════════════════════════════════════════════

class NFTCollection(Base):
    """Tracked NFT collection metadata."""
    __tablename__ = "nft_collections"

    id = Column(String, primary_key=True, default=_uuid)
    contract_address = Column(String(128), nullable=False, index=True)
    chain = Column(String(32), nullable=False, default="ethereum")
    name = Column(String(256), nullable=True)
    symbol = Column(String(64), nullable=True)
    standard = Column(String(16), nullable=False, default="ERC-721")  # ERC-721, ERC-1155
    total_supply = Column(Integer, nullable=True)
    creator_address = Column(String(128), nullable=True)
    marketplace = Column(String(128), nullable=True)
    floor_price_eth = Column(Float, nullable=True)
    risk_score = Column(Integer, nullable=True)
    wash_trade_flag = Column(Boolean, default=False)
    metadata_json = Column(JSON, nullable=True)
    first_seen_at = Column(DateTime, default=_utcnow)
    last_updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)


class NFTTransfer(Base):
    """NFT transfer record for provenance tracking."""
    __tablename__ = "nft_transfers"

    id = Column(String, primary_key=True, default=_uuid)
    collection_id = Column(String, ForeignKey("nft_collections.id"), nullable=True, index=True)
    contract_address = Column(String(128), nullable=False, index=True)
    token_id = Column(String(128), nullable=False)
    from_address = Column(String(128), nullable=False, index=True)
    to_address = Column(String(128), nullable=False, index=True)
    tx_hash = Column(String(128), nullable=False)
    chain = Column(String(32), nullable=False, default="ethereum")
    price_eth = Column(Float, nullable=True)
    price_usd = Column(Float, nullable=True)
    marketplace = Column(String(128), nullable=True)
    is_wash_trade = Column(Boolean, default=False)
    transferred_at = Column(DateTime, nullable=True)
    indexed_at = Column(DateTime, default=_utcnow)


class WashTradingAlert(Base):
    """Detected wash trading activity on NFTs."""
    __tablename__ = "wash_trading_alerts"

    id = Column(String, primary_key=True, default=_uuid)
    collection_id = Column(String, ForeignKey("nft_collections.id"), nullable=True, index=True)
    contract_address = Column(String(128), nullable=False)
    detection_type = Column(String(64), nullable=False)  # self_trade, rapid_flip, circular_trade, price_manipulation
    addresses_involved = Column(JSON, nullable=False)  # List of addresses
    tx_hashes = Column(JSON, nullable=False)  # List of related tx hashes
    total_volume_eth = Column(Float, nullable=True)
    confidence = Column(Float, nullable=False, default=0.0)
    evidence_json = Column(JSON, nullable=True)
    detected_at = Column(DateTime, default=_utcnow)


# ═══════════════════════════════════════════════════════════════════
# DeFi Protocol Interactions
# ═══════════════════════════════════════════════════════════════════

class DeFiInteraction(Base):
    """Tracked DeFi protocol interaction for risk analysis."""
    __tablename__ = "defi_interactions"

    id = Column(String, primary_key=True, default=_uuid)
    address = Column(String(128), nullable=False, index=True)
    protocol_address = Column(String(128), nullable=False)
    protocol_name = Column(String(128), nullable=True)
    action_type = Column(String(64), nullable=False)  # swap, liquidity_add, liquidity_remove, lend, borrow, stake, unstake, flash_loan, governance_vote
    chain = Column(String(32), nullable=False, default="ethereum")
    value_eth = Column(Float, nullable=True)
    value_usd = Column(Float, nullable=True)
    tx_hash = Column(String(128), nullable=False)
    risk_level = Column(String(32), nullable=True)
    interacted_at = Column(DateTime, nullable=True)
    indexed_at = Column(DateTime, default=_utcnow)

    __table_args__ = (
        Index("ix_defi_interaction_address", "address"),
        Index("ix_defi_interaction_protocol", "protocol_address"),
    )


# ═══════════════════════════════════════════════════════════════════
# Investigation Sessions
# ═══════════════════════════════════════════════════════════════════

class InvestigationSession(Base):
    """Blockchain investigation session tracking."""
    __tablename__ = "investigation_sessions"

    id = Column(String, primary_key=True, default=_uuid)
    analyst = Column(String(128), nullable=False)
    title = Column(String(512), nullable=True)
    target_addresses = Column(JSON, nullable=True)
    chains_investigated = Column(JSON, nullable=True)
    findings_json = Column(JSON, nullable=True)
    status = Column(String(32), nullable=False, default="active")  # active, paused, completed
    started_at = Column(DateTime, default=_utcnow)
    completed_at = Column(DateTime, nullable=True)


class InvestigationEvidence(Base):
    """Evidence item collected during investigation."""
    __tablename__ = "investigation_evidence"

    id = Column(String, primary_key=True, default=_uuid)
    session_id = Column(String, ForeignKey("investigation_sessions.id"), nullable=False, index=True)
    evidence_type = Column(String(64), nullable=False)  # transaction, screenshot, note, graph_snapshot, api_response
    title = Column(String(256), nullable=True)
    description = Column(Text, nullable=True)
    data_json = Column(JSON, nullable=True)
    collected_at = Column(DateTime, default=_utcnow)
    collected_by = Column(String(128), nullable=False, default="system")
