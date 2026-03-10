import os
import logging
from typing import Optional
from sqlalchemy.orm import Session
from app.ai.llm_client import llm_client
from app.ai.schemas import GeneratedProjectResult
from app.ai.prompts import CODE_GENERATION_PROMPT

logger = logging.getLogger("healthops.compiler")


def generate_project_with_ai(
    workflow, 
    output_dir: str,
    db: Optional[Session] = None,
    user_id: Optional[str] = None
) -> bool:
    """
    Attempt to generate the project using the Gemini LLM.
    Returns True if successful, False if it should fall back to templates.
    """
    if not llm_client.is_configured():
        logger.info("AI generation skipped: GEMINI_API_KEY not configured. Falling back to templates.")
        return False

    logger.info(f"Generating project for workflow '{workflow.name}' using AI...")
    
    # Serialize the workflow nodes to pass to the AI
    nodes_data = [{"id": n.id, "type": n.type, "config": n.config} for n in workflow.nodes]
    edges_data = [{"from": e.from_node, "to": e.to_node} for e in workflow.edges]
    
    user_prompt = f"""
    Build a microservice/ETL pipeline for the following MedFlow workflow.
    
    Workflow Name: {workflow.name}
    
    Nodes:
    {nodes_data}
    
    Edges:
    {edges_data}
    
    Please generate all necessary Python files (main.py, models.py, etl_pipeline.py if applicable) 
    and a README.md explaining how to run it.
    """

    try:
        result = llm_client.generate_structured(
            system_prompt=CODE_GENERATION_PROMPT,
            user_prompt=user_prompt,
            response_model=GeneratedProjectResult,
            temperature=0.2,
            db=db,
            user_id=user_id
        )
        
        # Write the AI-generated files to the output directory
        os.makedirs(output_dir, exist_ok=True)
        
        for file in result.files:
            file_path = os.path.join(output_dir, file.filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(file.content)
                
        # Write README
        with open(os.path.join(output_dir, "README.md"), "w", encoding="utf-8") as f:
            f.write(result.readme)
            
        logger.info("AI project generation successful.")
        return True
        
    except Exception as e:
        logger.error(f"AI project generation failed: {str(e)}. Falling back to templates.")
        return False
