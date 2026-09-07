import sys
import os
backend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
sys.path.insert(0, backend_path)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import hashlib

# Connect directly to database
engine = create_engine(f"sqlite:///{os.path.join(backend_path, 'LEAtTrace.db')}")
Session = sessionmaker(bind=engine)
session = Session()

# Import models
from app import models

logs = session.query(models.AuditLog).order_by(models.AuditLog.timestamp.asc()).all()

prev_hash = "0"
for idx, log in enumerate(logs):
    timestamp_str = log.timestamp.isoformat() if log.timestamp else ""
    raw_str = f"{prev_hash}_{log.id}_{log.action}_{timestamp_str}_{log.status}"
    computed_hash = hashlib.sha256(raw_str.encode('utf-8')).hexdigest()
    
    print(f"--- Log {idx} ({log.id}) ---")
    print(f"Action: {log.action}")
    print(f"Timestamp: {timestamp_str}")
    print(f"Stored prev_hash: {log.prev_hash}")
    print(f"Computed prev_hash: {prev_hash}")
    print(f"Stored hash: {log.hash}")
    print(f"Computed hash: {computed_hash}")
    print(f"Matches: {log.hash == computed_hash}")
    print(f"Raw string used: '{raw_str}'")
    
    prev_hash = log.hash
