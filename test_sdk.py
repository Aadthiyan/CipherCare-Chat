import cyborgdb
import inspect

client = cyborgdb.Client(api_key='test', base_url='http://localhost:8002')

# Check load_index signature
print("load_index signature:")
print(inspect.signature(client.load_index))

# Check create_index signature  
print("\ncreate_index signature:")
print(inspect.signature(client.create_index))

# Check what load_index returns
print("\nload_index docstring:")
print(client.load_index.__doc__)

print("\ncreate_index docstring:")
print(client.create_index.__doc__)
