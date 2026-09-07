import yaml
from typing import Dict, Any, List

class SigmaEngine:
    def parse_rule(self, rule_yaml: str) -> Dict[str, Any]:
        """Parses and validates a standard YAML Sigma rule."""
        try:
            rule_data = yaml.safe_load(rule_yaml)
            # Enforce minimal schema checks
            if not rule_data.get("title") or not rule_data.get("detection"):
                raise ValueError("Missing title or detection fields in Sigma rule")
            return rule_data
        except Exception as e:
            raise ValueError(f"Failed to parse Sigma rule: {str(e)}")

    def evaluate_rule(self, rule_data: Dict[str, Any], event_log: Dict[str, Any]) -> bool:
        """Evaluates whether an event log matches the parsed Sigma rule conditions."""
        detection = rule_data.get("detection", {})
        selection = detection.get("selection", {})
        
        # Simple logical AND matches on all selection criteria
        for field, expected_val in selection.items():
            actual_val = event_log.get(field)
            if actual_val is None:
                return False
                
            # If expected value is a list, match any element (OR behavior for list values)
            if isinstance(expected_val, list):
                if actual_val not in expected_val:
                    return False
            else:
                if str(actual_val).lower() != str(expected_val).lower():
                    return False
                    
        return True

sigma_engine = SigmaEngine()
