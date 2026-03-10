import requests

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
    print("Got token. Fetching datasets...")
    
    headers = {"Authorization": f"Bearer {token}"}
    res2 = requests.get("http://localhost:8000/datasets/general", headers=headers)
    
    print(f"Status: {res2.status_code}")
    print(f"Response: {res2.text}")

if __name__ == "__main__":
    test()
