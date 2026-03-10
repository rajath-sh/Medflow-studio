from .ir_builder import Workflow

def classify_workflow(workflow: Workflow) -> str:
    """
    Classifies a workflow into an execution type:
    - 'etl_pipeline': Only data extraction, transforms, and loads. Contains 'trigger', 'data_source'. No APIs.
    - 'api_service': Exposes API endpoints and maps them to transforms/destinations.
    - 'hybrid': Contains both active data ingestion (e.g. scheduled sources) AND exposed APIs.
    """
    has_api = False
    has_trigger_or_source = False
    
    for node in workflow.nodes:
        if node.type == "api_endpoint":
            has_api = True
        elif node.type in ["trigger", "data_source", "source"]:
            has_trigger_or_source = True
            
    if has_api and has_trigger_or_source:
        workflow.workflow_type = "hybrid"
    elif has_api:
        workflow.workflow_type = "api_service"
    else:
        workflow.workflow_type = "etl_pipeline"
        
    return workflow.workflow_type
