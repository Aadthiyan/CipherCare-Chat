import os
import json
import random
import uuid
import base64
from datetime import datetime, timedelta
from faker import Faker

fake = Faker()

# Data Constants
CONDITIONS = [
    {"code": "I10", "display": "Essential (primary) hypertension"},
    {"code": "E11.9", "display": "Type 2 diabetes mellitus without complications"},
    {"code": "J45.909", "display": "Unspecified asthma, uncomplicated"},
    {"code": "M54.5", "display": "Low back pain"},
    {"code": "E78.5", "display": "Hyperlipidemia, unspecified"},
    {"code": "F41.1", "display": "Generalized anxiety disorder"},
]

MEDICATIONS = [
    {"code": "197517", "display": "Lisinopril 10 MG Oral Tablet"},
    {"code": "860975", "display": "Metformin hydrochloride 500 MG Oral Tablet"},
    {"code": "308136", "display": "Atorvastatin 20 MG Oral Tablet"},
]

NOTE_TEMPLATES = [
    """Subjective:
Patient presents with {complaint}. Reports onset {duration} ago.
Objective:
BP: {bp_sys}/{bp_dia} mmHg, HR: {hr} bpm.
Assessment:
{condition}.
Plan:
Continue medications. Follow up in 4 weeks.
"""
]

COMPLAINTS = [
    "worsening headache", "persistent cough", "fatigue", "dizziness", 
    "back pain"
]

def generate_patient():
    gender = random.choice(["male", "female"])
    first = fake.first_name_male() if gender == "male" else fake.first_name_female()
    last = fake.last_name()
    dob = fake.date_of_birth(minimum_age=18, maximum_age=90).isoformat()
    
    return {
        "resourceType": "Patient",
        "id": str(uuid.uuid4()),
        "active": True,
        "name": [{"use": "official", "family": last, "given": [first]}],
        "gender": gender,
        "birthDate": dob,
        "address": [{
            "use": "home",
            "line": [fake.street_address()],
            "city": fake.city(),
            "state": fake.state_abbr(),
            "postalCode": fake.zipcode()
        }]
    }

def main():
    OUTPUT_DIR = "data/synthetic"
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    outfile = os.path.join(OUTPUT_DIR, "synthetic_fhir_dataset.json")
    
    entries = []
    
    # Generate 100 Patients
    print("Generating 100 patients...")
    for _ in range(100):
        pat = generate_patient()
        entries.append({"resource": pat})
        
        # Condition
        cond_data = random.choice(CONDITIONS)
        cond = {
            "resourceType": "Condition",
            "id": str(uuid.uuid4()),
            "clinicalStatus": {
                "coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": "active"}]
            },
            "code": {
                "coding": [{"system": "http://hl7.org/fhir/sid/icd-10", "code": cond_data['code'], "display": cond_data['display']}]
            },
            "subject": {"reference": f"Patient/{pat['id']}"},
            "onsetDateTime": fake.date_this_decade().isoformat()
        }
        entries.append({"resource": cond})
        
        # Clinical Note
        note_text = random.choice(NOTE_TEMPLATES).format(
            complaint=random.choice(COMPLAINTS), 
            duration=f"{random.randint(1,4)} days",
            bp_sys=random.randint(110, 150),
            bp_dia=random.randint(70, 90),
            hr=random.randint(60, 100),
            condition=cond_data['display']
        )
        encoded_note = base64.b64encode(note_text.encode('utf-8')).decode('utf-8')
        
        doc = {
            "resourceType": "DocumentReference",
            "id": str(uuid.uuid4()),
            "status": "current",
            "docStatus": "final",
            "type": {
                "coding": [{"system": "http://loinc.org", "code": "11506-3", "display": "Progress note"}]
            },
            "subject": {"reference": f"Patient/{pat['id']}"},
            "date": datetime.now().isoformat(),
            "content": [{
                "attachment": {
                    "contentType": "text/plain",
                    "data": encoded_note
                }
            }],
            "description": note_text # custom helper field
        }
        entries.append({"resource": doc})

    bundle = {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": entries
    }
    
    with open(outfile, 'w', encoding='utf-8') as f:
        json.dump(bundle, f, indent=2)
        
    print(f"Generated {len(entries)} resources.")
    print(f"Saved to {outfile}")

if __name__ == "__main__":
    main()
