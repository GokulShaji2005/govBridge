from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Any
from sqlmodel import Session, select
from db import engine
from models_db import Consent, ConsentItem

router = APIRouter(prefix="/consent", tags=["Consent Management"])

class GrantConsentRequest(BaseModel):
    citizen_id: str
    purpose: str
    data_scope: List[str]  # e.g. ["identity", "tax", "address", "registry"]

class RevokeConsentRequest(BaseModel):
    citizen_id: str
    purpose: str

def grant_consent_db(citizen_id: str, purpose: str, data_scope: List[str]) -> Dict[str, Any]:
    with Session(engine) as session:
        # Revoke any existing active consents for this citizen and purpose
        existing_list = session.exec(
            select(Consent).where(
                Consent.citizen_id == citizen_id,
                Consent.purpose == purpose,
                Consent.status == "ACTIVE"
            )
        ).all()
        for e in existing_list:
            e.status = "SUPERSEDED"
            session.add(e)
            
        consent = Consent(citizen_id=citizen_id, purpose=purpose, status="ACTIVE")
        session.add(consent)
        session.commit()
        session.refresh(consent)
        
        c_id = consent.id
        c_purpose = consent.purpose
        
        for scope in data_scope:
            item = ConsentItem(consent_id=c_id, scope_name=scope)
            session.add(item)
        session.commit()
        
        return {"id": c_id, "purpose": c_purpose, "status": "ACTIVE"}

def check_consent_db(citizen_id: str, purpose: str) -> bool:
    with Session(engine) as session:
        consent = session.exec(
            select(Consent).where(
                Consent.citizen_id == citizen_id,
                Consent.purpose == purpose,
                Consent.status == "ACTIVE"
            )
        ).first()
        return consent is not None

def revoke_consent_db(citizen_id: str, purpose: str) -> bool:
    with Session(engine) as session:
        consents = session.exec(
            select(Consent).where(
                Consent.citizen_id == citizen_id,
                Consent.purpose == purpose,
                Consent.status == "ACTIVE"
            )
        ).all()
        if not consents:
            return False
        for c in consents:
            c.status = "REVOKED"
            session.add(c)
        session.commit()
        return True

@router.post("/grant")
async def grant_consent(req: GrantConsentRequest):
    consent_info = grant_consent_db(req.citizen_id, req.purpose, req.data_scope)
    return {"status": "SUCCESS", "consent_id": consent_info["id"], "purpose": consent_info["purpose"]}

@router.get("/check")
async def check_consent(citizen_id: str = Query(...), purpose: str = Query(...)):
    valid = check_consent_db(citizen_id, purpose)
    return {"valid": valid, "citizen_id": citizen_id, "purpose": purpose}

@router.post("/revoke")
async def revoke_consent(req: RevokeConsentRequest):
    revoked = revoke_consent_db(req.citizen_id, req.purpose)
    return {"status": "REVOKED" if revoked else "NOT_FOUND", "citizen_id": req.citizen_id, "purpose": req.purpose}
