import datetime
import uuid
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="investigator")  # admin, supervisor, investigator, analyst, auditor, readonly
    is_active = Column(Boolean, default=True)
    mfa_enabled = Column(Boolean, default=False)
    mfa_secret = Column(String, nullable=True)
    oauth_provider = Column(String, nullable=True)
    oauth_id = Column(String, nullable=True)
    department = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

class Case(Base):
    __tablename__ = "cases"

    id = Column(String, primary_key=True, index=True)
    case_number = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(String, default="medium")  # low, medium, high, critical
    status = Column(String, default="open")  # open, active, suspended, closed
    investigator_id = Column(String, ForeignKey("users.id"))
    investigator_name = Column(String, nullable=True)
    department = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)

    # Relationships
    wallets = relationship("Wallet", back_populates="case", cascade="all, delete-orphan")
    evidence = relationship("Evidence", back_populates="case", cascade="all, delete-orphan")

class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(String, primary_key=True, index=True)
    address = Column(String, index=True, nullable=False)
    chain = Column(String, nullable=False)  # bitcoin, ethereum, solana
    label = Column(String, nullable=True)
    tags = Column(String, nullable=True)  # Comma-separated list
    risk_score = Column(Integer, default=0)
    is_contract = Column(Boolean, default=False)
    case_id = Column(String, ForeignKey("cases.id"))

    # Relationships
    case = relationship("Case", back_populates="wallets")

class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(String, primary_key=True, index=True)
    case_id = Column(String, ForeignKey("cases.id"), nullable=False)
    filename = Column(String, nullable=False)
    file_hash = Column(String, nullable=False)  # SHA-256 integrity signature
    file_size = Column(Integer, nullable=False)
    uploaded_by = Column(String, nullable=False)
    upload_time = Column(DateTime, default=datetime.datetime.utcnow)
    description = Column(Text, nullable=True)
    storage_path = Column(String, nullable=False)

    # Relationships
    case = relationship("Case", back_populates="evidence")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, nullable=True)
    username = Column(String, nullable=False)
    action = Column(String, nullable=False)
    ip_address = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String, default="success")  # success, warning, failure
    actor = Column(String, default="Human")  # Human, AI, System
    decision_source = Column(String, nullable=True)  # e.g., "HITL Override", "SOIS Loop", "User Login"
    execution_result = Column(Text, nullable=True)
    validation_status = Column(String, default="Verified")  # Verified, Pending, Bypassed
    hash = Column(String, nullable=True)
    prev_hash = Column(String, nullable=True)

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String, primary_key=True, index=True)
    chain = Column(String, nullable=False)
    address = Column(String, nullable=False)
    alias = Column(String, nullable=True)
    type = Column(String, nullable=False)  # balance, incoming, outgoing
    threshold = Column(Float, nullable=False)
    status = Column(String, default="Active")  # Active, Triggered, Suspended
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    message = Column(Text, nullable=True)
    severity = Column(String, default="medium")  # low, medium, high, critical
    is_read = Column(Boolean, default=False)

class WatchlistEntry(Base):
    __tablename__ = "watchlist"

    id = Column(String, primary_key=True, index=True)
    address = Column(String, nullable=False)
    chain = Column(String, nullable=False)
    alias = Column(String, nullable=True)
    risk_score = Column(Integer, default=0)
    status = Column(String, default="Monitored")  # Monitored, Suspended
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Decision(Base):
    __tablename__ = "decisions"

    decision_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, index=True)
    input = Column(Text, nullable=True)
    output = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)
    risk_level = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class GovernanceLog(Base):
    __tablename__ = "governance_logs"

    log_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    action = Column(Text, nullable=True)
    allowed = Column(Boolean, default=True)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class SystemState(Base):
    __tablename__ = "system_state"

    state_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    module = Column(String, nullable=True)
    status = Column(String, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    refresh_token = Column(String, index=True, nullable=False)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)

class ChainOfCustody(Base):
    __tablename__ = "chain_of_custody"

    id = Column(String, primary_key=True, index=True)
    evidence_id = Column(String, ForeignKey("evidence.id"), nullable=False)
    action = Column(String, nullable=False)  # UPLOADED, TRANSFERRED, SEALED, EXPORTED
    performed_by = Column(String, nullable=False)
    recipient = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    notes = Column(Text, nullable=True)
    prev_hash = Column(String, nullable=True)
    hash_signature = Column(String, nullable=True)

class EvidenceSignature(Base):
    __tablename__ = "evidence_signatures"

    id = Column(String, primary_key=True, index=True)
    evidence_id = Column(String, ForeignKey("evidence.id"), nullable=False)
    signer_name = Column(String, nullable=False)
    signature = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    public_key_pem = Column(Text, nullable=False)

# --- Cryptographical Log Ledger Chaining ---
from sqlalchemy import event, text
import hashlib

@event.listens_for(AuditLog, 'before_insert')
def chain_audit_log(mapper, connection, target):
    # Fetch last hash
    try:
        # Execute query using the connection
        row = connection.execute(
            text("SELECT hash FROM audit_logs ORDER BY timestamp DESC LIMIT 1")
        ).fetchone()
        prev_hash = row[0] if row and row[0] else "0"
    except Exception as e:
        prev_hash = "0"

    if not target.id:
        target.id = f"log_{uuid.uuid4().hex[:7]}"

    if not target.timestamp:
        target.timestamp = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)

    timestamp_str = target.timestamp.isoformat()
    raw_str = f"{prev_hash}_{target.id}_{target.action}_{timestamp_str}_{target.status}"
    
    target.prev_hash = prev_hash
    target.hash = hashlib.sha256(raw_str.encode('utf-8')).hexdigest()


class BlockIndexCheckpoint(Base):
    __tablename__ = "block_index_checkpoints"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    chain = Column(String, index=True, nullable=False)
    block_number = Column(Integer, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class IndexedTransaction(Base):
    __tablename__ = "indexed_transactions"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    chain = Column(String, index=True, nullable=False)
    tx_hash = Column(String, index=True, unique=True, nullable=False)
    block_number = Column(Integer, index=True, nullable=False)
    from_address = Column(String, index=True, nullable=False)
    to_address = Column(String, index=True, nullable=False)
    value = Column(Float, nullable=False)
    gas_used = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False)


class IndexedTokenTransfer(Base):
    __tablename__ = "indexed_token_transfers"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    chain = Column(String, index=True, nullable=False)
    tx_hash = Column(String, index=True, nullable=False)
    contract_address = Column(String, index=True, nullable=False)
    from_address = Column(String, index=True, nullable=False)
    to_address = Column(String, index=True, nullable=False)
    value = Column(Float, nullable=False)
    token_type = Column(String, nullable=False)  # ERC-20, ERC-721, ERC-1155
    symbol = Column(String, nullable=True)
    timestamp = Column(DateTime, nullable=False)


class EntityLabel(Base):
    __tablename__ = "entity_labels"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    address = Column(String, index=True, unique=True, nullable=False)
    label = Column(String, nullable=False)
    category = Column(String, nullable=False)  # exchange, sanctioned, scam, retail
    source = Column(String, default="Local Compliance")
    confidence_score = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


# ===================================================================
# IAM Platform Tables
# ===================================================================

class OAuthClient(Base):
    __tablename__ = "oauth_clients"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = Column(String, unique=True, index=True, nullable=False)
    client_secret_hash = Column(String, nullable=False)
    client_name = Column(String, nullable=True)
    redirect_uris = Column(Text, nullable=False)  # JSON array
    grant_types = Column(Text, default='{"authorization_code","refresh_token"}')  # JSON array
    scopes = Column(String, default="openid profile email roles")
    description = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_confidential = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class TrustedDevice(Base):
    __tablename__ = "trusted_devices"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    device_fingerprint = Column(String, index=True, nullable=False)
    device_name = Column(String, default="Unknown Device")
    os_name = Column(String, nullable=True)
    browser_name = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    last_used = Column(DateTime, default=datetime.datetime.utcnow)
    is_trusted = Column(Boolean, default=True)
    trust_expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class RecoveryCode(Base):
    __tablename__ = "recovery_codes"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    code_hash = Column(String, nullable=False)
    is_used = Column(Boolean, default=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class SecurityPolicy(Base):
    __tablename__ = "security_policies"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    policy_name = Column(String, unique=True, nullable=False)
    policy_type = Column(String, nullable=False)  # abac, password, session, network
    policy_rules = Column(Text, nullable=False)  # JSON rules
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=100)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class PasswordHistory(Base):
    __tablename__ = "password_history"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class APIKey(Base):
    __tablename__ = "api_keys"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    key_hash = Column(String, unique=True, nullable=False)
    key_prefix = Column(String, nullable=False)  # First 8 chars for identification
    name = Column(String, nullable=False)
    scopes = Column(String, default="read")
    is_active = Column(Boolean, default=True)
    last_used = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


# ===================================================================
# AI Platform Tables
# ===================================================================

class MLModel(Base):
    __tablename__ = "ml_models"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    model_name = Column(String, index=True, nullable=False)
    model_version = Column(String, nullable=False)
    model_type = Column(String, nullable=False)  # classification, regression, clustering, anomaly
    framework = Column(String, default="sklearn")  # sklearn, xgboost, lightgbm, pytorch
    file_path = Column(String, nullable=True)
    feature_dim = Column(Integer, default=0)
    status = Column(String, default="trained")  # trained, deployed, champion, challenger, archived
    accuracy = Column(Float, nullable=True)
    precision_score = Column(Float, nullable=True)
    recall_score = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    training_samples = Column(Integer, nullable=True)
    metadata_json = Column(Text, nullable=True)  # JSON blob for extra metrics
    trained_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class VectorDocument(Base):
    __tablename__ = "vector_documents"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    doc_type = Column(String, index=True, nullable=False)  # wallet, transaction, case, evidence, threat, alert
    source_id = Column(String, index=True, nullable=False)
    content = Column(Text, nullable=False)
    embedding_model = Column(String, default="all-MiniLM-L6-v2")
    embedding_version = Column(Integer, default=1)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class AIExperiment(Base):
    __tablename__ = "ai_experiments"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    experiment_name = Column(String, index=True, nullable=False)
    run_id = Column(String, unique=True, nullable=False)
    run_name = Column(String, nullable=True)
    status = Column(String, default="RUNNING")  # RUNNING, COMPLETED, FAILED
    params_json = Column(Text, nullable=True)
    metrics_json = Column(Text, nullable=True)
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)


class TrainingJob(Base):
    __tablename__ = "training_jobs"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    model_name = Column(String, nullable=False)
    job_type = Column(String, default="full")  # full, incremental, evaluation
    status = Column(String, default="pending")  # pending, running, completed, failed
    trigger = Column(String, default="manual")  # manual, scheduled, drift
    samples_count = Column(Integer, nullable=True)
    metrics_json = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


# ===================================================================
# Blockchain Intelligence Tables
# ===================================================================

class WalletProfile(Base):
    __tablename__ = "wallet_profiles"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    address = Column(String, unique=True, index=True, nullable=False)
    chain = Column(String, default="ethereum")
    wallet_type = Column(String, default="eoa")  # eoa, contract, multisig, proxy
    entity_name = Column(String, nullable=True)
    entity_category = Column(String, nullable=True)  # exchange, defi, mixer, unknown
    cluster_id = Column(String, nullable=True, index=True)
    risk_score = Column(Integer, default=0)
    trust_score = Column(Integer, default=50)
    total_tx_count = Column(Integer, default=0)
    total_volume_eth = Column(Float, default=0.0)
    first_seen = Column(DateTime, nullable=True)
    last_seen = Column(DateTime, nullable=True)
    is_contract = Column(Boolean, default=False)
    is_sanctioned = Column(Boolean, default=False)
    mixer_exposure_pct = Column(Float, default=0.0)
    tags = Column(Text, nullable=True)  # JSON array
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class WalletCluster(Base):
    __tablename__ = "wallet_clusters"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    cluster_id = Column(String, unique=True, index=True, nullable=False)
    cluster_name = Column(String, nullable=True)
    entity_name = Column(String, nullable=True)
    heuristic_type = Column(String, default="co_spending")  # co_spending, behavioral, graph, exchange
    confidence = Column(Float, default=0.5)
    member_count = Column(Integer, default=0)
    total_volume_eth = Column(Float, default=0.0)
    risk_score = Column(Integer, default=0)
    addresses_json = Column(Text, nullable=True)  # JSON array of addresses
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class WalletRelationship(Base):
    __tablename__ = "wallet_relationships"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    source_address = Column(String, index=True, nullable=False)
    target_address = Column(String, index=True, nullable=False)
    relationship_type = Column(String, default="transfer")  # transfer, co_spend, bridge, funding
    tx_count = Column(Integer, default=1)
    total_value_eth = Column(Float, default=0.0)
    first_interaction = Column(DateTime, nullable=True)
    last_interaction = Column(DateTime, nullable=True)
    relationship_score = Column(Float, default=0.0)
    chain = Column(String, default="ethereum")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class CrossChainEvent(Base):
    __tablename__ = "cross_chain_events"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    source_chain = Column(String, nullable=False)
    destination_chain = Column(String, nullable=False)
    source_tx_hash = Column(String, index=True, nullable=True)
    destination_tx_hash = Column(String, nullable=True)
    bridge_protocol = Column(String, nullable=True)
    sender_address = Column(String, index=True, nullable=False)
    receiver_address = Column(String, nullable=True)
    token_symbol = Column(String, default="ETH")
    amount = Column(Float, default=0.0)
    bridge_fee = Column(Float, default=0.0)
    status = Column(String, default="detected")  # detected, confirmed, failed
    risk_score = Column(Integer, default=0)
    timestamp = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class BridgeEvent(Base):
    __tablename__ = "bridge_events"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    bridge_name = Column(String, nullable=False)
    bridge_address = Column(String, index=True, nullable=False)
    source_chain = Column(String, nullable=False)
    destination_chain = Column(String, nullable=False)
    tx_hash = Column(String, index=True, nullable=False)
    user_address = Column(String, index=True, nullable=False)
    token_in = Column(String, default="ETH")
    token_out = Column(String, default="WETH")
    amount_in = Column(Float, default=0.0)
    amount_out = Column(Float, default=0.0)
    timestamp = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class DecodedContract(Base):
    __tablename__ = "decoded_contracts"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    address = Column(String, index=True, nullable=False)
    chain = Column(String, default="ethereum")
    contract_name = Column(String, nullable=True)
    contract_type = Column(String, default="unknown")  # erc20, erc721, erc1155, defi, bridge, proxy
    is_proxy = Column(Boolean, default=False)
    implementation_address = Column(String, nullable=True)
    abi_json = Column(Text, nullable=True)
    protocol_name = Column(String, nullable=True)
    verified = Column(Boolean, default=False)
    risk_level = Column(String, default="unknown")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class RiskScore(Base):
    __tablename__ = "risk_scores"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    target_type = Column(String, nullable=False)  # wallet, transaction, token, bridge, contract, entity
    target_id = Column(String, index=True, nullable=False)  # address or tx_hash
    chain = Column(String, default="ethereum")
    overall_score = Column(Integer, default=0)
    mixer_score = Column(Integer, default=0)
    sanctions_score = Column(Integer, default=0)
    counterparty_score = Column(Integer, default=0)
    behavioral_score = Column(Integer, default=0)
    bridge_score = Column(Integer, default=0)
    fraud_probability = Column(Float, default=0.0)
    aml_risk = Column(Float, default=0.0)
    confidence = Column(Float, default=0.5)
    explanation = Column(Text, nullable=True)
    evidence_json = Column(Text, nullable=True)  # JSON array of supporting evidence
    scored_at = Column(DateTime, default=datetime.datetime.utcnow)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class BlockchainTimeline(Base):
    __tablename__ = "blockchain_timelines"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    investigation_id = Column(String, index=True, nullable=True)
    address = Column(String, index=True, nullable=False)
    event_type = Column(String, nullable=False)  # transfer, bridge, mixer, defi, contract_call
    event_description = Column(String, nullable=True)
    tx_hash = Column(String, nullable=True)
    chain = Column(String, default="ethereum")
    value_eth = Column(Float, default=0.0)
    counterparty = Column(String, nullable=True)
    risk_flag = Column(Boolean, default=False)
    timestamp = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Report(Base):
    """Investigation report metadata. Content stored as text; future: binary PDF attachment."""
    __tablename__ = "reports"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String, ForeignKey("cases.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    summary = Column(Text, nullable=True)
    conclusions = Column(Text, nullable=True)
    generated_by = Column(String, nullable=True)      # username of investigator
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Relationship
    case = relationship("Case", foreign_keys=[case_id])


# ─── TAXII / STIX Models ──────────────────────────────────────────────────────

class TaxiiSyncState(Base):
    """Tracks incremental sync state per TAXII collection."""
    __tablename__ = "taxii_sync_states"

    id             = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    collection_id  = Column(String, unique=True, nullable=False, index=True)
    last_synced_at = Column(DateTime, nullable=True)
    objects_synced = Column(Integer, default=0)
    error_count    = Column(Integer, default=0)
    api_root_url   = Column(String, nullable=True)
    created_at     = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at     = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class StixIndicator(Base):
    """Persisted STIX 2.1 Indicator objects from TAXII sync."""
    __tablename__ = "stix_indicators"

    id           = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    stix_id      = Column(String, unique=True, nullable=False, index=True)  # indicator--UUID
    name         = Column(String, nullable=True)
    pattern      = Column(Text, nullable=True)
    pattern_type = Column(String, default="stix")
    valid_from   = Column(DateTime, nullable=True)
    valid_until  = Column(DateTime, nullable=True)
    collection_id = Column(String, nullable=True, index=True)
    confidence   = Column(Integer, nullable=True)
    raw_json     = Column(Text, nullable=True)
    created_at   = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at   = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


# ─── Sanctions Models ─────────────────────────────────────────────────────────

class SanctionsEntry(Base):
    """A single sanctioned entity (address/entity) from a real sanctions provider."""
    __tablename__ = "sanctions_entries"

    id            = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    address       = Column(String, nullable=True, index=True)     # crypto address if applicable
    entity_name   = Column(String, nullable=True)                 # individual/entity name
    program       = Column(String, nullable=True)                 # e.g. "IRAN", "RUSSIA"
    list_type     = Column(String, nullable=False)                # "OFAC_SDN", "EU_CONSOLIDATED"
    source_id     = Column(String, nullable=True)                 # UID from the source list
    entry_type    = Column(String, nullable=True)                 # "individual", "entity", "vessel"
    raw_data      = Column(Text, nullable=True)                   # original XML/JSON
    hash_key      = Column(String, nullable=True, index=True)     # for deduplication
    created_at    = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at    = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class SanctionsSyncLog(Base):
    """Audit log of each sanctions sync run."""
    __tablename__ = "sanctions_sync_logs"

    id              = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    provider        = Column(String, nullable=False)   # "OFAC_SDN", "EU_CONSOLIDATED"
    status          = Column(String, nullable=False)   # "success", "error", "skipped"
    entries_added   = Column(Integer, default=0)
    entries_updated = Column(Integer, default=0)
    file_hash       = Column(String, nullable=True)    # SHA-256 of downloaded file
    error_message   = Column(Text, nullable=True)
    synced_at       = Column(DateTime, default=datetime.datetime.utcnow)


# ─── SIEM Models ──────────────────────────────────────────────────────────────

class SecurityIncident(Base):
    """A SIEM security incident record — DB-persisted, never hardcoded."""
    __tablename__ = "security_incidents"

    id               = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    severity         = Column(String, nullable=False, default="medium")  # critical/high/medium/low
    category         = Column(String, nullable=True)
    mitre_technique  = Column(String, nullable=True)
    message          = Column(Text, nullable=False)
    source           = Column(String, nullable=True)
    analyst_assigned = Column(String, nullable=True)
    status           = Column(String, nullable=False, default="open")  # open/acknowledged/closed
    source_ip        = Column(String, nullable=True)
    related_address  = Column(String, nullable=True)
    raw_event        = Column(Text, nullable=True)
    created_at       = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at       = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    closed_at        = Column(DateTime, nullable=True)




class AuthCode(Base):
    """
    OAuth 2.0 Authorization codes with PKCE support and TTL expiry.
    Replaces in-memory AUTH_CODES dict in oauth_server.py.
    """
    __tablename__ = "auth_codes"

    id                   = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    code                 = Column(String, unique=True, nullable=False, index=True)
    client_id            = Column(String, nullable=False)
    user_id              = Column(String, nullable=False)
    code_challenge       = Column(String, nullable=True)     # PKCE
    code_challenge_method = Column(String, nullable=True)    # "S256" or "plain"
    scopes               = Column(String, nullable=True)
    expires_at           = Column(DateTime, nullable=False)  # 10-minute TTL
    used                 = Column(Boolean, default=False)    # single-use enforcement
    created_at           = Column(DateTime, default=datetime.datetime.utcnow)


