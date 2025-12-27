#!/bin/bash
# run_tests.sh - Test execution script for CipherCare

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${GREEN}========================================${NC}\n"
}

print_status() {
    echo -e "${YELLOW}$1${NC}"
}

print_error() {
    echo -e "${RED}ERROR: $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Check dependencies
print_header "Checking Dependencies"

if ! command -v pytest &> /dev/null; then
    print_error "pytest not found. Installing..."
    pip install pytest pytest-cov pytest-mock
fi

print_success "pytest installed"

# Default test type
TEST_TYPE="${1:-all}"

case $TEST_TYPE in
    unit)
        print_header "Running Unit Tests"
        pytest tests/unit/ -v --tb=short
        ;;
    
    integration)
        print_header "Running Integration Tests"
        pytest tests/integration/ -v --tb=short
        ;;
    
    coverage)
        print_header "Running Tests with Coverage Report"
        pytest tests/ \
            --cov=backend \
            --cov=embeddings \
            --cov=encryption \
            --cov=data-pipeline \
            --cov-report=html \
            --cov-report=term-missing \
            --cov-fail-under=80 \
            -v
        print_success "Coverage report generated: htmlcov/index.html"
        ;;
    
    phi)
        print_header "Running PHI Masking Tests"
        pytest tests/unit/test_phi_masking.py -v -m phi
        ;;
    
    embedding)
        print_header "Running Embedding Tests"
        pytest tests/unit/test_embeddings.py -v -m embedding
        ;;
    
    encryption)
        print_header "Running Encryption Tests"
        pytest tests/unit/test_encryption.py -v -m encryption
        ;;
    
    rbac)
        print_header "Running RBAC Tests"
        pytest tests/unit/test_rbac.py -v -m rbac
        ;;
    
    api)
        print_header "Running API Validation Tests"
        pytest tests/unit/test_api_validation.py -v -m api
        ;;
    
    fast)
        print_header "Running Tests (excluding slow tests)"
        pytest tests/ -v -m "not slow" --tb=short
        ;;
    
    all)
        print_header "Running Full Test Suite"
        pytest tests/ -v --tb=short
        print_header "Running Coverage Report"
        pytest tests/ \
            --cov=backend \
            --cov=embeddings \
            --cov=encryption \
            --cov=data-pipeline \
            --cov-report=html \
            --cov-report=term-missing \
            --cov-fail-under=80
        print_success "All tests completed successfully!"
        print_success "Coverage report: htmlcov/index.html"
        ;;
    
    *)
        print_error "Unknown test type: $TEST_TYPE"
        echo -e "\n${YELLOW}Usage: ./run_tests.sh [test_type]${NC}\n"
        echo "Available test types:"
        echo "  unit          - Run unit tests only"
        echo "  integration   - Run integration tests only"
        echo "  coverage      - Run tests with coverage report"
        echo "  phi           - Run PHI masking tests"
        echo "  embedding     - Run embedding tests"
        echo "  encryption    - Run encryption tests"
        echo "  rbac          - Run RBAC tests"
        echo "  api           - Run API validation tests"
        echo "  fast          - Run all tests except slow ones"
        echo "  all           - Run all tests with coverage (default)"
        echo ""
        exit 1
        ;;
esac

exit 0
