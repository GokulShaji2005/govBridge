import uuid
import json
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Query, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlmodel import Session, select

from db import init_db, engine
from models_db import Application, WorkflowStep, WorkflowConfig, UserProfile
from mock_departments import router as mock_router, MUNICIPALITY_DOWN
import mock_departments
from consent import router as consent_router, ConsentMissingException
import workflow
import audit
from auth import (
    create_supabase_jwt, get_current_user, get_current_citizen_id,
    require_officer_role, verify_client_key, CLIENT_KEYS
)

# Initialize Database Schema & Seed Defaults
init_db()

def seed_defaults():
    from models_db import DeptIdentityRegistry, DeptTaxRegistry, DeptPropertyRegistry
    with Session(engine) as session:
        # Seed workflow configs
        if not session.exec(select(WorkflowConfig).where(WorkflowConfig.service_type == "business_registration")).first():
            session.add(WorkflowConfig(
                service_type="business_registration",
                steps_json=json.dumps(["identity", "tax", "address", "registry"])
            ))
        if not session.exec(select(WorkflowConfig).where(WorkflowConfig.service_type == "trade_license")).first():
            session.add(WorkflowConfig(
                service_type="trade_license",
                steps_json=json.dumps(["identity", "tax", "address"])
            ))

        # Seed default citizen user profile
        if not session.exec(select(UserProfile).where(UserProfile.citizen_id == "C10291")).first():
            session.add(UserProfile(
                supabase_user_id="sub_sup_c10291",
                citizen_id="C10291",
                name="Rahul Kumar",
                role="citizen"
            ))
        # Seed officer user profile
        if not session.exec(select(UserProfile).where(UserProfile.citizen_id == "C_OFFICER_01")).first():
            session.add(UserProfile(
                supabase_user_id="sub_sup_officer_01",
                citizen_id="C_OFFICER_01",
                name="Officer Admin",
                role="officer"
            ))

        # Seed Department Registries (Mock Department Databases)
        # 1. Identity Registry (UIDAI DB)
        identity_records = [
            ("123456789012", "Rahul Kumar", "1990-05-12", "Plot 42, Cyber Park, Ward 7"),
            ("999988887777", "Anjali Sharma", "1995-08-20", "Suite 101, IT Corridor, Ward 12"),
            ("888877776666", "Vikram Patel", "1988-11-04", "15 MG Road, Ward 4, Bengaluru"),
            ("555544443333", "Priya Nair", "1992-03-18", "42 Marine Drive, Ward 1, Mumbai"),
            ("777766665555", "Amitabh Roy", "1985-07-25", "88 Park Street, Ward 9, Kolkata"),
            ("333322221111", "Sneha Reddy", "1997-09-30", "23 Jubilee Hills, Ward 15, Hyderabad"),
            ("666655554444", "Mohammed Ali Khan", "1991-01-15", "7 Sector 17, Ward 2, Chandigarh")
        ]
        for a_ref, name, dob, addr in identity_records:
            if not session.exec(select(DeptIdentityRegistry).where(DeptIdentityRegistry.aadhaar_ref == a_ref)).first():
                session.add(DeptIdentityRegistry(aadhaar_ref=a_ref, full_name=name, date_of_birth=dob, address=addr))

        # 2. Income Tax Registry (CBDT DB)
        tax_records = [
            ("ABCDE1234F", "Rahul Kumar"),
            ("PANX99999F", "Anjali Sharma"),
            ("MISMATCH99F", "Imposter Taxpayer Name"),
            ("VPATL1122K", "Vikram Patel"),
            ("PNAIR4455M", "Priya Nair"),
            ("AROY7788P", "Amitabh Roy"),
            ("SREDD3344Q", "Sneha Reddy"),
            ("MKHAN6677R", "Mohammed Ali Khan")
        ]
        for pan, tp_name in tax_records:
            if not session.exec(select(DeptTaxRegistry).where(DeptTaxRegistry.pan_number == pan)).first():
                session.add(DeptTaxRegistry(pan_number=pan, taxpayer_name=tp_name, assessment_year="2025-2026", filing_status="COMPLIANT"))

        # 3. Municipal Property Registry (City Revenue DB)
        property_records = [
            ("OWN77821", "Rahul Kumar", "Plot 42, Cyber Park, Ward 7"),
            ("OWN55443", "Anjali Sharma", "Suite 101, IT Corridor, Ward 12"),
            ("OWN11223", "Vikram Patel", "15 MG Road, Ward 4, Bengaluru"),
            ("OWN44556", "Priya Nair", "42 Marine Drive, Ward 1, Mumbai"),
            ("OWN77889", "Amitabh Roy", "88 Park Street, Ward 9, Kolkata"),
            ("OWN33445", "Sneha Reddy", "23 Jubilee Hills, Ward 15, Hyderabad"),
            ("OWN66778", "Mohammed Ali Khan", "7 Sector 17, Ward 2, Chandigarh")
        ]
        for o_code, o_name, p_addr in property_records:
            if not session.exec(select(DeptPropertyRegistry).where(DeptPropertyRegistry.owner_code == o_code)).first():
                session.add(DeptPropertyRegistry(owner_code=o_code, owner_name=o_name, property_address=p_addr, tax_cleared=True))

        session.commit()

seed_defaults()

app = FastAPI(
    title="GovBridge Core Engine",
    description="Unified Data Exchange & 4-Boundary Authorization Architecture",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(mock_router)
app.include_router(consent_router)

class CreateApplicationRequest(BaseModel):
    citizen_id: Optional[str] = None
    service_type: str = "business_registration"  # "business_registration" | "trade_license"

class StartWorkflowRequest(BaseModel):
    allow_reuse: bool = False
    consent_token: Optional[str] = None

class LoginRequest(BaseModel):
    citizen_id: str = "C10291"
    role: str = "citizen"

@app.post("/auth/token-demo")
async def get_demo_token(req: LoginRequest):
    """Generates a real Supabase Auth JWT token for testing/demo purposes."""
    sub_id = f"sub_sup_{req.citizen_id.lower()}"
    with Session(engine) as session:
        user = session.exec(select(UserProfile).where(UserProfile.citizen_id == req.citizen_id)).first()
        if not user:
            user = UserProfile(
                supabase_user_id=sub_id,
                citizen_id=req.citizen_id,
                name="Rahul Kumar" if req.role == "citizen" else "Officer Admin",
                role=req.role
            )
            session.add(user)
            session.commit()
    token = create_supabase_jwt(sub_id, req.citizen_id, req.role)
    return {
        "access_token": token,
        "token_type": "bearer",
        "citizen_id": req.citizen_id,
        "role": req.role
    }

@app.post("/applications")
async def create_application(
    req: CreateApplicationRequest,
    current_citizen_id: str = Depends(get_current_citizen_id),
    client_key: str = Depends(verify_client_key)
):
    """
    Boundary 1 & Boundary 2 Protected:
    Extracts citizen_id from authenticated session (never trusts body citizen_id!).
    Validates portal client key header (X-Client-Key).
    """
    effective_citizen_id = current_citizen_id
    app_id = f"GB-2026-{uuid.uuid4().hex[:6].upper()}"

    # Load configured steps for this service
    steps = workflow.get_workflow_steps(req.service_type)

    with Session(engine) as session:
        new_app = Application(
            id=app_id,
            citizen_id=effective_citizen_id,
            service_type=req.service_type,
            status="CREATED"
        )
        session.add(new_app)
        session.commit()

        for step_name in steps:
            w_step = WorkflowStep(
                application_id=app_id,
                step_name=step_name,
                status="PENDING"
            )
            session.add(w_step)
        session.commit()

    audit.log_audit(app_id, "APPLICATION_CREATED", "SUCCESS")
    return {
        "application_id": app_id,
        "status": "CREATED",
        "citizen_id": effective_citizen_id,
        "service_type": req.service_type,
        "client_portal": CLIENT_KEYS.get(client_key, "Registered Client Portal")
    }

@app.get("/applications")
async def list_applications(user: UserProfile = Depends(get_current_user)):
    """
    Officer / Citizen List Endpoint:
    Officers can list all applications across citizens.
    Citizens only list their own applications (Data Ownership Check).
    """
    with Session(engine) as session:
        if user.role == "officer":
            apps = session.exec(select(Application).order_by(Application.created_at.desc())).all()
        else:
            apps = session.exec(
                select(Application)
                .where(Application.citizen_id == user.citizen_id)
                .order_by(Application.created_at.desc())
            ).all()

        result = []
        for a in apps:
            steps = session.exec(select(WorkflowStep).where(WorkflowStep.application_id == a.id)).all()
            step_summary = {s.step_name: s.status for s in steps}
            result.append({
                "id": a.id,
                "citizen_id": a.citizen_id,
                "service_type": a.service_type,
                "status": a.status,
                "created_at": a.created_at,
                "govbridge_person_id": a.govbridge_person_id,
                "steps": step_summary
            })
        return result

@app.get("/applications/{app_id}")
async def get_application_details(
    app_id: str,
    user: UserProfile = Depends(get_current_user)
):
    """
    Boundary 5 Enforcement (Data Ownership Check):
    Verifies that requested application belongs to authenticated citizen session.
    Reject with 403 Forbidden if attempting cross-citizen data read!
    """
    with Session(engine) as session:
        app_obj = session.exec(select(Application).where(Application.id == app_id)).first()
        if not app_obj:
            raise HTTPException(status_code=404, detail="Application not found")

        # Boundary 5 Data Ownership Check
        if app_obj.citizen_id != user.citizen_id and user.role != "officer":
            raise HTTPException(status_code=403, detail="Not authorized to view this application (Data Ownership Check)")

        steps = session.exec(select(WorkflowStep).where(WorkflowStep.application_id == app_id)).all()
        steps_detail = []
        for s in steps:
            data_parsed = None
            if s.data_json:
                try:
                    data_parsed = json.loads(s.data_json)
                except Exception:
                    data_parsed = s.data_json
            steps_detail.append({
                "step_name": s.step_name,
                "status": s.status,
                "data": data_parsed,
                "updated_at": s.updated_at
            })

        logs = audit.get_audit_logs(app_id)

        return {
            "id": app_obj.id,
            "citizen_id": app_obj.citizen_id,
            "service_type": app_obj.service_type,
            "status": app_obj.status,
            "govbridge_person_id": app_obj.govbridge_person_id,
            "created_at": app_obj.created_at,
            "steps": steps_detail,
            "audit_trail": logs
        }

@app.post("/applications/{app_id}/start-workflow")
async def start_workflow_endpoint(
    app_id: str,
    req: Optional[StartWorkflowRequest] = None,
    user: UserProfile = Depends(get_current_user),
    client_key: str = Depends(verify_client_key)
):
    """Executes config-driven workflow under Boundary 3 signed consent token."""
    with Session(engine) as session:
        app_obj = session.exec(select(Application).where(Application.id == app_id)).first()
        if not app_obj:
            raise HTTPException(status_code=404, detail="Application not found")
        if app_obj.citizen_id != user.citizen_id and user.role != "officer":
            raise HTTPException(status_code=403, detail="Not authorized to start workflow for this application")

    allow_reuse = req.allow_reuse if req else False
    consent_token_override = req.consent_token if req else None

    try:
        res = await workflow.run_workflow(app_id, allow_reuse=allow_reuse, consent_token_override=consent_token_override)
        return res
    except workflow.ConsentMissingException as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/applications/{app_id}/reuse-check")
async def check_reuse_availability(
    app_id: str,
    user: UserProfile = Depends(get_current_user)
):
    """Boundary 5 Data Ownership Check on reuse availability."""
    with Session(engine) as session:
        app_obj = session.exec(select(Application).where(Application.id == app_id)).first()
        if not app_obj:
            raise HTTPException(status_code=404, detail="Application not found")

        if app_obj.citizen_id != user.citizen_id and user.role != "officer":
            raise HTTPException(status_code=403, detail="Not authorized to inspect reuse availability for this application")

        citizen_id = app_obj.citizen_id

        reusable_summary = {}
        for step in ["identity", "tax", "address"]:
            existing_data = workflow.check_reusable_step(citizen_id, step)
            reusable_summary[step] = {
                "available": existing_data is not None,
                "data": json.loads(existing_data) if existing_data else None
            }

        return {
            "application_id": app_id,
            "citizen_id": citizen_id,
            "reusable_steps": reusable_summary
        }

@app.get("/applications/{app_id}/audit")
async def get_application_audit(
    app_id: str,
    user: UserProfile = Depends(get_current_user)
):
    """Boundary 5 Data Ownership Check on application audit trail."""
    with Session(engine) as session:
        app_obj = session.exec(select(Application).where(Application.id == app_id)).first()
        if not app_obj:
            raise HTTPException(status_code=404, detail="Application not found")
        if app_obj.citizen_id != user.citizen_id and user.role != "officer":
            raise HTTPException(status_code=403, detail="Not authorized to view audit trail for this application")

    return audit.get_audit_logs(app_id)

@app.post("/admin/toggle-municipality")
async def toggle_municipality():
    mock_departments.MUNICIPALITY_DOWN = not mock_departments.MUNICIPALITY_DOWN
    return {
        "status": "SUCCESS",
        "MUNICIPALITY_DOWN": mock_departments.MUNICIPALITY_DOWN,
        "message": f"Municipality server set to {'DOWN (503)' if mock_departments.MUNICIPALITY_DOWN else 'UP (200)'}"
    }

@app.post("/admin/wipe-db")
async def wipe_database_data():
    """Wipes all applications, workflow steps, audit logs, consents, aadhaar records, and identity mappings."""
    from models_db import Application, WorkflowStep, Consent, ConsentItem, RevokedConsentToken, AadhaarVerificationRecord, Person, IdentityMapping, AuditLog
    with Session(engine) as session:
        session.exec(WorkflowStep.__table__.delete())
        session.exec(Application.__table__.delete())
        session.exec(ConsentItem.__table__.delete())
        session.exec(Consent.__table__.delete())
        session.exec(RevokedConsentToken.__table__.delete())
        session.exec(AadhaarVerificationRecord.__table__.delete())
        session.exec(IdentityMapping.__table__.delete())
        session.exec(Person.__table__.delete())
        session.exec(AuditLog.__table__.delete())
        session.commit()
    return {
        "status": "SUCCESS",
        "message": "Database wiped successfully! All applications, steps, consents, and audit logs cleared."
    }

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "GovBridge Core Engine"}
