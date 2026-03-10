import os
import json
from jsonschema import validate, ValidationError

# Get the directory where the main app lives
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA_PATH = os.path.join(BASE_DIR, "workflow-spec", "workflow_schema.json")


def validate_workflow_dict(workflow: dict) -> tuple[bool, str]:
    """
    Validates a parsed workflow dictionary against:
    1. The JSON Schema
    2. DAG rules (no cycles, no orphans)
    Returns (is_valid, error_message).
    """
    
    # Load Schema
    if not os.path.exists(SCHEMA_PATH):
        return False, f"Schema file not found at {SCHEMA_PATH}"
        
    with open(SCHEMA_PATH, "r", encoding="utf-8") as schema_file:
        schema = json.load(schema_file)
        
    # 1. JSON Schema Validation
    try:
        validate(instance=workflow, schema=schema)
    except ValidationError as e:
        return False, f"JSON Schema Validation failed: {e.message}"
        
    # 2. DAG Validation
    nodes = workflow.get("nodes", [])
    edges = workflow.get("edges", [])
    
    node_ids = {node["id"] for node in nodes}
    in_degree = {n: 0 for n in node_ids}
    adj_list = {n: [] for n in node_ids}
    
    connected_nodes = set()

    for edge in edges:
        u = edge["from"]
        v = edge["to"]
        
        if u not in node_ids:
            return False, f"Edge from unknown node: {u}"
        if v not in node_ids:
            return False, f"Edge to unknown node: {v}"
            
        adj_list[u].append(v)
        in_degree[v] += 1
        
        connected_nodes.add(u)
        connected_nodes.add(v)
        
    # Check for orphan nodes
    if len(nodes) > 1:
        orphans = node_ids - connected_nodes
        if orphans:
            return False, f"Orphan nodes detected: {orphans}"

    # Check for cycles using Kahn's
    queue = [n for n in node_ids if in_degree[n] == 0]
    visited_count = 0
    
    if not queue and node_ids:
        return False, "Cycle detected: No start nodes found!"

    while queue:
        current = queue.pop(0)
        visited_count += 1
        
        for neighbor in adj_list[current]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
                
    if visited_count != len(node_ids):
        return False, "Cycle detected in workflow edges!"
        
    return True, "Valid"
