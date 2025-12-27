"""
Quick script to download and add Synthea sample data to CipherCare

This script:
1. Downloads pre-generated Synthea patient data
2. Converts to CipherCare format
3. Uploads to your CyborgDB

Usage:
    python quick_add_synthea_data.py
"""

import os
import sys
import subprocess
import json
from pathlib import Path


def run_command(cmd, description):
    """Run a shell command and show progress"""
    print(f"\n{'='*60}")
    print(f"📌 {description}")
    print(f"{'='*60}")
    print(f"Running: {cmd}\n")
    
    result = subprocess.run(cmd, shell=True, capture_output=False, text=True)
    
    if result.returncode != 0:
        print(f"❌ Error: Command failed with exit code {result.returncode}")
        return False
    return True


def download_synthea_samples():
    """Download pre-generated Synthea sample data"""
    
    print("\n🌐 Downloading Synthea Sample Data...")
    print("   Source: Synthea Public Repository")
    print("   Size: ~10 MB")
    print("   Patients: ~20 sample patients\n")
    
    # Create temp directory
    temp_dir = Path("temp_synthea_data")
    temp_dir.mkdir(exist_ok=True)
    
    # Download sample data from GitHub
    sample_url = "https://github.com/synthetichealth/synthea-sample-data/archive/refs/heads/master.zip"
    
    print("📥 Downloading...")
    
    try:
        import requests
        import zipfile
        import io
        
        response = requests.get(sample_url, stream=True)
        response.raise_for_status()
        
        print("📦 Extracting...")
        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # Find FHIR data directory
        fhir_dirs = list(temp_dir.glob("**/fhir"))
        if fhir_dirs:
            fhir_dir = fhir_dirs[0]
            print(f"✅ Downloaded to: {fhir_dir}")
            return str(fhir_dir)
        else:
            # Try to find any JSON files
            json_files = list(temp_dir.glob("**/*.json"))
            if json_files:
                print(f"✅ Downloaded {len(json_files)} JSON files")
                return str(temp_dir)
            else:
                print("⚠️  No FHIR data found in download")
                return None
                
    except ImportError:
        print("⚠️  'requests' library not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "requests"], check=True)
        return download_synthea_samples()  # Retry
    
    except Exception as e:
        print(f"❌ Download failed: {str(e)}")
        print("\n💡 Manual alternative:")
        print("   1. Visit: https://github.com/synthetichealth/synthea-sample-data")
        print("   2. Download and extract")
        print("   3. Run: python convert_synthea_to_cipercare.py --input <path> --upload")
        return None


def use_existing_data():
    """Use the existing synthetic data in the project"""
    
    existing_file = Path("data/synthetic/synthetic_fhir_dataset.json")
    
    if existing_file.exists():
        print(f"\n✅ Found existing synthetic data: {existing_file}")
        print(f"   Size: {existing_file.stat().st_size / 1024:.1f} KB")
        
        response = input("\n📤 Upload existing data to CyborgDB? (y/n): ")
        
        if response.lower() == 'y':
            return str(existing_file)
    
    return None


def check_dependencies():
    """Check if required packages are installed"""
    
    print("\n🔍 Checking dependencies...")
    
    required = {
        'sentence_transformers': 'sentence-transformers',
        'requests': 'requests'
    }
    
    missing = []
    
    for module, package in required.items():
        try:
            __import__(module.replace('_', '-'))
            print(f"   ✓ {package}")
        except ImportError:
            print(f"   ✗ {package}")
            missing.append(package)
    
    if missing:
        print(f"\n📦 Installing missing packages: {', '.join(missing)}")
        subprocess.run(
            [sys.executable, "-m", "pip", "install"] + missing,
            check=True
        )
        print("✅ Dependencies installed")
    else:
        print("✅ All dependencies installed")
    
    return True


def main():
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║        CipherCare - Add Synthea Patient Data                 ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    
    # Check dependencies
    if not check_dependencies():
        return
    
    # Ask user what they want to do
    print("\n🎯 Options:")
    print("   1. Use existing synthetic data in project")
    print("   2. Download fresh Synthea sample data")
    print("   3. Generate new data (requires Synthea installed)")
    
    choice = input("\nSelect option (1/2/3): ").strip()
    
    data_path = None
    
    if choice == '1':
        # Use existing data
        data_path = use_existing_data()
        
    elif choice == '2':
        # Download Synthea samples
        data_path = download_synthea_samples()
        
    elif choice == '3':
        # Generate new data
        num_patients = input("How many patients to generate? (default: 50): ").strip()
        num_patients = num_patients if num_patients else "50"
        
        print(f"\n🏥 Generating {num_patients} synthetic patients...")
        print("   This requires Java and Synthea to be installed.")
        print("   See: https://github.com/synthetichealth/synthea\n")
        
        response = input("Do you have Synthea installed? (y/n): ")
        
        if response.lower() == 'y':
            synthea_path = input("Enter Synthea directory path: ").strip()
            
            if os.path.exists(synthea_path):
                run_command(
                    f"cd {synthea_path} && ./run_synthea -p {num_patients}",
                    f"Generating {num_patients} patients"
                )
                data_path = os.path.join(synthea_path, "output", "fhir")
            else:
                print(f"❌ Path not found: {synthea_path}")
        else:
            print("\n💡 To install Synthea:")
            print("   git clone https://github.com/synthetichealth/synthea.git")
            print("   cd synthea")
            print("   ./run_synthea -p 50")
            return
    
    else:
        print("❌ Invalid option")
        return
    
    # Convert and upload
    if data_path:
        print(f"\n🔄 Converting data from: {data_path}")
        
        # Run conversion script
        cmd = f'"{sys.executable}" convert_synthea_to_cipercare.py --input "{data_path}" --upload'
        
        if run_command(cmd, "Converting and uploading to CyborgDB"):
            print("\n" + "="*60)
            print("✅ SUCCESS! Patient data added to CipherCare")
            print("="*60)
            print("\n📊 Next steps:")
            print("   1. Start the backend: python run_backend.py")
            print("   2. Open frontend: cd frontend && npm run dev")
            print("   3. Query patient data in the UI")
            print("\n🎉 Your system is ready to test!")
        else:
            print("\n❌ Upload failed. Check error messages above.")
    else:
        print("\n❌ No data source available. Try another option.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)
