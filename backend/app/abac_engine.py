from typing import Dict, Any

class ABACEngine:
    def evaluate_policy(self, user_attributes: Dict[str, Any], resource_attributes: Dict[str, Any], environment_attributes: Dict[str, Any]) -> bool:
        """Evaluates whether an investigator has access based on user, resource, and environmental contexts."""
        # 1. Security Clearance Check
        user_clearance = user_attributes.get("clearance_level", 1)
        resource_clearance = resource_attributes.get("clearance_required", 1)
        if user_clearance < resource_clearance:
            return False
            
        # 2. Department Lock check (e.g. Cybercrime vs Forensic unit isolation)
        user_dept = user_attributes.get("department")
        resource_dept = resource_attributes.get("department_restriction")
        if resource_dept and user_dept != resource_dept:
            # Exception: Super Admin can bypass department isolation
            if user_attributes.get("role") != "super_admin":
                return False
                
        # 3. Geo-location restriction (e.g. access restricted to office region)
        user_region = user_attributes.get("region", "IN")
        allowed_regions = resource_attributes.get("allowed_regions")
        if allowed_regions and user_region not in allowed_regions:
            return False
            
        # 4. Safe Working Hours (e.g. 06:00 to 22:00)
        access_hour = environment_attributes.get("current_hour", 12)
        is_restricted_resource = resource_attributes.get("restricted_hours_only", False)
        if is_restricted_resource:
            if not (6 <= access_hour <= 22):
                return False
                
        return True

abac_engine = ABACEngine()
