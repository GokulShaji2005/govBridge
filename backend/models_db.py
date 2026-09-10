from typing import Optional, List
from sqlmodel import SQLModel, Field
from datetime import datetime

class UserProfile(SQLModel, table=True):
    __tablename__ = "user_profiles"
    id: Optional[int] = Field(default=None, primary_key=True)
    supabase_user_id: str = Field(index=True, unique=True)
    citizen_id: str = Field(index=True)
    name: str = "Rahul Kumar"
    role: str = "citizen"  # "citizen" | "officer"
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class Person(SQLModel, table=True):
    __tablename__ = "persons"
    govbridge_person_id: str = Field(primary_key=True)  # e.g. P-10001
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

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
    status: str = "ACTIVE"  # ACTIVE | REVOKED | SUPERSEDED
    consent_token: Optional[str] = None  # Signed JWT string
    granted_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class ConsentItem(SQLModel, table=True):
    __tablename__ = "consent_items"
    id: Optional[int] = Field(default=None, primary_key=True)
    consent_id: int
    scope_name: str  # "identity:verify" | "tax:verify" | "address:verify" | "registry:write"

class RevokedConsentToken(SQLModel, table=True):
    __tablename__ = "revoked_consent_tokens"
    id: Optional[int] = Field(default=None, primary_key=True)
    jti: str = Field(index=True, unique=True)
    revoked_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class AadhaarVerificationRecord(SQLModel, table=True):
    __tablename__ = "aadhaar_verifications"
    id: Optional[int] = Field(default=None, primary_key=True)
    verification_token: str = Field(index=True, unique=True)
    citizen_id: str = Field(index=True)
    aadhaar_ref: str
    name: str
    date_of_birth: str
    verified_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class WorkflowStep(SQLModel, table=True):
    __tablename__ = "workflow_steps"
    id: Optional[int] = Field(default=None, primary_key=True)
    application_id: str
    step_name: str  # "identity" | "tax" | "address" | "registry"
    status: str = "PENDING"  # PENDING | IN_PROGRESS | DONE | FAILED | REUSED
    data_json: Optional[str] = None  # canonical JSON serialized
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class WorkflowConfig(SQLModel, table=True):
    __tablename__ = "workflow_configs"
    service_type: str = Field(primary_key=True)  # "business_registration" | "trade_license"
    steps_json: str  # JSON list string e.g. '["identity", "tax", "address", "registry"]'

class IdentityMapping(SQLModel, table=True):
    __tablename__ = "identity_mappings"
    id: Optional[int] = Field(default=None, primary_key=True)
    govbridge_person_id: str = Field(index=True)  # e.g. P-10001
    department: str  # "identity" | "tax" | "municipality"
    department_local_id: str

class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_logs"
    id: Optional[int] = Field(default=None, primary_key=True)
    application_id: str
    action: str
    result: str  # "SUCCESS" | "FAILED" | "REVOKED" | "SKIPPED_REUSE"
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

