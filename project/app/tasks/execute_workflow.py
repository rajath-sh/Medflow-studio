import time
from app.celery_app import celery_app
from app.database import SessionLocal
from app.db_models import Job, JobLog
from datetime import datetime, timezone
import json

@celery_app.task(bind=True, max_retries=3)
def execute_workflow_task(self, job_id: str, workflow_definition: dict):
    """
    Background task to execute a workflow.
    """
    db = SessionLocal()
    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        db.close()
        return

    # Update state to RUNNING
    job.status = "running"
    job.started_at = datetime.now(timezone.utc)
    db.commit()

    def log_msg(level: str, msg: str):
        log = JobLog(job_id=job.id, level=level, message=msg)
        db.add(log)
        db.commit()

    log_msg("INFO", f"Starting workflow execution job: {job_id}")

    try:
        # Example execution (placeholder for real dynamic node execution)
        nodes = workflow_definition.get("nodes", [])
        log_msg("INFO", f"Identified {len(nodes)} nodes to execute.")

        for i, node in enumerate(nodes):
            log_msg("INFO", f"Executing node {i+1}: {node.get('type')}")
            # Simulate work
            time.sleep(1)

        # Mark Success
        job.status = "SUCCESS"
        job.completed_at = datetime.now(timezone.utc)
        log_msg("INFO", "Workflow executed successfully.")

    except Exception as exc:
        # Log failure
        job.status = "FAILED"
        job.error = str(exc)
        job.completed_at = datetime.now(timezone.utc)
        log_msg("ERROR", f"Workflow execution failed: {str(exc)}")
        
        db.commit()
        db.close()
        # Retry with exponential backoff (e.g. 10s, 20s, 40s)
        raise self.retry(exc=exc, countdown=10 * (2 ** self.request.retries))

    db.commit()
    db.close()
    return {"status": "SUCCESS", "job_id": job_id}
