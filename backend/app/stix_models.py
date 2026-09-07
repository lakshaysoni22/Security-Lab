"""
LEATrace STIX 2.1 + Threat Intelligence Database Models — Production.

Complete SQLAlchemy models for:
- All 20 STIX 2.1 SDO/SRO object types
- IOC entries with lifecycle, versioning, source tracking
- TI provider configuration and health
- Enrichment results
- Feed priority scores
- IOC observations/sightings

PRODUCTION INVARIANTS:
- No hardcoded data in any model.
- All data comes from live providers or analyst input.
- Full audit trail via version history tables.
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
# STIX 2.1 Base Mixin
# ═══════════════════════════════════════════════════════════════════════════════

class StixBaseMixin:
    """Common fields for all STIX 2.1 objects."""
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    stix_id = Column(String, unique=True, nullable=False, index=True)
    stix_type = Column(String, nullable=False, index=True)
    spec_version = Column(String, default="2.1")
    created = Column(DateTime, nullable=True)
    modified = Column(DateTime, nullable=True)
    created_by_ref = Column(String, nullable=True)
    revoked = Column(Boolean, default=False)
    confidence = Column(Integer, nullable=True)
    lang = Column(String, nullable=True)
    labels = Column(JSON, nullable=True)
    external_references = Column(JSON, nullable=True)
    object_marking_refs = Column(JSON, nullable=True)
    granular_markings = Column(JSON, nullable=True)
    raw_json = Column(Text, nullable=True)
    collection_id = Column(String, nullable=True, index=True)
    source_provider = Column(String, nullable=True, index=True)
    ingested_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow,
                        onupdate=datetime.datetime.utcnow)


# ═══════════════════════════════════════════════════════════════════════════════
# STIX 2.1 Domain Objects (SDOs)
# ═══════════════════════════════════════════════════════════════════════════════

class StixThreatActor(StixBaseMixin, Base):
    """STIX 2.1 Threat Actor SDO."""
    __tablename__ = "stix_threat_actors"
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    threat_actor_types = Column(JSON, nullable=True)
    aliases = Column(JSON, nullable=True)
    first_seen = Column(DateTime, nullable=True)
    last_seen = Column(DateTime, nullable=True)
    roles = Column(JSON, nullable=True)
    goals = Column(JSON, nullable=True)
    sophistication = Column(String, nullable=True)
    resource_level = Column(String, nullable=True)
    primary_motivation = Column(String, nullable=True)
    secondary_motivations = Column(JSON, nullable=True)
    personal_motivations = Column(JSON, nullable=True)


class StixMalware(StixBaseMixin, Base):
    """STIX 2.1 Malware SDO."""
    __tablename__ = "stix_malware"
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    malware_types = Column(JSON, nullable=True)
    is_family = Column(Boolean, default=False)
    aliases = Column(JSON, nullable=True)
    first_seen = Column(DateTime, nullable=True)
    last_seen = Column(DateTime, nullable=True)
    operating_system_refs = Column(JSON, nullable=True)
    architecture_execution_envs = Column(JSON, nullable=True)
    implementation_languages = Column(JSON, nullable=True)
    capabilities = Column(JSON, nullable=True)
    sample_refs = Column(JSON, nullable=True)


class StixCampaign(StixBaseMixin, Base):
    """STIX 2.1 Campaign SDO."""
    __tablename__ = "stix_campaigns"
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    aliases = Column(JSON, nullable=True)
    first_seen = Column(DateTime, nullable=True)
    last_seen = Column(DateTime, nullable=True)
    objective = Column(Text, nullable=True)


class StixIdentity(StixBaseMixin, Base):
    """STIX 2.1 Identity SDO."""
    __tablename__ = "stix_identities"
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    roles = Column(JSON, nullable=True)
    identity_class = Column(String, nullable=True)
    sectors = Column(JSON, nullable=True)
    contact_information = Column(Text, nullable=True)


class StixTool(StixBaseMixin, Base):
    """STIX 2.1 Tool SDO."""
    __tablename__ = "stix_tools"
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    tool_types = Column(JSON, nullable=True)
    aliases = Column(JSON, nullable=True)
    kill_chain_phases = Column(JSON, nullable=True)
    tool_version = Column(String, nullable=True)


class StixInfrastructure(StixBaseMixin, Base):
    """STIX 2.1 Infrastructure SDO."""
    __tablename__ = "stix_infrastructure"
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    infrastructure_types = Column(JSON, nullable=True)
    aliases = Column(JSON, nullable=True)
    first_seen = Column(DateTime, nullable=True)
    last_seen = Column(DateTime, nullable=True)
    kill_chain_phases = Column(JSON, nullable=True)


class StixIntrusionSet(StixBaseMixin, Base):
    """STIX 2.1 Intrusion Set SDO."""
    __tablename__ = "stix_intrusion_sets"
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    aliases = Column(JSON, nullable=True)
    first_seen = Column(DateTime, nullable=True)
    last_seen = Column(DateTime, nullable=True)
    goals = Column(JSON, nullable=True)
    resource_level = Column(String, nullable=True)
    primary_motivation = Column(String, nullable=True)
    secondary_motivations = Column(JSON, nullable=True)


class StixAttackPattern(StixBaseMixin, Base):
    """STIX 2.1 Attack Pattern SDO."""
    __tablename__ = "stix_attack_patterns"
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    aliases = Column(JSON, nullable=True)
    kill_chain_phases = Column(JSON, nullable=True)


class StixObservedData(StixBaseMixin, Base):
    """STIX 2.1 Observed Data SDO."""
    __tablename__ = "stix_observed_data"
    first_observed = Column(DateTime, nullable=True)
    last_observed = Column(DateTime, nullable=True)
    number_observed = Column(Integer, default=1)
    object_refs = Column(JSON, nullable=True)


class StixCourseOfAction(StixBaseMixin, Base):
    """STIX 2.1 Course of Action SDO."""
    __tablename__ = "stix_courses_of_action"
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    action_type = Column(String, nullable=True)
    os_execution_envs = Column(JSON, nullable=True)
    action_bin = Column(Text, nullable=True)
    action_reference = Column(JSON, nullable=True)


class StixLocation(StixBaseMixin, Base):
    """STIX 2.1 Location SDO."""
    __tablename__ = "stix_locations"
    name = Column(String, nullable=True, index=True)
    description = Column(Text, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    precision = Column(Float, nullable=True)
    region = Column(String, nullable=True)
    country = Column(String, nullable=True)
    administrative_area = Column(String, nullable=True)
    city = Column(String, nullable=True)
    street_address = Column(String, nullable=True)
    postal_code = Column(String, nullable=True)


class StixMalwareAnalysis(StixBaseMixin, Base):
    """STIX 2.1 Malware Analysis SDO."""
    __tablename__ = "stix_malware_analyses"
    product = Column(String, nullable=True)
    version = Column(String, nullable=True)
    host_vm_ref = Column(String, nullable=True)
    operating_system_ref = Column(String, nullable=True)
    installed_software_refs = Column(JSON, nullable=True)
    configuration_version = Column(String, nullable=True)
    modules = Column(JSON, nullable=True)
    analysis_engine_version = Column(String, nullable=True)
    analysis_definition_version = Column(String, nullable=True)
    submitted = Column(DateTime, nullable=True)
    analysis_started = Column(DateTime, nullable=True)
    analysis_ended = Column(DateTime, nullable=True)
    result_name = Column(String, nullable=True)
    result = Column(String, nullable=True)
    analysis_sco_refs = Column(JSON, nullable=True)
    sample_ref = Column(String, nullable=True)


class StixReport(StixBaseMixin, Base):
    """STIX 2.1 Report SDO."""
    __tablename__ = "stix_reports"
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    report_types = Column(JSON, nullable=True)
    published = Column(DateTime, nullable=True)
    object_refs = Column(JSON, nullable=True)


class StixGrouping(StixBaseMixin, Base):
    """STIX 2.1 Grouping SDO."""
    __tablename__ = "stix_groupings"
    name = Column(String, nullable=True, index=True)
    description = Column(Text, nullable=True)
    context = Column(String, nullable=True)
    object_refs = Column(JSON, nullable=True)


class StixNote(StixBaseMixin, Base):
    """STIX 2.1 Note SDO."""
    __tablename__ = "stix_notes"
    abstract = Column(Text, nullable=True)
    content = Column(Text, nullable=False)
    authors = Column(JSON, nullable=True)
    object_refs = Column(JSON, nullable=True)


class StixOpinion(StixBaseMixin, Base):
    """STIX 2.1 Opinion SDO."""
    __tablename__ = "stix_opinions"
    explanation = Column(Text, nullable=True)
    authors = Column(JSON, nullable=True)
    opinion = Column(String, nullable=True)  # strongly-disagree .. strongly-agree
    object_refs = Column(JSON, nullable=True)


# ═══════════════════════════════════════════════════════════════════════════════
# STIX 2.1 Relationship Objects (SROs)
# ═══════════════════════════════════════════════════════════════════════════════

class StixRelationship(StixBaseMixin, Base):
    """STIX 2.1 Relationship SRO."""
    __tablename__ = "stix_relationships"
    relationship_type = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    source_ref = Column(String, nullable=False, index=True)
    target_ref = Column(String, nullable=False, index=True)
    start_time = Column(DateTime, nullable=True)
    stop_time = Column(DateTime, nullable=True)


class StixSighting(StixBaseMixin, Base):
    """STIX 2.1 Sighting SRO."""
    __tablename__ = "stix_sightings"
    description = Column(Text, nullable=True)
    first_seen = Column(DateTime, nullable=True)
    last_seen = Column(DateTime, nullable=True)
    count = Column(Integer, nullable=True)
    sighting_of_ref = Column(String, nullable=False, index=True)
    observed_data_refs = Column(JSON, nullable=True)
    where_sighted_refs = Column(JSON, nullable=True)
    summary = Column(Boolean, default=False)


# ═══════════════════════════════════════════════════════════════════════════════
# IOC Models
# ═══════════════════════════════════════════════════════════════════════════════

class IOCEntry(Base):
    """
    Enterprise IOC entry with lifecycle, versioning, and source tracking.

    PRODUCTION INVARIANTS:
    - All IOCs come from providers or analyst input. Never fabricated.
    - Confidence is computed by ConfidenceEngine, not hardcoded.
    """
    __tablename__ = "ioc_entries"
    __table_args__ = (
        Index("ix_ioc_type_value", "ioc_type", "normalized_value"),
        Index("ix_ioc_status_severity", "status", "severity"),
        Index("ix_ioc_source_created", "source_provider", "created_at"),
        Index("ix_ioc_confidence", "confidence_score"),
        Index("ix_ioc_expiration", "expiration_date"),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    ioc_type = Column(String, nullable=False, index=True)
    # One of: ip, domain, url, hash_md5, hash_sha1, hash_sha256, file,
    #         email, registry, mutex, process, certificate, yara_rule,
    #         sigma_rule, cve, cpe, attack_technique, attack_group

    value = Column(Text, nullable=False)
    normalized_value = Column(Text, nullable=False, index=True)
    # Normalized form: lowercase, stripped, defanged→refanged, etc.

    # Scoring
    confidence_score = Column(Float, default=0.0)  # 0.0-100.0
    severity = Column(String, default="medium")  # critical, high, medium, low, info
    tlp = Column(String, default="TLP:AMBER")  # TLP:RED, TLP:AMBER, TLP:GREEN, TLP:WHITE

    # Lifecycle
    status = Column(String, default="active", index=True)
    # active, expired, revoked, false_positive, under_review
    first_seen = Column(DateTime, nullable=True)
    last_seen = Column(DateTime, nullable=True)
    expiration_date = Column(DateTime, nullable=True)
    version = Column(Integer, default=1)

    # Source tracking
    source_provider = Column(String, nullable=True, index=True)
    source_feed = Column(String, nullable=True)
    source_reference = Column(String, nullable=True)
    created_by = Column(String, nullable=True)
    stix_indicator_id = Column(String, nullable=True, index=True)

    # Attribution and context
    tags = Column(JSON, nullable=True)
    attribution = Column(JSON, nullable=True)
    related_cases = Column(JSON, nullable=True)
    kill_chain_phases = Column(JSON, nullable=True)
    mitre_attack_ids = Column(JSON, nullable=True)
    description = Column(Text, nullable=True)

    # Observation counts
    observation_count = Column(Integer, default=1)
    false_positive_count = Column(Integer, default=0)

    # Deduplication
    dedup_hash = Column(String, nullable=True, index=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow,
                        onupdate=datetime.datetime.utcnow)


class IOCVersion(Base):
    """Tracks version history of IOC changes for audit trail."""
    __tablename__ = "ioc_versions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    ioc_id = Column(String, ForeignKey("ioc_entries.id"), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    field_changed = Column(String, nullable=False)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    changed_by = Column(String, nullable=True)
    reason = Column(Text, nullable=True)
    changed_at = Column(DateTime, default=datetime.datetime.utcnow)


class IOCObservation(Base):
    """Records individual observations/sightings of an IOC."""
    __tablename__ = "ioc_observations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    ioc_id = Column(String, ForeignKey("ioc_entries.id"), nullable=False, index=True)
    observed_at = Column(DateTime, default=datetime.datetime.utcnow)
    source_provider = Column(String, nullable=True)
    source_feed = Column(String, nullable=True)
    context = Column(JSON, nullable=True)
    confidence_at_observation = Column(Float, nullable=True)


# ═══════════════════════════════════════════════════════════════════════════════
# Threat Intelligence Provider Models
# ═══════════════════════════════════════════════════════════════════════════════

class TIProviderConfig(Base):
    """Configuration for a threat intelligence provider."""
    __tablename__ = "ti_provider_configs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    provider_type = Column(String, nullable=False, index=True)
    # taxii, sanctions, mitre_attack, virustotal, abuseipdb, shodan, misp, otx
    name = Column(String, nullable=False, unique=True)
    enabled = Column(Boolean, default=True)
    priority = Column(Integer, default=50)  # 0=highest, 100=lowest
    config = Column(JSON, nullable=True)  # Provider-specific config
    sync_interval_minutes = Column(Integer, default=60)
    last_sync_at = Column(DateTime, nullable=True)
    status = Column(String, default="not_configured")
    # active, degraded, failed, disabled, not_configured
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow,
                        onupdate=datetime.datetime.utcnow)


class TIProviderHealth(Base):
    """Health check history for TI providers."""
    __tablename__ = "ti_provider_health"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    provider_id = Column(String, ForeignKey("ti_provider_configs.id"),
                         nullable=False, index=True)
    is_healthy = Column(Boolean, nullable=False)
    latency_ms = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    objects_available = Column(Integer, nullable=True)
    checked_at = Column(DateTime, default=datetime.datetime.utcnow)


class TISyncLog(Base):
    """Audit log for all TI sync operations across all providers."""
    __tablename__ = "ti_sync_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    provider_id = Column(String, nullable=True, index=True)
    provider_name = Column(String, nullable=False)
    provider_type = Column(String, nullable=False)
    status = Column(String, nullable=False)  # success, error, skipped, partial
    objects_fetched = Column(Integer, default=0)
    objects_new = Column(Integer, default=0)
    objects_updated = Column(Integer, default=0)
    objects_deduplicated = Column(Integer, default=0)
    duration_seconds = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    sync_type = Column(String, default="incremental")  # full, incremental, delta
    synced_at = Column(DateTime, default=datetime.datetime.utcnow)


class FeedPriorityScore(Base):
    """Computed priority score for a TI feed/provider."""
    __tablename__ = "feed_priority_scores"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    provider_id = Column(String, ForeignKey("ti_provider_configs.id"),
                         nullable=False, index=True)
    availability_score = Column(Float, default=0.0)
    latency_score = Column(Float, default=0.0)
    accuracy_score = Column(Float, default=0.0)
    update_frequency_score = Column(Float, default=0.0)
    coverage_score = Column(Float, default=0.0)
    reliability_score = Column(Float, default=0.0)
    analyst_trust_score = Column(Float, default=50.0)
    composite_score = Column(Float, default=0.0)
    computed_at = Column(DateTime, default=datetime.datetime.utcnow)


class EnrichmentResult(Base):
    """Cached enrichment data for IOCs."""
    __tablename__ = "enrichment_results"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    ioc_id = Column(String, ForeignKey("ioc_entries.id"), nullable=False, index=True)
    enrichment_type = Column(String, nullable=False, index=True)
    # geo, asn, whois, dns, passive_dns, certificate, mitre_attack,
    # kill_chain, threat_actor, campaign, malware_family, risk_level
    provider = Column(String, nullable=True)
    data = Column(JSON, nullable=True)
    status = Column(String, default="success")  # success, error, not_configured
    ttl_seconds = Column(Integer, default=86400)
    enriched_at = Column(DateTime, default=datetime.datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)


# ═══════════════════════════════════════════════════════════════════════════════
# STIX type → Model class mapping (for dynamic ingestion)
# ═══════════════════════════════════════════════════════════════════════════════

STIX_TYPE_TO_MODEL = {
    "threat-actor": StixThreatActor,
    "malware": StixMalware,
    "campaign": StixCampaign,
    "identity": StixIdentity,
    "tool": StixTool,
    "infrastructure": StixInfrastructure,
    "intrusion-set": StixIntrusionSet,
    "attack-pattern": StixAttackPattern,
    "observed-data": StixObservedData,
    "course-of-action": StixCourseOfAction,
    "location": StixLocation,
    "malware-analysis": StixMalwareAnalysis,
    "report": StixReport,
    "grouping": StixGrouping,
    "note": StixNote,
    "opinion": StixOpinion,
    "relationship": StixRelationship,
    "sighting": StixSighting,
}
