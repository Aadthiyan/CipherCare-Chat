from cyborgdb.openapi_client import models
print([m for m in dir(models) if 'delete' in m.lower() or 'index' in m.lower()])
