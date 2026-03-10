from app.compiler.classifier import classify_workflow

import uuid

# Mock classes for workflow
class MockNode:
    def __init__(self, type, config=None):
        self.id = str(uuid.uuid4())[:8]
        self.type = type
        self.config = config or {}

class MockWorkflow:
    def __init__(self, nodes):
        self.nodes = nodes

def test_classifier_etl_pipeline():
    # Only sources, transforms, destinations
    nodes = [
        MockNode("source"),
        MockNode("transform"),
        MockNode("destination")
    ]
    workflow = MockWorkflow(nodes)
    assert classify_workflow(workflow) == "etl_pipeline"

def test_classifier_api_service():
    # Has API endpoints but no triggers
    nodes = [
        MockNode("api_endpoint"),
        MockNode("transform"),
        MockNode("destination")
    ]
    workflow = MockWorkflow(nodes)
    assert classify_workflow(workflow) == "api_service"

def test_classifier_hybrid():
    # Has both triggers (ETL) and APIs
    nodes = [
        MockNode("trigger"),
        MockNode("api_endpoint"),
        MockNode("destination")
    ]
    workflow = MockWorkflow(nodes)
    assert classify_workflow(workflow) == "hybrid"
