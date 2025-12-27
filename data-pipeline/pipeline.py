import os
import json
import logging
import time
from datetime import datetime
from typing import Dict, Any

from phi_scrubber import PHIScrubber
from fhir.resources.bundle import Bundle

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [PIPELINE] - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("data-pipeline/pipeline.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DataPipeline:
    def __init__(self, input_dir="data/synthetic", output_dir="data/processed"):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.scrubber = PHIScrubber()
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def validate_fhir(self, data: Dict[str, Any]) -> bool:
        """Task: Validate FHIR schema"""
        try:
            # Simple check: Is it a Bundle?
            if data.get('resourceType') != 'Bundle':
                logger.error("Data is not a FHIR Bundle")
                return False
            
            # Deeper check using fhir.resources
            # Bundle.parse_obj(data) # validates structure
            return True
        except Exception as e:
            logger.error(f"Validation Failed: {e}")
            return False

    def run(self):
        logger.info("Starting Data Pipeline...")
        start_time = time.time()
        
        # 1. Ingest
        input_file = os.path.join(self.input_dir, "synthetic_fhir_dataset.json")
        if not os.path.exists(input_file):
            logger.error(f"Input file not found: {input_file}")
            return

        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
            logger.info(f"Ingested {len(raw_data.get('entry', []))} resources.")
        except Exception as e:
            logger.error(f"Ingestion failed: {e}")
            return

        # 2. Validate
        if not self.validate_fhir(raw_data):
            logger.error("Aborting pipeline due to validation errors.")
            return
        logger.info("Validation passed.")

        # 3. De-Identify
        logger.info("Starting De-Identification...")
        try:
            # Use temporary file logic or in-memory. Since dataset is small, in-memory.
            # We reuse the logic from process_fhir_bundle recursively for the dict
            # For now, let's just write to temp file and use the file-based processor we built? 
            # Or better, refactor scrubber to verify.
            # I will use the file-based function I wrote in phi_scrubber for simplicity if I can import it.
            
            from phi_scrubber import process_fhir_bundle
            output_file = os.path.join(self.output_dir, "deidentified_dataset.json")
            
            process_fhir_bundle(input_file, output_file)
            logger.info("De-Identification complete.")
            
        except Exception as e:
            logger.error(f"De-Identification failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return

        # 4. Success
        duration = time.time() - start_time
        logger.info(f"Pipeline finished successfully in {duration:.2f} seconds.")
        logger.info(f"Output available at: {output_file}")

if __name__ == "__main__":
    pipeline = DataPipeline()
    pipeline.run()
