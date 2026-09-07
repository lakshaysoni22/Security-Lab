from typing import Dict, Any
from .abi_service import abi_engine

class SmartContractDecoder:
    def decode_input(self, input_data: str) -> Dict[str, Any]:
        """Translates raw input bytes to method signatures."""
        if not input_data or input_data == "0x":
            return {"is_contract_call": False, "method_name": "Ether Transfer"}
            
        method_sig = input_data[:10].lower()
        method_name = abi_engine.resolve_selector(method_sig)
        
        return {
            "is_contract_call": True,
            "method_selector": method_sig,
            "method_name": method_name
        }

contract_decoder = SmartContractDecoder()
