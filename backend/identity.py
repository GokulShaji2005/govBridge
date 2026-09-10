import uuid
from typing import Dict, Optional
from sqlmodel import Session, select
from db import engine
from models_db import Person, IdentityMapping

def resolve_or_create_person(citizen_id: str, local_ids: Optional[Dict[str, str]] = None) -> str:
    """
    Master Data Linking (Identity Resolution):
    C10291 is the trigger — first time identity verification succeeds for a citizen_id,
    GovBridge creates a new person anchor (e.g. P-10001) and links department local IDs.
    """
    local_ids = local_ids or {}
    pan = local_ids.get("tax", "ABCDE1234F")
    owner_code = local_ids.get("municipality", "OWN77821")

    with Session(engine) as session:
        # Lookup existing mapping for citizen_id under department 'identity'
        stmt = select(IdentityMapping).where(
            IdentityMapping.department == "identity",
            IdentityMapping.department_local_id == citizen_id
        )
        existing = session.exec(stmt).first()
        if existing:
            gb_person_id = existing.govbridge_person_id
            # Ensure tax & municipality mappings are present if updated
            tax_map = session.exec(select(IdentityMapping).where(
                IdentityMapping.govbridge_person_id == gb_person_id,
                IdentityMapping.department == "tax"
            )).first()
            if not tax_map and pan:
                session.add(IdentityMapping(govbridge_person_id=gb_person_id, department="tax", department_local_id=pan))

            muni_map = session.exec(select(IdentityMapping).where(
                IdentityMapping.govbridge_person_id == gb_person_id,
                IdentityMapping.department == "municipality"
            )).first()
            if not muni_map and owner_code:
                session.add(IdentityMapping(govbridge_person_id=gb_person_id, department="municipality", department_local_id=owner_code))

            session.commit()
            return gb_person_id

        # Create new GovBridge neutral person ID anchor
        person_count = len(session.exec(select(Person)).all())
        new_gb_id = f"P-{10000 + person_count + 1}"
        session.add(Person(govbridge_person_id=new_gb_id))

        mappings = [
            IdentityMapping(govbridge_person_id=new_gb_id, department="identity", department_local_id=citizen_id)
        ]
        if pan:
            mappings.append(IdentityMapping(govbridge_person_id=new_gb_id, department="tax", department_local_id=pan))
        if owner_code:
            mappings.append(IdentityMapping(govbridge_person_id=new_gb_id, department="municipality", department_local_id=owner_code))

        for m in mappings:
            session.add(m)
        session.commit()
        return new_gb_id

def get_local_id(person_id: str, department: str, default_fallback: str = "") -> str:
    """
    Direction of translation when calling departments:
    Always translate GovBridge's internal ID -> department's own local ID before calling.
    Never send P-10001 to any department!
    """
    with Session(engine) as session:
        stmt = select(IdentityMapping).where(
            IdentityMapping.govbridge_person_id == person_id,
            IdentityMapping.department == department
        )
        mapping = session.exec(stmt).first()
        if mapping and mapping.department_local_id:
            return mapping.department_local_id
        return default_fallback
