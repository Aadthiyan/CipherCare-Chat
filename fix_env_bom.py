"""Fix BOM issue in .env file"""
import os

# Read the .env file
with open('.env', 'r', encoding='utf-8-sig') as f:
    content = f.read()

# Write it back without BOM
with open('.env', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ BOM removed from .env file")
print("✓ Please restart the backend now")
