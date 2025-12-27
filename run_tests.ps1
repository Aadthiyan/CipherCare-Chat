# run_tests.ps1 - Test execution script for CipherCare (Windows PowerShell)

param(
    [string]$TestType = "all"
)

# Helper functions
function Print-Header {
    param([string]$Message)
    Write-Host "`n========================================" -ForegroundColor Green
    Write-Host $Message -ForegroundColor Green
    Write-Host "========================================`n" -ForegroundColor Green
}

function Print-Status {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Yellow
}

function Print-Error {
    param([string]$Message)
    Write-Host "ERROR: $Message" -ForegroundColor Red
}

function Print-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

# Check dependencies
Print-Header "Checking Dependencies"

$pytest = Get-Command pytest -ErrorAction SilentlyContinue
if (-not $pytest) {
    Print-Error "pytest not found. Installing..."
    pip install pytest pytest-cov pytest-mock
}

Print-Success "pytest installed"

# Run tests based on type
switch ($TestType) {
    "unit" {
        Print-Header "Running Unit Tests"
        pytest tests/unit/ -v --tb=short
    }
    
    "integration" {
        Print-Header "Running Integration Tests"
        pytest tests/integration/ -v --tb=short
    }
    
    "coverage" {
        Print-Header "Running Tests with Coverage Report"
        pytest tests/ `
            --cov=backend `
            --cov=embeddings `
            --cov=encryption `
            --cov=data-pipeline `
            --cov-report=html `
            --cov-report=term-missing `
            --cov-fail-under=80 `
            -v
        Print-Success "Coverage report generated: htmlcov/index.html"
    }
    
    "phi" {
        Print-Header "Running PHI Masking Tests"
        pytest tests/unit/test_phi_masking.py -v -m phi
    }
    
    "embedding" {
        Print-Header "Running Embedding Tests"
        pytest tests/unit/test_embeddings.py -v -m embedding
    }
    
    "encryption" {
        Print-Header "Running Encryption Tests"
        pytest tests/unit/test_encryption.py -v -m encryption
    }
    
    "rbac" {
        Print-Header "Running RBAC Tests"
        pytest tests/unit/test_rbac.py -v -m rbac
    }
    
    "api" {
        Print-Header "Running API Validation Tests"
        pytest tests/unit/test_api_validation.py -v -m api
    }
    
    "fast" {
        Print-Header "Running Tests (excluding slow tests)"
        pytest tests/ -v -m "not slow" --tb=short
    }
    
    "all" {
        Print-Header "Running Full Test Suite"
        pytest tests/ -v --tb=short
        Print-Header "Running Coverage Report"
        pytest tests/ `
            --cov=backend `
            --cov=embeddings `
            --cov=encryption `
            --cov=data-pipeline `
            --cov-report=html `
            --cov-report=term-missing `
            --cov-fail-under=80
        Print-Success "All tests completed successfully!"
        Print-Success "Coverage report: htmlcov/index.html"
    }
    
    default {
        Print-Error "Unknown test type: $TestType"
        Write-Host "`nUsage: .\run_tests.ps1 -TestType <type>`n"
        Write-Host "Available test types:"
        Write-Host "  unit          - Run unit tests only"
        Write-Host "  integration   - Run integration tests only"
        Write-Host "  coverage      - Run tests with coverage report"
        Write-Host "  phi           - Run PHI masking tests"
        Write-Host "  embedding     - Run embedding tests"
        Write-Host "  encryption    - Run encryption tests"
        Write-Host "  rbac          - Run RBAC tests"
        Write-Host "  api           - Run API validation tests"
        Write-Host "  fast          - Run all tests except slow ones"
        Write-Host "  all           - Run all tests with coverage (default)"
        Write-Host ""
        exit 1
    }
}

exit $LASTEXITCODE
