import uuid
import json
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlmodel import Session, select

from db import init_db, engine
from models_db import Application, WorkflowStep
from mock_departments import router as mock_router, MUNICIPALITY_DOWN
import mock_departments
from consent import router as consent_router
import workflow
import audit

# Initialize Database Schema
init_db()

app = FastAPI(
    title="GovBridge Core Engine",
    description="Unified Data Exchange & Consent-Gated Architecture",
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
    citizen_id: str
    service_type: str = "business_registration"  # "business_registration" | "trade_license"

class StartWorkflowRequest(BaseModel):
    allow_reuse: bool = False

@app.post("/applications")
async def create_application(req: CreateApplicationRequest):
    app_id = f"GB-2026-{uuid.uuid4().hex[:6].upper()}"
    with Session(engine) as session:
        new_app = Application(
            id=app_id,
            citizen_id=req.citizen_id,
            service_type=req.service_type,
            status="CREATED"
        )
        session.add(new_app)
        session.commit()
        
        # Initialize 4 workflow step placeholders
        for step_name in ["identity", "tax", "address", "registry"]:
            w_step = WorkflowStep(
                application_id=app_id,
                step_name=step_name,
                status="PENDING"
            )
            session.add(w_step)
        session.commit()

    audit.log_audit(app_id, "APPLICATION_CREATED", "SUCCESS")
    return {"application_id": app_id, "status": "CREATED", "citizen_id": req.citizen_id, "service_type": req.service_type}

@app.get("/applications")
async def list_applications():
    with Session(engine) as session:
        apps = session.exec(select(Application).order_by(Application.created_at.desc())).all()
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
async def get_application_details(app_id: str):
    with Session(engine) as session:
        app_obj = session.exec(select(Application).where(Application.id == app_id)).first()
        if not app_obj:
            raise HTTPException(status_code=404, detail="Application not found")
        
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
async def start_workflow_endpoint(app_id: str, req: Optional[StartWorkflowRequest] = None):
    allow_reuse = req.allow_reuse if req else False
    try:
        res = await workflow.run_workflow(app_id, allow_reuse=allow_reuse)
        return res
    except workflow.ConsentMissingException as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/applications/{app_id}/reuse-check")
async def check_reuse_availability(app_id: str):
    with Session(engine) as session:
        app_obj = session.exec(select(Application).where(Application.id == app_id)).first()
        if not app_obj:
            raise HTTPException(status_code=404, detail="Application not found")
        
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
async def get_application_audit(app_id: str):
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
