import cyborgdb

client = cyborgdb.Client(api_key='cyborg_9e8c1c2e25c944d78f41ac7f23376d23', base_url='http://localhost:8002')

print("Client created successfully")
print("Testing health check...")
health = client.get_health()
print(f"Health: {health}")
