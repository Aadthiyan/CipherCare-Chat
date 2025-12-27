# ============================================================================
# CipherCare Performance Test Execution Script (Windows PowerShell)
# ============================================================================
# Executes all load testing and benchmarking scenarios
# Usage: .\run_performance_tests.ps1 -Scenario all -Duration 3600 -Users 5

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet('warmup', 'components', 'steady', 'peak', 'stress', 'sustained', 'profile', 'all')]
    [string]$Scenario = 'all',
    
    [Parameter(Mandatory=$false)]
    [int]$Duration = 0,
    
    [Parameter(Mandatory=$false)]
    [int]$Users = 5,
    
    [Parameter(Mandatory=$false)]
    [string]$BackendUrl = 'http://localhost:8000'
)

$ErrorActionPreference = 'Stop'

# Configuration
$WARM_UP_DURATION = 300  # 5 minutes
$BENCHMARK_ITERATIONS = 100
$LOCUST_HEADLESS = $true
$LOCUST_SPAWN_RATE = 1

# ============================================================================
# Helper Functions
# ============================================================================

function Print-Header {
    param([string]$Message)
    Write-Host "========================================================================" -ForegroundColor Blue
    Write-Host $Message -ForegroundColor Blue
    Write-Host "========================================================================" -ForegroundColor Blue
}

function Print-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Print-Error {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

function Print-Warning {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor Yellow
}

function Check-Backend {
    Write-Host "Checking backend availability..." -ForegroundColor Blue
    try {
        $response = Invoke-WebRequest -Uri "$BackendUrl/health" -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            Print-Success "Backend is running at $BackendUrl"
            return $true
        }
    } catch {
        Print-Error "Backend is not responding at $BackendUrl"
        Write-Host "Make sure the backend is running:"
        Write-Host "  python backend/main.py"
        exit 1
    }
}

function Create-Directories {
    $dirs = @(
        'benchmarks/results',
        'benchmarks/logs',
        'benchmarks/reports'
    )
    
    foreach ($dir in $dirs) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
        }
    }
}

# ============================================================================
# Warm-up Phase
# ============================================================================

function Warmup-System {
    Print-Header "SYSTEM WARM-UP (5 minutes)"
    Write-Host "Stabilizing system and initializing connections..."
    
    & python benchmarks/component_benchmarks.py `
        --component api `
        --iterations 20
    
    Print-Success "Warm-up complete"
}

# ============================================================================
# Component Benchmarking
# ============================================================================

function Benchmark-Components {
    Print-Header "COMPONENT BENCHMARKING"
    
    Write-Host "Benchmarking individual components..."
    & python benchmarks/component_benchmarks.py `
        --component all `
        --iterations $BENCHMARK_ITERATIONS
    
    Print-Success "Component benchmarking complete"
}

# ============================================================================
# Load Testing Scenarios
# ============================================================================

function Run-SteadyState {
    Print-Header "SCENARIO 1: STEADY STATE LOAD TEST"
    Write-Host "Testing 5 concurrent clinicians for 10 minutes"
    
    & locust `
        -f benchmarks/locustfile.py `
        --host=$BackendUrl `
        --users=5 `
        --spawn-rate=1 `
        --run-time=10m `
        --headless `
        --csv=benchmarks/results/steady_state `
        --loglevel=INFO
    
    Print-Success "Steady state test complete"
}

function Run-PeakLoad {
    Print-Header "SCENARIO 2: PEAK LOAD TEST"
    Write-Host "Testing 50 concurrent clinicians for 5 minutes"
    
    & locust `
        -f benchmarks/locustfile.py `
        --host=$BackendUrl `
        --users=50 `
        --spawn-rate=10 `
        --run-time=5m `
        --headless `
        --csv=benchmarks/results/peak_load `
        --loglevel=INFO
    
    Print-Success "Peak load test complete"
}

function Run-StressTest {
    Print-Header "SCENARIO 3: STRESS TEST"
    Write-Host "Ramping up to 100 concurrent clinicians for 2 minutes"
    
    & locust `
        -f benchmarks/locustfile.py `
        --host=$BackendUrl `
        --users=100 `
        --spawn-rate=20 `
        --run-time=7m `
        --headless `
        --csv=benchmarks/results/stress_test `
        --loglevel=INFO
    
    Print-Success "Stress test complete"
}

function Run-SustainedLoad {
    Print-Header "SCENARIO 4: SUSTAINED LOAD TEST (1 HOUR)"
    Write-Host "Testing 20 concurrent clinicians for 1 hour"
    
    & locust `
        -f benchmarks/locustfile.py `
        --host=$BackendUrl `
        --users=20 `
        --spawn-rate=2 `
        --run-time=1h `
        --headless `
        --csv=benchmarks/results/sustained_load `
        --loglevel=INFO
    
    Print-Success "Sustained load test complete"
}

# ============================================================================
# Profiling
# ============================================================================

function Profile-Components {
    Print-Header "PERFORMANCE PROFILING"
    Write-Host "Running profiling with py-spy..."
    
    # Check if py-spy is installed
    try {
        $pySpyTest = & py-spy --version 2>&1
        Write-Host "Using py-spy: $pySpyTest"
        
        & py-spy record `
            -o benchmarks/logs/profile.svg `
            -- python benchmarks/component_benchmarks.py `
                --component all `
                --iterations 50
        
        Print-Success "Profiling complete: benchmarks/logs/profile.svg"
    } catch {
        Print-Warning "py-spy not installed. Install with: pip install py-spy"
    }
}

# ============================================================================
# Results Analysis
# ============================================================================

function Analyze-Results {
    Print-Header "GENERATING PERFORMANCE REPORT"
    
    & python benchmarks/analyze_results.py `
        --results benchmarks/results `
        --output performance_report.html
    
    Print-Success "Report generated: benchmarks/reports/performance_report.html"
}

# ============================================================================
# Main Execution
# ============================================================================

function Main {
    Print-Header "CipherCare Performance Testing"
    Write-Host "Backend URL: $BackendUrl"
    Write-Host "Scenario: $Scenario"
    Write-Host "Start time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    
    # Validate inputs
    Create-Directories
    Check-Backend
    
    switch ($Scenario) {
        'warmup' {
            Warmup-System
        }
        'components' {
            Benchmark-Components
        }
        'steady' {
            Run-SteadyState
            Analyze-Results
        }
        'peak' {
            Run-PeakLoad
            Analyze-Results
        }
        'stress' {
            Run-StressTest
            Analyze-Results
        }
        'sustained' {
            Run-SustainedLoad
            Analyze-Results
        }
        'profile' {
            Profile-Components
        }
        'all' {
            Warmup-System
            Benchmark-Components
            Run-SteadyState
            Run-PeakLoad
            Run-StressTest
            Run-SustainedLoad
            Profile-Components
            Analyze-Results
        }
        default {
            Write-Host "Usage: .\run_performance_tests.ps1 -Scenario [scenario] -BackendUrl [url]"
            Write-Host ""
            Write-Host "Scenarios:"
            Write-Host "  warmup       - Warm up system (5 minutes)"
            Write-Host "  components   - Benchmark individual components"
            Write-Host "  steady       - Steady state load (5 users, 10 min)"
            Write-Host "  peak         - Peak load test (50 users, 5 min)"
            Write-Host "  stress       - Stress test (100 users, 2 min)"
            Write-Host "  sustained    - Sustained load (20 users, 1 hour)"
            Write-Host "  profile      - Profile components with py-spy"
            Write-Host "  all          - Run all scenarios sequentially (Default)"
            Write-Host ""
            Write-Host "Examples:"
            Write-Host "  .\run_performance_tests.ps1"
            Write-Host "  .\run_performance_tests.ps1 -Scenario steady"
            Write-Host "  .\run_performance_tests.ps1 -Scenario all -BackendUrl http://localhost:8000"
            exit 1
        }
    }
    
    Print-Header "TESTING COMPLETE"
    Write-Host "End time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    Write-Host ""
    Print-Success "All tests completed successfully!"
    Write-Host ""
    Write-Host "Results location:"
    Write-Host "  CSV Results:  benchmarks/results/"
    Write-Host "  Logs:         benchmarks/logs/"
    Write-Host "  Report:       benchmarks/reports/performance_report.html"
}

# Run main
Main
