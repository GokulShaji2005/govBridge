from fastapi import APIRouter, Response, HTTPException, status
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/mock", tags=["Mock Departments"])

# In-memory flag for Stage 11 failure demo lever
MUNICIPALITY_DOWN = False

class IdentityVerifyRequest(BaseModel):
    citizen_id: str

class TaxVerifyRequest(BaseModel):
    pan: str

class MunicipalityVerifyRequest(BaseModel):
    owner_code: str

class BusinessRegisterRequest(BaseModel):
    applicant_name: Optional[str] = "Rahul Kumar"
    business_name: Optional[str] = "Apex Technologies"

@router.post("/identity/verify")
async def verify_identity(req: IdentityVerifyRequest):
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

@router.post("/tax/verify")
async def verify_tax(req: TaxVerifyRequest):
    xml_content = f"""<TaxResult><PAN>{req.pan}</PAN><TaxpayerName>Rahul Kumar</TaxpayerName><Status>ACTIVE</Status></TaxResult>"""
    return Response(content=xml_content, media_type="text/xml")

@router.post("/municipality/verify")
async def verify_municipality(req: MunicipalityVerifyRequest):
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

@router.post("/business/register")
async def register_business(req: BusinessRegisterRequest):
    return {
        "registrationNumber": "BR-2026-00121",
        "status": "REGISTERED",
        "businessName": req.business_name
    }

@router.get("/health/all")
async def department_health():
    global MUNICIPALITY_DOWN
    return {
        "identity": {"status": "UP", "latency_ms": 12},
        "tax": {"status": "UP", "latency_ms": 24},
        "municipality": {"status": "DOWN" if MUNICIPALITY_DOWN else "UP", "latency_ms": 999 if MUNICIPALITY_DOWN else 35},
        "registry": {"status": "UP", "latency_ms": 18}
    }
