import asyncio
import os
import sys
import json
import httpx

# Clean old DB before importing main/db models to ensure fresh table schema
DB_PATH = os.path.join(os.path.dirname(__file__), "govbridge.db")
if os.path.exists(DB_PATH):
    try:
        os.remove(DB_PATH)
    except Exception:
        pass

from sqlmodel import Session, select
from db import init_db, engine
from models_db import Application, UserProfile, IdentityMapping, Person, WorkflowConfig
from auth import create_supabase_jwt

async def main():
    print("=== STARTING GOVBRIDGE SPEC VERIFICATION ===")

    # 1. Start test server or import app using TestClient
    from fastapi.testclient import TestClient
    from main import app

    client = TestClient(app)

    # A. Get Demo Citizen Token (Boundary 1)
    res = client.post("/auth/token-demo", json={"citizen_id": "C10291", "role": "citizen"})
    assert res.status_code == 200, f"Token demo failed: {res.text}"
    citizen_jwt = res.json()["access_token"]
    print("[PASS] Boundary 1: Generated Supabase Auth JWT for citizen C10291")

    # B. Test Boundary 2: Portal Client API Key (X-Client-Key)
    headers_citizen = {
        "Authorization": f"Bearer {citizen_jwt}",
        "X-Client-Key": "KEY_BUS_REG_123"
    }

    res_bad_key = client.post(
        "/applications",
        json={"service_type": "business_registration"},
        headers={"Authorization": f"Bearer {citizen_jwt}", "X-Client-Key": "INVALID_KEY_999"}
    )
    assert res_bad_key.status_code == 401, f"Expected 401 for bad client key, got {res_bad_key.status_code}"
    print("[PASS] Boundary 2: Successfully rejected invalid X-Client-Key with 401 Unauthorized")

    # C. Test Precondition: Grant Consent WITHOUT eKYC should fail!
    res_consent_fail = client.post(
        "/consent/grant",
        json={"citizen_id": "C10291_NEW_UNVERIFIED", "purpose": "business_registration"}
    )
    assert res_consent_fail.status_code == 400, f"Expected 400 for missing eKYC precondition, got {res_consent_fail.status_code}"
    print("[PASS] Boundary 3 Precondition: Rejected consent grant for unverified citizen (eKYC required)")

    # D. Test Aadhaar/eKYC OTP Verification (Stage 4)
    res_otp_bad = client.post("/aadhaar/verify-otp", json={"aadhaar_number": "123456789012", "otp": "999999", "citizen_id": "C10291"})
    assert res_otp_bad.status_code == 400, "Expected 400 for wrong OTP"

    res_otp_good = client.post("/aadhaar/verify-otp", json={"aadhaar_number": "123456789012", "otp": "123456", "citizen_id": "C10291"})
    assert res_otp_good.status_code == 200, f"Aadhaar OTP verify failed: {res_otp_good.text}"
    ekyc_data = res_otp_good.json()
    assert ekyc_data["verified"] is True
    v_token = ekyc_data["verification_token"]
    print(f"[PASS] Stage 4 Identity Verification Mock: Aadhaar OTP verified! Token: {v_token}")

    # E. Grant Signed Consent JWT (Boundary 3)
    res_grant = client.post(
        "/consent/grant",
        json={
            "citizen_id": "C10291",
            "purpose": "business_registration",
            "data_scope": ["identity:verify", "tax:verify", "address:verify", "registry:write"],
            "local_ids": {"tax": "ABCDE1234F", "municipality": "OWN77821"},
            "verification_token": v_token
        }
    )
    assert res_grant.status_code == 200, f"Consent grant failed: {res_grant.text}"
    consent_data = res_grant.json()
    consent_jwt = consent_data["consent_token"]
    jti = consent_data["jti"]
    print(f"[PASS] Boundary 3 Consent Gate: Issued signed consent JWT (JTI: {jti})")

    # F. Create Application (Boundary 1 + Boundary 2)
    res_create = client.post(
        "/applications",
        json={"service_type": "business_registration"},
        headers=headers_citizen
    )
    assert res_create.status_code == 200, f"Create app failed: {res_create.text}"
    app_id = res_create.json()["application_id"]
    print(f"[PASS] Application Created: {app_id}")

    # G. Test Boundary 4: Direct Unauthenticated / Unscoped Call to Mock Dept Endpoint should fail!
    res_dept_unauth = client.post("/mock/identity/verify", json={"citizen_id": "C10291"})
    assert res_dept_unauth.status_code == 401, f"Expected 401 on unauthenticated department API call, got {res_dept_unauth.status_code}"
    print("[PASS] Boundary 4: Direct call to mock department API rejected with 401 Unauthorized")

    # H. Run Workflow under Signed Consent Token & Client Key
    res_wf = client.post(
        f"/applications/{app_id}/start-workflow",
        json={"consent_token": consent_jwt},
        headers=headers_citizen
    )
    assert res_wf.status_code == 200, f"Workflow execution failed: {res_wf.text}"
    wf_result = res_wf.json()
    assert wf_result["status"] == "APPROVED", f"Expected APPROVED, got {wf_result}"
    print(f"[PASS] Config-Driven Workflow executed successfully! Result: {wf_result['status']}")

    # I. Verify Identity Resolution (P-10001 created and linked)
    res_details = client.get(f"/applications/{app_id}", headers=headers_citizen)
    assert res_details.status_code == 200
    details = res_details.json()
    gb_person_id = details["govbridge_person_id"]
    assert gb_person_id is not None and gb_person_id.startswith("P-"), f"Invalid GovBridge person ID: {gb_person_id}"
    print(f"[PASS] Master Data Linking: GovBridge Neutral Person Anchor created: {gb_person_id}")

    # J. Test Boundary 5: Data Ownership Check (Preventing Cross-Citizen Data Leakage)
    # Generate token for another citizen C99999
    res_other_tok = client.post("/auth/token-demo", json={"citizen_id": "C99999", "role": "citizen"})
    other_citizen_jwt = res_other_tok.json()["access_token"]
    headers_other = {
        "Authorization": f"Bearer {other_citizen_jwt}",
        "X-Client-Key": "KEY_BUS_REG_123"
    }

    res_cross_read = client.get(f"/applications/{app_id}", headers=headers_other)
    assert res_cross_read.status_code == 403, f"Expected 403 Data Ownership block, got {res_cross_read.status_code}"
    print("[PASS] Boundary 5 (Data Ownership Check): Blocked cross-citizen application read attempt with 403 Forbidden")

    # K. Test Revoke Endpoint (/consent/revoke)
    res_revoke = client.post(
        "/consent/revoke",
        json={"citizen_id": "C10291", "purpose": "business_registration", "consent_token": consent_jwt}
    )
    assert res_revoke.status_code == 200
    print("[PASS] Consent Revocation: Consent token added to revocation list (/consent/revoke)")

    # L. Test Failure Simulation (MUNICIPALITY_DOWN)
    client.post("/admin/toggle-municipality")
    res_app2 = client.post("/applications", json={"service_type": "business_registration"}, headers=headers_citizen)
    app2_id = res_app2.json()["application_id"]

    # Re-grant consent for app2
    res_grant2 = client.post("/consent/grant", json={"citizen_id": "C10291", "purpose": "business_registration", "data_scope": ["identity:verify", "tax:verify", "address:verify", "registry:write"], "verification_token": v_token})
    consent2_jwt = res_grant2.json()["consent_token"]

    res_wf_fail = client.post(f"/applications/{app2_id}/start-workflow", json={"consent_token": consent2_jwt}, headers=headers_citizen)
    assert res_wf_fail.status_code == 200
    fail_data = res_wf_fail.json()
    assert fail_data["status"] == "FAILED" and fail_data["failed_step"] == "address"
    print("[PASS] Resilience Demo: Municipality outage simulated; workflow failed gracefully at address step without crashing.")

    # Reset failure simulation
    client.post("/admin/toggle-municipality")

    print("\n=== ALL SPECIFICATION REQUIREMENTS PASSED PERFECTLY ===")

if __name__ == "__main__":
    asyncio.run(main())
