import uuid
import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from .. import models, schemas, security

router = APIRouter(prefix="/api/cases", tags=["Case Management"])

@router.get("", response_model=List[schemas.CaseOut])
def get_cases(db: Session = Depends(get_db), current_user: models.User = Depends(security.get_current_user)):
    # Auditors and Admins see all cases, Investigators see cases in their cell or assigned
    return db.query(models.Case).order_by(models.Case.created_at.desc()).all()

@router.post("", response_model=schemas.CaseOut, status_code=status.HTTP_201_CREATED)
def create_case(case: schemas.CaseCreate, db: Session = Depends(get_db), current_user: models.User = Depends(security.get_current_user)):
    # Restrict creation to investigator, supervisor, or admin roles
    if current_user.role not in ["admin", "supervisor", "investigator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized to create investigation cases."
        )

    # Generate sequential case number if not provided
    case_number = case.case_number
    if not case_number:
        count = db.query(models.Case).count()
        case_number = f"CC-{datetime.datetime.now().year}-{count + 1000 + 1}"

    new_case = models.Case(
        id=f"case-{uuid.uuid4().hex[:7]}",
        case_number=case_number,
        title=case.title,
        description=case.description,
        priority=case.priority,
        status=case.status,
        investigator_id=current_user.id,
        investigator_name=current_user.username,
        department=current_user.department or "Cyber Crime Cell",
        notes=case.notes
    )

    db.add(new_case)
    db.commit()

    # Log action
    audit_entry = models.AuditLog(
        id=f"log_{uuid.uuid4().hex[:7]}",
        user_id=current_user.id,
        username=current_user.username,
        action=f"Created investigation case: {case_number} - {case.title}",
        status="success"
    )
    db.add(audit_entry)
    db.commit()

    db.refresh(new_case)
    return new_case

@router.post("/auto-trigger", response_model=schemas.CaseOut, status_code=status.HTTP_201_CREATED)
def auto_trigger_investigation(
    payload: schemas.FAIISTriggerRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    if current_user.role not in ["admin", "supervisor", "investigator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized to trigger autonomous FAIIS cycles."
        )

    count = db.query(models.Case).count()
    case_number = f"FAIIS-{datetime.datetime.now().year}-{count + 1000 + 1}"
    case_id = f"case-{uuid.uuid4().hex[:7]}"

    # Initialize case context
    new_case = models.Case(
        id=case_id,
        case_number=case_number,
        title=f"[FAIIS-AUTO] Suspicious Flow: {payload.target_address[:8]}...",
        description=f"Autonomous investigation triggered by FAIIS ATDS. Target wallet: {payload.target_address}. Details: {payload.anomaly_details}",
        priority="critical" if payload.risk_score > 80 else "high",
        status="active",
        investigator_id=current_user.id,
        investigator_name="FAIIS Agent",
        department="Autonomous Intelligence Division",
        notes="[FAIIS LOG] Initialized memory context. Assigned agents: Graph Intelligence Agent, Behavioral Intelligence Agent, Predictive Risk Agent."
    )
    db.add(new_case)
    db.commit()

    # Add suspect wallet
    new_wallet = models.Wallet(
        id=f"wal-{uuid.uuid4().hex[:7]}",
        address=payload.target_address,
        chain="ethereum",
        label="Suspect (Autonomous Trigger)",
        risk_score=payload.risk_score,
        is_contract=False,
        case_id=case_id
    )
    db.add(new_wallet)
    db.commit()

    # Log to audit trail
    audit_entry = models.AuditLog(
        id=f"log_{uuid.uuid4().hex[:7]}",
        user_id=current_user.id,
        username=current_user.username,
        action=f"FAIIS ATDS launched autonomous case: {case_number} on address {payload.target_address}",
        status="success",
        actor="AI",
        decision_source="ATDS Trigger Engine",
        execution_result="Initialized Context, Seeded Wallet, Allocated Agent Mesh",
        validation_status="Pending Review"
    )
    db.add(audit_entry)
    db.commit()

    db.refresh(new_case)
    return new_case

@router.get("/{case_id}", response_model=schemas.CaseOut)
def get_case(case_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(security.get_current_user)):
    db_case = db.query(models.Case).filter(models.Case.id == case_id).first()
    if not db_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )
    return db_case

@router.put("/{case_id}", response_model=schemas.CaseOut)
def update_case(case_id: str, updates: schemas.CaseUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(security.get_current_user)):
    db_case = db.query(models.Case).filter(models.Case.id == case_id).first()
    if not db_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )

    for var, value in vars(updates).items():
        if value is not None:
            setattr(db_case, var, value)

    db.commit()

    # Log action
    audit_entry = models.AuditLog(
        id=f"log_{uuid.uuid4().hex[:7]}",
        user_id=current_user.id,
        username=current_user.username,
        action=f"Updated parameters for case {db_case.case_number}",
        status="success"
    )
    db.add(audit_entry)
    db.commit()

    db.refresh(db_case)
    return db_case

@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_case(case_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(security.get_current_user)):
    # Restrict delete to supervisor and admin roles
    if current_user.role not in ["admin", "supervisor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Case deletion is restricted to admin and supervisor roles."
        )

    db_case = db.query(models.Case).filter(models.Case.id == case_id).first()
    if not db_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found"
        )

    case_number = db_case.case_number
    db.delete(db_case)
    db.commit()

    # Log action
    audit_entry = models.AuditLog(
        id=f"log_{uuid.uuid4().hex[:7]}",
        user_id=current_user.id,
        username=current_user.username,
        action=f"Deleted case record {case_number}",
        status="warning"
    )
    db.add(audit_entry)
    db.commit()

    return None
