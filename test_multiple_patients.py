"""Test queries for multiple patient IDs to verify enrichment across all datasets."""
import requests
import json
from dotenv import load_dotenv

load_dotenv()

# Test a variety of patients from both Synthea and MIMIC
test_patients = [
    "PID-102",  # MIMIC
    "PID-104",  # MIMIC
    "PID-110",  # Synthea
    "PID-117",  # Synthea
    "PID-150",  # Synthea
    "PID-180",  # Synthea
    "PID-200",  # Synthea
    "PID-250",  # Synthea
]

def main():
    # Login once
    login_url = "http://127.0.0.1:8000/auth/login"
    login_data = {
        "username": "jsmith",
        "password": "Aadhithiyan@99"
    }
    
    print("🔐 Logging in...")
    login_response = requests.post(login_url, json=login_data)
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return
    
    tokens = login_response.json()
    access_token = tokens.get("access_token")
    print(f"✅ Login successful\n")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Test each patient
    results = []
    query_url = "http://127.0.0.1:8000/api/v1/query"
    
    print("=" * 80)
    print("TESTING MULTIPLE PATIENT IDS")
    print("=" * 80)
    
    for patient_id in test_patients:
        print(f"\n📊 Testing {patient_id}...")
        
        query_data = {
            "patient_id": patient_id,
            "question": "Summarize this patient's diagnoses and medications.",
            "retrieve_k": 5
        }
        
        try:
            response = requests.post(query_url, json=query_data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                num_sources = len(result.get('sources', []))
                answer_preview = result.get('answer', '')[:100]
                
                results.append({
                    'patient_id': patient_id,
                    'status': '✅ SUCCESS',
                    'sources': num_sources,
                    'answer_preview': answer_preview
                })
                
                print(f"  ✅ HTTP 200 - Sources: {num_sources}")
                print(f"  Answer preview: {answer_preview}...")
                
            elif response.status_code == 403:
                results.append({
                    'patient_id': patient_id,
                    'status': '⚠️  NO ACCESS',
                    'sources': 0,
                    'answer_preview': 'User does not have access'
                })
                print(f"  ⚠️  HTTP 403 - Access Denied")
                
            elif response.status_code == 404:
                results.append({
                    'patient_id': patient_id,
                    'status': '❌ NOT FOUND',
                    'sources': 0,
                    'answer_preview': 'Patient not found'
                })
                print(f"  ❌ HTTP 404 - Patient not found")
                
            else:
                results.append({
                    'patient_id': patient_id,
                    'status': f'❌ HTTP {response.status_code}',
                    'sources': 0,
                    'answer_preview': str(response.text)[:100]
                })
                print(f"  ❌ HTTP {response.status_code}")
                
        except requests.exceptions.Timeout:
            results.append({
                'patient_id': patient_id,
                'status': '⏱️  TIMEOUT',
                'sources': 0,
                'answer_preview': 'Request timed out'
            })
            print(f"  ⏱️  Request timed out")
            
        except Exception as e:
            results.append({
                'patient_id': patient_id,
                'status': '❌ ERROR',
                'sources': 0,
                'answer_preview': str(e)[:100]
            })
            print(f"  ❌ Error: {str(e)[:100]}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    success_count = sum(1 for r in results if '✅' in r['status'])
    total_sources = sum(r['sources'] for r in results)
    
    print(f"\n{'Patient ID':<12} {'Status':<20} {'Sources':<10}")
    print("-" * 42)
    for r in results:
        print(f"{r['patient_id']:<12} {r['status']:<20} {r['sources']:<10}")
    
    print("\n" + "-" * 42)
    print(f"✅ Successful queries: {success_count}/{len(test_patients)}")
    print(f"📚 Total sources retrieved: {total_sources}")
    print(f"📊 Average sources per successful query: {total_sources // success_count if success_count > 0 else 0}")

if __name__ == "__main__":
    main()
