"""
LEAtTrace IAM — Permission Matrix.

Complete permission matrix with 12 enterprise roles and granular permissions
covering all platform modules: cases, blockchain, evidence, AI, SIEM, admin.
"""

from typing import Set, Dict, List


# ===================================================================
# 12 Enterprise Roles
# ===================================================================

ROLE_HIERARCHY = {
    "super_admin": {"admin", "auditor"},
    "admin": {"senior_investigator", "soc_manager"},
    "soc_manager": {"soc_analyst", "incident_responder"},
    "senior_investigator": {"investigator", "digital_forensic_analyst"},
    "investigator": {"read_only"},
    "blockchain_analyst": {"read_only"},
    "threat_intel_analyst": {"read_only"},
    "digital_forensic_analyst": {"read_only"},
    "soc_analyst": {"read_only"},
    "incident_responder": {"read_only"},
    "auditor": {"read_only"},
    "read_only": set(),
}

# ===================================================================
# Granular Permission Matrix
# ===================================================================

ROLE_PERMISSIONS: Dict[str, Set[str]] = {
    "read_only": {
        "case:view", "blockchain:view", "reports:view",
        "dashboard:view", "graph:view",
    },

    "investigator": {
        "case:create", "case:edit", "case:assign",
        "blockchain:scan", "blockchain:analyze",
        "evidence:view", "evidence:upload",
        "watchlist:view", "watchlist:add",
        "alert:view", "alert:acknowledge",
    },

    "senior_investigator": {
        "evidence:delete", "evidence:export", "evidence:chain_of_custody",
        "case:close", "case:reopen",
        "incident:write", "incident:assign",
        "report:generate", "report:sign",
    },

    "blockchain_analyst": {
        "blockchain:scan", "blockchain:analyze", "blockchain:deep_trace",
        "graph:create", "graph:export",
        "watchlist:view", "watchlist:add", "watchlist:remove",
        "case:view", "evidence:view",
    },

    "threat_intel_analyst": {
        "threat:view", "threat:create", "threat:analyze",
        "ioc:create", "ioc:delete",
        "stix:import", "stix:export",
        "case:view", "evidence:view",
    },

    "digital_forensic_analyst": {
        "evidence:view", "evidence:upload", "evidence:analyze",
        "evidence:chain_of_custody", "evidence:export",
        "yara:scan", "yara:create",
        "case:view",
    },

    "soc_analyst": {
        "siem:view", "siem:query",
        "incident:view", "incident:triage",
        "alert:view", "alert:acknowledge", "alert:escalate",
        "sigma:view",
    },

    "incident_responder": {
        "incident:view", "incident:triage", "incident:resolve", "incident:escalate",
        "siem:view", "siem:query",
        "alert:view", "alert:acknowledge",
        "case:create",
    },

    "soc_manager": {
        "siem:admin", "siem:configure",
        "incident:resolve", "incident:assign",
        "alert:configure",
        "sigma:create", "sigma:delete",
        "team:manage",
    },

    "auditor": {
        "audit:view", "audit:export",
        "compliance:view", "compliance:report",
        "user:view", "session:view",
        "policy:view",
    },

    "admin": {
        "user:invite", "user:deactivate", "user:edit_role",
        "settings:edit", "settings:security",
        "api_key:create", "api_key:revoke",
        "policy:create", "policy:edit",
        "system:backup",
    },

    "super_admin": {
        "system:admin", "system:maintenance",
        "secret:rotate", "key:rotate",
        "user:delete", "user:create",
        "oauth:manage", "oauth:client_register",
        "ai:train", "ai:deploy", "ai:configure",
        "database:admin",
    },
}


# ===================================================================
# Enhanced RBAC Engine
# ===================================================================

class PermissionMatrix:
    """Enterprise RBAC with hierarchical role resolution and permission checking."""

    def get_all_roles_in_hierarchy(self, role: str) -> Set[str]:
        """Traverses the role hierarchy to get all inherited roles."""
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

    def get_all_permissions(self, role: str) -> Set[str]:
        """Returns the complete set of permissions for a role including inherited."""
        active_roles = self.get_all_roles_in_hierarchy(role)
        permissions = set()
        for active_role in active_roles:
            role_perms = ROLE_PERMISSIONS.get(active_role, set())
            permissions.update(role_perms)
        return permissions

    def has_permission(self, role: str, permission: str) -> bool:
        """Checks if a role has a specific permission."""
        return permission in self.get_all_permissions(role)

    def has_any_permission(self, role: str, permissions: List[str]) -> bool:
        """Checks if a role has any of the specified permissions."""
        all_perms = self.get_all_permissions(role)
        return any(p in all_perms for p in permissions)

    def has_all_permissions(self, role: str, permissions: List[str]) -> bool:
        """Checks if a role has all of the specified permissions."""
        all_perms = self.get_all_permissions(role)
        return all(p in all_perms for p in permissions)

    def list_roles(self) -> List[Dict]:
        """Returns all roles with their direct permissions and hierarchy."""
        result = []
        for role in ROLE_HIERARCHY:
            result.append({
                "role": role,
                "inherits_from": sorted(ROLE_HIERARCHY.get(role, set())),
                "direct_permissions": sorted(ROLE_PERMISSIONS.get(role, set())),
                "total_permissions": len(self.get_all_permissions(role)),
            })
        return result

    def get_role_details(self, role: str) -> Dict:
        """Returns detailed information about a specific role."""
        if role not in ROLE_HIERARCHY and role not in ROLE_PERMISSIONS:
            return {"error": f"Role '{role}' not found"}
        return {
            "role": role,
            "hierarchy": sorted(self.get_all_roles_in_hierarchy(role)),
            "inherits_from": sorted(ROLE_HIERARCHY.get(role, set())),
            "direct_permissions": sorted(ROLE_PERMISSIONS.get(role, set())),
            "all_permissions": sorted(self.get_all_permissions(role)),
            "total_permissions": len(self.get_all_permissions(role)),
        }


permission_matrix = PermissionMatrix()
