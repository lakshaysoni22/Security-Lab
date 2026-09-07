"""
LEATrace European Union Consolidated Sanctions Provider — Production.

Downloads, parses, and formats the EU Consolidated Sanctions List.

PRODUCTION INVARIANTS:
- Downloads real data from https://webgate.ec.europa.eu
- Never fabricates entities or wallet addresses
- Uses exponential backoff retry via base class
- Rate-limited to prevent endpoint abuse
"""

from __future__ import annotations

import datetime
import hashlib
import logging
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional

from .sanctions_provider_base import SanctionsProvider

logger = logging.getLogger("leatrace.providers.eu")

DEFAULT_EU_URL = "https://webgate.ec.europa.eu/fsd/fsf/public/files/xmlFullSanctionsList_1_1/content"


class EUConsolidatedSanctionsProvider(SanctionsProvider):
    """European Union Consolidated Sanctions List Provider."""

    def __init__(
        self,
        provider_id: str = "eu_consolidated",
        name: str = "EU Consolidated Sanctions",
        priority: int = 20,
        feed_url: Optional[str] = None,
    ):
        super().__init__(
            provider_id=provider_id,
            name=name,
            priority=priority,
            max_retries=3,
            backoff_factor=2.0,
            initial_backoff_seconds=2.0,
            max_backoff_seconds=60.0,
            requests_per_minute=6,
            connect_timeout=30,
            read_timeout=120,
        )
        self.feed_url = feed_url or DEFAULT_EU_URL

    def is_configured(self) -> bool:
        return bool(self.feed_url)

    def _download_and_parse_impl(self) -> Dict[str, Any]:
        """Downloads real EU Consolidated XML and parses it into normalized structures."""
        if not self.is_configured():
            raise ValueError(f"Provider {self.name} is not configured.")

        logger.info("Downloading EU Consolidated list from %s", self.feed_url)
        headers = {"User-Agent": "LEATrace-Sanctions-Compliance/2.0"}

        req = urllib.request.Request(self.feed_url, headers=headers)
        with urllib.request.urlopen(req, timeout=self.read_timeout) as response:
            content_bytes = response.read()

        checksum = hashlib.sha256(content_bytes).hexdigest()
        content_size = len(content_bytes)
        logger.info(
            "Downloaded %d bytes (%.1f MB), EU SHA-256: %s",
            content_size, content_size / (1024 * 1024), checksum,
        )

        # Parse XML
        entities = self._parse_xml(content_bytes)

        return {
            "checksum": checksum,
            "entities": entities,
            "raw_data": content_bytes,
            "record_count": len(entities),
            "download_size_bytes": content_size,
        }

    def health_check(self) -> Dict[str, Any]:
        """Checks connectivity to EU Consolidated server."""
        try:
            req = urllib.request.Request(
                self.feed_url, method="HEAD",
                headers={"User-Agent": "LEATrace/2.0"},
            )
            with urllib.request.urlopen(req, timeout=self.connect_timeout) as resp:
                status_code = resp.status
            return {
                "provider_id": self.provider_id,
                "is_healthy": status_code == 200,
                "status_code": status_code,
                "url": self.feed_url,
                "checked_at": datetime.datetime.utcnow().isoformat() + "Z",
            }
        except Exception as e:
            return {
                "provider_id": self.provider_id,
                "is_healthy": False,
                "error": str(e)[:300],
                "url": self.feed_url,
                "checked_at": datetime.datetime.utcnow().isoformat() + "Z",
            }

    def _parse_xml(self, xml_bytes: bytes) -> List[Dict[str, Any]]:
        """Parses EU Consolidated Sanctions XML and extracts normalized records."""
        try:
            root = ET.fromstring(xml_bytes)
        except ET.ParseError as e:
            logger.error("Failed to parse EU XML: %s", e)
            raise ValueError(f"Malformed XML: {e}")

        # The root could be {http://eu.europa.ec/fise}export or just export
        ns_map = {}
        if "}" in root.tag:
            ns_url = root.tag.split("}")[0][1:]
            ns_map = {"eu": ns_url}

        ns_prefix = "eu:" if ns_map else ""
        entries = root.findall(f".//{ns_prefix}sanctionEntity", ns_map) or root.findall(".//sanctionEntity")

        logger.info("EU: parsing %d sanctionEntity elements", len(entries))
        parsed_entities = []

        for entry in entries:
            logical_id = entry.attrib.get("logicalId")
            if not logical_id:
                logical_id = entry.findtext(f"{ns_prefix}logicalId", "", ns_map) or str(entry.findtext("logicalId", ""))
            if not logical_id:
                continue

            # Extract subject type ('individual' or 'entity')
            subject_type_node = entry.find(f"{ns_prefix}subjectType", ns_map) or entry.find("subjectType")
            subject_type_code = "entity"
            if subject_type_node is not None:
                subject_type_code = subject_type_node.attrib.get("code", "entity").lower()

            # Name aliases
            aliases = []
            primary_name = ""

            name_aliases = entry.findall(f"{ns_prefix}nameAlias", ns_map) or entry.findall("nameAlias")
            for alias in name_aliases:
                first = self._get_node_text(alias, f"{ns_prefix}firstName", ns_map) or ""
                middle = self._get_node_text(alias, f"{ns_prefix}middleName", ns_map) or ""
                last = self._get_node_text(alias, f"{ns_prefix}lastName", ns_map) or ""
                whole = self._get_node_text(alias, f"{ns_prefix}wholeName", ns_map) or ""

                alias_name = whole or f"{first} {middle} {last}".replace("  ", " ").strip()
                is_primary = alias.findtext(f"{ns_prefix}strong", "", ns_map) == "true" or alias.findtext("strong") == "true"

                if alias_name:
                    if is_primary and not primary_name:
                        primary_name = alias_name
                    else:
                        aliases.append({
                            "alias_name": alias_name,
                            "alias_type": "a.k.a.",
                        })

            if not primary_name:
                primary_name = aliases[0]["alias_name"] if aliases else f"EU-Entity-{logical_id}"

            # Regimes / Programs
            regime_els = entry.findall(f"{ns_prefix}regime", ns_map) or entry.findall("regime")
            regimes = []
            for r in regime_els:
                regime_name = r.attrib.get("regime") or r.attrib.get("name")
                if not regime_name:
                    regime_name = self._get_node_text(r, f"{ns_prefix}regimeName", ns_map) or r.attrib.get("regimeName")
                if regime_name:
                    regimes.append(regime_name)
            program_str = ";".join(filter(None, regimes))

            # Identifications (includes wallets / addresses)
            wallets = []
            identifications = entry.findall(f"{ns_prefix}identification", ns_map) or entry.findall("identification")
            for ident in identifications:
                id_type = self._get_node_text(ident, f"{ns_prefix}identificationType", ns_map) or ident.attrib.get("identificationType", "")
                number = self._get_node_text(ident, f"{ns_prefix}number", ns_map) or ident.attrib.get("number", "")

                if id_type and "Digital Currency" in id_type and number:
                    currency = id_type.replace("Digital Currency Address - ", "").strip()
                    wallets.append({
                        "address": number.strip(),
                        "currency": currency,
                    })

            # Countries
            countries = []
            citizenships = entry.findall(f"{ns_prefix}citizenship", ns_map) or entry.findall("citizenship")
            for cit in citizenships:
                country = self._get_node_text(cit, f"{ns_prefix}country", ns_map) or cit.attrib.get("country", "")
                if country:
                    countries.append({
                        "country_code": country[:2].upper(),
                        "country_name": country,
                        "association_type": "citizenship",
                    })

            # Birth details (additional country associations)
            birth_details = entry.findall(f"{ns_prefix}birthdate", ns_map) or entry.findall("birthdate")
            for bd in birth_details:
                bd_country = self._get_node_text(bd, f"{ns_prefix}country", ns_map) or bd.attrib.get("country", "")
                if bd_country and not any(c["country_name"] == bd_country for c in countries):
                    countries.append({
                        "country_code": bd_country[:2].upper(),
                        "country_name": bd_country,
                        "association_type": "birth",
                    })

            # Remarks
            remark_node = entry.find(f"{ns_prefix}remark", ns_map) or entry.find("remark")
            remarks = remark_node.text.strip() if remark_node is not None and remark_node.text else ""

            parsed_entities.append({
                "entity_uid": logical_id,
                "name": primary_name,
                "entity_type": subject_type_code,
                "program": program_str,
                "remarks": remarks,
                "wallets": wallets,
                "aliases": aliases,
                "countries": countries,
            })

        logger.info("EU Consolidated: Parsed %d entities, %d with wallets",
                     len(parsed_entities),
                     sum(1 for e in parsed_entities if e["wallets"]))
        return parsed_entities

    @staticmethod
    def _get_node_text(element: ET.Element, xpath: str, ns: Dict[str, str], default: str = "") -> str:
        child = element.find(xpath, ns)
        if child is None:
            bare_tag = xpath.split(":")[-1] if ":" in xpath else xpath
            child = element.find(bare_tag)
        return (child.text or default).strip() if child is not None else default
