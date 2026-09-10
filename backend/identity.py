import uuid
from sqlmodel import Session, select
from db import engine
from models_db import IdentityMapping

def resolve_or_create_person(citizen_id: str, pan: str = "", owner_code: str = "") -> str:
    with Session(engine) as session:
        # Lookup existing mapping for citizen_id under department 'identity'
        stmt = select(IdentityMapping).where(
            IdentityMapping.department == "identity",
            IdentityMapping.department_identifier == citizen_id
        )
        existing = session.exec(stmt).first()
        if existing:
            return existing.govbridge_id
        
        # Create new GovBridge person ID
        new_gb_id = f"P-{uuid.uuid4().hex[:6].upper()}"
        
        # Save mappings for identity, tax, municipality
        mappings = [
            IdentityMapping(govbridge_id=new_gb_id, department="identity", department_identifier=citizen_id)
        ]
        if pan:
            mappings.append(IdentityMapping(govbridge_id=new_gb_id, department="tax", department_identifier=pan))
        if owner_code:
            mappings.append(IdentityMapping(govbridge_id=new_gb_id, department="municipality", department_identifier=owner_code))
        
        for m in mappings:
            session.add(m)
        session.commit()
        return new_gb_id
