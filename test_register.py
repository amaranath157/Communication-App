import requests

url = "http://localhost:8000/api/v1/auth/register/"
data = {
    "name": "testuser",
    "email": "testuser@example.com",
    "password": "password123"
}
response = requests.post(url, json=data)
print(response.status_code)
print(response.json())
