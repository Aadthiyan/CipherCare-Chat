import cyborgdb
import os
from dotenv import load_dotenv

load_dotenv()

client = cyborgdb.Client(
    api_key=os.getenv("CYBORGDB_API_KEY"),
    base_url=os.getenv("CYBORGDB_BASE_URL", "http://localhost:8002")
)

# Check client methods
print("Client methods:")
methods = [m for m in dir(client) if not m.startswith('_') and 'index' in m.lower()]
print(methods)
