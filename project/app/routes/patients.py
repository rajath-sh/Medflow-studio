"""
Patient routes -- Protected with RBAC + tenant scoping.

Every route now requires:
1. Authentication (valid JWT)
2. Specific permission (checked via require_permission)
3. Tenant scoping (users only see their org's patients)
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone

from app.dependencies import get_db
from app.db_models import PatientRecord
from app.authorization import require_permission, get_tenant_id
from app.services.audit import log_audit_event
import uuid

router = APIRouter(prefix="/patients", tags=["Patients"])


class PatientCreate(BaseModel):
    name: str = Field(..., min_length=1)
    age: Optional[int] = None
    gender: Optional[str] = None
    height_cm: Optional[float] = None


# ── CREATE ────────────────────────────────────────────────

@router.post("/", status_code=201)
def create_patient(
    request: Request,
    data: PatientCreate,
    user: dict = Depends(require_permission("create:patient")),
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    patient = PatientRecord(
        patient_id=str(uuid.uuid4())[:8],
        name=data.name,
        age=data.age,
        gender=data.gender,
        height_cm=data.height_cm,
        tenant_id=tenant_id,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    
    log_audit_event(db, request, "patient.create", "success", patient.patient_id)
    
    return {"patient_id": patient.patient_id, "name": patient.name}


# ── LIST ──────────────────────────────────────────────────

@router.get("/")
def list_patients(
    request: Request,
    user: dict = Depends(require_permission("read:patient")),
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """List patients -- filtered by tenant (multi-tenancy)."""
    patients = db.query(PatientRecord).filter(
        PatientRecord.tenant_id == tenant_id,
        PatientRecord.deleted_at.is_(None),
    ).all()
    
    log_audit_event(db, request, "patient.list", "success", f"returned:{len(patients)}")
    
    return [
        {
            "id": str(p.id),
            "patient_id": p.patient_id,
            "name": p.name,
            "age": p.age,
            "gender": p.gender,
            "height_cm": p.height_cm,
        }
        for p in patients
    ]


# ── GET BY ID ─────────────────────────────────────────────

@router.get("/{patient_id}")
def get_patient(
    request: Request,
    patient_id: str,
    user: dict = Depends(require_permission("read:patient")),
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    patient = db.query(PatientRecord).filter(
        PatientRecord.patient_id == patient_id,
        PatientRecord.tenant_id == tenant_id,
        PatientRecord.deleted_at.is_(None),
    ).first()
    if not patient:
        log_audit_event(db, request, "patient.read", "failure", patient_id)
        raise HTTPException(status_code=404, detail="Patient not found")
        
    log_audit_event(db, request, "patient.read", "success", patient_id)
        
    return {
        "id": str(patient.id),
        "patient_id": patient.patient_id,
        "name": patient.name,
        "age": patient.age,
        "gender": patient.gender,
        "height_cm": patient.height_cm,
    }


# ── UPDATE ────────────────────────────────────────────────

@router.put("/{patient_id}")
def update_patient(
    request: Request,
    patient_id: str,
    data: PatientCreate,
    user: dict = Depends(require_permission("update:patient")),
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    patient = db.query(PatientRecord).filter(
        PatientRecord.patient_id == patient_id,
        PatientRecord.tenant_id == tenant_id,
        PatientRecord.deleted_at.is_(None),
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    patient.name = data.name
    if data.age is not None:
        patient.age = data.age
    if data.gender is not None:
        patient.gender = data.gender
    if data.height_cm is not None:
        patient.height_cm = data.height_cm

    db.commit()
    db.refresh(patient)
    
    log_audit_event(db, request, "patient.update", "success", patient_id)
    
    return {"patient_id": patient.patient_id, "name": patient.name}


# ── DELETE (soft) ─────────────────────────────────────────

@router.delete("/{patient_id}")
def delete_patient(
    request: Request,
    patient_id: str,
    user: dict = Depends(require_permission("delete:patient")),
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    """Soft delete -- sets deleted_at instead of removing the row."""
    patient = db.query(PatientRecord).filter(
        PatientRecord.patient_id == patient_id,
        PatientRecord.tenant_id == tenant_id,
        PatientRecord.deleted_at.is_(None),
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    patient.deleted_at = datetime.now(timezone.utc)
    db.commit()
    
    log_audit_event(db, request, "patient.delete", "success", patient_id)
    
    return {"message": "Patient deleted"}
