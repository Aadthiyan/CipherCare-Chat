#!/usr/bin/env python3
"""Query first 50 patients via backend API and report number of sources returned."""
import os
import requests
import time
from backend.cyborg_lite_manager import get_cyborg_manager

LOGIN_URL = "http://127.0.0.1:8000/auth/login"
QUERY_URL = "http://127.0.0.1:8000/api/v1/query"

def get_patient_ids(limit=50):
    mgr = get_cyborg_manager()
    ids = mgr.get_all_patient_ids()
    return ids[:limit]

def login(username="jsmith", password="Aadhithiyan@99"):
    # Try provided credentials first, fallback to local mock attending if needed
    for cred in [ (username, password), ("attending", "password123") ]:
        try:
            r = requests.post(LOGIN_URL, json={"username": cred[0], "password": cred[1]}, timeout=10)
            if r.status_code == 200:
                return r.json().get("access_token")
        except Exception:
            continue
    # If both fail, raise
    raise Exception("Login failed for both primary and fallback credentials")

def query_patient(token, patient_id):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"patient_id": patient_id, "question": "Summary", "retrieve_k": 5}
    try:
        r = requests.post(QUERY_URL, json=payload, headers=headers, timeout=15)
        if r.status_code != 200:
            return (False, r.status_code, r.text)
        data = r.json()
        sources = data.get("sources") or data.get("documents") or []
        return (True, len(sources), data.get("answer") if isinstance(data, dict) else None)
    except Exception as e:
        return (False, None, str(e))

def main():
    print("Fetching patient IDs...")
    patients = get_patient_ids(50)
    print(f"Found {len(patients)} patients to test")

    print("Logging in...")
    token = login()
    print("Logged in, running queries...")

    results = []
    for i, pid in enumerate(patients, 1):
        ok, info, extra = query_patient(token, pid)
        if ok:
            results.append((pid, info))
            print(f"{i:02d}. {pid}: {info} sources")
        else:
            results.append((pid, 0))
            print(f"{i:02d}. {pid}: FAILED ({info})")
        time.sleep(0.2)

    have = sum(1 for _, c in results if c and c > 0)
    print("\nSUMMARY")
    print(f"Patients tested: {len(results)}")
    print(f"Patients with >=1 source: {have}")
    print(f"Patients with 0 sources: {len(results)-have}")

if __name__ == '__main__':
    main()
