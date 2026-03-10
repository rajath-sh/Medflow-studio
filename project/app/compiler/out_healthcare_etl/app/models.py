import os
from pydantic import BaseModel
from typing import Optional


class PatientRecords(BaseModel):

    patient_id: str

    name: str

    height_cm: float


