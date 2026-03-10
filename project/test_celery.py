import time
import requests

BASE_URL = "http://localhost:8000"

def test_celery_execution():
    # 1. Login to get token
    print("1. Logging in as Admin...")
    resp = requests.post(f"{BASE_URL}/auth/login", json={"username": "admin", "password": "Admin@12345678"})
    if resp.status_code != 200:
        print("Login failed:", resp.text)
        return
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Add an empty workflow (dummy definition) to test execution
    print("2. Creating a test workflow...")
    workflow_data = {
        "name": "Test Celery Execution Workflow",
        "description": "Triggering celery",
        "definition": {
            "workflow_name": "basic_patient_etl",
            "nodes": [
                {"id": "test_node", "type": "data_source", "config": {"source_type": "csv", "path": "test.csv"}}
            ],
            "edges": []
        }
    }
    resp = requests.post(f"{BASE_URL}/workflows/", json=workflow_data, headers=headers)
    if resp.status_code != 201:
        print("Workflow creation failed:", resp.text)
        return
    workflow_id = resp.json()["id"]
    print(f"   Created workflow: {workflow_id}")

    # 3. Trigger execution
    print("3. Triggering execution...")
    resp = requests.post(f"{BASE_URL}/workflows/{workflow_id}/execute", headers=headers)
    if resp.status_code != 202:
        print("Execution trigger failed:", resp.text)
        return
    job_id = resp.json()["job_id"]
    print(f"   Job started: {job_id}")

    # 4. Poll job status
    print("4. Polling job status...")
    for _ in range(10):
        time.sleep(1)
        resp = requests.get(f"{BASE_URL}/jobs/{job_id}", headers=headers)
        if resp.status_code == 200:
            status = resp.json()["status"]
            print(f"   Status: {status}")
            if status in ["SUCCESS", "FAILED"]:
                break
        else:
            print("Failed to get job status:", resp.text)
            break

    # 5. Fetch logs
    print("5. Fetching job logs...")
    resp = requests.get(f"{BASE_URL}/jobs/{job_id}/logs", headers=headers)
    if resp.status_code == 200:
        logs = resp.json()
        for log in logs:
            print(f"   [{log['timestamp']}] {log['level']}: {log['message']}")
    else:
        print("Failed to get job logs:", resp.text)

if __name__ == "__main__":
    test_celery_execution()
