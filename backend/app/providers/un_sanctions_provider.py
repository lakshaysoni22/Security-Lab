"""
LEATrace United Nations Consolidated Sanctions Provider — Production.

Downloads, parses, and formats the UN Security Council Consolidated
Sanctions List.

PRODUCTION INVARIANTS:
- Downloads real data from https://scsanctions.un.org
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

logger = logging.getLogger("leatrace.providers.un")

DEFAULT_UN_URL = "https://scsanctions.un.org/resources/xml/en/consolidated.xml"


class UNConsolidatedSanctionsProvider(SanctionsProvider):
    """United Nations Security Council Consolidated Sanctions List Provider."""

    def __init__(
        self,
        provider_id: str = "un_consolidated",
        name: str = "UN SC Consolidated Sanctions",
        priority: int = 30,
        feed_url: Optional[str] = None,
    ):
        super().__init__(
            provider_id=provider_id,
            name=name,
            priority=priority,
            max_retries=3,
            backoff_factor=2.0,
            initial_backoff_seconds=3.0,
            max_backoff_seconds=90.0,
            requests_per_minute=4,
            connect_timeout=30,
            read_timeout=180,
        )
        self.feed_url = feed_url or DEFAULT_UN_URL

    def is_configured(self) -> bool:
        return bool(self.feed_url)

    def _download_and_parse_impl(self) -> Dict[str, Any]:
        """Downloads real UN Consolidated XML and parses it."""
        if not self.is_configured():
            raise ValueError(f"Provider {self.name} is not configured.")

        logger.info("Downloading UN Consolidated list from %s", self.feed_url)
        headers = {"User-Agent": "LEATrace-Sanctions-Compliance/2.0"}

        req = urllib.request.Request(self.feed_url, headers=headers)
        with urllib.request.urlopen(req, timeout=self.read_timeout) as response:
            content_bytes = response.read()

        checksum = hashlib.sha256(content_bytes).hexdigest()
        content_size = len(content_bytes)
        logger.info(
            "Downloaded %d bytes (%.1f MB), UN SHA-256: %s",
            content_size, content_size / (1024 * 1024), checksum,
        )

        entities = self._parse_xml(content_bytes)

        return {
            "checksum": checksum,
            "entities": entities,
            "raw_data": content_bytes,
            "record_count": len(entities),
            "download_size_bytes": content_size,
        }

    def health_check(self) -> Dict[str, Any]:
        """Checks connectivity to UN sanctions server."""
        try:
            req = urllib.request.Request(
                self.feed_url, method="HEAD",
                headers={"User-Agent": "LEATrace/2.0"},
            )
            with urllib.request.urlopen(req, timeout=self.connect_timeout) as resp:
                status_code = resp.status
            return {
                "provider_id": self.provider_id,
                "is_healthy": status_code in (200, 302),
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
        """
        Parses the UN Consolidated Sanctions XML.

        The UN XML schema uses <INDIVIDUAL> and <ENTITY> elements
        under <INDIVIDUALS> and <ENTITIES> sections.
        """
        try:
            root = ET.fromstring(xml_bytes)
        except ET.ParseError as e:
            logger.error("Failed to parse UN XML: %s", e)
            raise ValueError(f"Malformed XML: {e}")

        parsed_entities = []

        # Parse INDIVIDUALS
        for individual in root.findall(".//INDIVIDUAL"):
            uid = self._text(individual, "DATAID") or self._text(individual, "REFERENCE_NUMBER")
            if not uid:
                continue

            first = self._text(individual, "FIRST_NAME") or ""
            second = self._text(individual, "SECOND_NAME") or ""
            third = self._text(individual, "THIRD_NAME") or ""
            fourth = self._text(individual, "FOURTH_NAME") or ""
            full_name = " ".join(filter(None, [first, second, third, fourth])).strip()
            if not full_name:
                full_name = f"UN-Individual-{uid}"

            # UN list type designation
            un_list_type = self._text(individual, "UN_LIST_TYPE") or ""
            listed_on = self._text(individual, "LISTED_ON") or ""
            comments = self._text(individual, "COMMENTS1") or ""

            # Aliases
            aliases = []
            for alias_el in individual.findall(".//INDIVIDUAL_ALIAS"):
                alias_name = self._text(alias_el, "ALIAS_NAME")
                if alias_name:
                    quality = self._text(alias_el, "QUALITY") or "a.k.a."
                    aliases.append({"alias_name": alias_name, "alias_type": quality})

            # Nationality
            countries = []
            for nat_el in individual.findall(".//NATIONALITY"):
                val = self._text(nat_el, "VALUE")
                if val:
                    countries.append({
                        "country_code": val[:2].upper(),
                        "country_name": val,
                        "association_type": "nationality",
                    })

            # Documents / IDs (check for digital currency)
            wallets = []
            for doc_el in individual.findall(".//INDIVIDUAL_DOCUMENT"):
                doc_type = self._text(doc_el, "TYPE_OF_DOCUMENT") or ""
                doc_number = self._text(doc_el, "NUMBER") or ""
                if "digital currency" in doc_type.lower() and doc_number:
                    currency = doc_type.replace("Digital Currency Address - ", "").strip()
                    wallets.append({"address": doc_number.strip(), "currency": currency})

            parsed_entities.append({
                "entity_uid": f"UN-{uid}",
                "name": full_name,
                "entity_type": "individual",
                "program": un_list_type or "UN_SANCTIONS",
                "remarks": comments[:500] if comments else "",
                "wallets": wallets,
                "aliases": aliases,
                "countries": countries,
            })

        # Parse ENTITIES (organizations)
        for entity in root.findall(".//ENTITY"):
            uid = self._text(entity, "DATAID") or self._text(entity, "REFERENCE_NUMBER")
            if not uid:
                continue

            name = self._text(entity, "FIRST_NAME") or self._text(entity, "NAME") or f"UN-Entity-{uid}"
            un_list_type = self._text(entity, "UN_LIST_TYPE") or ""
            comments = self._text(entity, "COMMENTS1") or ""

            # Aliases
            aliases = []
            for alias_el in entity.findall(".//ENTITY_ALIAS"):
                alias_name = self._text(alias_el, "ALIAS_NAME")
                if alias_name:
                    quality = self._text(alias_el, "QUALITY") or "a.k.a."
                    aliases.append({"alias_name": alias_name, "alias_type": quality})

            # Address countries
            countries = []
            for addr_el in entity.findall(".//ENTITY_ADDRESS"):
                country = self._text(addr_el, "COUNTRY")
                if country and not any(c["country_name"] == country for c in countries):
                    countries.append({
                        "country_code": country[:2].upper(),
                        "country_name": country,
                        "association_type": "location",
                    })

            parsed_entities.append({
                "entity_uid": f"UN-{uid}",
                "name": name,
                "entity_type": "organization",
                "program": un_list_type or "UN_SANCTIONS",
                "remarks": comments[:500] if comments else "",
                "wallets": [],
                "aliases": aliases,
                "countries": countries,
            })

        logger.info("UN Consolidated: Parsed %d entities (%d individuals, %d organizations)",
                     len(parsed_entities),
                     sum(1 for e in parsed_entities if e["entity_type"] == "individual"),
                     sum(1 for e in parsed_entities if e["entity_type"] == "organization"))
        return parsed_entities

    @staticmethod
    def _text(element: ET.Element, tag: str) -> str:
        """Extracts text content from a child element."""
        child = element.find(tag)
        if child is not None and child.text:
            return child.text.strip()
        return ""
