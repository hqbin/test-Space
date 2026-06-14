import requests

token = input("Enter token: ")
resp = requests.get("http://localhost:8000/api/aml-patch/projects", headers={"Authorization": f"Bearer {token}"})
print(resp.status_code)
print(resp.text)