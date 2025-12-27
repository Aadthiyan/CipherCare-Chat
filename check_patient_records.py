"""Check record counts for each test patient to see which ones have data."""
from dotenv import load_dotenv
from backend.cyborg_lite_manager import get_cyborg_manager

load_dotenv()

test_patients = [
    "PID-102", "PID-104", "PID-110", "PID-117", 
    "PID-150", "PID-180", "PID-200", "PID-250"
]

def main():
    mgr = get_cyborg_manager()
    
    print("\n" + "=" * 60)
    print("RECORD COUNTS BY PATIENT")
    print("=" * 60)
    
    print(f"\n{'Patient ID':<12} {'Records':<12} {'Status':<20}")
    print("-" * 44)
    
    for pid in test_patients:
        try:
            count = mgr.get_patient_records_count(pid)
            status = "✅ Has data" if count > 0 else "⚠️  No records"
            print(f"{pid:<12} {count:<12} {status:<20}")
        except Exception as e:
            print(f"{pid:<12} {'ERROR':<12} {str(e)[:20]:<20}")
    
    # Get all patient IDs with counts
    print("\n" + "-" * 44)
    all_ids = mgr.get_all_patient_ids()
    print(f"Total unique patients in index: {len(all_ids)}")
    
    # Show which test patients have records
    test_with_records = [p for p in test_patients if p in all_ids]
    print(f"Test patients with records: {len(test_with_records)}")
    if test_with_records:
        print(f"  {', '.join(test_with_records)}")

if __name__ == "__main__":
    main()
