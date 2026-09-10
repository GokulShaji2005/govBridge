from typing import Optional, List
from sqlmodel import SQLModel, Field
from datetime import datetime

class Application(SQLModel, table=True):
    __tablename__ = "applications"
    id: str = Field(primary_key=True)  # GB-2026-000124
    citizen_id: str
    service_type: str  # "business_registration" | "trade_license"
    status: str = "PENDING"  # PENDING, IN_PROGRESS, APPROVED, REJECTED, FAILED
    govbridge_person_id: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class Consent(SQLModel, table=True):
    __tablename__ = "consents"
    id: Optional[int] = Field(default=None, primary_key=True)
    citizen_id: str
    purpose: str  # e.g., "business_registration"
    status: str = "ACTIVE"  # ACTIVE | REVOKED
    granted_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class ConsentItem(SQLModel, table=True):
    __tablename__ = "consent_items"
    id: Optional[int] = Field(default=None, primary_key=True)
    consent_id: int
    scope_name: str  # "identity" | "tax" | "address" | "registry"

class WorkflowStep(SQLModel, table=True):
    __tablename__ = "workflow_steps"
    id: Optional[int] = Field(default=None, primary_key=True)
    application_id: str
    step_name: str  # "identity" | "tax" | "address" | "registry"
    status: str = "PENDING"  # PENDING | IN_PROGRESS | DONE | FAILED | REUSED
    data_json: Optional[str] = None  # canonical JSON serialized
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class IdentityMapping(SQLModel, table=True):
    __tablename__ = "identity_mappings"
    id: Optional[int] = Field(default=None, primary_key=True)
    govbridge_id: str
    department: str  # "identity" | "tax" | "municipality"
    department_identifier: str

class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_logs"
    id: Optional[int] = Field(default=None, primary_key=True)
    application_id: str
    action: str
    result: str  # "SUCCESS" | "FAILED" | "REVOKED" | "SKIPPED_REUSE"
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
