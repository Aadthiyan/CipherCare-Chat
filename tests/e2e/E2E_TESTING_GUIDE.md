# CipherCare End-to-End Testing Guide
## Complete E2E Test Suite Documentation

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Test Scenarios](#test-scenarios)
3. [Setup & Prerequisites](#setup--prerequisites)
4. [Running Tests](#running-tests)
5. [Test Results Interpretation](#test-results-interpretation)
6. [Validation Checklist](#validation-checklist)
7. [Troubleshooting](#troubleshooting)
8. [Demo Preparation](#demo-preparation)

---

## 🎯 Overview

The E2E testing suite comprehensively validates CipherCare's critical workflows, security controls, compliance features, and error handling across all system components.

### Test Coverage

- **6 Complete Scenarios** covering all user journeys
- **40+ Individual Test Cases** validating specific functionality
- **Security & Compliance** validation (RBAC, audit logging, encryption)
- **Error Handling** and graceful degradation
- **Performance** monitoring (<5s latency requirements)
- **Safety Guardrails** verification

### Architecture

```
tests/e2e/
├── conftest.py                 # Fixtures, test utilities, API client
├── test_scenarios_1_3.py       # Scenarios 1-3 (Happy Path, Access Control, Security)
├── test_scenarios_4_6.py       # Scenarios 4-6 (Compliance, Error Handling, Safety)
├── run_tests.py                # Test orchestration & execution
└── results/                    # Generated test results
    ├── junit_*.xml
    ├── e2e_test_results_*.json
    └── execution.log
```

---

## 🧪 Test Scenarios

### Scenario 1: Happy Path ✓
**User Journey**: Clinician logs in → Selects patient → Asks clinical question → Receives answer with sources → Verifies audit log → Logs out

**Test Cases**:
```
✓ test_clinician_login              - Verify authentication works
✓ test_patient_selection             - List accessible patients
✓ test_get_patient_data              - Retrieve patient medical data
✓ test_clinical_query                - Submit and get clinical answer
✓ test_response_quality              - Verify answer is medically reasonable
✓ test_audit_log_entry_created       - Confirm query logged
✓ test_logout                        - Verify logout works
✓ test_complete_workflow             - Full end-to-end flow
```

**Expected Results**:
- ✅ Login succeeds with valid credentials
- ✅ Patient list returned with accessible patients only
- ✅ Response includes answer + sources + disclaimer
- ✅ Query appears in audit log with timestamp, user ID
- ✅ Response time <5 seconds
- ✅ Logout clears authentication

**Example Execution**:
```bash
python -m pytest tests/e2e/test_scenarios_1_3.py::TestScenario1HappyPath -v
```

---

### Scenario 2: Access Control (RBAC) 🔒
**Purpose**: Verify unauthorized access is rejected with 403 Forbidden

**Test Cases**:
```
✓ test_unauthorized_patient_access_forbidden        - Clinician A cannot query patient assigned to B
✓ test_unauthorized_patient_data_access_forbidden   - Data access blocked for unauthorized users
✓ test_audit_log_records_denied_access              - Failed access attempts logged
✓ test_unauthenticated_request_rejected             - No token = 401/403
✓ test_invalid_token_rejected                       - Expired/invalid token rejected
```

**Expected Results**:
- ✅ HTTP 403 Forbidden on unauthorized query
- ✅ HTTP 403/404 on data access
- ✅ HTTP 401/403 on missing authentication
- ✅ Audit log shows failed access attempts
- ✅ Error response includes appropriate message

**Example Execution**:
```bash
python -m pytest tests/e2e/test_scenarios_1_3.py::TestScenario2AccessControl -v
```

---

### Scenario 3: Data Security 🔐
**Purpose**: Verify encrypted search works without plaintext exposure

**Test Cases**:
```
✓ test_embeddings_encrypted_in_storage     - Verify no plaintext embeddings on disk
✓ test_encrypted_search_returns_correct_results - Search returns correct results
✓ test_search_result_consistency           - Identical queries return consistent results
✓ test_no_plaintext_patient_data_in_logs   - Sensitive data not in logs
```

**Expected Results**:
- ✅ Embeddings file encrypted (not readable as JSON floats)
- ✅ Search queries return correct medical information
- ✅ Repeated searches return consistent results
- ✅ Patient names/SSN not in plaintext logs

**Example Execution**:
```bash
python -m pytest tests/e2e/test_scenarios_1_3.py::TestScenario3DataSecurity -v
```

---

### Scenario 4: Compliance & Audit Trail 📋
**Purpose**: Verify complete audit logging of all actions

**Test Cases**:
```
✓ test_audit_trail_captures_all_actions       - All queries logged
✓ test_audit_log_contains_timestamps          - Valid ISO timestamps
✓ test_audit_log_contains_user_ids            - User identification logged
✓ test_audit_log_contains_outcomes            - Action outcomes recorded
✓ test_audit_trail_sequence                   - Chronological order
✓ test_audit_log_immutability                 - Entries cannot be modified
```

**Expected Results**:
- ✅ Every query appears in audit log
- ✅ Timestamps in ISO format, within 1 hour of now
- ✅ User ID/email present in all entries
- ✅ Status/outcome recorded (SUCCESS/FAILED)
- ✅ Entries ordered chronologically
- ✅ Same entry retrieved later is identical

**Audit Entry Structure**:
```json
{
  "id": "unique_id",
  "timestamp": "2024-12-16T10:30:45.123Z",
  "action": "QUERY",
  "user_id": "clinician_a@test.com",
  "patient_id": "patient_001",
  "resource": "/query",
  "status": "SUCCESS",
  "ip_address": "127.0.0.1",
  "details": {
    "question": "What medications?",
    "response_time_ms": 245
  }
}
```

**Example Execution**:
```bash
python -m pytest tests/e2e/test_scenarios_4_6.py::TestScenario4Compliance -v
```

---

### Scenario 5: Error Handling ⚠️
**Purpose**: Verify graceful failure and recovery

**Test Cases**:
```
✓ test_backend_health_check                  - Health endpoint works
✓ test_graceful_error_on_backend_unavailable - Handles unavailable service
✓ test_timeout_handling                      - Graceful timeout handling
✓ test_query_with_invalid_patient_id         - Invalid input handled
✓ test_malformed_request_handling            - Bad requests handled
✓ test_error_response_structure              - Consistent error format
✓ test_error_scenarios (parametrized)        - Connection/timeout/server errors
```

**Expected Results**:
- ✅ Health endpoint returns status
- ✅ Connection errors return error (not crash)
- ✅ Timeouts handled gracefully
- ✅ Invalid patient IDs return 404
- ✅ Malformed requests return 400
- ✅ All errors include message

**Error Response Format**:
```json
{
  "success": false,
  "error": "Patient not found",
  "status_code": 404,
  "timestamp": "2024-12-16T10:30:45.123Z"
}
```

**Example Execution**:
```bash
python -m pytest tests/e2e/test_scenarios_4_6.py::TestScenario5ErrorHandling -v
```

---

### Scenario 6: Safety Guardrails 🛡️
**Purpose**: Verify response filtering and safety measures

**Test Cases**:
```
✓ test_response_includes_disclaimer               - Medical disclaimer present
✓ test_response_includes_sources                  - Sources/attribution included
✓ test_jailbreak_attempt_rejection                - Harmful prompts caught
✓ test_response_filtering_flags_unsafe_content    - Unsafe responses flagged
✓ test_response_length_reasonable                 - No hallucination/truncation
✓ test_private_data_in_response_redacted          - Private data not exposed
✓ test_response_consistency_with_guidelines       - Medically appropriate
```

**Expected Results**:
- ✅ Every response includes medical disclaimer
- ✅ Sources listed for medical information
- ✅ Jailbreak attempts rejected or handled safely
- ✅ Unsafe responses flagged
- ✅ Response length 20-10,000 chars
- ✅ No SSN/exact address exposed
- ✅ Advice follows medical guidelines

**Example Disclaimer**:
```
IMPORTANT MEDICAL DISCLAIMER: This information is for educational purposes 
only and does not constitute medical advice. Always consult with a qualified 
healthcare professional before making any medical decisions.
```

**Example Execution**:
```bash
python -m pytest tests/e2e/test_scenarios_4_6.py::TestScenario6SafetyGuardrails -v
```

---

## 🔧 Setup & Prerequisites

### System Requirements

- Python 3.9+
- Backend running on `http://localhost:8000`
- Frontend running on `http://localhost:3000` (for UI tests)
- PostgreSQL/database with test data
- All dependencies installed

### Installation

```bash
# Install test dependencies
pip install pytest pytest-json-report requests pytest-timeout

# Or use provided requirements file
pip install -r tests/requirements_test.txt
```

### Environment Setup

**1. Start Backend**:
```bash
# Terminal 1
python backend/main.py
```

**2. Verify Backend Health**:
```bash
curl http://localhost:8000/health
# Should return: {"status": "healthy"}
```

**3. Load Test Data**:
```bash
# If needed, populate test patients and users
python tests/e2e/setup_test_data.py
```

**4. Configure Test Credentials**:

Edit `tests/e2e/conftest.py`:
```python
TEST_CLINICIAN_A = {
    "username": "clinician_a@test.com",
    "password": "SecurePassword123!",
    "clinic_id": "clinic_001"
}

TEST_PATIENT_A = {
    "patient_id": "patient_001",
    "name": "John Doe",
    "assigned_to": "clinician_a@test.com"
}
```

---

## 🚀 Running Tests

### Quick Start (All Tests)

```bash
# Run all scenarios
python tests/e2e/run_tests.py --all

# Or using pytest directly
pytest tests/e2e/ -v
```

### Run Specific Scenario

```bash
# Run Scenario 1 (Happy Path)
python tests/e2e/run_tests.py --scenario 1

# Run Scenario 2 (Access Control)
python tests/e2e/run_tests.py --scenario 2

# etc...
```

### Run Specific Test Class

```bash
# Just happy path tests
pytest tests/e2e/test_scenarios_1_3.py::TestScenario1HappyPath -v

# Just access control tests
pytest tests/e2e/test_scenarios_1_3.py::TestScenario2AccessControl -v
```

### Run Single Test Function

```bash
# Just the login test
pytest tests/e2e/test_scenarios_1_3.py::TestScenario1HappyPath::test_clinician_login -v
```

### Advanced Options

```bash
# With health check
python tests/e2e/run_tests.py --all --check-health

# Custom backend URL
python tests/e2e/run_tests.py --all --backend-url http://prod.local:8000

# Verbose output with full tracebacks
pytest tests/e2e/ -vv --tb=long

# Stop on first failure
pytest tests/e2e/ -x

# Show print statements
pytest tests/e2e/ -s

# Run with timeout (10 seconds per test)
pytest tests/e2e/ --timeout=10
```

---

## 📊 Test Results Interpretation

### Result Files

Test execution generates multiple result files:

```
tests/e2e/results/
├── e2e_test_results_20241216_103045.json   # Main results file
├── junit_Scenario1_HappyPath.xml           # JUnit XML format
├── junit_Scenario2_AccessControl.xml
├── execution.log                            # Detailed execution log
```

### Reading Results JSON

```json
{
  "execution_time": "2024-12-16T10:30:45.123456",
  "total_scenarios": 6,
  "passed": 6,
  "failed": 0,
  "errors": 0,
  "success_rate": "100.0%",
  "duration_seconds": 245.32,
  "results": [
    {
      "scenario": "Scenario1_HappyPath",
      "status": "PASSED",
      "exit_code": 0,
      "timestamp": "2024-12-16T10:30:52.123Z"
    },
    ...
  ]
}
```

### Console Output

```
======================================================================
E2E TEST EXECUTION SUMMARY
======================================================================
Execution Time: 2024-12-16T10:30:45.123456
Total Scenarios: 6
Passed: 6 ✓
Failed: 0 ✗
Errors: 0 ⚠
Success Rate: 100.0%
Duration: 245.32 seconds

Detailed Results:
----------------------------------------------------------------------
✓ Scenario1_HappyPath: PASSED
✓ Scenario2_AccessControl: PASSED
✓ Scenario3_DataSecurity: PASSED
✓ Scenario4_Compliance: PASSED
✓ Scenario5_ErrorHandling: PASSED
✓ Scenario6_SafetyGuardrails: PASSED
======================================================================
```

### Interpreting Failures

**Test Failure**:
```
FAILED tests/e2e/test_scenarios_1_3.py::TestScenario1HappyPath::test_clinical_query
AssertionError: Query failed: {'success': False, 'status_code': 500}
```

**Resolution Steps**:
1. Check backend logs: `tail -f logs/backend.log`
2. Verify test data exists
3. Check network connectivity: `curl http://localhost:8000/health`
4. Review detailed error in `execution.log`

---

## ✅ Validation Checklist

All items must pass for system to be demo-ready:

### Core Functionality
- [ ] Scenario 1: Happy path workflow completes without errors
- [ ] Login/logout cycle works correctly
- [ ] Patient data retrieval succeeds
- [ ] Clinical query returns answer + sources + disclaimer
- [ ] Performance <5s on all queries

### Security & Access Control
- [ ] Scenario 2: Unauthorized access rejected (403)
- [ ] RBAC enforced correctly
- [ ] Invalid tokens rejected (401)
- [ ] Unauthenticated requests rejected

### Data Security & Encryption
- [ ] Scenario 3: Embeddings encrypted on disk
- [ ] Encrypted search returns correct results
- [ ] No plaintext patient data in logs
- [ ] Search results consistent across queries

### Compliance & Audit
- [ ] Scenario 4: All queries in audit log
- [ ] Audit entries have timestamps
- [ ] User IDs recorded correctly
- [ ] Action outcomes logged
- [ ] Audit entries immutable

### Error Handling
- [ ] Scenario 5: Graceful failure on backend outage
- [ ] No unhandled exceptions
- [ ] Error responses include messages
- [ ] Timeouts handled appropriately
- [ ] Invalid input rejected gracefully

### Safety & Guardrails
- [ ] Scenario 6: All responses include disclaimer
- [ ] Sources attributed correctly
- [ ] Jailbreak attempts caught
- [ ] Response length reasonable
- [ ] Advice follows medical guidelines

### Performance & Stability
- [ ] No memory leaks in sustained test
- [ ] CPU usage <80% under load
- [ ] Response times consistently <5s
- [ ] Error rate <1%
- [ ] System stable for demo duration (≥1 hour)

---

## 🔍 Troubleshooting

### Backend Connection Issues

**Problem**: `ConnectionError: Failed to establish a new connection`

**Solution**:
```bash
# Check if backend is running
curl http://localhost:8000/health

# Start backend if needed
cd /path/to/cipercare
python backend/main.py

# Check port 8000 is not in use
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows
```

### Authentication Issues

**Problem**: `AssertionError: Failed to login`

**Solution**:
```bash
# Verify test credentials in conftest.py
# Make sure user exists in database
python -c "from backend.auth import verify_user; verify_user('clinician_a@test.com')"

# Check password policy
# Reset password if needed
python backend/auth.py reset-password clinician_a@test.com
```

### Patient Data Not Found

**Problem**: `AssertionError: No patients available`

**Solution**:
```bash
# Verify test patients exist
python backend/models.py list-patients

# Create test patients if needed
python tests/e2e/setup_test_data.py --create-patients

# Check patient assignments
python backend/models.py list-patient-assignments
```

### Audit Log Not Recording

**Problem**: `AssertionError: No audit entries found`

**Solution**:
```bash
# Check audit logging is enabled
grep "AUDIT_LOGGING" backend/config.py

# Verify audit database/file exists
ls -la logs/audit.log

# Check database connection
python -c "from backend.logging_config import check_audit_db; check_audit_db()"
```

### Encryption Verification Fails

**Problem**: `AssertionError: Vectors appear to be unencrypted (floats)`

**Solution**:
```bash
# Verify encryption is enabled
grep "ENCRYPTION_ENABLED" backend/config.py

# Check encryption keys are loaded
python -c "from encryption.crypto_service import CryptoService; print(CryptoService.check_keys())"

# Regenerate embeddings if needed
python embeddings/embedder.py --recreate-encrypted
```

### Test Timeout

**Problem**: `TimeoutError: Test took too long`

**Solution**:
```bash
# Check backend performance
curl -w "Time: %{time_total}s\n" http://localhost:8000/patients

# Increase timeout in conftest.py
API_TIMEOUT = 30  # Increase from 10

# Check system resources
top  # or Task Manager on Windows
```

---

## 🎬 Demo Preparation

### Pre-Demo Checklist

- [ ] **24 Hours Before**
  - [ ] Run full test suite: `pytest tests/e2e/ -v`
  - [ ] All scenarios passing
  - [ ] Performance acceptable <5s
  - [ ] Zero errors or warnings

- [ ] **1 Hour Before**
  - [ ] Start backend: `python backend/main.py`
  - [ ] Start frontend: `cd frontend && npm start`
  - [ ] Check system health: `curl http://localhost:8000/health`
  - [ ] Load test data: `python tests/e2e/setup_test_data.py`
  - [ ] Run quick validation: `pytest tests/e2e/test_scenarios_1_3.py::TestScenario1HappyPath -v`

- [ ] **15 Minutes Before**
  - [ ] Clear browser cache and cookies
  - [ ] Close unnecessary applications
  - [ ] Disable screen saver
  - [ ] Test network connectivity
  - [ ] Verify projector/screen sharing
  - [ ] Have backup API endpoint ready

- [ ] **During Demo**
  - [ ] Use test credentials (provided in conftest.py)
  - [ ] Use predefined test patients
  - [ ] Have troubleshooting guide ready
  - [ ] Monitor backend logs: `tail -f logs/backend.log`
  - [ ] Have fallback demo (screenshots) if system fails

### Demo Talking Points

**Scenario 1**: "Let me show you a complete user journey. Here's a clinician logging in, selecting a patient, asking a clinical question, and getting a detailed answer with sources and safety disclaimer."

**Scenario 2**: "Security is critical. Let me demonstrate that another clinician cannot access this patient's data—they get a 403 Forbidden error."

**Scenario 3**: "All medical data is encrypted. Even though we're querying encrypted data, the search returns correct results."

**Scenario 4**: "Every action is logged for compliance. You can see the complete audit trail with timestamps, user IDs, and outcomes."

**Scenario 5**: "The system handles errors gracefully. Even if components fail, users get helpful error messages."

**Scenario 6**: "We include safety guardrails—every response has a medical disclaimer, sources are attributed, and unsafe prompts are caught."

### Known Limitations

See [KNOWN_LIMITATIONS.md](./KNOWN_LIMITATIONS.md) for system constraints and workarounds.

### Troubleshooting During Demo

See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for quick fixes to common issues.

---

## 📞 Support

### Getting Help

1. Check [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
2. Review [KNOWN_LIMITATIONS.md](./KNOWN_LIMITATIONS.md)  
3. Check backend logs: `tail -f logs/backend.log`
4. Run health check: `python tests/e2e/run_tests.py --check-health`
5. Run specific scenario with verbose output: `pytest tests/e2e/ -vv -s`

### Reporting Issues

When reporting test failures, include:
- Test scenario name
- Full error message
- Platform (Windows/Mac/Linux)
- Python version: `python --version`
- Backend URL being used
- Backend logs: `tail -100 logs/backend.log`
- Test results JSON: `cat tests/e2e/results/e2e_test_results_*.json`

---

**Status**: ✅ Ready for Testing and Demo  
**Last Updated**: December 2024  
**Version**: 1.0.0
