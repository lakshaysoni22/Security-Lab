import secrets
from typing import Dict, Tuple

# Token family storage: family_id -> { active_token, used_tokens: set }
TOKEN_FAMILIES = {} # type: Dict[str, Dict]
REFRESH_TO_FAMILY = {} # refresh_token -> family_id

class RefreshTokenService:
    def create_family(self) -> Tuple[str, str]:
        """Creates a new token family and generates the initial active refresh token."""
        family_id = f"fam_{secrets.token_hex(8)}"
        initial_token = f"ref_{secrets.token_hex(16)}"
        
        TOKEN_FAMILIES[family_id] = {
            "active_token": initial_token,
            "used_tokens": set()
        }
        REFRESH_TO_FAMILY[initial_token] = family_id
        return family_id, initial_token

    def rotate_token(self, old_token: str) -> Tuple[str, str]:
        """Performs token rotation. Returns (new_refresh_token, new_access_token)."""
        family_id = REFRESH_TO_FAMILY.get(old_token)
        if not family_id:
            raise Exception("Invalid refresh token")
            
        family = TOKEN_FAMILIES.get(family_id)
        if not family:
            raise Exception("Token family not found")
            
        # Check for token reuse (replay attack detection)
        if old_token in family["used_tokens"]:
            # Critical Replay Attack! Revoke the entire family
            TOKEN_FAMILIES.pop(family_id, None)
            raise Exception("Token reuse detected! Revoking token family.")
            
        if family["active_token"] != old_token:
            raise Exception("Outdated refresh token")
            
        # Generate new tokens
        new_refresh = f"ref_{secrets.token_hex(16)}"
        new_access = f"acc_{secrets.token_hex(16)}"
        
        # Mark old token as used and set new active token
        family["used_tokens"].add(old_token)
        family["active_token"] = new_refresh
        
        # Link new token to family
        REFRESH_TO_FAMILY[new_refresh] = family_id
        
        return new_refresh, new_access

refresh_service = RefreshTokenService()
