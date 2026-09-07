"""
LEATrace U.S. OFAC SDN Sanctions Provider — Production.

Downloads, parses, and formats the Specially Designated Nationals (SDN)
sanctions list from U.S. Treasury OFAC.

PRODUCTION INVARIANTS:
- Downloads real data from https://sanctionslistservice.ofac.treas.gov
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

logger = logging.getLogger("leatrace.providers.ofac")

DEFAULT_OFAC_URL = "https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/SDN.XML"


class OFACSDNProvider(SanctionsProvider):
    """OFAC Specially Designated Nationals (SDN) List Provider."""

    def __init__(
        self,
        provider_id: str = "ofac_sdn",
        name: str = "U.S. OFAC SDN List",
        priority: int = 10,
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
        self.feed_url = feed_url or DEFAULT_OFAC_URL

    def is_configured(self) -> bool:
        return bool(self.feed_url)

    def _download_and_parse_impl(self) -> Dict[str, Any]:
        """Downloads real OFAC SDN XML and parses it into normalized structures."""
        if not self.is_configured():
            raise ValueError(f"Provider {self.name} is not configured.")

        logger.info("Downloading OFAC SDN list from %s", self.feed_url)
        headers = {"User-Agent": "LEATrace-Sanctions-Compliance/2.0"}

        req = urllib.request.Request(self.feed_url, headers=headers)
        with urllib.request.urlopen(req, timeout=self.read_timeout) as response:
            content_bytes = response.read()

        checksum = hashlib.sha256(content_bytes).hexdigest()
        content_size = len(content_bytes)
        logger.info(
            "Downloaded %d bytes (%.1f MB), SHA-256: %s",
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
        """Checks connectivity to OFAC SDN server."""
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
        """Parses the OFAC SDN XML and extracts normalized entities, aliases, countries, and wallets."""
        try:
            root = ET.fromstring(xml_bytes)
        except ET.ParseError as e:
            logger.error("Failed to parse OFAC XML: %s", e)
            raise ValueError(f"Malformed XML: {e}")

        # Namespaces
        ns_map = {"sdn": "http://tempuri.org/sdnList.xsd"}
        entries = root.findall(".//sdn:sdnEntry", ns_map) or root.findall(".//sdnEntry")

        parsed_entities = []

        for entry in entries:
            ns_prefix = "sdn:" if root.findall(".//sdn:sdnEntry", ns_map) else ""

            uid = self._get_node_text(entry, f"{ns_prefix}uid", ns_map)
            if not uid:
                continue

            first_name = self._get_node_text(entry, f"{ns_prefix}firstName", ns_map) or ""
            last_name = self._get_node_text(entry, f"{ns_prefix}lastName", ns_map) or ""
            primary_name = f"{first_name} {last_name}".strip() or last_name or f"Entity-{uid}"
            entity_type = self._get_node_text(entry, f"{ns_prefix}sdnType", ns_map, "Entity")

            # In OFAC, type can be "Individual", "Entity", "Vessel", "Aircraft"
            norm_type = entity_type.lower().strip()

            # Sanctions program(s)
            prog_els = entry.findall(f"{ns_prefix}programList/{ns_prefix}program", ns_map) or entry.findall("programList/program")
            programs = [p.text.strip() for p in prog_els if p.text]
            program_str = ";".join(filter(None, programs))

            remarks = self._get_node_text(entry, f"{ns_prefix}remarks", ns_map)

            # ── Extract Wallets, Aliases, Countries
            wallets = []
            aliases = []
            countries = []

            # ID List (includes Digital Currency Addresses)
            id_list = entry.findall(f"{ns_prefix}idList/{ns_prefix}id", ns_map) or entry.findall("idList/id")
            for id_node in id_list:
                id_type = self._get_node_text(id_node, f"{ns_prefix}idType", ns_map)
                id_number = self._get_node_text(id_node, f"{ns_prefix}idNumber", ns_map)

                if id_type and "Digital Currency" in id_type and id_number:
                    # e.g., 'Digital Currency Address - XBT' or 'Digital Currency Address - ETH'
                    currency = id_type.replace("Digital Currency Address - ", "").strip()
                    wallets.append({
                        "address": id_number.strip(),
                        "currency": currency,
                    })

            # Aka List (Aliases)
            aka_list = entry.findall(f"{ns_prefix}akaList/{ns_prefix}aka", ns_map) or entry.findall("akaList/aka")
            for aka_node in aka_list:
                aka_first = self._get_node_text(aka_node, f"{ns_prefix}firstName", ns_map) or ""
                aka_last = self._get_node_text(aka_node, f"{ns_prefix}lastName", ns_map) or ""
                aka_name = f"{aka_first} {aka_last}".strip()
                aka_type = self._get_node_text(aka_node, f"{ns_prefix}type", ns_map, "a.k.a.")
                if aka_name:
                    aliases.append({
                        "alias_name": aka_name,
                        "alias_type": aka_type,
                    })

            # Citizenships & Locations (Countries)
            citizenship_list = entry.findall(f"{ns_prefix}citizenshipList/{ns_prefix}citizenship", ns_map) or entry.findall("citizenshipList/citizenship")
            for cit_node in citizenship_list:
                country = self._get_node_text(cit_node, f"{ns_prefix}country", ns_map)
                if country:
                    countries.append({
                        "country_code": country[:2].upper(),  # Approximate code
                        "country_name": country,
                        "association_type": "citizenship",
                    })

            # Nationality list
            nationality_list = entry.findall(f"{ns_prefix}nationalityList/{ns_prefix}nationality", ns_map) or entry.findall("nationalityList/nationality")
            for nat_node in nationality_list:
                country = self._get_node_text(nat_node, f"{ns_prefix}country", ns_map)
                if country:
                    countries.append({
                        "country_code": country[:2].upper(),
                        "country_name": country,
                        "association_type": "nationality",
                    })

            # Address list
            addr_list = entry.findall(f"{ns_prefix}addressList/{ns_prefix}address", ns_map) or entry.findall("addressList/address")
            for addr_node in addr_list:
                addr_country = self._get_node_text(addr_node, f"{ns_prefix}country", ns_map)
                if addr_country and not any(c["country_name"] == addr_country for c in countries):
                    countries.append({
                        "country_code": addr_country[:2].upper(),
                        "country_name": addr_country,
                        "association_type": "location",
                    })

            parsed_entities.append({
                "entity_uid": uid,
                "name": primary_name,
                "entity_type": norm_type,
                "program": program_str,
                "remarks": remarks,
                "wallets": wallets,
                "aliases": aliases,
                "countries": countries,
            })

        logger.info("OFAC SDN: Parsed %d entities, %d with wallets",
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
