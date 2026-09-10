import time
import uuid
import jwt
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Header, Depends
from pydantic import BaseModel
from sqlmodel import Session, select
from db import engine
from models_db import Consent, ConsentItem, RevokedConsentToken, AadhaarVerificationRecord

router = APIRouter(prefix="/consent", tags=["Consent Management (Boundary 3)"])

CONSENT_JWT_SECRET = "govbridge_signed_consent_secret_key_2026"
CONSENT_JWT_ALGORITHM = "HS256"

class GrantConsentRequest(BaseModel):
    citizen_id: str
    purpose: str
    data_scope: List[str] = ["identity:verify", "tax:verify", "address:verify", "registry:write"]
    local_ids: Optional[Dict[str, str]] = {"tax": "ABCDE1234F", "municipality": "OWN77821"}
    verification_token: Optional[str] = None

class RevokeConsentRequest(BaseModel):
    citizen_id: str
    purpose: str
    consent_token: Optional[str] = None

class ConsentMissingException(Exception):
    pass

def create_consent_jwt(citizen_id: str, purpose: str, scopes: List[str], local_ids: Dict[str, str]) -> tuple[str, str]:
    now = int(time.time())
    jti = f"CONSENT-JTI-{uuid.uuid4().hex[:12].upper()}"
    payload = {
        "citizen_id": citizen_id,
        "purpose": purpose,
        "scopes": scopes,
        "local_ids": local_ids,
        "identity_verified_via": "aadhaar-ekyc",
        "jti": jti,
        "iat": now,
        "exp": now + 3600  # Valid for 1 hour
    }
    token = jwt.encode(payload, CONSENT_JWT_SECRET, algorithm=CONSENT_JWT_ALGORITHM)
    return token, jti

def verify_consent_jwt(token: str, required_scope: Optional[str] = None) -> dict:
    """
    Boundary 3 Defense-in-Depth Verification:
    Decodes signed JWT, checks signature, checks expiration, checks revocation DB table,
    and checks if required_scope is in the consent token scopes list.
    """
    try:
        payload = jwt.decode(token, CONSENT_JWT_SECRET, algorithms=[CONSENT_JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise ConsentMissingException("Consent token has expired. Please re-grant consent.")
    except jwt.InvalidTokenError:
        raise ConsentMissingException("Invalid or tampered consent token signature.")

    jti = payload.get("jti")
    if jti:
        with Session(engine) as session:
            revoked = session.exec(select(RevokedConsentToken).where(RevokedConsentToken.jti == jti)).first()
            if revoked:
                raise ConsentMissingException("Consent token has been revoked by the citizen.")

    if required_scope:
        scopes = payload.get("scopes", [])
        if required_scope not in scopes:
            raise ConsentMissingException(f"Consent token lacks required scope '{required_scope}' for this step.")

    return payload

def check_ekyc_precondition(citizen_id: str, verification_token: Optional[str] = None) -> bool:
    """Hard precondition: Consent can ONLY be granted after Aadhaar eKYC succeeds."""
    with Session(engine) as session:
        if verification_token:
            rec = session.exec(
                select(AadhaarVerificationRecord).where(AadhaarVerificationRecord.verification_token == verification_token)
            ).first()
            if rec:
                return True

        rec_cit = session.exec(
            select(AadhaarVerificationRecord).where(AadhaarVerificationRecord.citizen_id == citizen_id)
        ).first()
        return rec_cit is not None

def grant_consent_db(
    citizen_id: str,
    purpose: str,
    data_scope: List[str],
    local_ids: Dict[str, str],
    verification_token: Optional[str] = None
) -> Dict[str, Any]:
    # HARD PRECONDITION: Aadhaar eKYC must be verified first!
    if not check_ekyc_precondition(citizen_id, verification_token):
        raise HTTPException(
            status_code=400,
            detail="Hard Precondition Violation: Identity verification (Aadhaar eKYC) must succeed before granting consent."
        )

    normalized_scopes = []
    scope_map = {
        "identity": "identity:verify",
        "tax": "tax:verify",
        "address": "address:verify",
        "registry": "registry:write"
    }
    for s in data_scope:
        normalized_scopes.append(scope_map.get(s, s))

    consent_jwt, jti = create_consent_jwt(citizen_id, purpose, normalized_scopes, local_ids)

    with Session(engine) as session:
        # Supersede any existing active consents for this citizen and purpose
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

        consent = Consent(
            citizen_id=citizen_id,
            purpose=purpose,
            status="ACTIVE",
            consent_token=consent_jwt
        )
        session.add(consent)
        session.commit()
        session.refresh(consent)

        c_id = consent.id

        for scope in normalized_scopes:
            item = ConsentItem(consent_id=c_id, scope_name=scope)
            session.add(item)
        session.commit()

        return {
            "consent_id": c_id,
            "purpose": purpose,
            "status": "ACTIVE",
            "consent_token": consent_jwt,
            "jti": jti,
            "scopes": normalized_scopes,
            "local_ids": local_ids
        }

def check_consent_db(citizen_id: str, purpose: str) -> bool:
    with Session(engine) as session:
        consent = session.exec(
            select(Consent).where(
                Consent.citizen_id == citizen_id,
                Consent.purpose == purpose,
                Consent.status == "ACTIVE"
            )
        ).first()
        if not consent or not consent.consent_token:
            return False
        try:
            verify_consent_jwt(consent.consent_token)
            return True
        except ConsentMissingException:
            return False

def get_active_consent_token(citizen_id: str, purpose: str) -> Optional[str]:
    with Session(engine) as session:
        consent = session.exec(
            select(Consent).where(
                Consent.citizen_id == citizen_id,
                Consent.purpose == purpose,
                Consent.status == "ACTIVE"
            )
        ).first()
        if consent and consent.consent_token:
            return consent.consent_token
        return None

def revoke_consent_db(citizen_id: str, purpose: str, consent_token: Optional[str] = None) -> bool:
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

        revoked_jtis = set()
        for c in consents:
            c.status = "REVOKED"
            session.add(c)
            if c.consent_token:
                try:
                    payload = jwt.decode(c.consent_token, CONSENT_JWT_SECRET, algorithms=[CONSENT_JWT_ALGORITHM], options={"verify_signature": False})
                    jti = payload.get("jti")
                    if jti and jti not in revoked_jtis:
                        revoked_jtis.add(jti)
                        if not session.exec(select(RevokedConsentToken).where(RevokedConsentToken.jti == jti)).first():
                            session.add(RevokedConsentToken(jti=jti))
                except Exception:
                    pass

        if consent_token:
            try:
                payload = jwt.decode(consent_token, CONSENT_JWT_SECRET, algorithms=[CONSENT_JWT_ALGORITHM], options={"verify_signature": False})
                jti = payload.get("jti")
                if jti and jti not in revoked_jtis:
                    revoked_jtis.add(jti)
                    if not session.exec(select(RevokedConsentToken).where(RevokedConsentToken.jti == jti)).first():
                        session.add(RevokedConsentToken(jti=jti))
            except Exception:
                pass

        session.commit()
        return True

@router.post("/grant")
async def grant_consent(req: GrantConsentRequest):
    consent_info = grant_consent_db(
        req.citizen_id,
        req.purpose,
        req.data_scope,
        req.local_ids or {"tax": "ABCDE1234F", "municipality": "OWN77821"},
        req.verification_token
    )
    return {
        "status": "SUCCESS",
        "consent_id": consent_info["consent_id"],
        "purpose": consent_info["purpose"],
        "consent_token": consent_info["consent_token"],
        "jti": consent_info["jti"],
        "scopes": consent_info["scopes"],
        "local_ids": consent_info["local_ids"]
    }

@router.get("/check")
async def check_consent(citizen_id: str = Query(...), purpose: str = Query(...)):
    valid = check_consent_db(citizen_id, purpose)
    token = get_active_consent_token(citizen_id, purpose)
    return {"valid": valid, "citizen_id": citizen_id, "purpose": purpose, "consent_token": token}

@router.post("/revoke")
async def revoke_consent(req: RevokeConsentRequest):
    revoked = revoke_consent_db(req.citizen_id, req.purpose, req.consent_token)
    return {
        "status": "REVOKED" if revoked else "NOT_FOUND",
        "citizen_id": req.citizen_id,
        "purpose": req.purpose,
        "message": "Consent token added to revocation list; future reuse blocked." if revoked else "No active consent found"
    }
