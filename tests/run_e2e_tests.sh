#!/bin/bash
#
# CipherCare E2E Testing Script for Unix/Linux
# Comprehensive end-to-end testing and validation
#

set -e

# Configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
TEST_DIR="$SCRIPT_DIR"
RESULTS_DIR="$TEST_DIR/results"
LOG_FILE="$RESULTS_DIR/e2e_execution.log"
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"

# Test mode
TEST_MODE="${1:-all}"
VERBOSE="${VERBOSE:-0}"
SCREENSHOTS="${SCREENSHOTS:-0}"
HEADLESS="${HEADLESS:-0}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo ""
    echo -e "${MAGENTA}========================================================================${NC}"
    echo -e "${MAGENTA}  $1${NC}"
    echo -e "${MAGENTA}========================================================================${NC}"
    echo ""
}

print_section() {
    echo ""
    echo -e "${CYAN}>>> $1${NC}"
    echo -e "${CYAN}------------------------------------------------------------${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

check_backend() {
    print_section "Checking Backend Health"
    
    if curl -s "$BACKEND_URL/health" > /dev/null 2>&1; then
        print_success "Backend is healthy"
        return 0
    else
        print_error "Cannot connect to backend at $BACKEND_URL"
        print_warning "Make sure to run: python backend/main.py"
        return 1
    fi
}

create_directories() {
    mkdir -p "$RESULTS_DIR"
    print_success "Results directory: $RESULTS_DIR"
}

run_python_test() {
    local description="$1"
    local scenario_number="$2"
    
    print_section "Running $description"
    
    local python_args=(
        "run_e2e_tests.py"
        "--backend-url" "$BACKEND_URL"
        "--scenario" "$scenario_number"
    )
    
    if [ "$VERBOSE" = "1" ]; then
        python_args+=("--verbose")
    fi
    
    if [ "$SCREENSHOTS" = "1" ]; then
        python_args+=("--screenshots")
    fi
    
    if [ "$HEADLESS" = "1" ]; then
        python_args+=("--headless")
    fi
    
    if python "${python_args[@]}" 2>&1; then
        print_success "$description PASSED"
        return 0
    else
        print_error "$description FAILED"
        return 1
    fi
}

run_all_scenarios() {
    print_header "CipherCare E2E Testing Suite - All Scenarios"
    
    local passed=0
    local failed=0
    
    declare -A results
    
    # Run all scenarios
    if run_python_test "Scenario 1: Happy Path" "1"; then
        results["scenario1"]=1
        ((passed++))
    else
        results["scenario1"]=0
        ((failed++))
    fi
    
    if run_python_test "Scenario 2: Access Control" "2"; then
        results["scenario2"]=1
        ((passed++))
    else
        results["scenario2"]=0
        ((failed++))
    fi
    
    if run_python_test "Scenario 3: Data Security" "3"; then
        results["scenario3"]=1
        ((passed++))
    else
        results["scenario3"]=0
        ((failed++))
    fi
    
    if run_python_test "Scenario 4: Compliance" "4"; then
        results["scenario4"]=1
        ((passed++))
    else
        results["scenario4"]=0
        ((failed++))
    fi
    
    if run_python_test "Scenario 5: Error Handling" "5"; then
        results["scenario5"]=1
        ((passed++))
    else
        results["scenario5"]=0
        ((failed++))
    fi
    
    if run_python_test "Scenario 6: Safety Guardrails" "6"; then
        results["scenario6"]=1
        ((passed++))
    else
        results["scenario6"]=0
        ((failed++))
    fi
    
    # Print summary
    print_section "Test Results Summary"
    
    echo ""
    echo "Scenario Results:"
    echo "------------------------------------------------------------"
    
    for scenario in "${!results[@]}"; do
        local status="PASS"
        local color="$GREEN"
        if [ "${results[$scenario]}" -eq 0 ]; then
            status="FAIL"
            color="$RED"
        fi
        echo -e "${color}${scenario}: ${status}${NC}"
    done
    
    echo ""
    echo "============================================================"
    echo "Total Scenarios: 6"
    echo -e "${GREEN}Passed: $passed${NC}"
    echo -e "${RED}Failed: $failed${NC}"
    
    if [ $failed -eq 0 ]; then
        echo -e "${GREEN}Overall Status: PASS${NC}"
        return 0
    else
        echo -e "${RED}Overall Status: FAIL${NC}"
        return 1
    fi
}

run_quick_tests() {
    print_header "CipherCare E2E Testing Suite - Quick Tests"
    
    local passed=0
    local failed=0
    
    if run_python_test "Scenario 1: Happy Path" "1"; then
        ((passed++))
    else
        ((failed++))
    fi
    
    if run_python_test "Scenario 4: Compliance" "4"; then
        ((passed++))
    else
        ((failed++))
    fi
    
    print_section "Test Results Summary"
    
    echo ""
    echo "============================================================"
    echo "Total Scenarios: 2"
    echo -e "${GREEN}Passed: $passed${NC}"
    echo -e "${RED}Failed: $failed${NC}"
    
    if [ $failed -eq 0 ]; then
        echo -e "${GREEN}Overall Status: PASS${NC}"
        return 0
    else
        echo -e "${RED}Overall Status: FAIL${NC}"
        return 1
    fi
}

generate_report() {
    print_section "Generating Test Report"
    
    if python run_e2e_tests.py --backend-url "$BACKEND_URL" 2>&1; then
        print_success "Report generated successfully"
        return 0
    else
        print_error "Error generating report"
        return 1
    fi
}

show_usage() {
    echo "Usage: $0 [test_mode] [options]"
    echo ""
    echo "Test Modes:"
    echo "  all              Run all 6 scenarios (default)"
    echo "  quick            Run critical scenarios (1, 4)"
    echo "  full             Run all scenarios with full reporting"
    echo "  scenario1        Run Scenario 1: Happy Path"
    echo "  scenario2        Run Scenario 2: Access Control"
    echo "  scenario3        Run Scenario 3: Data Security"
    echo "  scenario4        Run Scenario 4: Compliance"
    echo "  scenario5        Run Scenario 5: Error Handling"
    echo "  scenario6        Run Scenario 6: Safety Guardrails"
    echo ""
    echo "Options:"
    echo "  --verbose        Verbose output"
    echo "  --screenshots    Capture screenshots"
    echo "  --headless       Run browser tests in headless mode"
    echo ""
    echo "Environment Variables:"
    echo "  BACKEND_URL      Backend service URL (default: http://localhost:8000)"
    echo "  VERBOSE          Set to 1 for verbose output"
    echo "  SCREENSHOTS      Set to 1 to capture screenshots"
    echo "  HEADLESS         Set to 1 for headless mode"
}

# Main
main() {
    print_header "CipherCare E2E Testing Suite"
    
    echo "Test Mode: $TEST_MODE"
    echo "Backend URL: $BACKEND_URL"
    echo "Timestamp: $(date)"
    echo ""
    
    # Setup
    create_directories
    
    # Check backend
    if ! check_backend; then
        exit 1
    fi
    
    # Run tests based on mode
    local success=true
    
    case "$TEST_MODE" in
        help|-h|--help)
            show_usage
            exit 0
            ;;
        scenario1)
            run_python_test "Scenario 1: Happy Path" "1"
            success=$?
            ;;
        scenario2)
            run_python_test "Scenario 2: Access Control" "2"
            success=$?
            ;;
        scenario3)
            run_python_test "Scenario 3: Data Security" "3"
            success=$?
            ;;
        scenario4)
            run_python_test "Scenario 4: Compliance" "4"
            success=$?
            ;;
        scenario5)
            run_python_test "Scenario 5: Error Handling" "5"
            success=$?
            ;;
        scenario6)
            run_python_test "Scenario 6: Safety Guardrails" "6"
            success=$?
            ;;
        quick)
            run_quick_tests
            success=$?
            ;;
        full|all)
            run_all_scenarios
            success=$?
            ;;
        *)
            print_error "Unknown test mode: $TEST_MODE"
            show_usage
            exit 1
            ;;
    esac
    
    print_section "Test Execution Complete"
    
    if [ $success -eq 0 ]; then
        print_success "All tests passed!"
        exit 0
    else
        print_error "Some tests failed!"
        exit 1
    fi
}

# Make script executable
chmod +x "$0"

# Run main
main "$@"
