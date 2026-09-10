import json
from typing import Dict, Any, Optional
from sqlmodel import Session, select
from db import engine
from models_db import Application, WorkflowStep
from consent import check_consent_db
import connectors
import mapping
from audit import log_audit
from identity import resolve_or_create_person

STEPS = ["identity", "tax", "address", "registry"]

class ConsentMissingException(Exception):
    pass

def update_application_status(app_id: str, status: str):
    with Session(engine) as session:
        app = session.exec(select(Application).where(Application.id == app_id)).first()
        if app:
            app.status = status
            session.add(app)
            session.commit()

def set_step_status(app_id: str, step_name: str, status: str, data_json: Optional[str] = None):
    with Session(engine) as session:
        step = session.exec(
            select(WorkflowStep).where(
                WorkflowStep.application_id == app_id,
                WorkflowStep.step_name == step_name
            )
        ).first()
        if not step:
            step = WorkflowStep(application_id=app_id, step_name=step_name, status=status)
        else:
            step.status = status
        if data_json:
            step.data_json = data_json
        session.add(step)
        session.commit()

def check_reusable_step(citizen_id: str, step_name: str) -> Optional[str]:
    """Check if a previously APPROVED step exists for this citizen."""
    with Session(engine) as session:
        # Find any application for this citizen
        apps = session.exec(select(Application).where(Application.citizen_id == citizen_id)).all()
        app_ids = [a.id for a in apps]
        if not app_ids:
            return None
        
        reused_step = session.exec(
            select(WorkflowStep).where(
                WorkflowStep.application_id.in_(app_ids),
                WorkflowStep.step_name == step_name,
                WorkflowStep.status.in_(["DONE", "REUSED"]),
                WorkflowStep.data_json.is_not(None)
            )
        ).first()
        if reused_step and reused_step.data_json:
            return reused_step.data_json
        return None

async def run_workflow(application_id: str, allow_reuse: bool = False):
    with Session(engine) as session:
        app = session.exec(select(Application).where(Application.id == application_id)).first()
        if not app:
            raise ValueError(f"Application {application_id} not found")
        citizen_id = app.citizen_id
        service_type = app.service_type

    # 1. Consent Gate Check
    if not check_consent_db(citizen_id, service_type):
        log_audit(application_id, "CONSENT_CHECK", "FAILED_NO_ACTIVE_CONSENT")
        update_application_status(application_id, "FAILED")
        raise ConsentMissingException(f"No active consent found for citizen {citizen_id} for purpose {service_type}")

    log_audit(application_id, "CONSENT_CHECK", "VERIFIED_ACTIVE")
    update_application_status(application_id, "IN_PROGRESS")

    # Resolve person ID
    gb_person_id = resolve_or_create_person(citizen_id, pan="ABCDE1234F", owner_code="OWN77821")
    with Session(engine) as session:
        app_db = session.exec(select(Application).where(Application.id == application_id)).first()
        if app_db:
            app_db.govbridge_person_id = gb_person_id
            session.add(app_db)
            session.commit()

    # Step Execution Loop
    for step in STEPS:
        set_step_status(application_id, step, "IN_PROGRESS")
        log_audit(application_id, f"STEP_{step.upper()}", "IN_PROGRESS")

        # Reuse fast-path check
        if allow_reuse and step != "registry":
            reused_data = check_reusable_step(citizen_id, step)
            if reused_data:
                set_step_status(application_id, step, "DONE", reused_data)
                log_audit(application_id, f"STEP_{step.upper()}", "SKIPPED_REUSE")
                continue

        try:
            if step == "identity":
                raw = await connectors.call_identity(citizen_id)
                canonical_obj = mapping.map_identity(raw)
                data_json = canonical_obj.model_dump_json()
            elif step == "tax":
                raw_xml = await connectors.call_tax("ABCDE1234F")
                canonical_obj = mapping.map_tax(raw_xml)
                data_json = canonical_obj.model_dump_json()
            elif step == "address":
                raw = await connectors.call_municipality("OWN77821")
                canonical_obj = mapping.map_municipality(raw)
                data_json = canonical_obj.model_dump_json()
            elif step == "registry":
                reg_payload = {"applicant_name": "Rahul Kumar", "service": service_type}
                raw = await connectors.call_registry(reg_payload)
                data_json = json.dumps(raw)

            set_step_status(application_id, step, "DONE", data_json)
            log_audit(application_id, f"STEP_{step.upper()}", "SUCCESS")

        except Exception as e:
            set_step_status(application_id, step, "FAILED")
            log_audit(application_id, f"STEP_{step.upper()}", f"FAILED: {str(e)}")
            update_application_status(application_id, "FAILED")
            return {"status": "FAILED", "failed_step": step, "error": str(e)}

    update_application_status(application_id, "APPROVED")
    log_audit(application_id, "WORKFLOW", "APPROVED")
    return {"status": "APPROVED", "application_id": application_id}
