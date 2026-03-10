import os
from jinja2 import Environment, FileSystemLoader
from .classifier import classify_workflow
import sys
from typing import Optional

# To allow importing from the main app
from sqlalchemy.orm import Session
from app.config import get_settings
from .ai_generator import generate_project_with_ai

TYPE_MAP = {
    "str": "str",
    "string": "str",
    "int": "int",
    "float": "float",
    "bool": "bool"
}

def _ensure_infra(output_dir, workflow_type):
    """
    Ensures Dockerfile, docker-compose.yml, and requirements.txt exist.
    Will NOT overwrite if already present (e.g. from AI).
    """
    templates_dir = os.path.join(os.path.dirname(__file__), "templates")
    env = Environment(loader=FileSystemLoader(templates_dir))

    # 1. requirements.txt
    req_path = os.path.join(output_dir, "requirements.txt")
    if not os.path.exists(req_path):
        req_template = env.get_template("requirements.txt.j2")
        with open(req_path, "w") as f:
            f.write(req_template.render(has_api=(workflow_type in ["api_service", "hybrid"])))

    # 2. Dockerfile
    docker_path = os.path.join(output_dir, "Dockerfile")
    if not os.path.exists(docker_path):
        docker_template = env.get_template("Dockerfile.j2")
        with open(docker_path, "w") as f:
            f.write(docker_template.render())

    # 3. docker-compose.yml
    compose_path = os.path.join(output_dir, "docker-compose.yml")
    if not os.path.exists(compose_path):
        compose_template = env.get_template("docker-compose.yml.j2")
        with open(compose_path, "w") as f:
            f.write(compose_template.render())

def generate_project(
    workflow,
    output_dir="generated_project",
    db: Optional[Session] = None,
    user_id: Optional[str] = None
):
    # Classify workflow type early
    workflow_type = classify_workflow(workflow)

    # 1. Attempt AI-powered generation first
    if generate_project_with_ai(workflow, output_dir, db, user_id):
        # AI generated the core files. Ensure infra exists.
        _ensure_infra(output_dir, workflow_type)
        print(f"[SUCCESS] AI Project generated at {output_dir}")
        return

    # 2. Fall back to templates if AI fails or is not configured
    print("[INFO] Using template-based generation fallback")
    os.makedirs(output_dir, exist_ok=True)
    app_dir = os.path.join(output_dir, "app")
    os.makedirs(app_dir, exist_ok=True)

    # Set up Jinja2 environment
    templates_dir = os.path.join(os.path.dirname(__file__), "templates")
    env = Environment(loader=FileSystemLoader(templates_dir))

    # --------------------
    # Generate Models
    # --------------------
    models_data = []
    for node in workflow.nodes:
        if node.type == "destination" and node.config.get("destination_type") == "database":
            model_name = node.config.get("table", "Record").title().replace("_", "")
            fields = []
            for field, f_type in node.config.get("schema", {}).items():
                optional = f_type.endswith("?")
                b_type = f_type.replace("?", "")
                fields.append({
                    "name": field,
                    "type": TYPE_MAP.get(b_type, "str"),
                    "optional": optional
                })
            models_data.append({"name": model_name, "fields": fields})

    # Always generate models.py (even if empty) to satisfy relative imports
    models_template = env.get_template("models.py.j2")
    with open(os.path.join(app_dir, "models.py"), "w") as f:
        f.write(models_template.render(models=models_data))

    # --------------------
    # Generate Main / API / ETL
    # --------------------
    endpoints = []
    for node in workflow.nodes:
        if node.type in ["api_endpoint", "destination"]:
            endpoints.append({
                "name": f"handle_{node.id}",
                "method": node.config.get("method", "POST"),
                "route": "/" + node.config.get("route", node.config.get("table", node.id)).lstrip("/"),
                "input_model": node.config.get("table", "").title().replace("_", "") if node.type == "destination" else None,
                "output_model": None
            })
            
    # Always generate main.py as a microservice entry point
    main_template = env.get_template("main.py.j2")
    with open(os.path.join(app_dir, "main.py"), "w") as f:
        f.write(main_template.render(
            workflow_name=workflow.name,
            endpoints=endpoints
        ))

    if workflow_type in ["etl_pipeline", "hybrid"]:
        etl_template = env.get_template("etl_pipeline.py.j2")
        with open(os.path.join(output_dir, "etl_pipeline.py"), "w") as f:
            f.write(etl_template.render(
                workflow_name=workflow.name,
                nodes=workflow.nodes
            ))

    # --------------------
    # Generate Environment & Config
    # --------------------
    _ensure_infra(output_dir, workflow_type)

    # Ensure app module imports nicely
    open(os.path.join(app_dir, "__init__.py"), "w").close()

    print(f"[SUCCESS] Project generated ({workflow_type}) at {output_dir}")
