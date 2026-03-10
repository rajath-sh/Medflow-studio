from parser import load_workflow
from ir_builder import build_ir

workflow_dict = load_workflow("../workflow-spec/examples/simple_etl.json")
workflow = build_ir(workflow_dict)

print(workflow)
for node in workflow.nodes:
    print(node)
