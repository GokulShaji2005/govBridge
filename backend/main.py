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

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "GovBridge Core Engine"}
