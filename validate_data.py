import json
from fhir.resources.bundle import Bundle

def validate():
    print("Validating FHIR dataset...")
    try:
        with open("data/synthetic/synthetic_fhir_dataset.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Parse into Pydantic model - this performs validation
        bundle = Bundle.parse_obj(data)
        print("SUCCESS: Dataset is valid FHIR R4 Bundle.")
        print(f"Contains {len(bundle.entry)} entries.")
        
    except Exception as e:
        print("VALIDATION FAILED:")
        print(e)
        import sys
        sys.exit(1)

if __name__ == "__main__":
    validate()
