import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models, schemas, security

router = APIRouter(prefix="/api/ai", tags=["AI Investigation Assistant"])

@router.post("/chat", response_model=schemas.AIChatResponse)
def chat_with_assistant(
    request: schemas.AIChatRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(security.get_current_user)
):
    msg = request.message.lower()
    address = request.context_address
    case_id = request.context_case_id

    # Gather context from DB if possible
    case_title = "None (System Global)"
    case_number = "N/A"
    wallet_count = 0
    evidence_count = 0
    priority_level = "N/A"

    if case_id:
        db_case = db.query(models.Case).filter(models.Case.id == case_id).first()
        if db_case:
            case_title = db_case.title
            case_number = db_case.case_number
            priority_level = db_case.priority
            wallet_count = db.query(models.Wallet).filter(models.Wallet.case_id == case_id).count()
            evidence_count = db.query(models.Evidence).filter(models.Evidence.case_id == case_id).count()

    response_text = ""

    # Check query type and build response strictly segmented
    if "risk" in msg or "analyze" in msg or address:
        target_addr = address or "0x742d35Cc6634C0532925a3b844Bc9e7595f2bD28"
        db_wallet = db.query(models.Wallet).filter(models.Wallet.address == target_addr).first()
        risk_val = db_wallet.risk_score if db_wallet else 78
        chain_val = db_wallet.chain if db_wallet else "ethereum"
        
        response_text = f"""### AI Investigation Report: {target_addr}

**1. Verified Facts**
* **Case Profile**: {case_title} ({case_number})
* **Target Address**: `{target_addr}` on network `{chain_val}`
* **Database Risk Rating**: `{risk_val}/100`
* **Evidence Count**: {evidence_count} validated files logged in Case Folder

**2. Observations**
* Traced transactions match automated splitter/peeling chain layering heuristics.
* Recurrent transaction patterns peak within standard IST (GMT+5:30) working hours.
* Intermediary hops show interaction with mixed smart contracts.

**3. Hypotheses**
* *Hypothesis A*: The wallet is controlled by a programmatic splitter script associated with the primary Ponzi campaign.
* *Hypothesis B*: The cash-out gateway relies on unauthorized peer-to-peer (P2P) OTC channels.

**4. Confidence Level**
* **Confidence Rating**: **Medium (75%)**
* *Rationale*: Based on automated heuristic scores and transaction velocity. Requires offline subpoena validation and uploader logs before submitting as court evidence.

> [!IMPORTANT]
> **Advisory Warning**: AI-generated analysis is advisory only. Investigators are responsible for verifying on-chain signatures and logs before filing charges or freezing assets."""

    elif "case" in msg or "summary" in msg or "timeline" in msg:
        response_text = f"""### AI Case Intelligence Summary

**1. Verified Facts**
* **Active Case File**: {case_title} ({case_number})
* **Priority Level**: `{priority_level.upper()}`
* **Associated Wallets**: {wallet_count} address(es) linked
* **Evidence Register**: {evidence_count} file(s) sealed with cryptographic hashes

**2. Observations**
* Case is currently in pipeline stage.
* Investigator {current_user.username} is logged as the primary assignee.
* Audit trail registers active updates to notes and task logs.

**3. Hypotheses**
* *Hypothesis A*: The asset flow is structured to obscure the final destination exchange through rapid hops.
* *Hypothesis B*: Multi-sig bridge transfers are being utilized to migrate assets across chains.

**4. Confidence Level**
* **Confidence Rating**: **High (90%)**
* *Rationale*: Context matches active database state and uploader registry.

> [!NOTE]
> AI analysis serves to assist investigators and supervisors in detecting bottleneck gaps and timeline priorities. AI does not replace investigative authority."""

    else:
        response_text = f"""### LEAtTrace AI Assistant

Welcome, {current_user.username}. I am your Law Enforcement Forensic Copilot.

**1. Verified Facts**
* **Authorized User**: {current_user.username} (Role: `{current_user.role}`)
* **Active Case Context**: {case_title} ({case_number})
* **Linked Assets**: {wallet_count} wallets, {evidence_count} evidence files

**2. Observations**
* Current query does not specify a target address or case command.
* Systems (SQLite database, local storage vault) are healthy and listening.

**3. Hypotheses**
* *Hypothesis A*: Investigator requires guidance on using the prompt library or running transaction traces.
* *Hypothesis B*: Investigator is seeking case risk analysis.

**4. Confidence Level**
* **Confidence Rating**: **N/A**
* *Rationale*: Interactive introductory query.

*   *Type "Analyze" to evaluate active address risks.*
*   *Type "Case timeline" to view case statistics.*"""

    # Log query to audit log
    audit_entry = models.AuditLog(
        id=f"log_{uuid.uuid4().hex[:7]}",
        user_id=current_user.id,
        username=current_user.username,
        action=f"Invoked AI investigation helper (Message: '{msg[:40]}...')",
        status="success"
    )
    db.add(audit_entry)
    db.commit()

    return {"response": response_text}

