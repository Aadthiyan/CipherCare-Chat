#!/usr/bin/env python3
import requests

key=None
with open('.env') as f:
    for line in f:
        if line.strip().startswith('CYBORGDB_API_KEY'):
            key=line.split('=',1)[1].strip(); break
print('Using key from .env:', key)
try:
    r=requests.get('http://localhost:8002/health', headers={'x-api-key': key}, timeout=5)
    print('status', r.status_code)
    print(r.text)
except Exception as e:
    print('Request failed:', e)
