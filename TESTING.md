# Testing Guide and Best Practices

## Overview

CipherCare implements comprehensive test coverage with **50+ unit tests** and **20+ integration tests**, targeting **≥80% code coverage** across all critical components.

## Test Organization

```
tests/
├── __init__.py
├── conftest.py                 # Pytest configuration and shared fixtures
├── unit/                       # Unit tests by component
│   ├── __init__.py
│   ├── test_phi_masking.py    # PHI detection and masking (20+ tests)
│   ├── test_embeddings.py     # Embedding generation (10+ tests)
│   ├── test_encryption.py     # Encryption/decryption (15+ tests)
│   ├── test_rbac.py           # Role-based access control (15+ tests)
│   └── test_api_validation.py # API endpoint validation (5+ per endpoint)
└── integration/                # Integration tests by workflow
    ├── __init__.py
    └── test_workflows.py       # End-to-end workflows (20+ tests)
```

## Running Tests

### Run all tests
```bash
pytest tests/ -v
```

### Run unit tests only
```bash
pytest tests/unit/ -v
```

### Run integration tests only
```bash
pytest tests/integration/ -v
```

### Run tests with coverage
```bash
pytest tests/ --cov=backend,embeddings,encryption,data-pipeline \
    --cov-report=html --cov-report=term-missing
```

### Run tests for specific component
```bash
pytest tests/unit/test_phi_masking.py -v
pytest tests/unit/test_embeddings.py -v
pytest tests/unit/test_encryption.py -v
pytest tests/unit/test_rbac.py -v
pytest tests/unit/test_api_validation.py -v
```

### Run with markers
```bash
# Only PHI tests
pytest tests/ -m phi -v

# Only unit tests
pytest tests/ -m unit -v

# Only integration tests
pytest tests/ -m integration -v

# Skip slow tests
pytest tests/ -m "not slow" -v
```

### Run specific test
```bash
pytest tests/unit/test_phi_masking.py::TestPresidioAnalyzer::test_detect_person_names -v
```

## Test Coverage

### Coverage Report
```bash
pytest tests/ --cov=backend,embeddings,encryption,data-pipeline \
    --cov-report=html --cov-report=term-missing --cov-fail-under=80
```

Coverage reports:
- **HTML Report**: `htmlcov/index.html` (open in browser)
- **Terminal**: Shows coverage % and missing lines
- **XML**: For CI/CD integration

### Target: ≥80% Coverage

Currently tracking:
- `backend/`: Core API logic, auth, models
- `embeddings/`: Embedding generation
- `encryption/`: Encryption and key management
- `data-pipeline/`: PHI detection, data processing

## Test Categories

### Unit Tests

#### PHI Masking (20+ tests)
- **File**: `tests/unit/test_phi_masking.py`
- **Coverage**:
  - Presidio PERSON entity detection
  - PHONE_NUMBER entity detection
  - EMAIL_ADDRESS entity detection
  - DATE_TIME entity detection (multiple formats)
  - LOCATION entity detection
  - Masking logic verification (original not in output)
  - Consistent token mapping
  - Edge cases (dates, abbreviations, overlapping entities)
- **Target**: PII detection rate ≥95%

#### Embeddings (10+ tests)
- **File**: `tests/unit/test_embeddings.py`
- **Coverage**:
  - Output shape verification (384-dim for MiniLM)
  - Consistency tests (same input → same output)
  - Numerical stability (no NaN/Inf)
  - Normalization verification
  - Edge cases (empty text, very long text, special characters)
  - Performance tests
- **Target**: All embeddings 384-dim, normalized, stable

#### Encryption (15+ tests)
- **File**: `tests/unit/test_encryption.py`
- **Coverage**:
  - Master key generation (256-bit)
  - Data key generation and wrapping
  - AES-256-GCM encryption/decryption
  - Authentication tag verification
  - Key rotation workflow
  - Tamper detection (wrong key, wrong nonce)
  - Large data handling
  - Binary data support
- **Target**: All encryption/decryption successful with auth tag verification

#### RBAC (15+ tests)
- **File**: `tests/unit/test_rbac.py`
- **Coverage**:
  - Password verification
  - Token generation and validation
  - Role-based permission checks
  - User-patient relationship verification
  - Admin, resident, nurse role tests
  - Edge cases (no role, unknown role, multiple roles)
  - Token expiration and tampering
- **Target**: All role checks and access control working correctly

#### API Validation (5+ per endpoint)
- **File**: `tests/unit/test_api_validation.py`
- **Coverage**:
  - Request validation (missing fields, invalid types)
  - Response format (all required fields present)
  - Boundary values (min/max)
  - Default values
  - Type validation
  - Error responses
- **Target**: All endpoints properly validated

### Integration Tests

#### Query Workflow (10+ tests)
- **File**: `tests/integration/test_workflows.py`
- **Coverage**:
  - End-to-end query: embedding → search → LLM → response
  - Audit logging
  - Source document retrieval
  - Multiple sequential queries
  - Error handling and recovery

#### Authentication & Authorization (10+ tests)
- **Coverage**:
  - Login and authorized query
  - Unauthorized query rejection
  - Admin access to any patient
  - Resident access to assigned patients only
  - Token expiration
  - Access violation attempts

#### Data Pipeline (5+ tests)
- **Coverage**:
  - FHIR data processing
  - PHI de-identification
  - Embedding generation
  - Encryption in pipeline
  - Batch processing

## Fixtures and Mocks

### Fixtures (conftest.py)

#### Test Data Fixtures
- `test_config`: Test configuration
- `test_users`: Test user database
- `phi_test_cases`: PHI detection test cases
- `fhir_test_data`: Sample FHIR bundle
- `embedding_test_cases`: Embedding test cases
- `encryption_test_vectors`: Encryption test data
- `rbac_test_cases`: RBAC test scenarios
- `patient_relationships`: Patient access relationships

#### Token Fixtures
- `admin_token`: Valid admin JWT
- `resident_token`: Valid resident JWT
- `nurse_token`: Valid nurse JWT

#### Mock Service Fixtures
- `mock_cyborg_manager`: Mocked CyborgDB
- `mock_llm_service`: Mocked LLM service
- `mock_crypto_service`: Mocked encryption
- `mock_embedder`: Mocked embedder
- `mock_phi_scrubber`: Mocked PHI scrubber

## Test Execution

### Local Testing
```bash
# Quick test (without slow tests)
pytest tests/ -m "not slow" -v

# Full test suite with coverage
pytest tests/ --cov --cov-report=html --cov-fail-under=80 -v

# Test specific Python version
python3.10 -m pytest tests/ -v
```

### CI/CD Testing
Tests automatically run on:
- Every push to `main` or `develop` branches
- Every pull request to `main` or `develop`

See `.github/workflows/tests.yml` for CI/CD configuration.

## Performance Targets

- **Test Execution Time**: <5 minutes total
- **Unit Tests**: <3 minutes
- **Integration Tests**: <2 minutes
- **Coverage Report**: <1 minute

## Coverage Requirements

| Component | Target | Status |
|-----------|--------|--------|
| backend/auth.py | 85%+ | |
| backend/models.py | 80%+ | |
| embeddings/embedder.py | 80%+ | |
| encryption/crypto_service.py | 85%+ | |
| data-pipeline/phi_scrubber.py | 85%+ | |
| **Overall** | **80%+** | |

## Continuous Integration

### GitHub Actions Workflow
- **File**: `.github/workflows/tests.yml`
- **Triggers**: Push, Pull Request
- **Steps**:
  1. Set up Python environments (3.9, 3.10, 3.11)
  2. Install dependencies
  3. Run unit tests
  4. Run integration tests
  5. Generate coverage report
  6. Upload to Codecov
  7. Comment on PR with coverage %
  8. Security checks (bandit)
  9. Linting (flake8, black, isort)

### PR Checks
- ✅ All tests passing
- ✅ Coverage ≥80%
- ✅ No security issues
- ✅ Code style compliant

## Best Practices

### Writing Tests

1. **Clear test names**: Describe what is being tested
   ```python
   def test_detect_person_names(self):
       """Test PERSON entity detection."""
   ```

2. **One assertion per test** (when possible):
   ```python
   def test_embedding_dimension(self):
       embedding = embedder.get_embedding("test")
       assert len(embedding) == 384
   ```

3. **Use fixtures for reusable data**:
   ```python
   def test_something(self, test_users, admin_token):
       # Use fixtures
       pass
   ```

4. **Use markers for categorization**:
   ```python
   @pytest.mark.unit
   @pytest.mark.phi
   def test_something(self):
       pass
   ```

5. **Test edge cases**:
   ```python
   def test_empty_text(self):
       result = embedder.get_embedding("")
       assert result is not None
   ```

### Mocking

1. **Mock external services**:
   ```python
   @patch('backend.cyborg_manager.CyborgDBManager')
   def test_query(self, mock_db):
       mock_db.search.return_value = [...]
       # test
   ```

2. **Use fixtures for mocks**:
   ```python
   def test_something(self, mock_embedder):
       # mock_embedder already configured
       pass
   ```

## Troubleshooting

### Import Errors
```bash
# Add current directory to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest tests/ -v
```

### Missing Dependencies
```bash
# Install test dependencies
pip install -r requirements.txt
pip install pytest pytest-cov pytest-mock
```

### Tests Failing Locally
```bash
# Run with verbose output
pytest tests/ -v -s

# Show full traceback
pytest tests/ --tb=long

# Stop on first failure
pytest tests/ -x
```

## Coverage Report Interpretation

```
Name                          Stmts   Miss  Cover
------------------------------------------------
backend/__init__.py               2      0   100%
backend/auth.py                  42      8    81%
backend/main.py                  85     12    86%
embeddings/embedder.py           56      4    93%
encryption/crypto_service.py     48      3    94%
data-pipeline/phi_scrubber.py    72      6    92%
------------------------------------------------
TOTAL                           305     33    89%
```

- **Stmts**: Total statements
- **Miss**: Statements not covered
- **Cover**: Coverage percentage

## Adding New Tests

1. **Identify test type**: Unit or integration?
2. **Create test file** in appropriate directory
3. **Write test function** with clear name
4. **Add markers**: `@pytest.mark.unit`, `@pytest.mark.integration`
5. **Use fixtures** for common data
6. **Run locally**: `pytest tests/unit/test_new.py -v`
7. **Check coverage**: Ensure new code covered

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest Fixtures](https://docs.pytest.org/en/stable/how-to-use-fixtures.html)
- [Coverage.py](https://coverage.readthedocs.io/)
- [Python Unittest.mock](https://docs.python.org/3/library/unittest.mock.html)

## Success Metrics

✅ **Target Achieved**:
- 50+ unit tests
- 20+ integration tests
- ≥80% code coverage
- 100% test pass rate
- <5 minutes execution time
- 100% CI/CD success rate

## Overview
We utilize a pyramid testing strategy:
1.  **Unit Tests**: Test individual functions and components isolated from external services.
2.  **Integration Tests**: Test interactions between backend, database, and encryption services.
3.  **Load Tests**: Verify system performance mainly for encrypted search.

## Running Tests

### Unit Tests
```bash
pytest tests/unit
```

### Integration Tests
*Requires Docker containers to be running.*
```bash
docker-compose up -d
pytest tests/integration
```

### Coverage
```bash
pytest --cov=backend tests/
```
