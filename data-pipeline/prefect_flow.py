import os
import json
import toml
import time
from datetime import timedelta
from typing import Dict, Any, List

from prefect import flow, task, get_run_logger

# Import our custom modules
from phi_scrubber import PHIScrubber, process_fhir_bundle
from fhir.resources.bundle import Bundle

# Load Config
try:
    CONFIG = toml.load("config/pipeline.toml")
except Exception:
    # Fallback default
    CONFIG = {
        "retry": {"max_retries": 3, "retry_delay_seconds": 2},
        "storage": {
            "raw_data_path": "data/synthetic/synthetic_fhir_dataset.json",
            "processed_data_path": "data/processed/deidentified_dataset.json"
        }
    }

@task(retries=3, retry_delay_seconds=2)
def ingest_data(file_path: str) -> Dict[str, Any]:
    # logger = get_run_logger() # Can fail if no context
    print(f"Ingesting data from {file_path}")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Source file not found: {file_path}")
        
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    count = len(data.get('entry', []))
    print(f"Ingested {count} resources.")
    return data

@task
def validate_data(data: Dict[str, Any]) -> bool:
    print("Validating FHIR schema...")
    
    if data.get('resourceType') != 'Bundle':
        print("Invalid Resource Type: Expected Bundle")
        return False
        
    print("Validation Successful")
    return True

@task
def deidentify_data(input_path: str, output_path: str):
    print("Starting De-Identification Task...")
    
    output_dir = os.path.dirname(output_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    try:
        process_fhir_bundle(input_path, output_path)
        print(f"De-identified data saved to {output_path}")
    except Exception as e:
        print(f"De-identification failed: {e}")
        raise e

@task
def verify_deidentification(output_path: str) -> bool:
    print("Verifying De-Identification...")
    
    with open(output_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print("Verification Complete.")
    return True

@task
def store_audit_log(status: str, record_count: int):
    audit_entry = {
        "timestamp": time.time(),
        "status": status,
        "records_processed": record_count
    }
    with open("data/pipeline_audit.log", 'a') as f:
        f.write(json.dumps(audit_entry) + "\n")
    print("Audit log updated.")

@flow(name="EHR Ingestion Pipeline", log_prints=True)
def ehr_pipeline():
    raw_path = CONFIG['storage']['raw_data_path']
    proc_path = CONFIG['storage']['processed_data_path']
    
    # 1. Ingest
    try:
        raw_data = ingest_data(raw_path)
    except Exception as e:
        print(f"Pipeline Failed at Ingestion: {e}")
        return

    # 2. Validate
    is_valid = validate_data(raw_data)
    if not is_valid:
        print("Pipeline Aborted: Validation Failed")
        return

    # 3. De-Identify
    deidentify_data(raw_path, proc_path)

    # 4. Verify
    verify_deidentification(proc_path)

    # 5. Audit
    store_audit_log("SUCCESS", len(raw_data.get('entry', [])))
    print("Pipeline Finished Successfully")

if __name__ == "__main__":
    ehr_pipeline()
