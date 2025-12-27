#!/usr/bin/env python3
"""
E2E Test Automation Runner for CipherCare
Orchestrates execution of all 6 test scenarios with logging, result collection, and reporting.
"""

import sys
import json
import time
import argparse
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import platform


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tests/results/e2e_execution.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TestRunner:
    """Orchestrates E2E test execution"""
    
    def __init__(self, base_dir: str = "tests"):
        self.base_dir = Path(base_dir)
        self.results_dir = self.base_dir / "results"
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.test_results = {}
        self.start_time = None
        self.end_time = None
        
    def print_header(self, text: str):
        """Print formatted header"""
        print("\n" + "="*70)
        print(f"  {text}")
        print("="*70 + "\n")
        
    def print_section(self, text: str):
        """Print formatted section"""
        print(f"\n>>> {text}")
        print("-" * 60)
        
    def log_result(self, scenario: str, status: str, details: Dict):
        """Log individual test result"""
        self.test_results[scenario] = {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details
        }
        
    def run_scenario(self, scenario_name: str, scenario_file: str, 
                     test_markers: List[str] = None) -> Dict:
        """
        Run a single scenario using pytest
        
        Args:
            scenario_name: Display name
            scenario_file: pytest file pattern
            test_markers: pytest markers to run
            
        Returns:
            Result dictionary
        """
        self.print_section(f"Running {scenario_name}")
        
        # Build pytest command
        cmd = ["pytest", str(self.base_dir / scenario_file), "-v", "--tb=short"]
        
        if test_markers:
            for marker in test_markers:
                cmd.extend(["-m", marker])
        
        # Add JSON results output
        json_output = self.results_dir / f"{scenario_name.lower().replace(' ', '_')}_results.json"
        cmd.extend(["--json-report", f"--json-report-file={json_output}"])
        
        # Add coverage if requested
        cmd.extend(["--cov=backend", "--cov-report=html"])
        
        try:
            logger.info(f"Executing: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            success = result.returncode == 0
            
            print(result.stdout)
            if result.stderr:
                logger.error(result.stderr)
            
            details = {
                "command": " ".join(cmd),
                "return_code": result.returncode,
                "stdout": result.stdout[-500:] if result.stdout else "",  # Last 500 chars
                "stderr": result.stderr[-500:] if result.stderr else "",
                "duration": 0  # Updated by pytest-benchmark
            }
            
            status = "PASS" if success else "FAIL"
            self.log_result(scenario_name, status, details)
            
            return {
                "scenario": scenario_name,
                "status": status,
                "success": success,
                "details": details
            }
            
        except subprocess.TimeoutExpired:
            logger.error(f"Test timeout for {scenario_name}")
            self.log_result(scenario_name, "TIMEOUT", {"timeout": True})
            return {
                "scenario": scenario_name,
                "status": "TIMEOUT",
                "success": False,
                "details": {"error": "Test execution timed out"}
            }
        except Exception as e:
            logger.error(f"Error running {scenario_name}: {e}")
            self.log_result(scenario_name, "ERROR", {"error": str(e)})
            return {
                "scenario": scenario_name,
                "status": "ERROR",
                "success": False,
                "details": {"error": str(e)}
            }
    
    def run_all_scenarios(self, backend_url: str = "http://localhost:8000",
                         skip_scenarios: List[str] = None) -> Dict:
        """
        Run all 6 test scenarios
        
        Args:
            backend_url: Backend service URL
            skip_scenarios: List of scenarios to skip
            
        Returns:
            Overall results summary
        """
        skip_scenarios = skip_scenarios or []
        self.start_time = datetime.now()
        
        self.print_header("CipherCare E2E Testing Suite")
        logger.info(f"Starting E2E tests at {self.start_time}")
        logger.info(f"Backend URL: {backend_url}")
        logger.info(f"Test environment: {platform.platform()}")
        
        # Verify backend health
        if not self.check_backend_health(backend_url):
            logger.error("Backend is not healthy. Run 'python backend/main.py' first.")
            return {"success": False, "error": "Backend not available"}
        
        results = []
        
        # Scenario 1: Happy Path
        if "happy_path" not in skip_scenarios:
            result = self.run_scenario(
                "Scenario 1: Happy Path",
                "e2e/test_scenario_1_happy_path.py",
                ["happy_path"]
            )
            results.append(result)
        
        # Scenario 2: Access Control
        if "access_control" not in skip_scenarios:
            result = self.run_scenario(
                "Scenario 2: Access Control",
                "e2e/test_scenario_2_access_control.py",
                ["access_control"]
            )
            results.append(result)
        
        # Scenario 3: Data Security
        if "data_security" not in skip_scenarios:
            result = self.run_scenario(
                "Scenario 3: Data Security",
                "e2e/test_scenario_3_data_security.py",
                ["data_security"]
            )
            results.append(result)
        
        # Scenario 4: Compliance
        if "compliance" not in skip_scenarios:
            result = self.run_scenario(
                "Scenario 4: Compliance",
                "e2e/test_scenario_4_compliance.py",
                ["compliance"]
            )
            results.append(result)
        
        # Scenario 5: Error Handling
        if "error_handling" not in skip_scenarios:
            result = self.run_scenario(
                "Scenario 5: Error Handling",
                "e2e/test_scenario_5_error_handling.py",
                ["error_handling"]
            )
            results.append(result)
        
        # Scenario 6: Safety Guardrails
        if "safety_guardrails" not in skip_scenarios:
            result = self.run_scenario(
                "Scenario 6: Safety Guardrails",
                "e2e/test_scenario_6_safety_guardrails.py",
                ["safety_guardrails"]
            )
            results.append(result)
        
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds()
        
        # Summary
        return self.generate_summary(results, duration)
    
    def check_backend_health(self, backend_url: str) -> bool:
        """Check if backend is running and healthy"""
        self.print_section("Checking Backend Health")
        
        try:
            import requests
            response = requests.get(f"{backend_url}/health", timeout=5)
            if response.status_code == 200:
                logger.info("✓ Backend is healthy")
                print("✓ Backend is healthy")
                return True
            else:
                logger.error(f"Backend returned status {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            logger.error(f"Cannot connect to backend at {backend_url}")
            print(f"✗ Cannot connect to backend at {backend_url}")
            return False
        except Exception as e:
            logger.error(f"Error checking backend: {e}")
            return False
    
    def generate_summary(self, results: List[Dict], duration: float) -> Dict:
        """Generate test execution summary"""
        self.print_section("Test Results Summary")
        
        total = len(results)
        passed = sum(1 for r in results if r["status"] == "PASS")
        failed = sum(1 for r in results if r["status"] == "FAIL")
        timeout = sum(1 for r in results if r["status"] == "TIMEOUT")
        errors = sum(1 for r in results if r["status"] == "ERROR")
        
        summary = {
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": duration,
            "total_scenarios": total,
            "passed": passed,
            "failed": failed,
            "timeout": timeout,
            "errors": errors,
            "success_rate": (passed / total * 100) if total > 0 else 0,
            "scenarios": results,
            "overall_status": "PASS" if failed == 0 and timeout == 0 and errors == 0 else "FAIL"
        }
        
        # Print summary table
        print(f"\n{'Scenario':<40} {'Status':<10} {'Duration'}")
        print("-" * 60)
        for result in results:
            print(f"{result['scenario']:<40} {result['status']:<10}")
        
        print("\n" + "="*60)
        print(f"Total Scenarios: {total}")
        print(f"Passed: {passed} ({summary['success_rate']:.1f}%)")
        print(f"Failed: {failed}")
        print(f"Timeout: {timeout}")
        print(f"Errors: {errors}")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Overall Status: {summary['overall_status']}")
        print("="*60)
        
        # Save results
        self.save_results(summary)
        
        return summary
    
    def save_results(self, summary: Dict):
        """Save test results to JSON"""
        output_file = self.results_dir / f"e2e_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(output_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Results saved to {output_file}")
        print(f"\n✓ Results saved to {output_file}")
    
    def run_specific_scenario(self, scenario_number: int, 
                             backend_url: str = "http://localhost:8000"):
        """Run a single specific scenario"""
        scenarios = {
            1: ("Scenario 1: Happy Path", "e2e/test_scenario_1_happy_path.py"),
            2: ("Scenario 2: Access Control", "e2e/test_scenario_2_access_control.py"),
            3: ("Scenario 3: Data Security", "e2e/test_scenario_3_data_security.py"),
            4: ("Scenario 4: Compliance", "e2e/test_scenario_4_compliance.py"),
            5: ("Scenario 5: Error Handling", "e2e/test_scenario_5_error_handling.py"),
            6: ("Scenario 6: Safety Guardrails", "e2e/test_scenario_6_safety_guardrails.py"),
        }
        
        if scenario_number not in scenarios:
            logger.error(f"Invalid scenario number: {scenario_number}")
            return None
        
        self.start_time = datetime.now()
        name, file = scenarios[scenario_number]
        result = self.run_scenario(name, file)
        self.end_time = datetime.now()
        
        return result


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="CipherCare E2E Testing Suite Runner"
    )
    
    parser.add_argument(
        "--backend-url",
        default="http://localhost:8000",
        help="Backend service URL (default: http://localhost:8000)"
    )
    
    parser.add_argument(
        "--scenario",
        type=int,
        choices=[1, 2, 3, 4, 5, 6],
        help="Run specific scenario (1-6). If not specified, runs all."
    )
    
    parser.add_argument(
        "--skip",
        nargs="+",
        default=[],
        help="Scenarios to skip (happy_path, access_control, data_security, compliance, error_handling, safety_guardrails)"
    )
    
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output"
    )
    
    parser.add_argument(
        "--screenshots",
        "-s",
        action="store_true",
        help="Capture screenshots (requires Selenium browser)"
    )
    
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser tests in headless mode"
    )
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    if args.scenario:
        # Run specific scenario
        logger.info(f"Running scenario {args.scenario}")
        result = runner.run_specific_scenario(args.scenario, args.backend_url)
        if result:
            print(f"\nResult: {result['status']}")
            sys.exit(0 if result["success"] else 1)
        else:
            sys.exit(1)
    else:
        # Run all scenarios
        results = runner.run_all_scenarios(args.backend_url, args.skip)
        sys.exit(0 if results.get("overall_status") == "PASS" else 1)


if __name__ == "__main__":
    main()
