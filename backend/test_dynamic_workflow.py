import sys
import asyncio
import json
import uuid
from sqlmodel import Session, select

sys.path.append(r"d:\sih\govbridge\backend")

from db import init_db, engine
from models_db import Application
from consent import grant_consent_db
from mock_departments import AadhaarVerifyOtpRequest, verify_aadhaar_otp
from workflow import run_workflow

async def main():
    print("=== Testing Real Dynamic Workflow Engine ===")
    try:
        init_db()
    except Exception:
        pass

    # 1. Test Aadhaar eKYC for Custom Citizen "Anjali Sharma"
    ekyc_req = AadhaarVerifyOtpRequest(
        aadhaar_number="999988887777",
        otp="123456",
        citizen_id="C99999",
        name="Anjali Sharma",
        date_of_birth="1995-08-20"
    )
    ekyc_res = await verify_aadhaar_otp(ekyc_req)
    print("1. eKYC Verified:", ekyc_res["name"], "| Token:", ekyc_res["verification_token"])
    assert ekyc_res["name"] == "Anjali Sharma"

    # 2. Grant Purpose Consent with Custom PAN and Property Code
    consent_res = grant_consent_db(
        citizen_id="C99999",
        purpose="business_registration",
        data_scope=["identity", "tax", "address", "registry"],
        local_ids={"tax": "PANX99999F", "municipality": "OWN55443"},
        verification_token=ekyc_res["verification_token"]
    )
    print("2. Consent Granted JWT:", consent_res["consent_token"][:30] + "...")

    # 3. Create Application record
    app_id = f"GB-2026-{uuid.uuid4().hex[:6].upper()}"
    with Session(engine) as session:
        app = Application(
            id=app_id,
            citizen_id="C99999",
            service_type="business_registration",
            status="SUBMITTED"
        )
        session.add(app)
        session.commit()

    print("3. Application Initialized ID:", app_id)

    # 4. Run Workflow for Clean Application (Names Match)
    res_clean = await run_workflow(app_id)
    print("4. Clean Application Workflow Result:", res_clean["status"])
    assert res_clean["status"] == "APPROVED"

    # 5. Test Fraud Safeguard (Mismatched Taxpayer Name)
    print("\n--- Testing Fraud Safeguard Mismatch ---")
    fraud_consent = grant_consent_db(
        citizen_id="C99999",
        purpose="business_registration",
        data_scope=["identity", "tax", "address", "registry"],
        local_ids={"tax": "PANX99999F", "municipality": "OWN55443", "taxpayer_name": "Imposter Identity"},
        verification_token=ekyc_res["verification_token"]
    )
    app_fraud_id = f"GB-2026-{uuid.uuid4().hex[:6].upper()}"
    with Session(engine) as session:
        app_fraud = Application(
            id=app_fraud_id,
            citizen_id="C99999",
            service_type="business_registration",
            status="SUBMITTED"
        )
        session.add(app_fraud)
        session.commit()

    res_fraud = await run_workflow(app_fraud_id, consent_token_override=fraud_consent["consent_token"])
    print("5. Fraud Application Workflow Result:", res_fraud["status"], "| Reason:", res_fraud.get("reason"))
    assert res_fraud["status"] == "MANUAL_REVIEW_FLAGGED"

    print("\n✅ ALL DYNAMIC WORKFLOW & FRAUD VERIFICATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(main())
