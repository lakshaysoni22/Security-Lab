"""
LEATrace Input Validation & Sanitization — Production.

Centralized input validation for blockchain addresses, chain IDs,
and query parameters. Prevents injection attacks and malformed input.
"""

import re
import logging
from typing import Optional

logger = logging.getLogger("leatrace.validators")

# ===================================================================
# Address Validators
# ===================================================================

_EVM_PATTERN = re.compile(r"^0x[0-9a-fA-F]{40}$")
_BTC_LEGACY = re.compile(r"^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$")
_BTC_BECH32 = re.compile(r"^bc1[a-zA-HJ-NP-Z0-9]{25,90}$")
_SOLANA_PATTERN = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")
_LTC_LEGACY = re.compile(r"^[LM3][a-km-zA-HJ-NP-Z1-9]{25,34}$")
_LTC_BECH32 = re.compile(r"^ltc1[a-zA-HJ-NP-Z0-9]{25,90}$")
_DOGE_PATTERN = re.compile(r"^[DA9][a-km-zA-HJ-NP-Z1-9]{25,34}$")
_TX_HASH_PATTERN = re.compile(r"^0x[0-9a-fA-F]{64}$")

# Dangerous patterns to reject
_SQL_INJECTION = re.compile(r"(--|;|'|\b(DROP|DELETE|INSERT|UPDATE|ALTER|EXEC)\b)", re.IGNORECASE)
_CYPHER_INJECTION = re.compile(r"(DETACH\s+DELETE|MERGE|CREATE|SET\s+\w+\s*=)", re.IGNORECASE)
_PATH_TRAVERSAL = re.compile(r"\.\./|\.\.\\")

VALID_CHAINS = {
    "ethereum", "polygon", "bnb", "arbitrum", "optimism",
    "avalanche", "base", "bitcoin", "solana", "litecoin",
    "dogecoin", "tron",
}


def validate_address(address: str, chain: Optional[str] = None) -> bool:
    """
    Validates a blockchain address format.
    If chain is specified, validates against that chain's format.
    If chain is None, checks all known formats.
    """
    if not address or len(address) > 128:
        return False

    # Reject injection attempts
    if _SQL_INJECTION.search(address) or _PATH_TRAVERSAL.search(address):
        logger.warning(f"Injection attempt detected in address: {address[:20]}...")
        return False

    if chain == "ethereum" or chain in {"polygon", "bnb", "arbitrum", "optimism", "avalanche", "base"}:
        return bool(_EVM_PATTERN.match(address))
    elif chain == "bitcoin":
        return bool(_BTC_LEGACY.match(address) or _BTC_BECH32.match(address))
    elif chain == "solana":
        return bool(_SOLANA_PATTERN.match(address))
    elif chain == "litecoin":
        return bool(_LTC_LEGACY.match(address) or _LTC_BECH32.match(address))
    elif chain == "dogecoin":
        return bool(_DOGE_PATTERN.match(address))
    elif chain is None:
        # Check all patterns
        return bool(
            _EVM_PATTERN.match(address)
            or _BTC_LEGACY.match(address)
            or _BTC_BECH32.match(address)
            or _SOLANA_PATTERN.match(address)
            or _LTC_LEGACY.match(address)
            or _LTC_BECH32.match(address)
            or _DOGE_PATTERN.match(address)
        )

    return False


def validate_tx_hash(tx_hash: str) -> bool:
    """Validates a transaction hash format (EVM 0x-prefixed hex)."""
    if not tx_hash or len(tx_hash) > 128:
        return False
    return bool(_TX_HASH_PATTERN.match(tx_hash))


def validate_chain_id(chain: str) -> bool:
    """Validates a chain identifier."""
    return chain.lower() in VALID_CHAINS


def sanitize_string(value: str, max_length: int = 256) -> str:
    """
    Sanitizes a user-provided string:
    - Truncates to max_length
    - Strips whitespace
    - Rejects injection patterns
    """
    if not value:
        return ""

    cleaned = value.strip()[:max_length]

    if _SQL_INJECTION.search(cleaned):
        logger.warning(f"SQL injection pattern detected and sanitized: {cleaned[:30]}...")
        return ""

    if _CYPHER_INJECTION.search(cleaned):
        logger.warning(f"Cypher injection pattern detected and sanitized: {cleaned[:30]}...")
        return ""

    if _PATH_TRAVERSAL.search(cleaned):
        logger.warning(f"Path traversal pattern detected and sanitized: {cleaned[:30]}...")
        return ""

    return cleaned


def sanitize_label(value: str) -> str:
    """Sanitizes a Neo4j node label — alphanumeric + underscore only."""
    if not value:
        return ""
    return re.sub(r"[^a-zA-Z0-9_]", "", value)[:64]
