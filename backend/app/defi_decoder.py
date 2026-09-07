"""
LEAtTrace Blockchain Intelligence — DeFi Intelligence Decoder.

Enterprise DeFi decoding: ERC-20/721/1155, liquidity pools, DEX swaps,
flash loans, staking, lending, governance, yield farming, and vault interactions.
"""

from typing import Dict, Any, Optional, List
from .protocol_registry import protocol_registry
from .pool_analyzer import pool_analyzer
from .contract_decoder import contract_decoder
from .price_oracle import price_oracle

# ERC Standard Event Topics
ERC20_TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
ERC20_APPROVAL = "0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925"
ERC721_TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"  # Same as ERC20 but with tokenId
ERC1155_SINGLE = "0xc3d58168c5ae7397731d063d5bbf3d657854427343f4c083240f7aacaa2d0f62"
ERC1155_BATCH = "0x4a39dc06d4c0dbc64b70af90fd698a233a518aa5d07e595d983b8c0526c8f7fb"

# DeFi Method Selectors
DEFI_METHODS = {
    "0x38ed1739": {"name": "swapExactTokensForTokens", "action": "DEX Swap", "category": "swap"},
    "0x7ff36ab5": {"name": "swapExactETHForTokens", "action": "DEX Swap (ETH→Token)", "category": "swap"},
    "0x18cbafe5": {"name": "swapExactTokensForETH", "action": "DEX Swap (Token→ETH)", "category": "swap"},
    "0x5c11d795": {"name": "swapExactTokensForTokensSupportingFeeOnTransferTokens", "action": "DEX Swap (FeeOnTransfer)", "category": "swap"},
    "0xe8e33700": {"name": "addLiquidity", "action": "Add Liquidity", "category": "liquidity"},
    "0xf305d719": {"name": "addLiquidityETH", "action": "Add Liquidity (ETH)", "category": "liquidity"},
    "0xbaa2abde": {"name": "removeLiquidity", "action": "Remove Liquidity", "category": "liquidity"},
    "0x02751cec": {"name": "removeLiquidityETH", "action": "Remove Liquidity (ETH)", "category": "liquidity"},
    "0xa9059cbb": {"name": "transfer", "action": "ERC-20 Transfer", "category": "transfer"},
    "0x095ea7b3": {"name": "approve", "action": "Token Approval", "category": "approval"},
    "0x23b872dd": {"name": "transferFrom", "action": "TransferFrom (Delegated)", "category": "transfer"},
    "0xd0e30db0": {"name": "deposit", "action": "Deposit / Wrap", "category": "deposit"},
    "0x2e1a7d4d": {"name": "withdraw", "action": "Withdraw / Unwrap", "category": "withdrawal"},
    "0xa0712d68": {"name": "mint", "action": "Mint Tokens", "category": "mint"},
    "0x42966c68": {"name": "burn", "action": "Burn Tokens", "category": "burn"},
    "0x1249c58b": {"name": "mint (no args)", "action": "Mint NFT", "category": "mint"},
    "0xe2bbb158": {"name": "deposit (staking)", "action": "Stake / Farm Deposit", "category": "staking"},
    "0x441a3e70": {"name": "withdraw (staking)", "action": "Unstake / Farm Withdraw", "category": "staking"},
    "0xb6b55f25": {"name": "deposit (vault)", "action": "Vault Deposit", "category": "vault"},
    # Note: 0x2e1a7d4d already mapped to "withdraw" above (lines 34). Vault withdraw shares the same selector.
    "0xe9fad8ee": {"name": "exit", "action": "Exit Position", "category": "staking"},
    "0x3d18b912": {"name": "getReward", "action": "Claim Rewards", "category": "reward"},
    "0xab033ea9": {"name": "setDelegate", "action": "Governance Delegate", "category": "governance"},
    "0x15373e3d": {"name": "castVote", "action": "Governance Vote", "category": "governance"},
    "0x56781388": {"name": "propose", "action": "Governance Proposal", "category": "governance"},
    # Flash Loans
    "0xab9c4b5d": {"name": "flashLoan", "action": "Flash Loan", "category": "flash_loan"},
    "0x5cffe9de": {"name": "flashLoan (Aave)", "action": "Flash Loan (Aave)", "category": "flash_loan"},
}


class DeFiDecoderService:
    """Enterprise DeFi transaction decoder with protocol detection and action classification."""

    def decode_defi_transaction(self, to_address: str, input_data: str, value_eth: float) -> Dict[str, Any]:
        """Full DeFi transaction decode: protocol, action, parameters."""
        target = to_address.strip().lower()
        protocol = protocol_registry.lookup(target)

        # Parse function selector
        method_info = self._decode_method(input_data)
        decoded_input = contract_decoder.decode_input(input_data)
        analysis = pool_analyzer.analyze_pool_interaction(input_data, value_eth)

        if protocol:
            return {
                "is_defi": True,
                "protocol_name": protocol["protocol"],
                "protocol_type": protocol["type"],
                "protocol_risk": protocol.get("risk_level", "low"),
                "action": method_info.get("action", analysis["resolved_action"]),
                "action_category": method_info.get("category", "unknown"),
                "method_name": method_info.get("name", "unknown"),
                "decoded": decoded_input,
                "value_eth": value_eth,
                "value_usd": analysis["estimated_value_usd"],
                "is_flash_loan": method_info.get("category") == "flash_loan",
            }

        return {
            "is_defi": False,
            "protocol_name": "Unknown Contract",
            "protocol_type": "Unknown",
            "action": method_info.get("action", decoded_input["method_name"]),
            "action_category": method_info.get("category", "unknown"),
            "method_name": method_info.get("name", decoded_input["method_name"]),
            "decoded": decoded_input,
            "value_eth": value_eth,
            "value_usd": price_oracle.convert_to_usd(value_eth, "ETH"),
            "is_flash_loan": False,
        }

    def decode_token_event(self, topics: List[str], data: str) -> Optional[Dict[str, Any]]:
        """Decodes ERC-20, ERC-721, and ERC-1155 token events from log topics."""
        if not topics:
            return None

        t0 = topics[0].lower() if topics else ""

        try:
            if t0 == ERC20_TRANSFER.lower():
                if len(topics) == 3:
                    # ERC-20 Transfer
                    from_addr = "0x" + topics[1][-40:]
                    to_addr = "0x" + topics[2][-40:]
                    val = int(data, 16) / (10**18) if data and data != "0x" else 0
                    return {
                        "type": "ERC-20 Transfer",
                        "standard": "ERC-20",
                        "from": from_addr,
                        "to": to_addr,
                        "value": val,
                    }
                elif len(topics) == 4:
                    # ERC-721 Transfer (includes tokenId in topic 3)
                    from_addr = "0x" + topics[1][-40:]
                    to_addr = "0x" + topics[2][-40:]
                    token_id = int(topics[3], 16)
                    return {
                        "type": "ERC-721 Transfer (NFT)",
                        "standard": "ERC-721",
                        "from": from_addr,
                        "to": to_addr,
                        "token_id": token_id,
                    }

            elif t0 == ERC20_APPROVAL.lower() and len(topics) >= 3:
                owner = "0x" + topics[1][-40:]
                spender = "0x" + topics[2][-40:]
                val = int(data, 16) if data and data != "0x" else 0
                return {
                    "type": "Token Approval",
                    "standard": "ERC-20",
                    "owner": owner,
                    "spender": spender,
                    "value": "Unlimited" if val > 2**250 else val / (10**18),
                }

            elif t0 == ERC1155_SINGLE.lower() and len(topics) >= 4:
                operator = "0x" + topics[1][-40:]
                from_addr = "0x" + topics[2][-40:]
                to_addr = "0x" + topics[3][-40:]
                # data contains token_id and amount
                return {
                    "type": "ERC-1155 Single Transfer",
                    "standard": "ERC-1155",
                    "operator": operator,
                    "from": from_addr,
                    "to": to_addr,
                }

            elif t0 == ERC1155_BATCH.lower() and len(topics) >= 4:
                operator = "0x" + topics[1][-40:]
                from_addr = "0x" + topics[2][-40:]
                to_addr = "0x" + topics[3][-40:]
                return {
                    "type": "ERC-1155 Batch Transfer",
                    "standard": "ERC-1155",
                    "operator": operator,
                    "from": from_addr,
                    "to": to_addr,
                }
        except Exception:
            return None

        return None

    def _decode_method(self, input_data: str) -> Dict[str, Any]:
        """Decodes the function selector from input data."""
        if not input_data or len(input_data) < 10:
            if input_data == "0x":
                return {"name": "native_transfer", "action": "Native ETH Transfer", "category": "transfer"}
            return {"name": "unknown", "action": "Unknown Method", "category": "unknown"}

        selector = input_data[:10].lower()
        if selector in DEFI_METHODS:
            return DEFI_METHODS[selector]

        return {"name": f"unknown_{selector}", "action": "Contract Interaction", "category": "unknown"}

    def detect_flash_loan(self, input_data: str, value_eth: float) -> Dict[str, Any]:
        """Specifically detects flash loan transactions."""
        method = self._decode_method(input_data)
        is_flash = method.get("category") == "flash_loan"
        return {
            "is_flash_loan": is_flash,
            "method": method.get("name", "unknown"),
            "estimated_loan_value_usd": price_oracle.convert_to_usd(value_eth, "ETH") if is_flash else 0,
            "risk_level": "high" if is_flash else "none",
        }

    def classify_defi_action(self, input_data: str) -> str:
        """Returns the DeFi action category for a given input."""
        method = self._decode_method(input_data)
        return method.get("category", "unknown")


defi_decoder = DeFiDecoderService()
