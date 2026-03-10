import pytest
from pydantic import ValidationError
from app.ai.schemas import GeneratedNode, GeneratedEdge, GeneratedWorkflowResult

def test_generated_node_validation():
    # Valid node
    node = GeneratedNode(id="ab12cd34", type="source", label="My Source", config={"source_type": "csv"})
    assert node.id == "ab12cd34"
    assert node.type == "source"

    # Missing required field
    with pytest.raises(ValidationError):
        GeneratedNode(id="ab12cd34", type="source")

def test_generated_edge_validation():
    edge = GeneratedEdge(**{"from": "node_a", "to": "node_b"})
    
    # We use alias 'from' for 'from_' in python
    assert edge.from_ == "node_a"
    assert edge.to == "node_b"

def test_workflow_result_schema():
    data = {
        "name": "Test Workflow",
        "nodes": [
            {"id": "n1", "type": "source", "label": "Start", "config": {}},
            {"id": "n2", "type": "destination", "label": "End", "config": {}}
        ],
        "edges": [
            {"from": "n1", "to": "n2"}
        ],
        "explanation": "This is a basic test workflow."
    }
    
    result = GeneratedWorkflowResult(**data)
    assert result.name == "Test Workflow"
    assert len(result.nodes) == 2
    assert len(result.edges) == 1
    assert result.explanation.startswith("This is")
