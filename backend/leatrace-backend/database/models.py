from sqlalchemy import Column, String, Float, Boolean, DateTime, Text, JSON
import datetime
import uuid
from database.connection import Base

class User(Base):
    __tablename__ = "users"

    user_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="user")
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
