import os
import sys
import asyncio
from pathlib import Path

# Ensure we're in the right directory
os.chdir(Path(__file__).parent)

# Load env vars explicitly
from dotenv import load_dotenv
load_dotenv()

# Verify GROQ key is loaded
if not os.getenv('GROQ_API_KEY'):
    print("ERROR: GROQ_API_KEY not loaded! Exiting.")
    sys.exit(1)

print(f"[+] GROQ_API_KEY loaded: {os.getenv('GROQ_API_KEY')[:10]}...")

# Force ProactorEventLoop on Windows for better stability
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Now import and run uvicorn
import uvicorn

if __name__ == "__main__":
    try:
        print(f"[*] Starting backend on http://0.0.0.0:8000...")
        sys.stdout.flush()
        uvicorn.run(
            "backend.main:app",
            host="0.0.0.0",
            port=8000,
            log_level="info",
            reload=False,
            access_log=True
        )
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
