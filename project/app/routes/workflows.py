"""
Workflow routes -- Protected with RBAC + tenant scoping.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.dependencies import get_db
from app.db_models import Workflow
from app.authorization import require_permission, get_tenant_id

router = APIRouter(prefix="/workflows", tags=["Workflows"])


class WorkflowCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    definition: Optional[dict] = None


# ── CREATE ────────────────────────────────────────────────

@router.post("/", status_code=201)
def create_workflow(
    data: WorkflowCreateRequest,
    user: dict = Depends(require_permission("create:workflow")),
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    workflow = Workflow(
        name=data.name,
        description=data.description,
        definition=data.definition,
        created_by=user.get("user_id"),
        tenant_id=tenant_id,
    )
    db.add(workflow)
    db.commit()
    db.refresh(workflow)
    return {"id": str(workflow.id), "name": workflow.name}


# ── LIST ──────────────────────────────────────────────────

@router.get("/")
def list_workflows(
    user: dict = Depends(require_permission("read:workflow")),
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    workflows = db.query(Workflow).filter(
        Workflow.tenant_id == tenant_id,
        Workflow.deleted_at.is_(None),
    ).all()
    return [
        {
            "id": str(wf.id),
            "name": wf.name,
            "description": wf.description,
            "version": wf.version,
            "definition": wf.definition,
        }
        for wf in workflows
    ]


# ── GET BY ID ─────────────────────────────────────────────

@router.get("/{workflow_id}")
def get_workflow(
    workflow_id: str,
    user: dict = Depends(require_permission("read:workflow")),
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    workflow = db.query(Workflow).filter(
        Workflow.id == workflow_id,
        Workflow.tenant_id == tenant_id,
        Workflow.deleted_at.is_(None),
    ).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {
        "id": str(workflow.id),
        "name": workflow.name,
        "description": workflow.description,
        "version": workflow.version,
        "definition": workflow.definition,
    }


# ── DELETE ────────────────────────────────────────────────

@router.delete("/{workflow_id}")
def delete_workflow(
    workflow_id: str,
    user: dict = Depends(require_permission("delete:workflow")),
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    from datetime import datetime, timezone
    workflow = db.query(Workflow).filter(
        Workflow.id == workflow_id,
        Workflow.tenant_id == tenant_id,
        Workflow.deleted_at.is_(None),
    ).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    workflow.deleted_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": "Workflow deleted"}

# ── EXECUTE ───────────────────────────────────────────────

@router.post("/{workflow_id}/execute", status_code=202)
def execute_workflow(
    workflow_id: str,
    user: dict = Depends(require_permission("create:job")),
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    from app.db_models import Job
    from app.tasks.execute_workflow import execute_workflow_task
    
    workflow = db.query(Workflow).filter(
        Workflow.id == workflow_id,
        Workflow.tenant_id == tenant_id,
        Workflow.deleted_at.is_(None),
    ).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    job = Job(workflow_id=workflow.id, status="PENDING", created_by=user.get("user_id"), tenant_id=tenant_id)
    db.add(job)
    db.commit()
    db.refresh(job)

    # Spawn Celery task
    execute_workflow_task.delay(str(job.id), workflow.definition)

    return {"message": "Execution started", "job_id": str(job.id)}


# ── GENERATE ──────────────────────────────────────────────

@router.post("/{workflow_id}/generate", status_code=202)
def generate_project(
    workflow_id: str,
    user: dict = Depends(require_permission("create:job")),
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    from app.db_models import Job
    from app.tasks.generate_project import generate_project_task
    
    workflow = db.query(Workflow).filter(
        Workflow.id == workflow_id,
        Workflow.tenant_id == tenant_id,
        Workflow.deleted_at.is_(None),
    ).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    job = Job(workflow_id=workflow.id, status="PENDING", created_by=user.get("user_id"), tenant_id=tenant_id)
    db.add(job)
    db.commit()
    db.refresh(job)

    # Spawn Celery task
    generate_project_task.delay(str(job.id), workflow.definition)

    return {"message": "Generation started", "job_id": str(job.id)}
