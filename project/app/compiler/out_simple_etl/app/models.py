import os
from pydantic import BaseModel
from typing import Optional


class PatientsClean(BaseModel):

    patient_id: str

    name: str

    age: int

    gender: str | None = None

    height_cm: float | None = None


