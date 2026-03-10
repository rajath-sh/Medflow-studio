from parser import load_workflow

workflow = load_workflow("../workflow-spec/examples/simple_etl.json")

print("Workflow loaded successfully!")
print(workflow)
