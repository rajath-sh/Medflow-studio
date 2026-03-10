import requests
import json

def test():
    print("Logging in...")
    res = requests.post("http://localhost:8000/auth/login", data={
        "username": "admin",
        "password": "password",
        "grant_type": "password"
    }, headers={"Content-Type": "application/x-www-form-urlencoded"})
    
    if res.status_code != 200:
        print("Login failed:", res.status_code, res.text)
        return
        
    token = res.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    print("\nAttempting to save workflow...")
    payload = {
        "name": "Test Workflow",
        "definition": {
            "name": "Test Workflow",
            "nodes": [],
            "edges": []
        }
    }
    
    res2 = requests.post("http://localhost:8000/workflows/", headers=headers, json=payload)
    print(f"Save Status: {res2.status_code}")
    print(f"Save Response: {res2.text}")
    
    if res2.status_code == 201:
        wf_id = res2.json().get("id")
        
        print("\nAttempting to execute workflow...")
        res3 = requests.post(f"http://localhost:8000/workflows/{wf_id}/execute", headers=headers)
        print(f"Execute Status: {res3.status_code}")
        print(f"Execute Response: {res3.text}")

if __name__ == "__main__":
    test()
