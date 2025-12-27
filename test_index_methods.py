import cyborgdb
import inspect
import secrets

client = cyborgdb.Client(api_key='cyborg_9e8c1c2e25c944d78f41ac7f23376d23', base_url='http://localhost:8002')

# Create a test index to see what methods it has
index_key = secrets.token_bytes(32)
try:
    index = client.create_index(
        index_name="test_index_methods",
        index_key=index_key
    )
    print("Index object methods (non-private):")
    methods = [m for m in dir(index) if not m.startswith('_')]
    print(methods)
    
    print("\n\nMethod signatures:")
    for method_name in ['upsert', 'query', 'get', 'delete']:
        if hasattr(index, method_name):
            method = getattr(index, method_name)
            print(f"\n{method_name}:")
            print(f"  Signature: {inspect.signature(method)}")
            print(f"  Docstring: {method.__doc__}")
    
except Exception as e:
    print(f"Error: {e}")
