import os
import shutil
from compiler.parser import load_workflow
from compiler.ir_builder import build_ir
from compiler.generator import generate_project
from compiler.packager import package_project

# Get the directory where this file lives
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXAMPLES_DIR = os.path.join(os.path.dirname(BASE_DIR), "workflow-spec", "examples")

def test_compiler(example_name):
    print(f"\n--- Testing compiler with {example_name} ---")
    workflow_path = os.path.join(EXAMPLES_DIR, f"{example_name}.json")
    
    # 1. Parse and Validate
    print("1. Parsing and Validating...")
    workflow_dict = load_workflow(workflow_path)
    
    # 2. Build IR
    print("2. Building IR...")
    workflow_ir = build_ir(workflow_dict)
    
    # 3. Code Generation
    print("3. Generating Code...")
    output_dir = os.path.join(BASE_DIR, f"out_{example_name}")
    generate_project(workflow_ir, output_dir=output_dir)
    
    # 4. Packaging
    print("4. Packaging Project...")
    zip_path = os.path.join(BASE_DIR, f"{example_name}_project.zip")
    package_project(output_dir, zip_path)
    print("------------------------------------------")

if __name__ == "__main__":
    test_compiler("healthcare_etl")
    test_compiler("simple_etl")
