"""
Job routes -- Protected with RBAC + tenant scoping.
Handles job status checking and log retrieval.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.db_models import Job, JobLog
from app.authorization import require_permission, get_tenant_id

router = APIRouter(prefix="/jobs", tags=["Jobs"])

# ── LIST JOBS ─────────────────────────────────────────────

@router.get("/")
def list_jobs(
    user: dict = Depends(require_permission("read:job")),
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db),
    limit: int = 50,
):
    jobs = db.query(Job).filter(Job.tenant_id == tenant_id).order_by(Job.started_at.desc()).limit(limit).all()
    return [
        {
            "id": str(job.id),
            "workflow_id": str(job.workflow_id),
            "status": job.status,
            "error": job.error,
            "started_at": str(job.started_at) if job.started_at else None,
            "completed_at": str(job.completed_at) if job.completed_at else None,
        }
        for job in jobs
    ]

# ── GET JOB STATUS ────────────────────────────────────────

@router.get("/{job_id}")
def get_job(
    job_id: str,
    user: dict = Depends(require_permission("read:job")),
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    job = db.query(Job).filter(Job.id == job_id, Job.tenant_id == tenant_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "id": str(job.id),
        "workflow_id": str(job.workflow_id),
        "status": job.status,
        "error": job.error,
        "started_at": str(job.started_at) if job.started_at else None,
        "completed_at": str(job.completed_at) if job.completed_at else None,
    }


# ── GET JOB LOGS ──────────────────────────────────────────

@router.get("/{job_id}/logs")
def get_job_logs(
    job_id: str,
    user: dict = Depends(require_permission("read:job")),
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    # First verify ownership
    job = db.query(Job).filter(Job.id == job_id, Job.tenant_id == tenant_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    logs = db.query(JobLog).filter(JobLog.job_id == job_id).order_by(JobLog.timestamp.asc()).all()
    return [
        {
            "id": log.id,
            "level": log.level,
            "message": log.message,
            "timestamp": str(log.timestamp),
        }
        for log in logs
    ]
    
# ── DOWNLOAD JOB RESULT ───────────────────────────────────

@router.get("/{job_id}/download")
def download_job_result(
    job_id: str,
    user: dict = Depends(require_permission("read:job")),
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db),
):
    import os
    import logging
    from fastapi.responses import FileResponse
    
    logger = logging.getLogger("healthops.jobs")
    logger.info(f"Download request for job_id: {job_id}")
    
    # First verify ownership and existence
    job = db.query(Job).filter(Job.id == job_id, Job.tenant_id == tenant_id).first()
    if not job:
        logger.warning(f"Job {job_id} not found for tenant {tenant_id}")
        raise HTTPException(status_code=404, detail="Job not found")

    # Check status case-insensitively
    s = job.status
    current_status = (s.value if hasattr(s, 'value') else str(s)).lower()
    logger.info(f"Job {job_id} status (normalized): {current_status}")
    
    if current_status != "success":
        raise HTTPException(status_code=400, detail=f"Job status is '{current_status}', not 'success'")

    # The ZIP file path (shared via volume)
    MEDFLOW_ROOT = "/app"
    zip_path = os.path.join(MEDFLOW_ROOT, f"project_{job_id}.zip")
    logger.info(f"Checking for ZIP at: {zip_path}")

    if not os.path.exists(zip_path):
        logger.error(f"ZIP file not found at {zip_path} (exists check failed)")
        raise HTTPException(status_code=404, detail="Result file not found on server")

    logger.info(f"Serving ZIP file: {zip_path}")
    return FileResponse(
        path=zip_path,
        filename=f"project_{job_id}.zip",
        media_type="application/zip"
    )
