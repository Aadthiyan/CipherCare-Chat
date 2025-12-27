#!/usr/bin/env python3
import requests
import json

r_login = requests.post('http://127.0.0.1:8000/auth/login', 
    json={'username': 'jsmith', 'password': 'Aadhithiyan@99'}, 
    timeout=5)
token = r_login.json()['access_token']

r = requests.get('http://127.0.0.1:8000/api/v1/patients', 
    headers={'Authorization': f'Bearer {token}'}, timeout=10)

print(f"Status: {r.status_code}")
print(f"Type of response: {type(r.json())}")
print(f"Response (first 1000 chars):\n{r.text[:1000]}")
