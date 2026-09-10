import uuid
from typing import Optional
from fastapi import APIRouter, Response, HTTPException, Header, status
from pydantic import BaseModel
from sqlmodel import Session
from db import engine
from models_db import AadhaarVerificationRecord

router = APIRouter(tags=["Mock Departments & Identity Verification"])

# In-memory flag for Stage 11 failure demo lever
MUNICIPALITY_DOWN = False

# Boundary 4: Department Static Scoped Credentials
DEPARTMENT_CREDENTIALS = {
    "DEPT_KEY_IDENTITY_99": {"department": "identity", "scopes": ["identity:verify"]},
    "DEPT_KEY_TAX_88": {"department": "tax", "scopes": ["tax:verify"]},
    "DEPT_KEY_MUNICIPALITY_77": {"department": "municipality", "scopes": ["address:verify"]},
    "DEPT_KEY_REGISTRY_66": {"department": "registry", "scopes": ["registry:write"]},
}

def validate_department_token(authorization: Optional[str], expected_dept: str, required_scope: str):
    """
    Boundary 4 Enforcement:
    Validates department credential token and scope.
    Rejects with HTTP 401 if missing, invalid, or lacking required scope.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Missing or invalid department credential token for {expected_dept} department"
        )
    token = authorization.split("Bearer ")[1].strip()
    cred = DEPARTMENT_CREDENTIALS.get(token)
    if not cred or cred["department"] != expected_dept or required_scope not in cred["scopes"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Unauthorized department API key or missing scope '{required_scope}' for department '{expected_dept}'"
        )

# Aadhaar eKYC Models
class AadhaarVerifyOtpRequest(BaseModel):
    aadhaar_number: str
    otp: str
    citizen_id: Optional[str] = "C10291"

class IdentityVerifyRequest(BaseModel):
    citizen_id: str

class TaxVerifyRequest(BaseModel):
    pan: str

class MunicipalityVerifyRequest(BaseModel):
    owner_code: str

class BusinessRegisterRequest(BaseModel):
    applicant_name: Optional[str] = "Rahul Kumar"
    business_name: Optional[str] = "Apex Technologies"

@router.post("/aadhaar/verify-otp")
async def verify_aadhaar_otp(req: AadhaarVerifyOtpRequest):
    """
    Aadhaar/eKYC Identity Verification Mock.
    Modeled on UIDAI OTP verification flow.
    Hardcoded demo OTP: 123456
    """
    if req.otp != "123456":
        raise HTTPException(status_code=400, detail="Invalid Aadhaar OTP. Enter demo OTP 123456.")

    v_token = f"EKYC-VERIFIED-{uuid.uuid4().hex[:8].upper()}"
    citizen_id = req.citizen_id or "C10291"
    aadhaar_ref = f"XXXX-XXXX-{req.aadhaar_number[-4:] if len(req.aadhaar_number) >= 4 else '1234'}"

    with Session(engine) as session:
        rec = AadhaarVerificationRecord(
            verification_token=v_token,
            citizen_id=citizen_id,
            aadhaar_ref=aadhaar_ref,
            name="Rahul Kumar",
            date_of_birth="1998-04-12"
        )
        session.add(rec)
        session.commit()

    return {
        "verified": True,
        "verification_token": v_token,
        "citizen_id": citizen_id,
        "name": "Rahul Kumar",
        "dateOfBirth": "1998-04-12",
        "address": {"houseNumber": "12A", "locality": "Kumaranallur", "city": "Kottayam"},
        "aadhaarRef": aadhaar_ref
    }

@router.post("/mock/identity/verify")
async def verify_identity(req: IdentityVerifyRequest, authorization: Optional[str] = Header(None)):
    validate_department_token(authorization, "identity", "identity:verify")
    return {
        "verified": True,
        "citizenId": req.citizen_id,
        "name": "Rahul Kumar",
        "dateOfBirth": "1998-04-12",
        "address": {
            "houseNumber": "12A",
            "locality": "Kumaranallur",
            "city": "Kottayam"
        }
    }

@router.post("/mock/tax/verify")
async def verify_tax(req: TaxVerifyRequest, authorization: Optional[str] = Header(None)):
    validate_department_token(authorization, "tax", "tax:verify")
    xml_content = f"""<TaxResult><PAN>{req.pan}</PAN><TaxpayerName>Rahul Kumar</TaxpayerName><Status>ACTIVE</Status></TaxResult>"""
    return Response(content=xml_content, media_type="text/xml")

@router.post("/mock/municipality/verify")
async def verify_municipality(req: MunicipalityVerifyRequest, authorization: Optional[str] = Header(None)):
    validate_department_token(authorization, "municipality", "address:verify")
    global MUNICIPALITY_DOWN
    if MUNICIPALITY_DOWN:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Municipality Server Unreachable (Simulated Outage)"
        )
    return {
        "OWNER_CODE": req.owner_code,
        "OWNER_NAME": "RAHUL KUMAR",
        "HOUSE_NO": "12A",
        "LOCALITY": "KUMARANALLUR"
    }

@router.post("/mock/business/register")
async def register_business(req: BusinessRegisterRequest, authorization: Optional[str] = Header(None)):
    validate_department_token(authorization, "registry", "registry:write")
    return {
        "registrationNumber": "BR-2026-00121",
        "status": "REGISTERED",
        "businessName": req.business_name
    }

@router.get("/mock/health/all")
async def department_health():
    global MUNICIPALITY_DOWN
    return {
        "identity": {"status": "UP", "latency_ms": 12},
        "tax": {"status": "UP", "latency_ms": 24},
        "municipality": {"status": "DOWN" if MUNICIPALITY_DOWN else "UP", "latency_ms": 999 if MUNICIPALITY_DOWN else 35},
        "registry": {"status": "UP", "latency_ms": 18}
    }
