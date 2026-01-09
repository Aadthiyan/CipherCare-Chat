"""
Admin routes for CipherCare backend
Includes data upload and management endpoints
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
import json
import os
from typing import Optional, List, Dict, Any
from backend.cyborg_lite_manager import CyborgLiteManager
import logging
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


class UploadStatus(BaseModel):
    status: str
    message: str
    records_processed: Optional[int] = 0
    total_records: Optional[int] = 0
    patients: Optional[int] = 0


class PrecomputedUploadRequest(BaseModel):
    items: List[Dict[str, Any]]


# Global upload status tracker
upload_status = {
    "in_progress": False,
    "records_processed": 0,
    "total_records": 0,
    "status": "idle",
    "message": "No upload in progress"
}


def upload_patient_data_task():
    """Background task to upload patient data"""
    global upload_status
    
    try:
        upload_status["in_progress"] = True
        upload_status["status"] = "loading_data"
        upload_status["message"] = "Loading patient data file..."
        
        # Load patient data
        data_file = os.path.join(os.path.dirname(__file__), '..', 'synthea_structured_cipercare.json')
        
        with open(data_file, 'r') as f:
            data = json.load(f)
        
        records = data['records']
        upload_status["total_records"] = len(records)
        
        logger.info(f"Loaded {len(records)} patient records")
        
        # Get unique patients
        patient_ids = set(record.get('patient_id', '') for record in records)
        upload_status["patients"] = len(patient_ids)
        
        logger.info(f"Found {len(patient_ids)} unique patients")
        
        # Get embedder service from main app
        from backend.main import services
        embedder = services.get("embedder")
        
        if not embedder:
            raise RuntimeError("Embedder service not initialized in backend")
        
        logger.info("Using existing embedder service")
        
        # Use existing multi-database manager from backend services
        upload_status["status"] = "initializing_db"
        upload_status["message"] = "Using multi-database service..."
        
        db = services.get("db")
        
        if not db:
            raise RuntimeError("Multi-database service not initialized in backend")
        
        logger.info("Multi-database manager ready")
        
        # Upload in batches with sharding
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
                    "patient_id": record.get('patient_id', ''),
                    "vector": embedding,
                    "metadata": {
                        "record_type": record.get('record_type', ''),
                        "display": record.get('display', ''),
                        "description": record.get('description', ''),
                        "date": record.get('date', ''),
                        "code": record.get('code', ''),
                        "system": record.get('system', '')
                    }
                })
            
            # Upload batch with sharding (records 0-49999 → DB1, 50000+ → DB2)
            await db.upsert_vectors(items, start_index=i)
            
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
async def upload_patient_data(background_tasks: BackgroundTasks):
    """
    Trigger patient data upload from synthea_structured_cipercare.json
    This runs in the background and generates embeddings on-the-fly
    """
    global upload_status
    
    # Check if upload already in progress
    if upload_status["in_progress"]:
        return UploadStatus(
            status="in_progress",
            message="Upload already in progress. Check /admin/upload-status for progress.",
            records_processed=upload_status["records_processed"],
            total_records=upload_status["total_records"]
        )
    
    # Reset status
    upload_status = {
        "in_progress": True,
        "records_processed": 0,
        "total_records": 0,
        "status": "starting",
        "message": "Initializing upload..."
    }
    
    # Start background task
    background_tasks.add_task(upload_patient_data_task)
    
    return UploadStatus(
        status="started",
        message="Patient data upload started in background. Check /admin/upload-status for progress."
    )


@router.post("/upload-precomputed")
async def upload_precomputed_embeddings(request: PrecomputedUploadRequest):
    """
    Upload pre-computed embeddings directly (MUCH FASTER!)
    This skips embedding generation and just stores the vectors
    """
    try:
        # Get pgvector manager
        from backend.main import services
        db = services.get("db")
        
        if not db:
            raise HTTPException(status_code=500, detail="pgvector service not initialized")
        
        # Upload items
        await db.upsert(request.items)
        
        logger.info(f"Uploaded {len(request.items)} pre-computed embeddings")
        
        return {
            "status": "success",
            "message": f"Uploaded {len(request.items)} embeddings",
            "count": len(request.items)
        }
        
    except Exception as e:
        logger.error(f"Failed to upload pre-computed embeddings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
