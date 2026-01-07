"""
Upload to Render's combined backend+CyborgDB service
"""

import os
import sys

# Override the URL for this upload
os.environ["CYBORGDB_BASE_URL"] = "https://ciphercare-backend.onrender.com"

# Import and run the upload script
from upload_sdk_fast import main

if __name__ == "__main__":
    print("=" * 70)
    print("🚀 Uploading to Render (Combined Backend+CyborgDB)")
    print("=" * 70)
    print(f"\nTarget: https://ciphercare-backend.onrender.com")
    print(f"Note: CyborgDB runs on port 8002 inside the container")
    print(f"      Backend proxies requests internally")
    print("=" * 70)
    
    main()
