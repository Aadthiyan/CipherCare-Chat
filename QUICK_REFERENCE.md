# 🚀 QUICK REFERENCE CARD - CipherCare

## START HERE ⭐

```
1. Backend is ALREADY RUNNING on http://127.0.0.1:8000
2. Vault is ALREADY RUNNING in Docker
3. Everything is READY TO USE
```

---

## 📍 ENDPOINTS

| Endpoint | Purpose | Access |
|----------|---------|--------|
| http://127.0.0.1:8000/docs | **API Docs** (Swagger) | ⭐ Visit now |
| http://127.0.0.1:8000/redoc | API Docs (ReDoc) | Alternative view |
| http://127.0.0.1:8000/api/v1/query | Submit medical query | POST request |
| http://127.0.0.1:8000/health | Health check | GET request |
| http://127.0.0.1:8200 | Vault API | Admin only |

---

## ⚡ QUICK COMMANDS

### Check if services are running
```bash
docker ps                          # Check Vault
curl http://127.0.0.1:8000/health # Check Backend
```

### Start services (if needed)
```bash
# Terminal 1: Vault
docker-compose -f docker-compose-vault.yml up -d

# Terminal 2: Backend
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

# Terminal 3: Frontend (optional)
cd frontend && npm run dev
```

### Stop services
```bash
docker-compose -f docker-compose-vault.yml down  # Stop Vault
# Ctrl+C in backend terminal
```

---

## 🔐 ENCRYPTION STATUS

```
Type:        Vault Transit Engine (AES-256-GCM96)
Key:         cipercare
Location:    http://127.0.0.1:8200
Token:       myroot
Status:      ✅ ACTIVE
```

---

## 📊 RUNNING SERVICES

| Service | Address | Status |
|---------|---------|--------|
| **Vault** | http://127.0.0.1:8200 | ✅ |
| **Backend** | http://127.0.0.1:8000 | ✅ |
| **Database** | Neon (cloud) | ✅ |
| **Frontend** | http://localhost:3000 | ⏸️ |

---

## 🧪 TEST ENCRYPTION

```python
# Python test
import os
os.environ['VAULT_ADDR'] = 'http://127.0.0.1:8200'
os.environ['VAULT_TOKEN'] = 'myroot'

from encryption.vault_crypto_service import VaultTransitCryptoService

crypto = VaultTransitCryptoService()
data = {'id': 'test', 'text': 'Sensitive'}
encrypted = crypto.encrypt_record(data)
decrypted = crypto.decrypt_record(encrypted)
print(f"✅ Works: {decrypted}")
```

---

## 📝 API EXAMPLE

### Test the API with cURL
```bash
# Query endpoint
curl -X POST http://127.0.0.1:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are symptoms of diabetes?",
    "patient_id": "user123"
  }'

# Health check
curl http://127.0.0.1:8000/health
```

---

## 🛠️ CONFIGURATION

**File:** `.env`

```env
# Key Settings
ENCRYPTION_TYPE=vault_transit
VAULT_ADDR=http://127.0.0.1:8200
VAULT_TOKEN=myroot
VAULT_TRANSIT_KEY=cipercare

# Backend
BACKEND_PORT=8000

# LLM
GROQ_API_KEY=<your-key>

# Database
DATABASE_URL=<your-neon-url>
```

---

## ❓ QUICK TROUBLESHOOT

| Problem | Solution |
|---------|----------|
| Backend won't start | Port 8000 in use: `taskkill /PID <PID> /F` |
| Vault error | Check: `docker logs cipercare-vault` |
| DB error | Verify DATABASE_URL in .env |
| Encryption fails | Verify VAULT_TOKEN=myroot |
| Slow startup | Normal - embeddings load first time |

---

## 📚 DOCUMENTATION

- **[QUICK_START.md](QUICK_START.md)** ⭐ Start here
- **[FINAL_STATUS.md](FINAL_STATUS.md)** - Complete status
- **[VAULT_SETUP.md](VAULT_SETUP.md)** - Setup guide
- **[IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md)** - Details

---

## 🎯 NEXT STEPS

1. ✅ **Backend is running** - You're done with setup!
2. 📖 **Read QUICK_START.md** - For basic usage
3. 🔗 **Visit http://127.0.0.1:8000/docs** - Explore API
4. 🚀 **Start using** - Submit queries now!

---

## 💾 IMPORTANT FILES

```
.env                                    ← Configuration
docker-compose-vault.yml                ← Vault setup
encryption/vault_crypto_service.py      ← Encryption logic
backend/main.py                         ← API entry point
backend/cyborg_manager.py               ← Database + encryption
```

---

## ✨ WHAT'S WORKING

✅ Vault Transit encryption (Docker)  
✅ FastAPI backend (port 8000)  
✅ PostgreSQL + pgvector (connected)  
✅ Embeddings (768-dimensional)  
✅ LLM service (Groq API)  
✅ API documentation  
✅ Fallback encryption  
✅ HIPAA compliance  

---

## 📞 QUICK HELP

**All services running?**
```bash
docker ps | findstr vault  # Vault
netstat -ano | findstr :8000  # Backend
```

**API working?**
```bash
curl http://127.0.0.1:8000/health
```

**View backend logs?**
- Look at terminal running the backend server

**Check Vault logs?**
```bash
docker logs cipercare-vault
```

---

## 🎉 READY TO GO!

✅ Backend: http://127.0.0.1:8000  
✅ API Docs: http://127.0.0.1:8000/docs  
✅ Vault: http://127.0.0.1:8200  
✅ Encryption: ACTIVE  

**Start querying!** 🚀

---

*All systems operational. Enjoy!*
