# CipherCare E2E Testing Script for Windows PowerShell
# Comprehensive end-to-end testing and validation

param(
    [ValidateSet('all', 'scenario1', 'scenario2', 'scenario3', 'scenario4', 'scenario5', 'scenario6', 'quick', 'full')]
    [string]$TestMode = 'all',
    
    [string]$BackendUrl = 'http://localhost:8000',
    
    [switch]$Verbose,
    [switch]$Screenshots,
    [switch]$Headless,
    [switch]$NoCleanup,
    [switch]$GenerateReport
)

# Configuration
$ErrorActionPreference = 'Stop'
$TestDir = Join-Path $PSScriptRoot '.'
$ResultsDir = Join-Path $TestDir 'results'
$LogFile = Join-Path $ResultsDir 'e2e_execution.log'

# Colors for output
$Colors = @{
    'Success' = 'Green'
    'Error' = 'Red'
    'Warning' = 'Yellow'
    'Info' = 'Cyan'
    'Header' = 'Magenta'
}

function Print-Header {
    param([string]$Text)
    Write-Host ""
    Write-Host "=" * 70 -ForegroundColor $Colors['Header']
    Write-Host "  $Text" -ForegroundColor $Colors['Header']
    Write-Host "=" * 70 -ForegroundColor $Colors['Header']
    Write-Host ""
}

function Print-Section {
    param([string]$Text)
    Write-Host "`n>>> $Text" -ForegroundColor $Colors['Info']
    Write-Host ("-" * 60) -ForegroundColor $Colors['Info']
}

function Print-Success {
    param([string]$Text)
    Write-Host "✓ $Text" -ForegroundColor $Colors['Success']
}

function Print-Error {
    param([string]$Text)
    Write-Host "✗ $Text" -ForegroundColor $Colors['Error']
}

function Print-Warning {
    param([string]$Text)
    Write-Host "⚠ $Text" -ForegroundColor $Colors['Warning']
}

function Check-Backend {
    Print-Section "Checking Backend Health"
    
    try {
        $response = Invoke-RestMethod -Uri "$BackendUrl/health" -Method Get -TimeoutSec 5 -ErrorAction Stop
        Print-Success "Backend is healthy"
        return $true
    }
    catch {
        Print-Error "Cannot connect to backend at $BackendUrl"
        Print-Warning "Make sure to run: python backend/main.py"
        return $false
    }
}

function Create-Directories {
    if (-not (Test-Path $ResultsDir)) {
        New-Item -ItemType Directory -Path $ResultsDir -Force | Out-Null
        Print-Success "Created results directory: $ResultsDir"
    }
}

function Run-PythonTest {
    param(
        [string]$Description,
        [string]$ScenarioNumber,
        [string[]]$SkipScenarios
    )
    
    Print-Section "Running $Description"
    
    $skipArgs = @()
    if ($SkipScenarios) {
        $skipArgs = @('--skip') + $SkipScenarios
    }
    
    $pythonArgs = @(
        'run_e2e_tests.py',
        '--backend-url', $BackendUrl,
        '--scenario', $ScenarioNumber
    )
    
    if ($Verbose) { $pythonArgs += '--verbose' }
    if ($Screenshots) { $pythonArgs += '--screenshots' }
    if ($Headless) { $pythonArgs += '--headless' }
    
    try {
        $output = & python @pythonArgs 2>&1
        Write-Host $output
        
        if ($LASTEXITCODE -eq 0) {
            Print-Success "$Description PASSED"
            return $true
        }
        else {
            Print-Error "$Description FAILED"
            return $false
        }
    }
    catch {
        Print-Error "Error running $Description : $_"
        return $false
    }
}

function Run-AllScenarios {
    Print-Header "CipherCare E2E Testing Suite - All Scenarios"
    
    $results = @{
        Scenario1 = $null
        Scenario2 = $null
        Scenario3 = $null
        Scenario4 = $null
        Scenario5 = $null
        Scenario6 = $null
    }
    
    # Run all scenarios
    $results['Scenario1'] = Run-PythonTest "Scenario 1: Happy Path" "1"
    $results['Scenario2'] = Run-PythonTest "Scenario 2: Access Control" "2"
    $results['Scenario3'] = Run-PythonTest "Scenario 3: Data Security" "3"
    $results['Scenario4'] = Run-PythonTest "Scenario 4: Compliance" "4"
    $results['Scenario5'] = Run-PythonTest "Scenario 5: Error Handling" "5"
    $results['Scenario6'] = Run-PythonTest "Scenario 6: Safety Guardrails" "6"
    
    return $results
}

function Run-QuickTests {
    Print-Header "CipherCare E2E Testing Suite - Quick Tests"
    
    $results = @{
        Scenario1 = $null
        Scenario4 = $null
    }
    
    # Run critical scenarios only
    $results['Scenario1'] = Run-PythonTest "Scenario 1: Happy Path" "1"
    $results['Scenario4'] = Run-PythonTest "Scenario 4: Compliance" "4"
    
    return $results
}

function Print-Summary {
    param([hashtable]$Results)
    
    Print-Section "Test Results Summary"
    
    $passed = ($Results.Values | Where-Object { $_ -eq $true }).Count
    $failed = ($Results.Values | Where-Object { $_ -eq $false }).Count
    $total = $Results.Count
    
    Write-Host ""
    Write-Host "Scenario Results:"
    Write-Host "-" * 50
    
    foreach ($scenario in $Results.Keys) {
        $status = if ($Results[$scenario]) { "PASS" } else { "FAIL" }
        $color = if ($Results[$scenario]) { $Colors['Success'] } else { $Colors['Error'] }
        Write-Host "$scenario : $status" -ForegroundColor $color
    }
    
    Write-Host "`n" + ("=" * 60)
    Write-Host "Total Scenarios: $total"
    Write-Host "Passed: $passed" -ForegroundColor $Colors['Success']
    Write-Host "Failed: $failed" -ForegroundColor $(if ($failed -gt 0) { $Colors['Error'] } else { $Colors['Success'] })
    
    if ($failed -eq 0) {
        Write-Host "Overall Status: PASS" -ForegroundColor $Colors['Success']
        return $true
    }
    else {
        Write-Host "Overall Status: FAIL" -ForegroundColor $Colors['Error']
        return $false
    }
}

function Generate-Report {
    Print-Section "Generating Test Report"
    
    try {
        $pythonArgs = @('run_e2e_tests.py', '--backend-url', $BackendUrl)
        & python @pythonArgs
        Print-Success "Report generated successfully"
    }
    catch {
        Print-Error "Error generating report: $_"
    }
}

# Main execution
function Main {
    Print-Header "CipherCare E2E Testing Suite"
    
    Write-Host "Test Mode: $TestMode"
    Write-Host "Backend URL: $BackendUrl"
    Write-Host "Timestamp: $(Get-Date)"
    Write-Host ""
    
    # Setup
    Create-Directories
    
    # Check backend
    if (-not (Check-Backend)) {
        exit 1
    }
    
    # Run tests based on mode
    $results = $null
    
    switch ($TestMode) {
        'scenario1' { Run-PythonTest "Scenario 1: Happy Path" "1" }
        'scenario2' { Run-PythonTest "Scenario 2: Access Control" "2" }
        'scenario3' { Run-PythonTest "Scenario 3: Data Security" "3" }
        'scenario4' { Run-PythonTest "Scenario 4: Compliance" "4" }
        'scenario5' { Run-PythonTest "Scenario 5: Error Handling" "5" }
        'scenario6' { Run-PythonTest "Scenario 6: Safety Guardrails" "6" }
        'quick' { $results = Run-QuickTests }
        'full' { $results = Run-AllScenarios }
        'all' { $results = Run-AllScenarios }
    }
    
    # Print summary
    if ($results) {
        $success = Print-Summary $results
    }
    else {
        $success = $true
    }
    
    # Generate report
    if ($GenerateReport) {
        Generate-Report
    }
    
    Print-Section "Test Execution Complete"
    
    if ($success) {
        Print-Success "All tests passed!"
        exit 0
    }
    else {
        Print-Error "Some tests failed!"
        exit 1
    }
}

# Run main
Main
