import uuid
from typing import Optional
from fastapi import APIRouter, Response, HTTPException, Header, status
from pydantic import BaseModel
from sqlmodel import Session, select
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
    name: Optional[str] = "Rahul Kumar"
    date_of_birth: Optional[str] = "1998-04-12"
    house_number: Optional[str] = "12A"
    locality: Optional[str] = "Kumaranallur"
    city: Optional[str] = "Kottayam"

class IdentityVerifyRequest(BaseModel):
    citizen_id: str

class TaxVerifyRequest(BaseModel):
    pan: str
    taxpayer_name: Optional[str] = None

class MunicipalityVerifyRequest(BaseModel):
    owner_code: str
    owner_name: Optional[str] = None

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
    c_name = req.name or "Rahul Kumar"
    c_dob = req.date_of_birth or "1998-04-12"
    h_no = req.house_number or "12A"
    loc = req.locality or "Kumaranallur"
    city_val = req.city or "Kottayam"

    with Session(engine) as session:
        # Check if record exists for this citizen_id, update or create
        rec = session.exec(select(AadhaarVerificationRecord).where(AadhaarVerificationRecord.citizen_id == citizen_id)).first()
        if rec:
            rec.verification_token = v_token
            rec.aadhaar_ref = aadhaar_ref
            rec.name = c_name
            rec.date_of_birth = c_dob
            session.add(rec)
        else:
            rec = AadhaarVerificationRecord(
                verification_token=v_token,
                citizen_id=citizen_id,
                aadhaar_ref=aadhaar_ref,
                name=c_name,
                date_of_birth=c_dob
            )
            session.add(rec)
        session.commit()

    return {
        "verified": True,
        "verification_token": v_token,
        "citizen_id": citizen_id,
        "name": c_name,
        "dateOfBirth": c_dob,
        "address": {"houseNumber": h_no, "locality": loc, "city": city_val},
        "aadhaarRef": aadhaar_ref
    }

@router.post("/mock/identity/verify")
async def verify_identity(req: IdentityVerifyRequest, authorization: Optional[str] = Header(None)):
    validate_department_token(authorization, "identity", "identity:verify")
    
    # Try retrieving verified eKYC record from DB
    c_name = "Rahul Kumar"
    c_dob = "1998-04-12"
    with Session(engine) as session:
        rec = session.exec(select(AadhaarVerificationRecord).where(AadhaarVerificationRecord.citizen_id == req.citizen_id)).first()
        if rec and rec.name:
            c_name = rec.name
            if rec.date_of_birth:
                c_dob = rec.date_of_birth

    return {
        "verified": True,
        "citizenId": req.citizen_id,
        "name": c_name,
        "dateOfBirth": c_dob,
        "address": {
            "houseNumber": "12A",
            "locality": "Kumaranallur",
            "city": "Kottayam"
        }
    }

@router.post("/mock/tax/verify")
async def verify_tax(req: TaxVerifyRequest, authorization: Optional[str] = Header(None)):
    validate_department_token(authorization, "tax", "tax:verify")
    from models_db import DeptTaxRegistry
    
    pan_clean = req.pan.strip().upper()
    
    with Session(engine) as session:
        tax_rec = session.exec(select(DeptTaxRegistry).where(DeptTaxRegistry.pan_number == pan_clean)).first()
        if tax_rec:
            # Found in DB! If caller passed taxpayer_name override (fraud test), use caller name, else DB name
            tp_name = req.taxpayer_name or tax_rec.taxpayer_name
        else:
            # Record NOT found in Income Tax DB -> 404 Error!
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tax PAN '{pan_clean}' not found in Income Tax Department Database (CBDT Registry)"
            )

    xml_content = f"""<TaxResult><PAN>{pan_clean}</PAN><TaxpayerName>{tp_name}</TaxpayerName><Status>ACTIVE</Status></TaxResult>"""
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
    from models_db import DeptPropertyRegistry
    owner_code_clean = req.owner_code.strip().upper()

    with Session(engine) as session:
        prop_rec = session.exec(select(DeptPropertyRegistry).where(DeptPropertyRegistry.owner_code == owner_code_clean)).first()
        if prop_rec:
            owner_name = (req.owner_name or prop_rec.owner_name).upper()
            prop_addr = prop_rec.property_address
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Property Code '{owner_code_clean}' not registered in Municipal Property Database"
            )

    return {
        "OWNER_CODE": owner_code_clean,
        "OWNER_NAME": owner_name,
        "PROPERTY_ADDRESS": prop_addr,
        "STATUS": "ACTIVE"
    }

@router.post("/mock/business/register")
async def register_business(req: BusinessRegisterRequest, authorization: Optional[str] = Header(None)):
    validate_department_token(authorization, "registry", "registry:write")
    reg_id = f"BR-2026-{uuid.uuid4().hex[:5].upper()}"
    return {
        "registrationNumber": reg_id,
        "status": "REGISTERED",
        "businessName": req.business_name or "Apex Technologies",
        "applicantName": req.applicant_name or "Rahul Kumar"
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
