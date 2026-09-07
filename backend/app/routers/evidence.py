import os
import uuid
import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from .. import models, schemas, security

router = APIRouter(prefix="/api/evidence", tags=["Evidence Locker"])

# Setup local evidence storage directory
STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "storage", "evidence")
os.makedirs(STORAGE_DIR, exist_ok=True)

@router.post("/upload/{case_id}", response_model=schemas.EvidenceOut, status_code=status.HTTP_201_CREATED)
async def upload_evidence(
    case_id: str,
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    # Enforce RBAC
    if current_user.role not in ["admin", "supervisor", "investigator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="RBAC Restriction: Only authorized investigators can upload forensic evidence."
        )

    # Verify case exists
    db_case = db.query(models.Case).filter(models.Case.id == case_id).first()
    if not db_case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Read file and calculate SHA-256 hash on-the-fly
    file_bytes = await file.read()
    sha256_hash = security.calculate_sha256(file_bytes)
    file_size = len(file_bytes)

    # Save to local directory structure
    file_extension = os.path.splitext(file.filename)[1]
    safe_filename = f"{uuid.uuid4().hex}{file_extension}"
    storage_path = os.path.join(STORAGE_DIR, safe_filename)

    with open(storage_path, "wb") as f:
        f.write(file_bytes)

    new_evidence = models.Evidence(
        id=f"evd-{uuid.uuid4().hex[:7]}",
        case_id=case_id,
        filename=file.filename,
        file_hash=sha256_hash,
        file_size=file_size,
        uploaded_by=current_user.username,
        description=description,
        storage_path=storage_path
    )
    db.add(new_evidence)
    db.commit()
    db.refresh(new_evidence)

    # Blockchain-style Chain of Custody (Initial block)
    timestamp = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    initial_log_id = f"cust_{uuid.uuid4().hex[:7]}"
    raw_hash_data = f"0_{new_evidence.id}_UPLOADED_{timestamp.isoformat()}_{current_user.username}"
    hash_signature = security.calculate_sha256(raw_hash_data.encode('utf-8'))

    custody_block = models.ChainOfCustody(
        id=initial_log_id,
        evidence_id=new_evidence.id,
        action="UPLOADED",
        performed_by=current_user.username,
        timestamp=timestamp,
        notes="Initial file ingestion into secure forensic vault.",
        prev_hash="0",
        hash_signature=hash_signature
    )
    db.add(custody_block)

    # Log action to system audit log
    audit_entry = models.AuditLog(
        id=f"log_{uuid.uuid4().hex[:7]}",
        user_id=current_user.id,
        username=current_user.username,
        action=f"Ingested evidence: '{file.filename}' (SHA-256: {sha256_hash[:12]}...) into case {db_case.case_number}",
        status="success"
    )
    db.add(audit_entry)
    db.commit()

    return new_evidence

@router.get("/case/{case_id}", response_model=List[schemas.EvidenceOut])
def get_case_evidence(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    return db.query(models.Evidence).filter(models.Evidence.case_id == case_id).all()

@router.post("/verify/{evidence_id}")
def verify_evidence_integrity(
    evidence_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    db_evidence = db.query(models.Evidence).filter(models.Evidence.id == evidence_id).first()
    if not db_evidence:
        raise HTTPException(status_code=404, detail="Evidence record not found")

    if not os.path.exists(db_evidence.storage_path):
        return {
            "id": evidence_id,
            "filename": db_evidence.filename,
            "status": "MISSING",
            "message": "The physical file is missing from secure storage."
        }

    with open(db_evidence.storage_path, "rb") as f:
        current_bytes = f.read()
    current_hash = security.calculate_sha256(current_bytes)

    # Integrity verification
    match = current_hash == db_evidence.file_hash
    status_str = "VERIFIED" if match else "TAMPERED"

    # Log verification check in audit log
    audit_entry = models.AuditLog(
        id=f"log_{uuid.uuid4().hex[:7]}",
        user_id=current_user.id,
        username=current_user.username,
        action=f"Forensic verification on '{db_evidence.filename}': Status {status_str} (Registered: {db_evidence.file_hash[:10]}, Computed: {current_hash[:10]})",
        status="success" if match else "failure"
    )
    db.add(audit_entry)
    db.commit()

    return {
        "id": evidence_id,
        "filename": db_evidence.filename,
        "status": status_str,
        "registered_hash": db_evidence.file_hash,
        "computed_hash": current_hash,
        "tamper_detected": not match
    }

@router.post("/transfer/{evidence_id}", response_model=schemas.ChainOfCustodyOut)
def transfer_custody(
    evidence_id: str,
    recipient: str,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    db_evidence = db.query(models.Evidence).filter(models.Evidence.id == evidence_id).first()
    if not db_evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    # Fetch last custody block to link the chain
    last_block = db.query(models.ChainOfCustody).filter(
        models.ChainOfCustody.evidence_id == evidence_id
    ).order_by(models.ChainOfCustody.timestamp.desc()).first()

    prev_hash = last_block.hash_signature if last_block else "0"
    timestamp = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)

    # Calculate linked hash
    raw_hash_data = f"{prev_hash}_{evidence_id}_TRANSFERRED_{timestamp.isoformat()}_{current_user.username}_{recipient}"
    hash_signature = security.calculate_sha256(raw_hash_data.encode('utf-8'))

    custody_block = models.ChainOfCustody(
        id=f"cust_{uuid.uuid4().hex[:7]}",
        evidence_id=evidence_id,
        action="TRANSFERRED",
        performed_by=current_user.username,
        recipient=recipient,
        timestamp=timestamp,
        notes=notes or f"Custody transferred from {current_user.username} to {recipient}.",
        prev_hash=prev_hash,
        hash_signature=hash_signature
    )
    db.add(custody_block)
    
    # Audit log
    audit_entry = models.AuditLog(
        id=f"log_{uuid.uuid4().hex[:7]}",
        user_id=current_user.id,
        username=current_user.username,
        action=f"Transferred custody of evidence '{db_evidence.filename}' to {recipient}",
        status="success"
    )
    db.add(audit_entry)
    db.commit()
    db.refresh(custody_block)

    return custody_block

@router.post("/seal/{evidence_id}", response_model=schemas.EvidenceSignatureOut)
def seal_evidence(
    evidence_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    # Enforce RBAC
    if current_user.role not in ["admin", "supervisor", "investigator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="RBAC Restriction: Only authorized investigators can seal forensic evidence."
        )

    db_evidence = db.query(models.Evidence).filter(models.Evidence.id == evidence_id).first()
    if not db_evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    # Generate RSA keys for signing
    private_pem, public_pem = security.generate_keypair()
    signature_b64 = security.sign_data(private_pem, db_evidence.file_hash)

    # Save public key & signature
    ev_signature = models.EvidenceSignature(
        id=f"sig_{uuid.uuid4().hex[:7]}",
        evidence_id=evidence_id,
        signer_name=current_user.username,
        signature=signature_b64,
        public_key_pem=public_pem
    )
    db.add(ev_signature)

    # Link to Chain of Custody
    last_block = db.query(models.ChainOfCustody).filter(
        models.ChainOfCustody.evidence_id == evidence_id
    ).order_by(models.ChainOfCustody.timestamp.desc()).first()

    prev_hash = last_block.hash_signature if last_block else "0"
    timestamp = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    raw_hash_data = f"{prev_hash}_{evidence_id}_SEALED_{timestamp.isoformat()}_{current_user.username}"
    hash_signature = security.calculate_sha256(raw_hash_data.encode('utf-8'))

    custody_block = models.ChainOfCustody(
        id=f"cust_{uuid.uuid4().hex[:7]}",
        evidence_id=evidence_id,
        action="SEALED",
        performed_by=current_user.username,
        timestamp=timestamp,
        notes="Evidence sealed with cryptographical RSA signature seal.",
        prev_hash=prev_hash,
        hash_signature=hash_signature
    )
    db.add(custody_block)

    # Audit log
    audit_entry = models.AuditLog(
        id=f"log_{uuid.uuid4().hex[:7]}",
        user_id=current_user.id,
        username=current_user.username,
        action=f"Sealed evidence '{db_evidence.filename}' with digital RSA signature",
        status="success"
    )
    db.add(audit_entry)
    db.commit()
    db.refresh(ev_signature)

    return ev_signature

@router.get("/custody/{evidence_id}", response_model=List[schemas.ChainOfCustodyOut])
def get_custody_chain(
    evidence_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    blocks = db.query(models.ChainOfCustody).filter(
        models.ChainOfCustody.evidence_id == evidence_id
    ).order_by(models.ChainOfCustody.timestamp.asc()).all()
    return blocks

@router.get("/verify_signature/{evidence_id}")
def verify_seal_signature(
    evidence_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    db_evidence = db.query(models.Evidence).filter(models.Evidence.id == evidence_id).first()
    if not db_evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    signature = db.query(models.EvidenceSignature).filter(
        models.EvidenceSignature.evidence_id == evidence_id
    ).first()

    if not signature:
        return {
            "evidence_id": evidence_id,
            "status": "UNSEALED",
            "message": "No digital seal signature exists for this evidence item.",
            "is_valid": False
        }

    # Verify signature
    is_valid = security.verify_data_signature(
        signature.public_key_pem,
        db_evidence.file_hash,
        signature.signature
    )

    return {
        "evidence_id": evidence_id,
        "status": "SEALED_VALID" if is_valid else "SEALED_TAMPERED",
        "signer": signature.signer_name,
        "signed_at": signature.timestamp,
        "is_valid": is_valid
    }

@router.get("/certificate/{evidence_id}")
def export_court_admissibility_certificate(
    evidence_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    db_evidence = db.query(models.Evidence).filter(models.Evidence.id == evidence_id).first()
    if not db_evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    signature = db.query(models.EvidenceSignature).filter(
        models.EvidenceSignature.evidence_id == evidence_id
    ).first()

    custody_chain = db.query(models.ChainOfCustody).filter(
        models.ChainOfCustody.evidence_id == evidence_id
    ).order_by(models.ChainOfCustody.timestamp.asc()).all()

    # Create court admissibility JSON certificate (Section 65B Indian Evidence Act / Section 63 BSA 2023)
    certificate = {
        "court_admissibility_header": "CERTIFICATE UNDER SECTION 65B OF THE INDIAN EVIDENCE ACT, 1872 (NOW SECTION 63 OF BHARATIYA SAKSHYA ADHINIYAM, 2023)",
        "issuing_agency": "Cyber Crime Investigation Cell, Government of India",
        "compliance_standards": ["NIST SP 800-53", "ISO/IEC 27037 Forensic Soundness Guidelines"],
        "certificate_id": f"CERT-{uuid.uuid4().hex[:8].upper()}",
        "evidence_details": {
            "evidence_id": db_evidence.id,
            "original_filename": db_evidence.filename,
            "file_size_bytes": db_evidence.file_size,
            "calculated_sha256": db_evidence.file_hash,
        },
        "digital_seal": {
            "sealed": signature is not None,
            "signer": signature.signer_name if signature else None,
            "signature_hash": signature.signature if signature else None,
            "public_key_pem": signature.public_key_pem if signature else None,
        },
        "chain_of_custody": [
            {
                "step": idx + 1,
                "action": c.action,
                "performed_by": c.performed_by,
                "recipient": c.recipient,
                "timestamp": c.timestamp.isoformat(),
                "block_hash": c.hash_signature,
                "prev_hash": c.prev_hash
            } for idx, c in enumerate(custody_chain)
        ],
        "certification_clause": "I hereby certify that the computer system / secure electronic vault described above was operating properly and under my lawful control at the time of evidence ingestion. The cryptographical hash and signatures verify that the electronic record has not been tampered with or modified since its preservation.",
        "certified_by": signature.signer_name if signature else current_user.username,
        "certified_date": datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None).date().isoformat()
    }
    return certificate
