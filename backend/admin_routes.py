"""
Admin routes for CipherCare backend
Includes data upload and management endpoints
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
import json
import os
from typing import Optional
from backend.cyborg_lite_manager import CyborgLiteManager
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


class UploadStatus(BaseModel):
    status: str
    message: str
    records_processed: Optional[int] = 0
    total_records: Optional[int] = 0
    patients: Optional[int] = 0


# Global upload status tracker
upload_status = {
    "in_progress": False,
    "records_processed": 0,
    "total_records": 0,
    "status": "idle",
    "message": ""
}


def upload_patient_data_task():
    """Background task to upload patient data to CyborgDB"""
    global upload_status
    
    try:
        upload_status["in_progress"] = True
        upload_status["status"] = "loading_data"
        upload_status["message"] = "Loading patient data file..."
        
        # Load patient data
        data_file = "synthea_structured_cipercare.json"
        if not os.path.exists(data_file):
            raise FileNotFoundError(f"Data file not found: {data_file}")
        
        with open(data_file, 'r') as f:
            all_records = json.load(f)
        
        # Limit to 150 patients (76,317 records)
        records = all_records[:76317]
        upload_status["total_records"] = len(records)
        upload_status["message"] = f"Loaded {len(records)} records"
        
        logger.info(f"Loaded {len(records)} patient records")
        
        # Count unique patients
        patient_ids = set(r.get('patient_id') for r in records if r.get('patient_id'))
        upload_status["message"] = f"Found {len(patient_ids)} unique patients"
        
        logger.info(f"Found {len(patient_ids)} unique patients")
        
        # Use existing embedder from backend services (already initialized!)
        upload_status["status"] = "loading_model"
        upload_status["message"] = "Using existing embedding service..."
        
        # Import backend services
        from backend.main import services
        embedder = services.get("embedder")
        
        if not embedder:
            raise RuntimeError("Embedder service not initialized in backend")
        
        logger.info("Using existing embedder service")
        
        # Use existing CyborgDB manager from backend services (already initialized!)
        upload_status["status"] = "initializing_db"
        upload_status["message"] = "Using existing CyborgDB service..."
        
        db = services.get("db")
        
        if not db:
            raise RuntimeError("CyborgDB service not initialized in backend")
        
        index = db.get_index("patient_records_v1")
        logger.info("CyborgDB index ready")
        
        # Upload in batches
        upload_status["status"] = "uploading"
        batch_size = 1000
        
        for i in range(0, len(records), batch_size):
            batch = records[i:i+batch_size]
            
            # Prepare batch for upload
            items = []
            
            for j, record in enumerate(batch):
                # Create text for embedding
                text = f"{record.get('record_type', '')}: {record.get('display', '')} {record.get('description', '')}"
                
                # Generate embedding using existing service
                embedding = embedder.get_embedding(text)
                
                items.append({
                    "id": str(record.get('record_id', f"record_{i+j}")),
                    "vector": embedding,
                    "metadata": {
                        "patient_id": record.get('patient_id', ''),
                        "record_type": record.get('record_type', ''),
                        "display": record.get('display', ''),
                        "description": record.get('description', ''),
                        "date": record.get('date', ''),
                        "code": record.get('code', ''),
                        "system": record.get('system', '')
                    }
                })
            
            # Upload batch
            index.upsert(items)
            
            upload_status["records_processed"] = i + len(batch)
            upload_status["message"] = f"Uploaded {upload_status['records_processed']}/{len(records)} records"
            
            logger.info(f"Uploaded batch {i//batch_size + 1}: {upload_status['records_processed']}/{len(records)}")
        
        # Success!
        upload_status["status"] = "completed"
        upload_status["message"] = f"Successfully uploaded {len(records)} records ({len(patient_ids)} patients)"
        upload_status["in_progress"] = False
        
        logger.info(f"Upload complete: {len(records)} records, {len(patient_ids)} patients")
        
    except Exception as e:
        upload_status["status"] = "error"
        upload_status["message"] = f"Upload failed: {str(e)}"
        upload_status["in_progress"] = False
        logger.error(f"Upload failed: {str(e)}", exc_info=True)


@router.post("/upload-patient-data", response_model=UploadStatus)
async def trigger_patient_data_upload(background_tasks: BackgroundTasks):
    """
    Trigger patient data upload to CyborgDB Embedded
    This runs in the background and can take ~30 minutes
    """
    global upload_status
    
    if upload_status["in_progress"]:
        return UploadStatus(
            status="in_progress",
            message="Upload already in progress",
            records_processed=upload_status["records_processed"],
            total_records=upload_status["total_records"]
        )
    
    # Reset status
    upload_status = {
        "in_progress": True,
        "records_processed": 0,
        "total_records": 0,
        "status": "starting",
        "message": "Upload started..."
    }
    
    # Start background task
    background_tasks.add_task(upload_patient_data_task)
    
    return UploadStatus(
        status="started",
        message="Patient data upload started in background. Check /admin/upload-status for progress."
    )


@router.get("/upload-status", response_model=UploadStatus)
async def get_upload_status():
    """
    Get current status of patient data upload
    """
    return UploadStatus(
        status=upload_status["status"],
        message=upload_status["message"],
        records_processed=upload_status["records_processed"],
        total_records=upload_status["total_records"]
    )
