"""
LEATrace Sanctions Database Models — Production.

Defines a fully normalized schema for tracking:
- Sanctions providers configuration
- Sanctioned entities (Individuals, Organizations, Vessels, etc.)
- Sanctioned cryptocurrency wallets
- Associated aliases and countries
- Physical addresses of sanctioned entities
- Sync version history and checksum validation
- Entity/Wallet delta changes (change history)
- Real-time screening audit logs
- Sync integrity reports

PRODUCTION INVARIANTS:
- No hardcoded data.
- Normalized tables to prevent data redundancy and optimize lookup speeds.
- Soft delete with audit trail.
- Version tracking with rollback support.
"""

from __future__ import annotations

import datetime
import uuid

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime,
    ForeignKey, Text, JSON, Index, UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .database import Base


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Provider Configuration & Health
# ═══════════════════════════════════════════════════════════════════════════════

class SanctionsProviderConfig(Base):
    """Configuration and health stats for each sanctions data feed."""
    __tablename__ = "sanctions_provider_configs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    provider_id = Column(String, unique=True, nullable=False, index=True)  # e.g., 'ofac_sdn', 'eu_consolidated'
    name = Column(String, nullable=False)
    enabled = Column(Boolean, default=True)
    priority = Column(Integer, default=50)  # Lower number = higher priority
    feed_url = Column(String, nullable=False)
    api_key_env = Column(String, nullable=True)  # Name of env var containing API key (if needed)
    sync_interval_hours = Column(Integer, default=24)
    max_retries = Column(Integer, default=3)
    last_sync_at = Column(DateTime, nullable=True)
    last_success_at = Column(DateTime, nullable=True)
    last_failure_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    consecutive_failures = Column(Integer, default=0)
    total_syncs = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    versions = relationship("SanctionsVersionHistory", back_populates="provider")


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Normalized Sanctions Dataset
# ═══════════════════════════════════════════════════════════════════════════════

class SanctionsListEntity(Base):
    """Normalized sanctioned individuals, organizations, vessels, and smart contracts."""
    __tablename__ = "sanctions_list_entities"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_uid = Column(String, nullable=False, index=True)  # Source UID (e.g., OFAC uid '26744')
    provider_id = Column(String, nullable=False, index=True)  # e.g., 'ofac_sdn'
    name = Column(String, nullable=False, index=True)
    entity_type = Column(String, nullable=False, index=True)  # 'individual', 'organization', 'vessel', 'aircraft', 'smart_contract', 'mixer', 'exchange'
    program = Column(String, nullable=True)  # e.g. "RUSSIA", "CYBER"
    remarks = Column(Text, nullable=True)
    status = Column(String, default="active", index=True)  # 'active', 'revoked', 'expired'
    version_id = Column(String, nullable=False)  # Link to SanctionsVersionHistory when this entity was last updated

    # Soft delete
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime, nullable=True)

    # Expiration tracking
    expires_at = Column(DateTime, nullable=True)

    # Evidence
    evidence_json = Column(Text, nullable=True)  # JSON blob of source evidence

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('entity_uid', 'provider_id', name='_entity_provider_uc'),
        Index('ix_entity_status_provider', 'status', 'provider_id'),
        Index('ix_entity_name_trgm', 'name'),  # For fuzzy search optimization
    )

    # Relationships
    wallets = relationship("SanctionsListWallet", back_populates="entity", cascade="all, delete-orphan")
    aliases = relationship("SanctionsAlias", back_populates="entity", cascade="all, delete-orphan")
    countries = relationship("SanctionsEntityCountry", back_populates="entity", cascade="all, delete-orphan")
    addresses = relationship("SanctionsEntityAddress", back_populates="entity", cascade="all, delete-orphan")


class SanctionsListWallet(Base):
    """Cryptocurrency addresses associated with a sanctioned entity."""
    __tablename__ = "sanctions_list_wallets"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_id = Column(String, ForeignKey("sanctions_list_entities.id", ondelete="CASCADE"), nullable=False)
    address = Column(String, nullable=False, index=True)
    normalized_address = Column(String, nullable=False, index=True)  # Lowercase, trimmed
    currency = Column(String, nullable=True, index=True)  # e.g. "BTC", "ETH", "USDT"
    status = Column(String, default="active")  # 'active', 'revoked'
    version_id = Column(String, nullable=False)

    # Soft delete
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('entity_id', 'normalized_address', name='_entity_wallet_uc'),
        Index('ix_wallet_normalized_active', 'normalized_address', 'status'),
    )

    entity = relationship("SanctionsListEntity", back_populates="wallets")


class SanctionsAlias(Base):
    """Aliases associated with a sanctioned entity (AKA, FKA, etc.)."""
    __tablename__ = "sanctions_aliases"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_id = Column(String, ForeignKey("sanctions_list_entities.id", ondelete="CASCADE"), nullable=False)
    alias_name = Column(String, nullable=False, index=True)
    alias_type = Column(String, nullable=True)  # 'a.k.a.', 'f.k.a.'
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    entity = relationship("SanctionsListEntity", back_populates="aliases")


class SanctionsEntityCountry(Base):
    """Countries associated with a sanctioned entity (Citizenship, residency, operations)."""
    __tablename__ = "sanctions_entity_countries"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_id = Column(String, ForeignKey("sanctions_list_entities.id", ondelete="CASCADE"), nullable=False)
    country_code = Column(String, nullable=False, index=True)  # e.g. "RU", "IR", "KP"
    country_name = Column(String, nullable=True)
    association_type = Column(String, nullable=True)  # 'citizenship', 'location', 'operations', 'nationality', 'birth'
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    entity = relationship("SanctionsListEntity", back_populates="countries")


class SanctionsEntityAddress(Base):
    """Physical addresses associated with a sanctioned entity."""
    __tablename__ = "sanctions_entity_addresses"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_id = Column(String, ForeignKey("sanctions_list_entities.id", ondelete="CASCADE"), nullable=False)
    address_line1 = Column(String, nullable=True)
    address_line2 = Column(String, nullable=True)
    city = Column(String, nullable=True, index=True)
    state_province = Column(String, nullable=True)
    postal_code = Column(String, nullable=True)
    country_code = Column(String, nullable=True, index=True)
    country_name = Column(String, nullable=True)
    address_type = Column(String, nullable=True)  # 'registered', 'operational', 'mailing'
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    entity = relationship("SanctionsListEntity", back_populates="addresses")


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Version Tracking, Checksums, and Deltas
# ═══════════════════════════════════════════════════════════════════════════════

class SanctionsVersionHistory(Base):
    """Track metadata, checksum, signatures, and stats for each provider sync run."""
    __tablename__ = "sanctions_version_history"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    provider_id = Column(String, ForeignKey("sanctions_provider_configs.provider_id", ondelete="CASCADE"), nullable=False)
    version = Column(Integer, nullable=False)  # Sequential version number per provider
    checksum = Column(String, nullable=False)  # SHA-256 of the source feed file
    signature = Column(String, nullable=True)  # Cryptographic signature of feed (if supported)
    status = Column(String, nullable=False)  # 'success', 'failed'
    entities_count = Column(Integer, default=0)
    wallets_count = Column(Integer, default=0)
    delta_added = Column(Integer, default=0)
    delta_updated = Column(Integer, default=0)
    delta_removed = Column(Integer, default=0)
    duration_seconds = Column(Float, nullable=True)
    synced_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('provider_id', 'version', name='_provider_version_uc'),
        Index('ix_version_provider_status', 'provider_id', 'status'),
    )

    provider = relationship("SanctionsProviderConfig", back_populates="versions")


class SanctionsChangeHistory(Base):
    """Track specific delta changes (audit logs for data mutation) per entity."""
    __tablename__ = "sanctions_change_history"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    version_id = Column(String, nullable=False, index=True)
    entity_uid = Column(String, nullable=False, index=True)
    provider_id = Column(String, nullable=False, index=True)
    action = Column(String, nullable=False)  # 'added', 'modified', 'removed'
    field_changed = Column(String, nullable=True)  # 'entity', 'wallet', 'alias', 'country', 'all', or comma-separated list
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    changed_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        Index('ix_change_version_action', 'version_id', 'action'),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Sync Integrity Reports
# ═══════════════════════════════════════════════════════════════════════════════

class SanctionsSyncIntegrityReport(Base):
    """Records integrity validation results for each sync operation."""
    __tablename__ = "sanctions_sync_integrity_reports"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    version_id = Column(String, nullable=False, index=True)
    provider_id = Column(String, nullable=False, index=True)
    checksum = Column(String, nullable=False)
    is_valid = Column(Boolean, nullable=False)
    total_entities = Column(Integer, default=0)
    unique_entities = Column(Integer, default=0)
    duplicate_uids = Column(Integer, default=0)
    total_wallets = Column(Integer, default=0)
    issues_json = Column(JSON, nullable=True)  # List of issue strings
    download_size_bytes = Column(Integer, default=0)
    validated_at = Column(DateTime, default=datetime.datetime.utcnow)


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Screening Audit Log (Compliance Zero-Trust Safeguards)
# ═══════════════════════════════════════════════════════════════════════════════

class SanctionsScreeningLog(Base):
    """Immutable audit trail of all manual and automated sanctions checks."""
    __tablename__ = "sanctions_screening_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    query_type = Column(String, nullable=False, index=True)  # 'wallet', 'entity_name', 'transaction', 'smart_contract', 'batch'
    query_value = Column(String, nullable=False, index=True)  # Address, TX hash, name, etc.
    matched = Column(Boolean, nullable=False, index=True)
    match_score = Column(Float, nullable=True)  # Matching confidence (0.0-1.0)
    matched_entity_id = Column(String, nullable=True)
    matched_entity_name = Column(String, nullable=True)
    matched_programs = Column(String, nullable=True)  # Semi-colon separated list
    provider_id = Column(String, nullable=True)  # Provider that matched
    versions_used = Column(JSON, nullable=True)  # Dict mapping provider_id to version number at query time
    checked_by = Column(String, nullable=True, index=True)  # Username or system service
    reason_context = Column(Text, nullable=True)  # Context e.g., 'Investigation Case #123'
    response_time_ms = Column(Float, nullable=True)  # Screening response time
    checked_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        Index('ix_screening_checked_at', 'checked_at'),
        Index('ix_screening_matched', 'matched', 'checked_at'),
    )
