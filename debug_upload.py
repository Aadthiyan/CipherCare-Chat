import json
from upload_patient_data import PatientDataUploader
from dotenv import load_dotenv
import traceback

load_dotenv()

# Load Synthea data
data = json.load(open('synthea_patients_221.json'))
first_key = list(data.keys())[0]

print(f"Testing {first_key}")
print(f"Data type: {type(data[first_key])}")
print(f"Keys: {list(data[first_key].keys())}")

# Create uploader
uploader = PatientDataUploader()

# Try to upload
try:
    result = uploader.upload_patient(first_key, data[first_key])
    print(f"Result: {result}")
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()
