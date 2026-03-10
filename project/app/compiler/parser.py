import json
from .validator import validate_workflow_dict

def load_workflow(workflow_path: str) -> dict:
    """
    Load, parse, and validate a workflow JSON file.
    """
    import os
    if not os.path.exists(workflow_path):
        raise FileNotFoundError(f"Workflow file not found: {workflow_path}")

    with open(workflow_path, "r", encoding="utf-8") as f:
        workflow = json.load(f)

    # Validate before returning
    is_valid, msg = validate_workflow_dict(workflow)
    if not is_valid:
        raise ValueError(f"Invalid workflow: {msg}")

    return workflow
