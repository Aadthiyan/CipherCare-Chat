try:
    print("Importing backend.main...")
    import backend.main
    print("Success!")
except Exception as e:
    print(f"CRITICAL ERROR: {e}")
    import traceback
    traceback.print_exc()
