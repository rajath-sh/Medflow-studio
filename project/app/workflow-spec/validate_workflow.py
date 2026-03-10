import json
import os
from jsonschema import validate, ValidationError

# Get the directory where this file lives
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Build full paths
schema_path = os.path.join(BASE_DIR, "workflow_schema.json")
workflow_path = os.path.join(BASE_DIR, "examples", "healthcare_etl.json")

def validate_dag(nodes, edges):
    """
    Validates that the workflow is a valid Directed Acyclic Graph (DAG) and has no orphan nodes.
    Returns (is_valid, error_message).
    """
    node_ids = {node["id"] for node in nodes}
    in_degree = {n: 0 for n in node_ids}
    adj_list = {n: [] for n in node_ids}
    
    # Track nodes that have edges
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
        
    # Check for orphan nodes (nodes with no edges, unless it's a 1-node workflow)
    if len(nodes) > 1:
        orphans = node_ids - connected_nodes
        if orphans:
            return False, f"Orphan nodes detected (no edges connecting them): {orphans}"

    # Check for cycles using Kahn's Algorithm
    queue = [n for n in node_ids if in_degree[n] == 0]
    visited_count = 0
    
    if not queue and node_ids:
        return False, "Cycle detected: No start nodes (in-degree 0) found!"

    while queue:
        current = queue.pop(0)
        visited_count += 1
        
        for neighbor in adj_list[current]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
                
    if visited_count != len(node_ids):
        return False, "Cycle detected in workflow edges!"
        
    return True, "DAG is valid"

def validate_workflow_file(file_path):
    print(f"Validating {os.path.basename(file_path)}...")
    
    with open(schema_path, "r") as schema_file:
        schema = json.load(schema_file)

    try:
        with open(file_path, "r", encoding="utf-8") as workflow_file:
            workflow = json.load(workflow_file)
            
        # 1. JSON Schema Validation
        validate(instance=workflow, schema=schema)
        print("[OK] JSON Schema is valid")
        
        # 2. DAG Validation
        nodes = workflow.get("nodes", [])
        edges = workflow.get("edges", [])
        
        is_dag_valid, dag_msg = validate_dag(nodes, edges)
        if not is_dag_valid:
            print(f"[FAIL] DAG Validation failed: {dag_msg}")
            return False
        else:
            print(f"[OK] {dag_msg}")
            
        print("[SUCCESS] Workflow is completely valid!\n")
        return True
        
    except ValidationError as e:
        print("[FAIL] JSON Schema Validation failed!")
        print(f"   {e.message}\n")
        return False
    except FileNotFoundError:
        print(f"[FAIL] File not found: {file_path}\n")
        return False

if __name__ == "__main__":
    # Test all examples in the directory
    examples_dir = os.path.join(BASE_DIR, "examples")
    if os.path.exists(examples_dir):
        for filename in os.listdir(examples_dir):
            if filename.endswith(".json"):
                validate_workflow_file(os.path.join(examples_dir, filename))
    else:
        # Fallback to single path if examples dir doesn't exist
        validate_workflow_file(workflow_path)
