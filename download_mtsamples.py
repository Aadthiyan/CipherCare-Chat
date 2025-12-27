"""
Download and convert MTSamples clinical notes for CipherCare
MTSamples provides 5,000+ real medical transcription samples
"""

import requests
import pandas as pd
import json
from pathlib import Path
from typing import List, Dict

def download_mtsamples() -> List[Dict]:
    """Download pre-compiled MTSamples dataset from GitHub"""
    
    print("📥 Downloading MTSamples dataset...")
    
    # Use the pre-compiled CSV from clinical-concepts repo
    url = "https://raw.githubusercontent.com/kavgan/clinical-concepts/master/data/mtsamples.csv"
    
    try:
        df = pd.read_csv(url)
        print(f"✓ Downloaded {len(df)} clinical samples")
        
        # Convert to CipherCare format
        patients = []
        
        for idx, row in df.iterrows():
            # Create rich clinical text for embeddings
            clinical_text = f"""
Medical Specialty: {row.get('medical_specialty', 'General')}

Description: {row.get('description', '')}

Sample Name: {row.get('sample_name', '')}

Transcription:
{row.get('transcription', '')}

Keywords: {row.get('keywords', '')}
            """.strip()
            
            patient_record = {
                "patient_id": f"MT{idx+1:05d}",
                "specialty": row.get('medical_specialty', 'General Medicine'),
                "description": row.get('description', ''),
                "sample_name": row.get('sample_name', ''),
                "clinical_note": row.get('transcription', ''),
                "keywords": row.get('keywords', ''),
                "full_text": clinical_text,  # For embeddings
                "source": "MTSamples",
                "category": "clinical_note"
            }
            
            patients.append(patient_record)
        
        return patients
        
    except Exception as e:
        print(f"❌ Error downloading MTSamples: {e}")
        return []


def save_for_cipercare(patients: List[Dict], output_file: str = "mtsamples_cipercare.json"):
    """Save in CipherCare-compatible format"""
    
    output_path = Path(output_file)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(patients, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Saved {len(patients)} records to {output_path}")
    
    # Also create a sample for quick testing
    sample_patients = patients[:10]
    sample_path = Path("mtsamples_sample_10.json")
    
    with open(sample_path, 'w', encoding='utf-8') as f:
        json.dump(sample_patients, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Created sample file with 10 records: {sample_path}")


def print_statistics(patients: List[Dict]):
    """Print dataset statistics"""
    
    print("\n" + "="*60)
    print("📊 DATASET STATISTICS")
    print("="*60)
    
    # Count by specialty
    specialties = {}
    for p in patients:
        spec = p.get('specialty', 'Unknown')
        specialties[spec] = specialties.get(spec, 0) + 1
    
    print(f"\nTotal Records: {len(patients)}")
    print(f"\nTop 10 Medical Specialties:")
    
    for spec, count in sorted(specialties.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  • {spec}: {count} samples")
    
    # Sample record
    print(f"\n📄 SAMPLE RECORD:")
    print("="*60)
    sample = patients[0]
    print(f"Patient ID: {sample['patient_id']}")
    print(f"Specialty: {sample['specialty']}")
    print(f"Description: {sample['description'][:100]}...")
    print(f"Clinical Note Length: {len(sample['clinical_note'])} characters")
    print("="*60)


def main():
    """Main execution"""
    
    print("🏥 MTSamples Data Downloader for CipherCare")
    print("="*60)
    
    # Download data
    patients = download_mtsamples()
    
    if not patients:
        print("❌ Failed to download data")
        return
    
    # Save in CipherCare format
    save_for_cipercare(patients)
    
    # Print statistics
    print_statistics(patients)
    
    print("\n✅ NEXT STEPS:")
    print("="*60)
    print("1. Review the sample file: mtsamples_sample_10.json")
    print("2. Upload to CipherCare:")
    print("   python upload_mtsamples.py")
    print("3. Test queries like:")
    print("   - 'Show me patients with cardiovascular conditions'")
    print("   - 'Find discharge summaries for diabetes patients'")
    print("   - 'What are the common procedures for orthopedic cases?'")
    print("="*60)


if __name__ == "__main__":
    main()
