import json
import logging
import uuid
import base64
from typing import Dict, List, Any
from datetime import datetime

from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PHIScrubber:
    def __init__(self, token_map_path="data/token_map.json"):
        # Initialize Presidio
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()
        self.token_map_path = token_map_path
        self.token_map = self._load_token_map()
        
    def _load_token_map(self) -> Dict:
        try:
            with open(self.token_map_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
            
    def _save_token_map(self):
        with open(self.token_map_path, 'w') as f:
            json.dump(self.token_map, f, indent=2)

    def _get_or_create_token(self, entity_type: str, original_value: str) -> str:
        # Simple Key: EntityType:Value
        key = f"{entity_type}:{original_value}"
        
        if key in self.token_map:
            return self.token_map[key]['token']
            
        # Generate new token
        if entity_type == "PERSON":
            token = f"[PATIENT_NAME_{uuid.uuid4().hex[:6].upper()}]"
        elif entity_type == "PHONE_NUMBER":
            token = f"[PHONE_{uuid.uuid4().hex[:6].upper()}]"
        elif entity_type == "DATE_TIME":
            token = f"[DATE_{uuid.uuid4().hex[:6].upper()}]" 
        elif entity_type == "EMAIL_ADDRESS":
            token = f"[EMAIL_{uuid.uuid4().hex[:6].upper()}]"
        elif entity_type == "LOCATION":
            token = f"[ADDRESS_{uuid.uuid4().hex[:6].upper()}]"
        else:
            token = f"[{entity_type}_{uuid.uuid4().hex[:6].upper()}]"
            
        self.token_map[key] = {
            "token": token,
            "original": original_value,
            "type": entity_type,
            "created_at": datetime.now().isoformat()
        }
        self._save_token_map()
        return token

    def custom_mask_operator(self, text, entity_type=None):
        # Lambda passes text. We use captured entity_type.
        return self._get_or_create_token(entity_type or "UNKNOWN", text)

    def scrub_text(self, text: str) -> str:
        if not text:
            return ""
            
        # 1. Analyze
        results = self.analyzer.analyze(text=text, language='en')
        
        # 2. Anonymize with Custom Logic (Tokenization)
        operators = {
            "PERSON": OperatorConfig("custom", {"lambda": lambda x: self.custom_mask_operator(x, "PERSON")}),
            "PHONE_NUMBER": OperatorConfig("custom", {"lambda": lambda x: self.custom_mask_operator(x, "PHONE_NUMBER")}),
            "EMAIL_ADDRESS": OperatorConfig("custom", {"lambda": lambda x: self.custom_mask_operator(x, "EMAIL_ADDRESS")}),
            "DATE_TIME": OperatorConfig("custom", {"lambda": lambda x: self.custom_mask_operator(x, "DATE_TIME")}),
            "LOCATION": OperatorConfig("custom", {"lambda": lambda x: self.custom_mask_operator(x, "LOCATION")}),
            "IP_ADDRESS": OperatorConfig("custom", {"lambda": lambda x: self.custom_mask_operator(x, "IP_ADDRESS")}),
            "CREDIT_CARD": OperatorConfig("custom", {"lambda": lambda x: self.custom_mask_operator(x, "CREDIT_CARD")}),
            "US_SSN": OperatorConfig("custom", {"lambda": lambda x: self.custom_mask_operator(x, "US_SSN")}),
        }
        
        anonymized_result = self.anonymizer.anonymize(
            text=text,
            analyzer_results=results,
            operators=operators
        )
        
        return anonymized_result.text

def process_fhir_bundle(input_path: str, output_path: str):
    scrubber = PHIScrubber()
    
    with open(input_path, 'r', encoding='utf-8') as f:
        bundle = json.load(f)
        
    entries = bundle.get('entry', [])
    processed_count = 0
    
    for entry in entries:
        resource = entry.get('resource', {})
        rtype = resource.get('resourceType')
        
        if rtype == "Patient":
            # Direct Field Masking
            if 'name' in resource:
                for name in resource['name']:
                    if 'family' in name:
                        name['family'] = scrubber._get_or_create_token("PERSON", name['family'])
                    if 'given' in name:
                        name['given'] = [scrubber._get_or_create_token("PERSON", g) for g in name['given']]
            if 'address' in resource:
                for addr in resource['address']:
                    if 'line' in addr:
                        addr['line'] = [scrubber._get_or_create_token("LOCATION", l) for l in addr['line']]
                    if 'city' in addr:
                        addr['city'] = scrubber._get_or_create_token("LOCATION", addr['city'])
        
        elif rtype == "DocumentReference":
            # Mask description
            if 'description' in resource:
                resource['description'] = scrubber.scrub_text(resource['description'])
                
            # Mask Base64 content
            if 'content' in resource:
                for content in resource['content']:
                    attachment = content.get('attachment', {})
                    if 'data' in attachment:
                        try:
                            raw_text = base64.b64decode(attachment['data']).decode('utf-8')
                            scrubbed_text = scrubber.scrub_text(raw_text)
                            attachment['data'] = base64.b64encode(scrubbed_text.encode('utf-8')).decode('utf-8')
                        except Exception as e:
                            logger.error(f"Failed to process DocumentReference: {e}")
            

        processed_count += 1

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(bundle, f, indent=2)
        
    logger.info(f"Processed {processed_count} resources. Saved to {output_path}")

if __name__ == "__main__":
    import os
    if not os.path.exists("data"):
        os.makedirs("data")
        
    process_fhir_bundle(
        "data/synthetic/synthetic_fhir_dataset.json",
        "data/synthetic/deidentified_dataset.json"
    )
