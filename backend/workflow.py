import json
from typing import Dict, Any, Optional, List
from sqlmodel import Session, select
from db import engine
from models_db import Application, WorkflowStep, WorkflowConfig
from consent import get_active_consent_token, verify_consent_jwt, ConsentMissingException
import connectors
import mapping
from audit import log_audit
from identity import resolve_or_create_person, get_local_id

# Default fallback step lists if DB config is uninitialized
DEFAULT_WORKFLOW_STEPS = {
    "business_registration": ["identity", "tax", "address", "registry"],
    "trade_license": ["identity", "tax", "address"]
}

STEP_REQUIRED_SCOPES = {
    "identity": "identity:verify",
    "tax": "tax:verify",
    "address": "address:verify",
    "registry": "registry:write"
}

def get_workflow_steps(service_type: str) -> List[str]:
    """Config-Driven Workflow: Reads step sequences from workflow_configs table in DB."""
    with Session(engine) as session:
        cfg = session.exec(select(WorkflowConfig).where(WorkflowConfig.service_type == service_type)).first()
        if cfg and cfg.steps_json:
            try:
                return json.loads(cfg.steps_json)
            except Exception:
                pass
    return DEFAULT_WORKFLOW_STEPS.get(service_type, ["identity", "tax", "address", "registry"])

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

async def run_workflow(application_id: str, allow_reuse: bool = False, consent_token_override: Optional[str] = None):
    with Session(engine) as session:
        app = session.exec(select(Application).where(Application.id == application_id)).first()
        if not app:
            raise ValueError(f"Application {application_id} not found")
        citizen_id = app.citizen_id
        service_type = app.service_type

    # 1. Boundary 3 Consent Gate Check & Token Retrieval
    consent_jwt = consent_token_override or get_active_consent_token(citizen_id, service_type)
    if not consent_jwt:
        log_audit(application_id, "CONSENT_CHECK", "FAILED_NO_ACTIVE_CONSENT")
        update_application_status(application_id, "FAILED")
        raise ConsentMissingException(f"No active signed consent token found for citizen {citizen_id} for purpose {service_type}")

    # Verify root consent token
    consent_claims = verify_consent_jwt(consent_jwt)
    log_audit(application_id, "CONSENT_CHECK", "VERIFIED_ACTIVE_SIGNED_JWT")
    update_application_status(application_id, "IN_PROGRESS")

    # Extract self-declared local IDs from signed consent claims
    local_ids = consent_claims.get("local_ids", {})
    pan_from_consent = local_ids.get("tax", "ABCDE1234F")
    owner_code_from_consent = local_ids.get("municipality", "OWN77821")

    # Identity Resolution: Create/Resolve GovBridge Person Anchor (e.g. P-10001)
    gb_person_id = resolve_or_create_person(citizen_id, local_ids)
    with Session(engine) as session:
        app_db = session.exec(select(Application).where(Application.id == application_id)).first()
        if app_db:
            app_db.govbridge_person_id = gb_person_id
            session.add(app_db)
            session.commit()

    # Load steps dynamically (Config-driven workflow)
    steps = get_workflow_steps(service_type)

    identity_name = None
    taxpayer_name = None

    # Step Execution Loop with Defense-in-Depth Scope Checking at EACH Step
    for step in steps:
        set_step_status(application_id, step, "IN_PROGRESS")
        log_audit(application_id, f"STEP_{step.upper()}", "IN_PROGRESS")

        # Boundary 3 Defense-In-Depth: Re-check scope at individual step!
        required_scope = STEP_REQUIRED_SCOPES.get(step)
        if required_scope:
            verify_consent_jwt(consent_jwt, required_scope=required_scope)
            log_audit(application_id, f"SCOPE_VERIFY_{step.upper()}", f"SCOPE_OK:{required_scope}")

        # Reuse fast-path check
        if allow_reuse and step != "registry":
            reused_data = check_reusable_step(citizen_id, step)
            if reused_data:
                set_step_status(application_id, step, "DONE", reused_data)
                log_audit(application_id, f"STEP_{step.upper()}", "SKIPPED_REUSE")
                continue

        try:
            if step == "identity":
                # Translate: identity department local ID for citizen
                dept_local_id = get_local_id(gb_person_id, "identity", default_fallback=citizen_id)
                raw = await connectors.call_identity(dept_local_id)
                canonical_obj = mapping.map_identity(raw)
                identity_name = canonical_obj.name
                data_json = canonical_obj.model_dump_json()

            elif step == "tax":
                # Translate: GovBridge person ID -> tax department PAN local ID
                dept_local_id = get_local_id(gb_person_id, "tax", default_fallback=pan_from_consent)
                raw_xml = await connectors.call_tax(dept_local_id)
                canonical_obj = mapping.map_tax(raw_xml)
                # Parse taxpayer name for cross-department fraud check
                try:
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(raw_xml.strip())
                    name_elem = root.find("TaxpayerName")
                    if name_elem is not None:
                        taxpayer_name = name_elem.text
                except Exception:
                    pass
                data_json = canonical_obj.model_dump_json()

            elif step == "address":
                # Translate: GovBridge person ID -> municipality department owner code
                dept_local_id = get_local_id(gb_person_id, "municipality", default_fallback=owner_code_from_consent)
                raw = await connectors.call_municipality(dept_local_id)
                canonical_obj = mapping.map_municipality(raw)
                data_json = canonical_obj.model_dump_json()

            elif step == "registry":
                reg_payload = {"applicant_name": identity_name or "Rahul Kumar", "service": service_type}
                raw = await connectors.call_registry(reg_payload)
                data_json = json.dumps(raw)

            set_step_status(application_id, step, "DONE", data_json)
            log_audit(application_id, f"STEP_{step.upper()}", "SUCCESS")

        except Exception as e:
            set_step_status(application_id, step, "FAILED")
            log_audit(application_id, f"STEP_{step.upper()}", f"FAILED: {str(e)}")
            update_application_status(application_id, "FAILED")
            return {"status": "FAILED", "failed_step": step, "error": str(e)}

    # Fraud Safeguard — Cross-department consistency check
    if identity_name and taxpayer_name and identity_name.strip().lower() != taxpayer_name.strip().lower():
        log_audit(application_id, "FRAUD_CHECK", f"FLAGGED_MANUAL_REVIEW:name_mismatch_identity_vs_tax ({identity_name} vs {taxpayer_name})")
        update_application_status(application_id, "MANUAL_REVIEW_FLAGGED")
        return {
            "status": "MANUAL_REVIEW_FLAGGED",
            "application_id": application_id,
            "reason": "name_mismatch_identity_vs_tax",
            "details": f"Identity dept name '{identity_name}' does not match Tax dept name '{taxpayer_name}'"
        }

    update_application_status(application_id, "APPROVED")
    log_audit(application_id, "WORKFLOW", "APPROVED")
    return {"status": "APPROVED", "application_id": application_id}
