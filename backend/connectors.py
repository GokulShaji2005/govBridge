import httpx
from typing import Dict, Any
from mock_departments import (
    verify_identity, verify_tax, verify_municipality, register_business,
    IdentityVerifyRequest, TaxVerifyRequest, MunicipalityVerifyRequest, BusinessRegisterRequest
)

DEPT_KEYS = {
    "identity": "DEPT_KEY_IDENTITY_99",
    "tax": "DEPT_KEY_TAX_88",
    "municipality": "DEPT_KEY_MUNICIPALITY_77",
    "registry": "DEPT_KEY_REGISTRY_66"
}

async def call_identity(citizen_id: str) -> Dict[str, Any]:
    req = IdentityVerifyRequest(citizen_id=citizen_id)
    return await verify_identity(req, authorization=f"Bearer {DEPT_KEYS['identity']}")

async def call_tax(pan: str) -> str:
    req = TaxVerifyRequest(pan=pan)
    res = await verify_tax(req, authorization=f"Bearer {DEPT_KEYS['tax']}")
    return res.body.decode("utf-8")

async def call_municipality(owner_code: str) -> Dict[str, Any]:
    req = MunicipalityVerifyRequest(owner_code=owner_code)
    return await verify_municipality(req, authorization=f"Bearer {DEPT_KEYS['municipality']}")

async def call_registry(payload: Dict[str, Any]) -> Dict[str, Any]:
    req = BusinessRegisterRequest(
        applicant_name=payload.get("applicant_name"),
        business_name=payload.get("business_name", "Apex Technologies")
    )
    return await register_business(req, authorization=f"Bearer {DEPT_KEYS['registry']}")
