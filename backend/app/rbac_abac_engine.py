"""
Role-Based and Attribute-Based Access Control (RBAC/ABAC) Engine
Enterprise-grade permission management for LEAtTrace
"""
import uuid
import datetime
from typing import List, Dict, Set, Optional, Any, Tuple
from enum import Enum
from pydantic import BaseModel
from functools import lru_cache

# ============= Enums =============

class Permission(str, Enum):
    """All available permissions in LEAtTrace."""
    
    # User Management
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_ASSIGN_ROLE = "user:assign_role"
    USER_REVOKE_MFA = "user:revoke_mfa"
    
    # Case Management
    CASE_CREATE = "case:create"
    CASE_READ = "case:read"
    CASE_UPDATE = "case:update"
    CASE_DELETE = "case:delete"
    CASE_CLOSE = "case:close"
    CASE_REASSIGN = "case:reassign"
    
    # Evidence Management
    EVIDENCE_UPLOAD = "evidence:upload"
    EVIDENCE_READ = "evidence:read"
    EVIDENCE_DOWNLOAD = "evidence:download"
    EVIDENCE_DELETE = "evidence:delete"
    EVIDENCE_VERIFY = "evidence:verify"
    
    # Wallet/Address Management
    WALLET_ADD = "wallet:add"
    WALLET_READ = "wallet:read"
    WALLET_UPDATE = "wallet:update"
    WALLET_DELETE = "wallet:delete"
    WALLET_TAG = "wallet:tag"
    WALLET_LABEL = "wallet:label"
    
    # Analytics & Reporting
    REPORT_CREATE = "report:create"
    REPORT_READ = "report:read"
    REPORT_DELETE = "report:delete"
    REPORT_EXPORT = "report:export"
    
    # System Administration
    SYSTEM_CONFIG = "system:config"
    SYSTEM_BACKUP = "system:backup"
    SYSTEM_RESTORE = "system:restore"
    SYSTEM_AUDIT_LOG = "system:audit_log"
    
    # Security & Access Control
    SECURITY_AUDIT = "security:audit"
    SECURITY_MFA_MANAGE = "security:mfa_manage"
    SECURITY_API_KEY = "security:api_key"
    
    # Audit & Compliance
    AUDIT_READ = "audit:read"
    AUDIT_EXPORT = "audit:export"
    
    # SIEM & Threat Detection
    SIEM_READ = "siem:read"
    SIEM_CONFIG = "siem:config"
    THREAT_DETECTION = "threat:detection"

class Department(str, Enum):
    """Government departments with access to system."""
    I4C = "i4c"  # Indian Cyber Crime
    CBI = "cbi"  # Central Bureau of Investigation
    NIA = "nia"  # National Investigation Agency
    CYBER_CELL = "cyber_cell"  # Cyber Crime Cell
    ADMIN = "admin"  # System administration

class CaseClassification(str, Enum):
    """Case classification levels."""
    OPEN = "open"
    CONFIDENTIAL = "confidential"
    SECRET = "secret"
    TOP_SECRET = "top_secret"

# ============= Models =============

class RolePermissionMapping(BaseModel):
    """Define permissions for a role."""
    role: str
    permissions: Set[Permission]
    description: str
    created_at: datetime.datetime

class Role(BaseModel):
    """Enhanced role model with hierarchy."""
    id: str
    name: str
    description: str
    
    # Role hierarchy
    inherits_from: Optional[List[str]] = None  # Parent roles
    
    # Permissions
    permissions: Set[Permission]
    
    # Constraints
    department: Optional[Department] = None
    max_cases_per_user: Optional[int] = None  # -1 = unlimited
    can_manage_users: bool = False
    can_access_all_cases: bool = False
    
    # Metadata
    active: bool = True
    created_at: datetime.datetime
    updated_at: datetime.datetime

class UserAttributes(BaseModel):
    """User attributes for ABAC evaluation."""
    user_id: str
    username: str
    email: str
    
    # Department and clearance
    department: Department
    clearance_level: int  # 1-5, where 5 is highest
    
    # Roles
    roles: List[str]
    
    # Context attributes
    team_id: Optional[str] = None
    supervisor_id: Optional[str] = None
    assigned_cases: List[str] = []
    
    # Location and device
    current_location: Optional[Dict[str, Any]] = None
    device_id: Optional[str] = None
    is_device_trusted: bool = False
    
    # Time-based attributes
    last_login: Optional[datetime.datetime] = None
    is_active: bool = True
    
    # Session attributes
    session_age_hours: float = 0
    is_mfa_verified: bool = False

class ResourceAttributes(BaseModel):
    """Resource attributes for ABAC evaluation."""
    resource_id: str
    resource_type: str  # case, evidence, wallet, report
    
    # Ownership
    owner_id: Optional[str] = None
    assigned_to: List[str] = []  # Users assigned to this resource
    
    # Department level
    department: Optional[Department] = None
    
    # Classification
    classification: CaseClassification = CaseClassification.OPEN
    sensitivity_score: int = 1  # 1-10
    
    # Related data
    related_users: List[str] = []
    related_cases: List[str] = []

class EnvironmentAttributes(BaseModel):
    """Environment attributes for ABAC evaluation."""
    current_time: datetime.datetime
    day_of_week: int  # 0-6
    is_business_hours: bool
    location: Optional[str] = None
    network_type: str  # internal, vpn, external
    is_geo_blocked: bool = False

class AccessPolicy(BaseModel):
    """ABAC policy for access control."""
    id: str
    name: str
    description: str
    
    # Condition evaluation
    conditions: Dict[str, Any]  # Key-value pairs to evaluate
    effect: str  # allow, deny
    
    # Scope
    applies_to_roles: List[str] = []
    applies_to_resources: List[str] = []
    applies_to_operations: List[str] = []
    
    # Priority
    priority: int = 100  # Higher number = higher priority
    
    active: bool = True
    created_at: datetime.datetime

# ============= RBAC Engine =============

class RBACEngine:
    """Role-Based Access Control Engine."""
    
    # Predefined roles
    PREDEFINED_ROLES = {
        "admin": Role(
            id="role_admin",
            name="Administrator",
            description="Full system access",
            permissions=set(Permission.__members__.values()),
            can_manage_users=True,
            can_access_all_cases=True,
            active=True,
            created_at=datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None),
            updated_at=datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        ),
        "supervisor": Role(
            id="role_supervisor",
            name="Supervisor",
            description="Manages investigators and cases",
            permissions={
                Permission.USER_READ, Permission.USER_ASSIGN_ROLE,
                Permission.CASE_CREATE, Permission.CASE_READ, Permission.CASE_UPDATE,
                Permission.CASE_REASSIGN, Permission.EVIDENCE_READ, Permission.EVIDENCE_VERIFY,
                Permission.REPORT_CREATE, Permission.REPORT_READ, Permission.AUDIT_READ,
                Permission.SIEM_READ, Permission.THREAT_DETECTION
            },
            can_manage_users=False,
            can_access_all_cases=True,
            active=True,
            created_at=datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None),
            updated_at=datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        ),
        "investigator": Role(
            id="role_investigator",
            name="Investigator",
            description="Conducts investigations on assigned cases",
            permissions={
                Permission.CASE_CREATE, Permission.CASE_READ, Permission.CASE_UPDATE,
                Permission.EVIDENCE_UPLOAD, Permission.EVIDENCE_READ, Permission.EVIDENCE_DOWNLOAD,
                Permission.WALLET_ADD, Permission.WALLET_READ, Permission.WALLET_UPDATE,
                Permission.REPORT_CREATE, Permission.REPORT_READ, Permission.REPORT_EXPORT
            },
            active=True,
            created_at=datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None),
            updated_at=datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        ),
        "analyst": Role(
            id="role_analyst",
            name="Analyst",
            description="Analyzes data and generates reports",
            permissions={
                Permission.CASE_READ, Permission.EVIDENCE_READ, Permission.EVIDENCE_DOWNLOAD,
                Permission.WALLET_READ, Permission.REPORT_CREATE, Permission.REPORT_READ,
                Permission.REPORT_EXPORT, Permission.SIEM_READ
            },
            active=True,
            created_at=datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None),
            updated_at=datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        ),
        "auditor": Role(
            id="role_auditor",
            name="Auditor",
            description="Audit and compliance officer",
            permissions={
                Permission.CASE_READ, Permission.EVIDENCE_READ, Permission.AUDIT_READ,
                Permission.AUDIT_EXPORT, Permission.REPORT_READ, Permission.SECURITY_AUDIT,
                Permission.SYSTEM_AUDIT_LOG
            },
            active=True,
            created_at=datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None),
            updated_at=datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        ),
        "readonly": Role(
            id="role_readonly",
            name="Read-Only User",
            description="View-only access to cases and reports",
            permissions={
                Permission.CASE_READ, Permission.EVIDENCE_READ, Permission.REPORT_READ,
                Permission.WALLET_READ
            },
            active=True,
            created_at=datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None),
            updated_at=datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        )
    }
    
    def __init__(self):
        """Initialize RBAC engine."""
        self.roles = self.PREDEFINED_ROLES.copy()
    
    def has_permission(
        self,
        user_roles: List[str],
        required_permission: Permission
    ) -> bool:
        """Check if user has required permission."""
        for role_name in user_roles:
            role = self.roles.get(role_name)
            if role and required_permission in role.permissions:
                return True
        
        return False
    
    def get_user_permissions(self, user_roles: List[str]) -> Set[Permission]:
        """Get all permissions for user based on roles."""
        permissions = set()
        
        for role_name in user_roles:
            role = self.roles.get(role_name)
            if role:
                permissions.update(role.permissions)
        
        return permissions
    
    def add_role(self, role: Role) -> bool:
        """Add new role."""
        if role.name in self.roles:
            return False
        
        self.roles[role.name] = role
        return True
    
    def add_permission_to_role(self, role_name: str, permission: Permission) -> bool:
        """Add permission to role."""
        role = self.roles.get(role_name)
        if not role:
            return False
        
        role.permissions.add(permission)
        return True

# ============= ABAC Engine =============

class ABACEngine:
    """Attribute-Based Access Control Engine."""
    
    def __init__(self):
        """Initialize ABAC engine."""
        self.policies: Dict[str, AccessPolicy] = {}
    
    def add_policy(self, policy: AccessPolicy) -> bool:
        """Add ABAC policy."""
        if policy.id in self.policies:
            return False
        
        self.policies[policy.id] = policy
        return True
    
    def evaluate_policy(
        self,
        user_attrs: UserAttributes,
        resource_attrs: ResourceAttributes,
        env_attrs: EnvironmentAttributes,
        operation: str
    ) -> Tuple[bool, List[str]]:
        """
        Evaluate if access should be allowed based on attributes.
        Returns: (allow, reason_strings)
        """
        reasons = []
        applicable_policies = self._get_applicable_policies(
            user_attrs.roles,
            resource_attrs.resource_type,
            operation
        )
        
        # Sort by priority (higher first)
        applicable_policies.sort(key=lambda p: p.priority, reverse=True)
        
        for policy in applicable_policies:
            if not policy.active:
                continue
            
            if self._evaluate_conditions(policy.conditions, user_attrs, resource_attrs, env_attrs):
                if policy.effect == "deny":
                    reasons.append(f"Denied by policy: {policy.name}")
                    return False, reasons
                elif policy.effect == "allow":
                    reasons.append(f"Allowed by policy: {policy.name}")
                    return True, reasons
        
        # Default deny if no matching allow policy
        reasons.append("No matching allow policy found")
        return False, reasons
    
    def _get_applicable_policies(
        self,
        user_roles: List[str],
        resource_type: str,
        operation: str
    ) -> List[AccessPolicy]:
        """Get policies applicable to user, resource, and operation."""
        applicable = []
        
        for policy in self.policies.values():
            # Check if policy applies to user roles
            if policy.applies_to_roles and not any(r in user_roles for r in policy.applies_to_roles):
                continue
            
            # Check if policy applies to resource
            if policy.applies_to_resources and resource_type not in policy.applies_to_resources:
                continue
            
            # Check if policy applies to operation
            if policy.applies_to_operations and operation not in policy.applies_to_operations:
                continue
            
            applicable.append(policy)
        
        return applicable
    
    def _evaluate_conditions(
        self,
        conditions: Dict[str, Any],
        user_attrs: UserAttributes,
        resource_attrs: ResourceAttributes,
        env_attrs: EnvironmentAttributes
    ) -> bool:
        """Evaluate condition expressions."""
        for key, expected_value in conditions.items():
            # Simple condition evaluation (can be extended with complex logic)
            if key == "department":
                if user_attrs.department != expected_value:
                    return False
            elif key == "min_clearance":
                if user_attrs.clearance_level < expected_value:
                    return False
            elif key == "resource_classification":
                if resource_attrs.classification != expected_value:
                    return False
            elif key == "business_hours_only":
                if expected_value and not env_attrs.is_business_hours:
                    return False
            elif key == "requires_trusted_device":
                if expected_value and not user_attrs.is_device_trusted:
                    return False
            elif key == "requires_mfa":
                if expected_value and not user_attrs.is_mfa_verified:
                    return False
        
        return True

# ============= Access Control Decision Engine =============

class AccessControlEngine:
    """Combined RBAC and ABAC access control."""
    
    def __init__(self):
        """Initialize access control engine."""
        self.rbac = RBACEngine()
        self.abac = ABACEngine()
        self._init_default_policies()
    
    def _init_default_policies(self):
        """Initialize default ABAC policies."""
        # Policy: Only investigators and supervisors can access confidential cases
        policy1 = AccessPolicy(
            id="policy_confidential_access",
            name="Confidential Case Access",
            description="Only investigators and supervisors can access confidential cases",
            conditions={
                "resource_classification": CaseClassification.CONFIDENTIAL
            },
            effect="allow",
            applies_to_roles=["investigator", "supervisor", "admin"],
            applies_to_resources=["case"],
            priority=200,
            active=True,
            created_at=datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        )
        self.abac.add_policy(policy1)
        
        # Policy: Require MFA for sensitive operations
        policy2 = AccessPolicy(
            id="policy_sensitive_mfa",
            name="Sensitive Operations MFA",
            description="MFA required for evidence download and case closure",
            conditions={"requires_mfa": True},
            effect="allow",
            applies_to_resources=["evidence"],
            applies_to_operations=["download"],
            priority=150,
            active=True,
            created_at=datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        )
        self.abac.add_policy(policy2)
    
    def check_access(
        self,
        user_attrs: UserAttributes,
        resource_attrs: ResourceAttributes,
        env_attrs: EnvironmentAttributes,
        operation: str,
        required_permission: Permission
    ) -> Tuple[bool, str]:
        """
        Check if user can access resource for operation.
        Returns: (allow, reason)
        """
        # Step 1: RBAC check
        rbac_allowed = self.rbac.has_permission(user_attrs.roles, required_permission)
        if not rbac_allowed:
            return False, f"Permission denied: {required_permission}"
        
        # Step 2: ABAC check
        abac_allowed, abac_reasons = self.abac.evaluate_policy(
            user_attrs, resource_attrs, env_attrs, operation
        )
        
        if not abac_allowed:
            return False, " | ".join(abac_reasons)
        
        return True, "Access granted"
    
    def check_case_access(
        self,
        user_id: str,
        user_roles: List[str],
        user_department: Department,
        case_id: str,
        case_owner_id: str,
        case_assigned_to: List[str],
        case_department: Department
    ) -> Tuple[bool, str]:
        """Check if user can access specific case."""
        # Admins can access all cases
        if "admin" in user_roles:
            return True, "Admin access"
        
        # Supervisors can access all cases in their department
        if "supervisor" in user_roles and user_department == case_department:
            return True, "Supervisor department access"
        
        # Investigators can access assigned cases
        if user_id == case_owner_id or user_id in case_assigned_to:
            return True, "Case owner/assignee access"
        
        # Otherwise deny
        return False, "Case access denied"
