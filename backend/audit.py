from typing import List, Dict, Any
from sqlmodel import Session, select
from db import engine
from models_db import AuditLog

def log_audit(application_id: str, action: str, result: str) -> AuditLog:
    with Session(engine) as session:
        log_entry = AuditLog(
            application_id=application_id,
            action=action,
            result=result
        )
        session.add(log_entry)
        session.commit()
        session.refresh(log_entry)
        return log_entry

def get_audit_logs(application_id: str) -> List[Dict[str, Any]]:
    with Session(engine) as session:
        logs = session.exec(
            select(AuditLog)
            .where(AuditLog.application_id == application_id)
            .order_by(AuditLog.id)
        ).all()
        return [
            {
                "id": log.id,
                "application_id": log.application_id,
                "action": log.action,
                "result": log.result,
                "timestamp": log.timestamp
            }
            for log in logs
        ]
