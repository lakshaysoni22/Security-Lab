from typing import List, Dict, Set

# Role hierarchies: child -> parent (inherits permissions)
ROLE_HIERARCHY = {
    "super_admin": {"admin", "auditor"},
    "admin": {"senior_investigator", "soc_manager"},
    "soc_manager": {"soc_analyst"},
    "senior_investigator": {"investigator"},
    "investigator": {"read_only"},
    "soc_analyst": {"read_only"},
    "auditor": {"read_only"},
    "read_only": set()
}

# Permissions mappings
ROLE_PERMISSIONS = {
    "read_only": {"case:view", "blockchain:view", "reports:view"},
    "investigator": {"case:create", "case:edit", "blockchain:scan", "evidence:view"},
    "senior_investigator": {"evidence:upload", "evidence:delete", "incident:write"},
    "soc_analyst": {"siem:view", "incident:view"},
    "soc_manager": {"siem:admin", "incident:resolve"},
    "auditor": {"audit:view"},
    "admin": {"user:invite", "settings:edit"},
    "super_admin": {"system:admin", "secret:rotate"}
}

class RBACEngine:
    def get_all_roles_in_hierarchy(self, role: str) -> Set[str]:
        """Traverses the role hierarchy recursively to extract all inherited roles."""
        roles = {role}
        queue = [role]
        
        while queue:
            current = queue.pop(0)
            inherited = ROLE_HIERARCHY.get(current, set())
            for child in inherited:
                if child not in roles:
                    roles.add(child)
                    queue.append(child)
        return roles

    def has_permission(self, role: str, permission: str) -> bool:
        """Checks if a role has a specific permission directly or via inheritance."""
        active_roles = self.get_all_roles_in_hierarchy(role)
        
        for active_role in active_roles:
            permissions = ROLE_PERMISSIONS.get(active_role, set())
            if permission in permissions:
                return True
        return False

rbac_engine = RBACEngine()
