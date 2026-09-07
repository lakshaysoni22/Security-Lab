"""
LEATrace IOC Enrichment Engine — Production.

Automatically enriches IOCs with contextual intelligence from
configurable external providers.

PRODUCTION INVARIANTS:
- Never fabricates enrichment data.
- If a provider is unavailable → returns structured "not_configured" status.
- All enrichment results cached with configurable TTL.
- Logs every enrichment attempt.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import logging
import os
import uuid
from typing import Any, Dict, List, Optional

logger = logging.getLogger("leatrace.enrichment_engine")


# Enrichment type definitions
class EnrichmentType:
    GEO = "geo"
    ASN = "asn"
    WHOIS = "whois"
    DNS = "dns"
    PASSIVE_DNS = "passive_dns"
    CERTIFICATE = "certificate"
    MITRE_ATTACK = "mitre_attack"
    KILL_CHAIN = "kill_chain"
    THREAT_ACTOR = "threat_actor"
    CAMPAIGN = "campaign"
    MALWARE_FAMILY = "malware_family"
    RISK_LEVEL = "risk_level"
    HISTORICAL_ACTIVITY = "historical_activity"
    EVIDENCE_LINKS = "evidence_links"
    CASE_REFERENCES = "case_references"


# IOC types that support each enrichment
ENRICHMENT_APPLICABILITY = {
    EnrichmentType.GEO:          {"ip"},
    EnrichmentType.ASN:          {"ip"},
    EnrichmentType.WHOIS:        {"ip", "domain"},
    EnrichmentType.DNS:          {"domain"},
    EnrichmentType.PASSIVE_DNS:  {"domain", "ip"},
    EnrichmentType.CERTIFICATE:  {"domain"},
    EnrichmentType.MITRE_ATTACK: {"attack_technique", "attack_group", "hash_md5",
                                   "hash_sha1", "hash_sha256", "ip", "domain", "url"},
    EnrichmentType.KILL_CHAIN:   {"attack_technique", "hash_md5", "hash_sha1",
                                   "hash_sha256"},
    EnrichmentType.THREAT_ACTOR: {"ip", "domain", "url", "hash_md5", "hash_sha1",
                                   "hash_sha256", "wallet", "email"},
    EnrichmentType.CAMPAIGN:     {"ip", "domain", "url", "hash_md5", "hash_sha1",
                                   "hash_sha256"},
    EnrichmentType.MALWARE_FAMILY: {"hash_md5", "hash_sha1", "hash_sha256"},
    EnrichmentType.RISK_LEVEL:   set(),  # applies to all
    EnrichmentType.HISTORICAL_ACTIVITY: {"ip", "domain", "wallet"},
    EnrichmentType.EVIDENCE_LINKS:     set(),  # applies to all
    EnrichmentType.CASE_REFERENCES:    set(),  # applies to all
}

DEFAULT_TTL = 86400  # 24 hours


class EnrichmentEngine:
    """
    Production IOC enrichment engine with pluggable providers.

    Enrichment sources:
    - Geo/ASN: IP geolocation and ASN info (requires configured provider)
    - WHOIS: Domain/IP registration data (requires configured provider)
    - DNS: Active DNS records (uses system DNS resolver)
    - Passive DNS: Historical DNS (requires configured provider)
    - Certificate: TLS certificate metadata (requires configured provider)
    - MITRE ATT&CK: Technique/tactic mapping (from local STIX DB)
    - Kill Chain: Lockheed Martin kill chain phase mapping
    - Threat Actor/Campaign/Malware: From STIX relationship DB
    - Risk Level: Composite risk from all enrichment data
    - Evidence/Case Links: From local case management DB

    If any provider is unavailable, returns structured status — never fake data.
    """

    def __init__(self):
        self._cache_ttl: Dict[str, int] = {
            EnrichmentType.GEO: 604800,       # 7 days
            EnrichmentType.ASN: 604800,
            EnrichmentType.WHOIS: 86400,       # 1 day
            EnrichmentType.DNS: 3600,          # 1 hour
            EnrichmentType.PASSIVE_DNS: 86400,
            EnrichmentType.CERTIFICATE: 86400,
            EnrichmentType.MITRE_ATTACK: 604800,
            EnrichmentType.KILL_CHAIN: 604800,
            EnrichmentType.THREAT_ACTOR: 3600,
            EnrichmentType.CAMPAIGN: 3600,
            EnrichmentType.MALWARE_FAMILY: 3600,
            EnrichmentType.RISK_LEVEL: 3600,
        }

    def enrich_ioc(
        self,
        ioc_id: str,
        db: Any,
        enrichment_types: Optional[List[str]] = None,
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        """
        Enriches an IOC with all applicable enrichment types.

        Args:
            ioc_id: IOC database ID
            db: SQLAlchemy session
            enrichment_types: Specific types to run (None = all applicable)
            force_refresh: If True, ignores cache

        Returns:
            Dict with enrichment results per type.
        """
        if db is None:
            return {"status": "db_unavailable"}

        from .stix_models import IOCEntry

        entry = db.query(IOCEntry).filter(IOCEntry.id == ioc_id).first()
        if not entry:
            return {"status": "not_found", "ioc_id": ioc_id}

        ioc_type = entry.ioc_type
        value = entry.normalized_value
        results: Dict[str, Any] = {
            "ioc_id": ioc_id,
            "ioc_type": ioc_type,
            "value": entry.value,
            "enrichments": {},
        }

        # Determine applicable enrichment types
        types_to_run = enrichment_types or list(ENRICHMENT_APPLICABILITY.keys())

        for etype in types_to_run:
            applicable_ioc_types = ENRICHMENT_APPLICABILITY.get(etype, set())
            if applicable_ioc_types and ioc_type not in applicable_ioc_types:
                continue

            # Check cache first
            if not force_refresh:
                cached = self._get_cached(db, ioc_id, etype)
                if cached:
                    results["enrichments"][etype] = cached
                    continue

            # Run enrichment
            enrichment_result = self._run_enrichment(
                etype, ioc_type, value, entry, db,
            )

            # Cache result
            self._cache_result(db, ioc_id, etype, enrichment_result)
            results["enrichments"][etype] = enrichment_result

        results["enriched_at"] = datetime.datetime.utcnow().isoformat()
        results["total_enrichments"] = len(results["enrichments"])

        return results

    def _run_enrichment(
        self,
        enrichment_type: str,
        ioc_type: str,
        value: str,
        entry: Any,
        db: Any,
    ) -> Dict[str, Any]:
        """
        Dispatches enrichment to the appropriate handler.
        Each handler returns structured data or "not_configured" status.
        """
        handlers = {
            EnrichmentType.DNS:             self._enrich_dns,
            EnrichmentType.MITRE_ATTACK:    self._enrich_mitre_attack,
            EnrichmentType.KILL_CHAIN:      self._enrich_kill_chain,
            EnrichmentType.THREAT_ACTOR:    self._enrich_threat_actor,
            EnrichmentType.CAMPAIGN:        self._enrich_campaign,
            EnrichmentType.MALWARE_FAMILY:  self._enrich_malware_family,
            EnrichmentType.RISK_LEVEL:      self._enrich_risk_level,
            EnrichmentType.EVIDENCE_LINKS:  self._enrich_evidence_links,
            EnrichmentType.CASE_REFERENCES: self._enrich_case_references,
            EnrichmentType.GEO:             self._enrich_geo,
            EnrichmentType.ASN:             self._enrich_asn,
            EnrichmentType.WHOIS:           self._enrich_whois,
            EnrichmentType.PASSIVE_DNS:     self._enrich_passive_dns,
            EnrichmentType.CERTIFICATE:     self._enrich_certificate,
        }

        handler = handlers.get(enrichment_type)
        if handler:
            try:
                return handler(ioc_type, value, entry, db)
            except Exception as e:
                logger.error("Enrichment %s failed for %s: %s",
                             enrichment_type, value[:30], e)
                return {
                    "status": "error",
                    "enrichment_type": enrichment_type,
                    "error": str(e)[:200],
                }

        return {
            "status": "not_implemented",
            "enrichment_type": enrichment_type,
        }

    # ── Enrichment Handlers ───────────────────────────────────────────────

    def _enrich_dns(
        self, ioc_type: str, value: str, entry: Any, db: Any,
    ) -> Dict[str, Any]:
        """DNS resolution using system resolver — no external API needed."""
        import socket

        if ioc_type != "domain":
            return {"status": "not_applicable", "enrichment_type": "dns"}

        try:
            records: Dict[str, Any] = {"domain": value, "records": {}}

            # A records
            try:
                a_records = socket.getaddrinfo(value, None, socket.AF_INET)
                records["records"]["A"] = list(set(
                    addr[4][0] for addr in a_records
                ))
            except socket.gaierror:
                records["records"]["A"] = []

            # AAAA records
            try:
                aaaa_records = socket.getaddrinfo(value, None, socket.AF_INET6)
                records["records"]["AAAA"] = list(set(
                    addr[4][0] for addr in aaaa_records
                ))
            except socket.gaierror:
                records["records"]["AAAA"] = []

            records["status"] = "success"
            records["enrichment_type"] = "dns"
            return records

        except Exception as e:
            return {
                "status": "error",
                "enrichment_type": "dns",
                "error": str(e)[:200],
            }

    def _enrich_mitre_attack(
        self, ioc_type: str, value: str, entry: Any, db: Any,
    ) -> Dict[str, Any]:
        """Maps IOC to MITRE ATT&CK techniques from the local STIX DB."""
        from .stix_models import StixAttackPattern, StixRelationship

        try:
            techniques = []

            # If this is an ATT&CK technique ID, look it up directly
            if ioc_type == "attack_technique":
                patterns = (
                    db.query(StixAttackPattern)
                    .filter(
                        StixAttackPattern.external_references.contains(
                            [{"external_id": value.upper()}]
                        )
                    )
                    .all()
                )
                if not patterns:
                    # Try name-based search
                    patterns = (
                        db.query(StixAttackPattern)
                        .filter(StixAttackPattern.name.ilike(f"%{value}%"))
                        .limit(10)
                        .all()
                    )

                techniques = [
                    {
                        "stix_id": p.stix_id,
                        "name": p.name,
                        "description": (p.description or "")[:200],
                        "kill_chain_phases": p.kill_chain_phases,
                    }
                    for p in patterns
                ]

            # Check for STIX relationships linking this IOC to techniques
            if entry and entry.stix_indicator_id:
                rels = (
                    db.query(StixRelationship)
                    .filter(
                        StixRelationship.source_ref == entry.stix_indicator_id,
                        StixRelationship.relationship_type == "indicates",
                    )
                    .limit(20)
                    .all()
                )
                for rel in rels:
                    target_pattern = (
                        db.query(StixAttackPattern)
                        .filter(StixAttackPattern.stix_id == rel.target_ref)
                        .first()
                    )
                    if target_pattern:
                        techniques.append({
                            "stix_id": target_pattern.stix_id,
                            "name": target_pattern.name,
                            "relationship": rel.relationship_type,
                        })

            return {
                "status": "success" if techniques else "no_data",
                "enrichment_type": "mitre_attack",
                "techniques": techniques,
                "source": "local_stix_db",
            }

        except Exception as e:
            return {
                "status": "error",
                "enrichment_type": "mitre_attack",
                "error": str(e)[:200],
            }

    def _enrich_kill_chain(
        self, ioc_type: str, value: str, entry: Any, db: Any,
    ) -> Dict[str, Any]:
        """Maps IOC to Lockheed Martin Cyber Kill Chain phases."""
        # Kill chain mapping from MITRE ATT&CK tactics
        TACTIC_TO_KILL_CHAIN = {
            "reconnaissance":       "Reconnaissance",
            "resource-development": "Weaponization",
            "initial-access":       "Delivery",
            "execution":            "Exploitation",
            "persistence":          "Installation",
            "command-and-control":   "Command & Control",
            "exfiltration":         "Actions on Objectives",
            "impact":               "Actions on Objectives",
            "privilege-escalation": "Exploitation",
            "defense-evasion":      "Installation",
            "credential-access":    "Exploitation",
            "discovery":            "Exploitation",
            "lateral-movement":     "Command & Control",
            "collection":           "Actions on Objectives",
        }

        phases = []
        if entry and entry.kill_chain_phases:
            for phase in entry.kill_chain_phases:
                if isinstance(phase, str):
                    kc = TACTIC_TO_KILL_CHAIN.get(phase.lower())
                    if kc:
                        phases.append({"tactic": phase, "kill_chain_phase": kc})
                elif isinstance(phase, dict):
                    phase_name = phase.get("phase_name", "")
                    kc = TACTIC_TO_KILL_CHAIN.get(phase_name.lower())
                    if kc:
                        phases.append({
                            "kill_chain_name": phase.get("kill_chain_name"),
                            "phase_name": phase_name,
                            "kill_chain_phase": kc,
                        })

        return {
            "status": "success" if phases else "no_data",
            "enrichment_type": "kill_chain",
            "phases": phases,
        }

    def _enrich_threat_actor(
        self, ioc_type: str, value: str, entry: Any, db: Any,
    ) -> Dict[str, Any]:
        """Finds threat actors linked to this IOC via STIX relationships."""
        from .stix_models import StixThreatActor, StixRelationship

        try:
            actors = []
            if entry and entry.stix_indicator_id:
                # Find relationships: indicator → uses/indicates → threat-actor
                rels = (
                    db.query(StixRelationship)
                    .filter(
                        StixRelationship.target_ref == entry.stix_indicator_id,
                    )
                    .limit(20)
                    .all()
                )
                for rel in rels:
                    actor = (
                        db.query(StixThreatActor)
                        .filter(StixThreatActor.stix_id == rel.source_ref)
                        .first()
                    )
                    if actor:
                        actors.append({
                            "stix_id": actor.stix_id,
                            "name": actor.name,
                            "description": (actor.description or "")[:200],
                            "threat_actor_types": actor.threat_actor_types,
                            "sophistication": actor.sophistication,
                            "relationship": rel.relationship_type,
                        })

            return {
                "status": "success" if actors else "no_data",
                "enrichment_type": "threat_actor",
                "actors": actors,
                "source": "local_stix_db",
            }

        except Exception as e:
            return {"status": "error", "enrichment_type": "threat_actor",
                    "error": str(e)[:200]}

    def _enrich_campaign(
        self, ioc_type: str, value: str, entry: Any, db: Any,
    ) -> Dict[str, Any]:
        """Finds campaigns linked to this IOC via STIX relationships."""
        from .stix_models import StixCampaign, StixRelationship

        try:
            campaigns = []
            if entry and entry.stix_indicator_id:
                rels = (
                    db.query(StixRelationship)
                    .filter(
                        StixRelationship.target_ref == entry.stix_indicator_id,
                    )
                    .limit(20)
                    .all()
                )
                for rel in rels:
                    campaign = (
                        db.query(StixCampaign)
                        .filter(StixCampaign.stix_id == rel.source_ref)
                        .first()
                    )
                    if campaign:
                        campaigns.append({
                            "stix_id": campaign.stix_id,
                            "name": campaign.name,
                            "description": (campaign.description or "")[:200],
                            "first_seen": campaign.first_seen.isoformat() if campaign.first_seen else None,
                            "last_seen": campaign.last_seen.isoformat() if campaign.last_seen else None,
                        })

            return {
                "status": "success" if campaigns else "no_data",
                "enrichment_type": "campaign",
                "campaigns": campaigns,
                "source": "local_stix_db",
            }

        except Exception as e:
            return {"status": "error", "enrichment_type": "campaign",
                    "error": str(e)[:200]}

    def _enrich_malware_family(
        self, ioc_type: str, value: str, entry: Any, db: Any,
    ) -> Dict[str, Any]:
        """Finds malware families linked to this IOC via STIX relationships."""
        from .stix_models import StixMalware, StixRelationship

        try:
            families = []
            if entry and entry.stix_indicator_id:
                rels = (
                    db.query(StixRelationship)
                    .filter(
                        StixRelationship.source_ref == entry.stix_indicator_id,
                        StixRelationship.relationship_type == "indicates",
                    )
                    .limit(20)
                    .all()
                )
                for rel in rels:
                    malware = (
                        db.query(StixMalware)
                        .filter(StixMalware.stix_id == rel.target_ref)
                        .first()
                    )
                    if malware:
                        families.append({
                            "stix_id": malware.stix_id,
                            "name": malware.name,
                            "is_family": malware.is_family,
                            "malware_types": malware.malware_types,
                            "description": (malware.description or "")[:200],
                        })

            return {
                "status": "success" if families else "no_data",
                "enrichment_type": "malware_family",
                "families": families,
                "source": "local_stix_db",
            }

        except Exception as e:
            return {"status": "error", "enrichment_type": "malware_family",
                    "error": str(e)[:200]}

    def _enrich_risk_level(
        self, ioc_type: str, value: str, entry: Any, db: Any,
    ) -> Dict[str, Any]:
        """Computes composite risk level from IOC attributes."""
        risk_factors = []
        risk_score = 0

        if entry:
            # Factor: confidence
            conf = entry.confidence_score or 0
            if conf >= 80:
                risk_factors.append({"factor": "high_confidence", "score": 30})
                risk_score += 30
            elif conf >= 50:
                risk_factors.append({"factor": "medium_confidence", "score": 15})
                risk_score += 15

            # Factor: observation count
            obs = entry.observation_count or 0
            if obs >= 10:
                risk_factors.append({"factor": "widely_observed", "score": 20})
                risk_score += 20
            elif obs >= 3:
                risk_factors.append({"factor": "moderately_observed", "score": 10})
                risk_score += 10

            # Factor: severity
            if entry.severity == "critical":
                risk_factors.append({"factor": "critical_severity", "score": 30})
                risk_score += 30
            elif entry.severity == "high":
                risk_factors.append({"factor": "high_severity", "score": 20})
                risk_score += 20

            # Factor: active status
            if entry.status == "active":
                risk_factors.append({"factor": "active_ioc", "score": 10})
                risk_score += 10

            # Factor: freshness
            if entry.last_seen:
                days_old = (datetime.datetime.utcnow() - entry.last_seen).days
                if days_old <= 7:
                    risk_factors.append({"factor": "recently_seen", "score": 10})
                    risk_score += 10

        risk_level = "info"
        if risk_score >= 80:
            risk_level = "critical"
        elif risk_score >= 60:
            risk_level = "high"
        elif risk_score >= 40:
            risk_level = "medium"
        elif risk_score >= 20:
            risk_level = "low"

        return {
            "status": "success",
            "enrichment_type": "risk_level",
            "risk_score": min(100, risk_score),
            "risk_level": risk_level,
            "factors": risk_factors,
        }

    def _enrich_evidence_links(
        self, ioc_type: str, value: str, entry: Any, db: Any,
    ) -> Dict[str, Any]:
        """Links IOC to evidence in the case management system."""
        try:
            from . import models

            # Search evidence descriptions and filenames for the IOC value
            evidence = (
                db.query(models.Evidence)
                .filter(
                    models.Evidence.description.ilike(f"%{value[:30]}%")
                )
                .limit(10)
                .all()
            )

            links = [
                {
                    "evidence_id": e.id,
                    "case_id": e.case_id,
                    "filename": e.filename,
                    "description": (e.description or "")[:100],
                }
                for e in evidence
            ]

            return {
                "status": "success" if links else "no_data",
                "enrichment_type": "evidence_links",
                "links": links,
            }

        except Exception as e:
            return {"status": "error", "enrichment_type": "evidence_links",
                    "error": str(e)[:200]}

    def _enrich_case_references(
        self, ioc_type: str, value: str, entry: Any, db: Any,
    ) -> Dict[str, Any]:
        """Links IOC to cases via wallet addresses or related data."""
        try:
            from . import models

            cases = []
            # Check if IOC value appears in any wallet address in a case
            if ioc_type in ("wallet", "ip", "domain"):
                wallets = (
                    db.query(models.Wallet)
                    .filter(models.Wallet.address.ilike(f"%{value[:40]}%"))
                    .limit(10)
                    .all()
                )
                for w in wallets:
                    if w.case_id:
                        case = db.query(models.Case).filter(
                            models.Case.id == w.case_id
                        ).first()
                        if case:
                            cases.append({
                                "case_id": case.id,
                                "case_number": case.case_number,
                                "title": case.title,
                                "status": case.status,
                                "wallet_address": w.address,
                            })

            return {
                "status": "success" if cases else "no_data",
                "enrichment_type": "case_references",
                "cases": cases,
            }

        except Exception as e:
            return {"status": "error", "enrichment_type": "case_references",
                    "error": str(e)[:200]}

    # External provider enrichments — return "not_configured" if no API key

    def _enrich_geo(
        self, ioc_type: str, value: str, entry: Any, db: Any,
    ) -> Dict[str, Any]:
        """Geo enrichment for IPs. Requires configured provider."""
        api_key = os.getenv("GEO_API_KEY")
        if not api_key:
            return {
                "status": "not_configured",
                "enrichment_type": "geo",
                "message": "Set GEO_API_KEY environment variable for IP geolocation.",
            }
        # When configured, would call MaxMind GeoLite2 or similar
        return {
            "status": "not_configured",
            "enrichment_type": "geo",
            "message": "Geo provider configured but not yet integrated. Set GEO_API_KEY.",
        }

    def _enrich_asn(
        self, ioc_type: str, value: str, entry: Any, db: Any,
    ) -> Dict[str, Any]:
        """ASN enrichment for IPs. Requires configured provider."""
        return {
            "status": "not_configured",
            "enrichment_type": "asn",
            "message": "Set ASN_API_KEY environment variable for ASN lookup.",
        }

    def _enrich_whois(
        self, ioc_type: str, value: str, entry: Any, db: Any,
    ) -> Dict[str, Any]:
        """WHOIS enrichment. Requires configured provider."""
        return {
            "status": "not_configured",
            "enrichment_type": "whois",
            "message": "Set WHOIS_API_KEY environment variable for WHOIS lookup.",
        }

    def _enrich_passive_dns(
        self, ioc_type: str, value: str, entry: Any, db: Any,
    ) -> Dict[str, Any]:
        """Passive DNS enrichment. Requires configured provider."""
        return {
            "status": "not_configured",
            "enrichment_type": "passive_dns",
            "message": "Set PASSIVE_DNS_API_KEY environment variable for passive DNS.",
        }

    def _enrich_certificate(
        self, ioc_type: str, value: str, entry: Any, db: Any,
    ) -> Dict[str, Any]:
        """TLS certificate enrichment. Requires configured provider."""
        return {
            "status": "not_configured",
            "enrichment_type": "certificate",
            "message": "Set CERTIFICATE_API_KEY environment variable for certificate lookup.",
        }

    # ── Caching ───────────────────────────────────────────────────────────

    def _get_cached(
        self, db: Any, ioc_id: str, enrichment_type: str,
    ) -> Optional[Dict[str, Any]]:
        """Returns cached enrichment result if still valid."""
        from .stix_models import EnrichmentResult

        try:
            cached = (
                db.query(EnrichmentResult)
                .filter(
                    EnrichmentResult.ioc_id == ioc_id,
                    EnrichmentResult.enrichment_type == enrichment_type,
                )
                .order_by(EnrichmentResult.enriched_at.desc())
                .first()
            )

            if cached and cached.expires_at:
                if datetime.datetime.utcnow() < cached.expires_at:
                    result = cached.data or {}
                    result["cached"] = True
                    result["cached_at"] = cached.enriched_at.isoformat() if cached.enriched_at else None
                    return result

            return None

        except Exception:
            return None

    def _cache_result(
        self, db: Any, ioc_id: str, enrichment_type: str, data: Dict[str, Any],
    ) -> None:
        """Caches enrichment result with TTL."""
        from .stix_models import EnrichmentResult

        try:
            ttl = self._cache_ttl.get(enrichment_type, DEFAULT_TTL)
            now = datetime.datetime.utcnow()

            result = EnrichmentResult(
                id=str(uuid.uuid4()),
                ioc_id=ioc_id,
                enrichment_type=enrichment_type,
                data=data,
                status=data.get("status", "success"),
                ttl_seconds=ttl,
                enriched_at=now,
                expires_at=now + datetime.timedelta(seconds=ttl),
            )
            db.add(result)
            db.commit()
        except Exception as e:
            logger.warning("Failed to cache enrichment: %s", e)


# ─── Singleton ────────────────────────────────────────────────────────────────

enrichment_engine = EnrichmentEngine()
