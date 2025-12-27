import cyborgdb
import os
from dotenv import load_dotenv

load_dotenv()

client = cyborgdb.Client(
    api_key=os.getenv("CYBORGDB_API_KEY"),
    base_url=os.getenv("CYBORGDB_BASE_URL", "http://localhost:8002")
)

# Check available methods
print("Available API methods:")
methods = [m for m in dir(client.api) if not m.startswith('_')]
print([m for m in methods if 'index' in m.lower()])
