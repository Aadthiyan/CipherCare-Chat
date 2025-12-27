#!/usr/bin/env bash
# ============================================================================
# CipherCare Performance Test Execution Script (Unix/Linux/macOS)
# ============================================================================
# Executes all load testing and benchmarking scenarios
# Usage: ./run_performance_tests.sh [scenario] [duration] [users]

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
WARM_UP_DURATION=300  # 5 minutes
BENCHMARK_ITERATIONS=100
LOCUST_HEADLESS=true
LOCUST_USERS=5
LOCUST_SPAWN_RATE=1

# ============================================================================
# Helper Functions
# ============================================================================

print_header() {
    echo -e "${BLUE}========================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

check_backend() {
    echo -e "${BLUE}Checking backend availability...${NC}"
    if curl -s "${BACKEND_URL}/health" > /dev/null 2>&1; then
        print_success "Backend is running at ${BACKEND_URL}"
    else
        print_error "Backend is not responding at ${BACKEND_URL}"
        echo "Make sure the backend is running:"
        echo "  python backend/main.py"
        exit 1
    fi
}

create_directories() {
    mkdir -p benchmarks/results
    mkdir -p benchmarks/logs
    mkdir -p benchmarks/reports
}

# ============================================================================
# Warm-up Phase
# ============================================================================

warmup_system() {
    print_header "SYSTEM WARM-UP (5 minutes)"
    echo "Stabilizing system and initializing connections..."
    
    python benchmarks/component_benchmarks.py \
        --component api \
        --iterations 20
    
    print_success "Warm-up complete"
}

# ============================================================================
# Component Benchmarking
# ============================================================================

benchmark_components() {
    print_header "COMPONENT BENCHMARKING"
    
    echo "Benchmarking individual components..."
    python benchmarks/component_benchmarks.py \
        --component all \
        --iterations "${BENCHMARK_ITERATIONS}"
    
    print_success "Component benchmarking complete"
}

# ============================================================================
# Load Testing Scenarios
# ============================================================================

run_steady_state() {
    print_header "SCENARIO 1: STEADY STATE LOAD TEST"
    echo "Testing 5 concurrent clinicians for 10 minutes"
    
    locust \
        -f benchmarks/locustfile.py \
        --host="${BACKEND_URL}" \
        --users=5 \
        --spawn-rate=1 \
        --run-time=10m \
        --headless \
        --csv=benchmarks/results/steady_state \
        --loglevel=INFO
    
    print_success "Steady state test complete"
}

run_peak_load() {
    print_header "SCENARIO 2: PEAK LOAD TEST"
    echo "Testing 50 concurrent clinicians for 5 minutes"
    
    locust \
        -f benchmarks/locustfile.py \
        --host="${BACKEND_URL}" \
        --users=50 \
        --spawn-rate=10 \
        --run-time=5m \
        --headless \
        --csv=benchmarks/results/peak_load \
        --loglevel=INFO
    
    print_success "Peak load test complete"
}

run_stress_test() {
    print_header "SCENARIO 3: STRESS TEST"
    echo "Ramping up to 100 concurrent clinicians for 2 minutes"
    
    locust \
        -f benchmarks/locustfile.py \
        --host="${BACKEND_URL}" \
        --users=100 \
        --spawn-rate=20 \
        --run-time=7m \
        --headless \
        --csv=benchmarks/results/stress_test \
        --loglevel=INFO
    
    print_success "Stress test complete"
}

run_sustained_load() {
    print_header "SCENARIO 4: SUSTAINED LOAD TEST (1 HOUR)"
    echo "Testing 20 concurrent clinicians for 1 hour"
    
    locust \
        -f benchmarks/locustfile.py \
        --host="${BACKEND_URL}" \
        --users=20 \
        --spawn-rate=2 \
        --run-time=1h \
        --headless \
        --csv=benchmarks/results/sustained_load \
        --loglevel=INFO
    
    print_success "Sustained load test complete"
}

# ============================================================================
# Profiling
# ============================================================================

profile_components() {
    print_header "PERFORMANCE PROFILING"
    echo "Running profiling with py-spy..."
    
    # Profile for 60 seconds
    if command -v py-spy &> /dev/null; then
        py-spy record \
            -o benchmarks/logs/profile.svg \
            -- python benchmarks/component_benchmarks.py \
                --component all \
                --iterations 50
        print_success "Profiling complete: benchmarks/logs/profile.svg"
    else
        print_warning "py-spy not installed. Install with: pip install py-spy"
    fi
}

# ============================================================================
# Results Analysis
# ============================================================================

analyze_results() {
    print_header "GENERATING PERFORMANCE REPORT"
    
    python benchmarks/analyze_results.py \
        --results benchmarks/results \
        --output performance_report.html
    
    print_success "Report generated: benchmarks/reports/performance_report.html"
}

# ============================================================================
# Main Execution
# ============================================================================

main() {
    print_header "CipherCare Performance Testing"
    echo "Backend URL: ${BACKEND_URL}"
    echo "Start time: $(date)"
    
    # Validate inputs
    create_directories
    check_backend
    
    # Parse arguments
    SCENARIO="${1:-all}"
    DURATION="${2:-}"
    USERS="${3:-}"
    
    case "${SCENARIO}" in
        warmup)
            warmup_system
            ;;
        components)
            benchmark_components
            ;;
        steady)
            run_steady_state
            analyze_results
            ;;
        peak)
            run_peak_load
            analyze_results
            ;;
        stress)
            run_stress_test
            analyze_results
            ;;
        sustained)
            run_sustained_load
            analyze_results
            ;;
        profile)
            profile_components
            ;;
        all)
            warmup_system
            benchmark_components
            run_steady_state
            run_peak_load
            run_stress_test
            run_sustained_load
            profile_components
            analyze_results
            ;;
        *)
            echo "Usage: $0 [warmup|components|steady|peak|stress|sustained|profile|all]"
            echo ""
            echo "Scenarios:"
            echo "  warmup       - Warm up system (5 minutes)"
            echo "  components   - Benchmark individual components"
            echo "  steady       - Steady state load (5 users, 10 min)"
            echo "  peak         - Peak load test (50 users, 5 min)"
            echo "  stress       - Stress test (100 users, 2 min)"
            echo "  sustained    - Sustained load (20 users, 1 hour)"
            echo "  profile      - Profile components with py-spy"
            echo "  all          - Run all scenarios sequentially"
            echo ""
            echo "Environment Variables:"
            echo "  BACKEND_URL  - Backend URL (default: http://localhost:8000)"
            exit 1
            ;;
    esac
    
    print_header "TESTING COMPLETE"
    echo "End time: $(date)"
    echo ""
    print_success "All tests completed successfully!"
    echo ""
    echo "Results location:"
    echo "  CSV Results:  benchmarks/results/"
    echo "  Logs:         benchmarks/logs/"
    echo "  Report:       benchmarks/reports/performance_report.html"
}

# Run main
main "$@"
