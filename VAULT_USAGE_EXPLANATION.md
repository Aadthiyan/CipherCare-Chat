# How Vault is Used in CipherCare

## Overview

**HashiCorp Vault** is an enterprise-grade secrets and encryption management system. In CipherCare, it's used for **zero-knowledge encryption** of patient medical data using the **Transit Engine**.

---

## Why Vault?

### Problem Without Vault:
- ❌ Encryption keys stored in code or environment variables
- ❌ No audit trail of who accessed what data
- ❌ Manual key rotation is risky
- ❌ Not HIPAA/SOC2 compliant for enterprise

### Solution With Vault:
- ✅ Keys **never leave Vault** (zero-knowledge)
- ✅ **Complete audit trail** for compliance
- ✅ **Automatic key rotation** support
- ✅ **Enterprise-grade encryption** (AES-256-GCM)
- ✅ HIPAA/SOC2/PCI-DSS ready

---

## Architecture

```
Patient Data (Plaintext)
        ↓
    [FastAPI Backend]
        ↓
    [Make API Call to Vault]
        ↓
    HashiCorp Vault Transit Engine
    ├─ Encrypts plaintext using Transit Key
    ├─ Returns ciphertext
    ├─ Logs operation in audit trail
    └─ Keys never exposed to app
        ↓
    Encrypted Data
        ↓
    [Store in PostgreSQL/CyborgDB]
        ↓
    Ciphertext in Database (Safe)
```

---

## Vault Components Used

### 1. **Transit Engine**
- **Location**: Secrets engine at `transit/` mount point
- **Purpose**: Handles all encryption/decryption operations
- **Key Feature**: Application never handles raw keys

### 2. **Transit Key**
- **Name**: `cipercare` (configurable)
- **Created at**: Runtime if doesn't exist
- **Encryption Method**: AES-256-GCM
- **Auto-rotation**: Enabled annually by default

### 3. **Audit Logging**
- **Enabled**: Yes, by default
- **Log Location**: Vault audit backend
- **Contains**: All encrypt/decrypt requests, user, timestamp, result
- **HIPAA Use**: Proves who accessed what data and when

---

## How It Works in CipherCare

### Setup Phase (One-time)

1. **Start Vault Server**
   ```powershell
   vault server -dev
   ```
   Returns root token: `s.xxxxxxxxxxxxxxxxxxxxxxxx`

2. **Configure Environment**
   ```bash
   VAULT_ADDR=http://127.0.0.1:8200
   VAULT_TOKEN=s.xxxxxxxxxxxxxxxxxxxxxxxx
   ENCRYPTION_TYPE=vault_transit
   VAULT_TRANSIT_KEY=cipercare
   ```

3. **Enable Transit Engine** (automatic)
   ```
   vault secrets enable transit
   vault write -f transit/keys/cipercare
   ```
   Creates a key that will encrypt/decrypt all data

---

### Runtime Phase (Every Request)

#### Patient Data Encryption (Upload)
```
1. Doctor uploads patient medical record
2. Backend receives plaintext data
3. Backend calls Vault Transit API:
   POST /v1/transit/encrypt/cipercare
   {
     "plaintext": base64(patient_data)
   }
4. Vault encrypts using Transit Key
5. Backend receives ciphertext
6. Backend stores ciphertext in database
7. Vault logs: "User X encrypted Y bytes at timestamp Z"
```

#### Patient Data Decryption (Query)
```
1. Doctor queries patient data
2. Backend retrieves ciphertext from database
3. Backend calls Vault Transit API:
   POST /v1/transit/decrypt/cipercare
   {
     "ciphertext": ciphertext_from_db
   }
4. Vault decrypts using Transit Key
5. Backend receives plaintext
6. Backend processes for LLM
7. Vault logs: "User X decrypted Y bytes at timestamp Z"
```

---

## Current Implementation Status

### Option A: Local Encryption (Currently Used ✅)
```python
# encryption/crypto_service.py
# Uses local AES-256-GCM encryption
# Master key stored in encryption/master.key
# Simpler, but no Vault features
```

### Option B: Vault Transit (Available But Not Active)
```python
# encryption/vault_crypto_service.py
# Uses HashiCorp Vault Transit Engine
# Zero-knowledge encryption
# Audit trail enabled
# Ready for production deployment
```

---

## How to Switch to Vault

### Step 1: Install Vault
```powershell
# Windows with Chocolatey
choco install vault

# Or Docker
docker run -p 8200:8200 vault server -dev
```

### Step 2: Start Vault
```powershell
vault server -dev
# Copy the Root Token from output
```

### Step 3: Configure .env
```bash
ENCRYPTION_TYPE=vault_transit
VAULT_ADDR=http://127.0.0.1:8200
VAULT_TOKEN=s.your_root_token_here
VAULT_TRANSIT_KEY=cipercare
```

### Step 4: Update backend/main.py
```python
# Change from:
from encryption.crypto_service import EncryptionService

# To:
from encryption.vault_crypto_service import VaultTransitCryptoService
```

### Step 5: Test
```bash
python encryption/vault_crypto_service.py
# Should show: ✓ Vault authentication successful
```

---

## Security Benefits

### 1. Zero-Knowledge Encryption
- Encryption keys **never** sent to/from backend
- Vault holds keys exclusively
- Backend only sends plaintext/ciphertext

### 2. Audit Trail
Every encryption/decryption operation logged:
```json
{
  "timestamp": "2025-12-23T17:47:07Z",
  "operation": "encrypt",
  "user": "attending",
  "key": "cipercare",
  "request_hash": "abc123...",
  "response_hash": "def456...",
  "result": "success"
}
```

### 3. Automatic Key Rotation
- Old encryption keys automatically rotated annually
- Data re-encrypted with new keys
- Complete transparency

### 4. Compliance Ready
- ✅ HIPAA: Audit trail + encryption
- ✅ SOC2: Zero-knowledge design
- ✅ PCI-DSS: AES-256 encryption
- ✅ GDPR: Encrypted patient data

---

## Comparison: Vault vs Local Encryption

| Feature | Local (Current) | Vault Transit | 
|---------|-----------------|----------------|
| Encryption | AES-256-GCM ✅ | AES-256-GCM ✅ |
| Key Storage | Local file | Vault server |
| Key Rotation | Manual | Automatic ✅ |
| Audit Trail | None | Complete ✅ |
| Zero-Knowledge | No | Yes ✅ |
| Production Ready | Dev only | Enterprise ✅ |
| Compliance | Basic | HIPAA/SOC2 ✅ |
| Complexity | Simple | Moderate |

---

## Example: Encrypt a Medical Record

### With Vault Transit:
```python
from encryption.vault_crypto_service import VaultTransitCryptoService

service = VaultTransitCryptoService(
    vault_addr="http://127.0.0.1:8200",
    vault_token="s.xxx",
    transit_key="cipercare"
)

# Encrypt
plaintext = "Patient has Type 2 Diabetes"
encrypted = service.encrypt(plaintext)
# Returns: encrypted_data (ciphertext from Vault)

# Vault's audit log now shows:
# [2025-12-23 17:47:07] User 'attending' encrypted 28 bytes with key 'cipercare'

# Decrypt
decrypted = service.decrypt(encrypted)
# Returns: "Patient has Type 2 Diabetes"

# Vault's audit log now shows:
# [2025-12-23 17:47:10] User 'attending' decrypted 28 bytes with key 'cipercare'
```

---

## Files Involved

| File | Purpose |
|------|---------|
| `encryption/vault_crypto_service.py` | Vault Transit integration |
| `encryption/crypto_service.py` | Local encryption (current) |
| `VAULT_SETUP.md` | Detailed setup guide |
| `VAULT_QUICK_REFERENCE.md` | Quick reference commands |
| `VAULT_INTEGRATION_COMPLETE.md` | Implementation details |
| `.env.example` | Shows VAULT_* variables |

---

## Common Issues

### Issue: "Connection refused"
```
Error: Failed to connect to http://127.0.0.1:8200
Solution: Run `vault server -dev` in another terminal
```

### Issue: "Invalid token"
```
Error: Invalid token s.xxxxx
Solution: Use the Root Token from vault server -dev output
```

### Issue: "Transit engine not found"
```
Error: transit engine not enabled
Solution: Run `vault secrets enable transit` (or auto-enabled)
```

---

## Next Steps

1. **Install Vault** (if transitioning to production)
   ```
   choco install vault  # Windows
   brew install vault   # macOS
   ```

2. **Start Vault Server**
   ```
   vault server -dev
   ```

3. **Update .env file** with Vault credentials

4. **Switch encryption backend** in `backend/main.py`

5. **Deploy with Vault** in production

---

## Summary

**Vault provides enterprise-grade encryption for CipherCare:**
- 🔐 Zero-knowledge encryption (keys never leave Vault)
- 📋 Complete audit trail (HIPAA compliance)
- 🔑 Automatic key rotation (security best practice)
- ✅ HIPAA/SOC2/PCI-DSS ready (compliance)
- 🚀 Production-proven (Netflix, HashiCorp use it)

**Current state**: Local encryption used, but Vault integration is ready to deploy.

