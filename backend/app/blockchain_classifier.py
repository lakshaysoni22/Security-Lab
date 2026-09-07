import re
from typing import Dict, Any

# Standard regex patterns for blockchain address formats
BTC_LEGACY_PATTERN = re.compile(r"^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$")
BTC_BECH32_PATTERN = re.compile(r"^bc1[qp][a-z0-9]{38,58}$")
EVM_PATTERN = re.compile(r"^0x[a-fA-F0-9]{40}$")
SOL_PATTERN = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")
TRON_PATTERN = re.compile(r"^T[a-km-zA-HJ-NP-Z1-9]{33}$")
LTC_LEGACY_PATTERN = re.compile(r"^[LM][a-km-zA-HJ-NP-Z1-9]{26,33}$")
LTC_BECH32_PATTERN = re.compile(r"^ltc1[qp][a-z0-9]{38,58}$")
DOGE_PATTERN = re.compile(r"^D[5-9A-HJ-NP-Za-km-z][1-9A-HJ-NP-Za-km-z]{24,33}$")
XRP_PATTERN = re.compile(r"^r[0-9a-zA-Z]{24,34}$")

class BlockchainClassifier:
    def classify_address(self, address: str) -> Dict[str, Any]:
        """Scans the address format and classifies which blockchain network it belongs to."""
        addr_clean = address.strip()
        
        # 1. EVM (Ethereum, Polygon, BSC, Base, etc.)
        if EVM_PATTERN.match(addr_clean):
            return {
                "detected": True,
                "blockchain": "EVM Compatible",
                "subchains": ["Ethereum", "Polygon", "BNB Chain", "Arbitrum", "Optimism", "Base", "Avalanche"],
                "address_type": "Hexadecimal Contract/EOA",
                "ticker": "ETH/BNB/MATIC"
            }
            
        # 2. Bitcoin (BTC)
        if BTC_BECH32_PATTERN.match(addr_clean):
            addr_type = "Native SegWit (Bech32)" if addr_clean.startswith("bc1q") else "Taproot (Bech32m)"
            return {
                "detected": True,
                "blockchain": "Bitcoin (BTC)",
                "subchains": ["Mainnet", "Lightning Network"],
                "address_type": addr_type,
                "ticker": "BTC"
            }
        if BTC_LEGACY_PATTERN.match(addr_clean):
            addr_type = "Legacy (P2PKH)" if addr_clean.startswith("1") else "Nested SegWit (P2SH)"
            return {
                "detected": True,
                "blockchain": "Bitcoin (BTC)",
                "subchains": ["Mainnet"],
                "address_type": addr_type,
                "ticker": "BTC"
            }
            
        # 3. Tron (TRX)
        if TRON_PATTERN.match(addr_clean):
            return {
                "detected": True,
                "blockchain": "Tron (TRX)",
                "subchains": ["Mainnet"],
                "address_type": "Base58 TRC-20 Address",
                "ticker": "TRX"
            }

        # 4. Solana (SOL)
        if SOL_PATTERN.match(addr_clean) and not addr_clean.startswith("0x"):
            # Exclude standard EVM false positives
            return {
                "detected": True,
                "blockchain": "Solana",
                "subchains": ["Mainnet Beta"],
                "address_type": "Base58 Public Key",
                "ticker": "SOL"
            }
            
        # 5. Litecoin (LTC)
        if LTC_BECH32_PATTERN.match(addr_clean) or LTC_LEGACY_PATTERN.match(addr_clean):
            return {
                "detected": True,
                "blockchain": "Litecoin",
                "subchains": ["Mainnet"],
                "address_type": "Bech32/M-prefix SegWit",
                "ticker": "LTC"
            }
            
        # 6. Dogecoin (DOGE)
        if DOGE_PATTERN.match(addr_clean):
            return {
                "detected": True,
                "blockchain": "Dogecoin",
                "subchains": ["Mainnet"],
                "address_type": "Legacy Doge Address",
                "ticker": "DOGE"
            }
            
        # 7. Ripple (XRP)
        if XRP_PATTERN.match(addr_clean):
            return {
                "detected": True,
                "blockchain": "Ripple",
                "subchains": ["XRPL"],
                "address_type": "Classic Address",
                "ticker": "XRP"
            }
            
        return {
            "detected": False,
            "blockchain": "Unknown / Invalid Format",
            "subchains": [],
            "address_type": "None",
            "ticker": "None"
        }

blockchain_classifier = BlockchainClassifier()
