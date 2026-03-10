import os
import sys

# In Docker, the app root is /app
MEDFLOW_ROOT = "/app"

from app.celery_app import celery_app
from app.database import SessionLocal
from app.db_models import Job, JobLog
from datetime import datetime, timezone
from app.compiler.ir_builder import build_ir
from app.compiler.generator import generate_project
from app.compiler.packager import package_project


@celery_app.task(bind=True, max_retries=3)
def generate_project_task(self, job_id: str, workflow_definition: dict):
    db = SessionLocal()
    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        db.close()
        return

    job.status = "running"
    job.started_at = datetime.now(timezone.utc)
    db.commit()

    def log_msg(level: str, msg: str):
        log = JobLog(job_id=job.id, level=level, message=msg)
        db.add(log)
        db.commit()

    log_msg("INFO", f"Starting project generation job: {job_id}")

    try:
        log_msg("INFO", "Building Intermediate Representation (IR)...")
        workflow_ir = build_ir(workflow_definition)
        
        output_dir = os.path.join(MEDFLOW_ROOT, f"out_job_{job_id}")
        zip_path = os.path.join(MEDFLOW_ROOT, f"project_{job_id}.zip")
        
        log_msg("INFO", "Generating code templates...")
        generate_project(
            workflow=workflow_ir, 
            output_dir=output_dir, 
            db=db, 
            user_id=str(job.created_by) if job.created_by else None
        )
        
        log_msg("INFO", "Packaging into ZIP archive...")
        package_project(output_dir, zip_path)

        # Mark success
        job.status = "success"
        job.completed_at = datetime.now(timezone.utc)
        log_msg("INFO", f"Project generated successfully. Target: project_{job_id}.zip")

    except Exception as exc:
        job.status = "FAILED"
        job.error = str(exc)
        job.completed_at = datetime.now(timezone.utc)
        log_msg("ERROR", f"Project generation failed: {str(exc)}")
        
        db.commit()
        db.close()
        raise self.retry(exc=exc, countdown=10 * (2 ** self.request.retries))

    db.commit()
    db.close()
    return {"status": "SUCCESS", "job_id": job_id, "zip_path": zip_path}
