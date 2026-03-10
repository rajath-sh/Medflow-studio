import os
from parser import load_workflow
from ir_builder import build_ir
from generator import generate_project

# Get absolute path to this file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Build correct path to workflow file
workflow_path = os.path.join(
    BASE_DIR,
    "..",
    "workflow-spec",
    "examples",
    "simple_etl.json"
)

workflow_dict = load_workflow(workflow_path)
workflow = build_ir(workflow_dict)

generate_project(workflow)
