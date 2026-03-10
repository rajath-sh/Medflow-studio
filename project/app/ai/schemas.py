"""
HealthOps Studio — AI Structured Output Schemas

Defines the exact JSON structures we expect the LLM to return.
We pass these to google-genai's response_schema parameter to guarantee output format.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

# ── 1. Workflow Generation Schemas ─────────────────────────

class GeneratedNode(BaseModel):
    id: str = Field(description="A short, unique 8-character ID for the node")
    type: str = Field(description="Must be one of: source, transform, destination, api_endpoint, trigger")
    label: str = Field(description="A human-readable label for the node")
    config: Dict[str, Any] = Field(description="Configuration parameters specific to the node type")

class GeneratedEdge(BaseModel):
    from_: str = Field(alias="from", description="ID of the source node")
    to: str = Field(description="ID of the target node")

class GeneratedWorkflowResult(BaseModel):
    """Schema for parsing natural language into a MedFlow workflow."""
    name: str = Field(description="A descriptive name for the workflow")
    nodes: List[GeneratedNode] = Field(description="List of nodes in the workflow pipeline")
    edges: List[GeneratedEdge] = Field(description="List of connections between the nodes")
    explanation: str = Field(description="A brief explanation of how this pipeline fulfills the user's request")

# ── 2. Code Generation Schemas ─────────────────────────────

class GeneratedFile(BaseModel):
    filename: str = Field(description="The relative path and filename, e.g. 'app/models.py'")
    content: str = Field(description="The complete, raw code content of the file")
    
class GeneratedProjectResult(BaseModel):
    """Schema for AI-generated FastAPI microservices/ETL pipelines."""
    files: List[GeneratedFile] = Field(description="List of files to create for the project")
    readme: str = Field(description="Content for the project README.md")
