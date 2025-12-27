"""Check whether patient PID-102 records are present in CyborgDB"""
import json
from dotenv import load_dotenv
from backend.cyborg_lite_manager import get_cyborg_manager
import os


def main():
    # Ensure environment variables from .env are loaded
    load_dotenv()
    pid = "PID-102"
    mgr = get_cyborg_manager()
    try:
        count = mgr.get_patient_records_count(pid)
        print(f"Records for {pid}: {count}")
        all_ids = mgr.get_all_patient_ids()
        print(f"Total unique patient IDs in index: {len(all_ids)}")
        print("PID-102 present in index?", pid in all_ids)
    except Exception as e:
        print("Error checking PID-102:", e)


if __name__ == "__main__":
    main()
