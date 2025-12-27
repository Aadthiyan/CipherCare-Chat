"""Fix .env file BOM issue"""
import os

env_file = '.env'

# Read in binary
with open(env_file, 'rb') as f:
    content = f.read()

# Remove UTF-8 BOM if present
if content.startswith(b'\xef\xbb\xbf'):
    content = content[3:]
    print("✓ Removed UTF-8 BOM from .env")

# Write back
with open(env_file, 'wb') as f:
    f.write(content)

# Test it
from dotenv import load_dotenv
load_dotenv(env_file)
db_url = os.getenv('DATABASE_URL')

if db_url:
    print(f"✓ DATABASE_URL successfully loaded!")
    print(f"  First 60 chars: {db_url[:60]}")
else:
    print("✗ DATABASE_URL still not loaded")
    # Debug
    with open(env_file, 'r') as f:
        lines = f.readlines()
        print(f"  First line: {repr(lines[0][:80])}")
