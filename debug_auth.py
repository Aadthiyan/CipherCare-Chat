try:
    print("Importing os...")
    import os
    print("Importing jwt...")
    import jwt
    print("Importing fastapi...")
    from fastapi import Depends
    print("Importing backend.models...")
    from backend.models import TokenData
    print("Importing backend.auth...")
    import backend.auth
    print("Success!")
except Exception as e:
    print(f"CRITICAL ERROR: {e}")
    import traceback
    traceback.print_exc()
