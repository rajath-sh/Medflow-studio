from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import List
import os
import shutil
import csv
from app.authorization import require_permission

router = APIRouter(tags=["Datasets"])

DATA_ROOT = os.environ.get("DATA_DIR", "/app/data")

def get_base_path(category: str, identifier: str = None) -> str:
    path = os.path.join(DATA_ROOT, category)
    if identifier:
        path = os.path.join(path, str(identifier))
    os.makedirs(path, exist_ok=True)
    return path

# ── General Datasets ──────────────────────────────────────

@router.post("/datasets/general")
async def upload_general_dataset(
    file: UploadFile = File(...),
    user: dict = Depends(require_permission("create:patient")) # Same permission level for now
):
    path = get_base_path("general")
    file_path = os.path.join(path, file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return {"message": "File uploaded successfully", "filename": file.filename, "path": f"general/{file.filename}"}

@router.get("/datasets/general")
def list_general_datasets(
    user: dict = Depends(require_permission("read:patient"))
):
    path = get_base_path("general")
    files = []
    for f in os.listdir(path):
        if os.path.isfile(os.path.join(path, f)):
            files.append({
                "filename": f,
                "path": f"general/{f}",
                "size": os.path.getsize(os.path.join(path, f))
            })
    return files

@router.delete("/datasets/general/{filename}")
def delete_general_dataset(
    filename: str,
    user: dict = Depends(require_permission("delete:patient"))
):
    file_path = os.path.join(get_base_path("general"), filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        return {"message": "File deleted"}
    raise HTTPException(status_code=404, detail="File not found")

# ── Patient Datasets ──────────────────────────────────────

@router.post("/patients/{patient_id}/datasets")
async def upload_patient_dataset(
    patient_id: str,
    file: UploadFile = File(...),
    user: dict = Depends(require_permission("update:patient"))
):
    path = get_base_path("patients", patient_id)
    file_path = os.path.join(path, file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return {"message": "File uploaded successfully", "filename": file.filename, "path": f"patients/{patient_id}/{file.filename}"}

@router.get("/patients/{patient_id}/datasets")
def list_patient_datasets(
    patient_id: str,
    user: dict = Depends(require_permission("read:patient"))
):
    path = get_base_path("patients", patient_id)
    files = []
    for f in os.listdir(path):
        if os.path.isfile(os.path.join(path, f)):
            files.append({
                "filename": f,
                "path": f"patients/{patient_id}/{f}",
                "size": os.path.getsize(os.path.join(path, f))
            })
    return files

@router.delete("/patients/{patient_id}/datasets/{filename}")
def delete_patient_dataset(
    patient_id: str,
    filename: str,
    user: dict = Depends(require_permission("update:patient"))
):
    file_path = os.path.join(get_base_path("patients", patient_id), filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        return {"message": "File deleted"}
    raise HTTPException(status_code=404, detail="File not found")

# ── Preview Endpoint ──────────────────────────────────────

@router.get("/datasets/preview")
def preview_dataset(
    path: str,
    user: dict = Depends(require_permission("read:patient"))
):
    """
    Reads the first few rows of a dataset to provide context to the AI.
    Path format expected: 'general/filename.csv' or 'patients/id/filename.csv'
    """
    if ".." in path or path.startswith("/"):
        raise HTTPException(status_code=400, detail="Invalid path")
        
    full_path = os.path.join(DATA_ROOT, path)
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="File not found")
        
    try:
        preview_data = []
        headers = []
        with open(full_path, "r", encoding="utf-8") as f:
            if full_path.endswith(".csv"):
                reader = csv.reader(f)
                try:
                    headers = next(reader)
                    for _ in range(3): # Get up to 3 sample rows
                        preview_data.append(next(reader))
                except StopIteration:
                    pass
            else:
                # Basic text preview for non-CSV files
                lines = [next(f) for _ in range(5)]
                preview_data = [{"content": line.strip()} for line in lines]
                
        return {
            "path": path,
            "headers": headers,
            "sample_rows": preview_data,
            "file_type": "csv" if full_path.endswith(".csv") else "text"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")
