"""
E2E Test Execution Runner
Orchestrates test execution with scenario selection, logging, and result collection
"""

import pytest
import json
import os
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import argparse
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tests/e2e/execution.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class E2ETestRunner:
    """Orchestrate E2E test execution"""
    
    def __init__(self, backend_url: str = "http://localhost:8000",
                 frontend_url: str = "http://localhost:3000",
                 output_dir: str = "tests/e2e/results"):
        self.backend_url = backend_url
        self.frontend_url = frontend_url
        self.output_dir = output_dir
        self.results = {}
        self.start_time = None
        self.end_time = None
        
        # Create output directory
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
    
    def check_backend_health(self) -> bool:
        """Verify backend is running and healthy"""
        import requests
        try:
            response = requests.get(
                f"{self.backend_url}/health",
                timeout=5
            )
            logger.info(f"Backend health: {response.status_code}")
            return response.status_code in [200, 404]
        except Exception as e:
            logger.error(f"Backend health check failed: {str(e)}")
            return False
    
    def check_frontend_health(self) -> bool:
        """Verify frontend is running"""
        import requests
        try:
            response = requests.get(
                f"{self.frontend_url}/",
                timeout=5
            )
            logger.info(f"Frontend health: {response.status_code}")
            return response.status_code in [200, 304]
        except Exception as e:
            logger.error(f"Frontend health check failed: {str(e)}")
            return False
    
    def run_scenario(self, scenario_name: str, 
                    test_module: str,
                    test_class: Optional[str] = None) -> Dict:
        """Run specific test scenario"""
        logger.info(f"Running scenario: {scenario_name}")
        
        # Build pytest command
        if test_class:
            pytest_args = [
                test_module,
                "-v",
                f"-k {test_class}",
                f"--tb=short",
                f"--junit-xml={self.output_dir}/junit_{scenario_name}.xml"
            ]
        else:
            pytest_args = [
                test_module,
                "-v",
                f"--tb=short",
                f"--junit-xml={self.output_dir}/junit_{scenario_name}.xml"
            ]
        
        # Run pytest
        result = pytest.main(pytest_args)
        
        # Collect results
        scenario_result = {
            "scenario": scenario_name,
            "status": "PASSED" if result == 0 else "FAILED",
            "exit_code": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Scenario {scenario_name}: {scenario_result['status']}")
        return scenario_result
    
    def run_all_scenarios(self) -> Dict:
        """Run all test scenarios"""
        scenarios = [
            {
                "name": "Scenario1_HappyPath",
                "module": "tests/e2e/test_scenarios_1_3.py",
                "class": "TestScenario1HappyPath"
            },
            {
                "name": "Scenario2_AccessControl",
                "module": "tests/e2e/test_scenarios_1_3.py",
                "class": "TestScenario2AccessControl"
            },
            {
                "name": "Scenario3_DataSecurity",
                "module": "tests/e2e/test_scenarios_1_3.py",
                "class": "TestScenario3DataSecurity"
            },
            {
                "name": "Scenario4_Compliance",
                "module": "tests/e2e/test_scenarios_4_6.py",
                "class": "TestScenario4Compliance"
            },
            {
                "name": "Scenario5_ErrorHandling",
                "module": "tests/e2e/test_scenarios_4_6.py",
                "class": "TestScenario5ErrorHandling"
            },
            {
                "name": "Scenario6_SafetyGuardrails",
                "module": "tests/e2e/test_scenarios_4_6.py",
                "class": "TestScenario6SafetyGuardrails"
            }
        ]
        
        self.start_time = datetime.utcnow()
        all_results = []
        
        for scenario in scenarios:
            try:
                result = self.run_scenario(
                    scenario["name"],
                    scenario["module"],
                    scenario["class"]
                )
                all_results.append(result)
                time.sleep(1)  # Brief delay between scenarios
            except Exception as e:
                logger.error(f"Error running {scenario['name']}: {str(e)}")
                all_results.append({
                    "scenario": scenario["name"],
                    "status": "ERROR",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                })
        
        self.end_time = datetime.utcnow()
        self.results = all_results
        
        return all_results
    
    def run_specific_scenario(self, scenario_number: int) -> Dict:
        """Run specific scenario by number"""
        scenarios = {
            1: ("Scenario1_HappyPath", "tests/e2e/test_scenarios_1_3.py", "TestScenario1HappyPath"),
            2: ("Scenario2_AccessControl", "tests/e2e/test_scenarios_1_3.py", "TestScenario2AccessControl"),
            3: ("Scenario3_DataSecurity", "tests/e2e/test_scenarios_1_3.py", "TestScenario3DataSecurity"),
            4: ("Scenario4_Compliance", "tests/e2e/test_scenarios_4_6.py", "TestScenario4Compliance"),
            5: ("Scenario5_ErrorHandling", "tests/e2e/test_scenarios_4_6.py", "TestScenario5ErrorHandling"),
            6: ("Scenario6_SafetyGuardrails", "tests/e2e/test_scenarios_4_6.py", "TestScenario6SafetyGuardrails")
        }
        
        if scenario_number not in scenarios:
            raise ValueError(f"Invalid scenario number: {scenario_number}")
        
        name, module, test_class = scenarios[scenario_number]
        self.start_time = datetime.utcnow()
        result = self.run_scenario(name, module, test_class)
        self.end_time = datetime.utcnow()
        
        return result
    
    def generate_summary_report(self) -> Dict:
        """Generate summary report of test execution"""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.get("status") == "PASSED")
        failed_tests = sum(1 for r in self.results if r.get("status") == "FAILED")
        error_tests = sum(1 for r in self.results if r.get("status") == "ERROR")
        
        duration = None
        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()
        
        summary = {
            "execution_time": self.start_time.isoformat() if self.start_time else None,
            "total_scenarios": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "errors": error_tests,
            "success_rate": f"{(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "N/A",
            "duration_seconds": duration,
            "results": self.results
        }
        
        return summary
    
    def save_results_json(self) -> str:
        """Save test results to JSON file"""
        summary = self.generate_summary_report()
        
        output_file = os.path.join(
            self.output_dir,
            f"e2e_test_results_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        with open(output_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Results saved to: {output_file}")
        return output_file
    
    def print_summary(self):
        """Print execution summary to console"""
        summary = self.generate_summary_report()
        
        print("\n" + "="*70)
        print("E2E TEST EXECUTION SUMMARY")
        print("="*70)
        print(f"Execution Time: {summary['execution_time']}")
        print(f"Total Scenarios: {summary['total_scenarios']}")
        print(f"Passed: {summary['passed']} ✓")
        print(f"Failed: {summary['failed']} ✗")
        print(f"Errors: {summary['errors']} ⚠")
        print(f"Success Rate: {summary['success_rate']}")
        if summary['duration_seconds']:
            print(f"Duration: {summary['duration_seconds']:.2f} seconds")
        
        print("\nDetailed Results:")
        print("-"*70)
        for result in summary['results']:
            status_symbol = "✓" if result['status'] == "PASSED" else "✗"
            print(f"{status_symbol} {result['scenario']}: {result['status']}")
        
        print("="*70 + "\n")


def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description="E2E Test Runner for CipherCare"
    )
    
    parser.add_argument(
        "--scenario",
        type=int,
        choices=[1, 2, 3, 4, 5, 6],
        help="Run specific scenario (1-6)"
    )
    
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all scenarios"
    )
    
    parser.add_argument(
        "--backend-url",
        default="http://localhost:8000",
        help="Backend URL (default: http://localhost:8000)"
    )
    
    parser.add_argument(
        "--frontend-url",
        default="http://localhost:3000",
        help="Frontend URL (default: http://localhost:3000)"
    )
    
    parser.add_argument(
        "--check-health",
        action="store_true",
        help="Check backend/frontend health before running tests"
    )
    
    parser.add_argument(
        "--output-dir",
        default="tests/e2e/results",
        help="Output directory for results"
    )
    
    return parser.parse_args()


def main():
    """Main entry point"""
    args = parse_arguments()
    
    # Create runner
    runner = E2ETestRunner(
        backend_url=args.backend_url,
        frontend_url=args.frontend_url,
        output_dir=args.output_dir
    )
    
    # Check health if requested
    if args.check_health:
        logger.info("Checking system health...")
        backend_ok = runner.check_backend_health()
        frontend_ok = runner.check_frontend_health()
        
        if not backend_ok:
            logger.error("Backend is not running!")
            sys.exit(1)
        
        if not frontend_ok:
            logger.warning("Frontend is not running (optional for API tests)")
    
    # Run tests
    try:
        if args.scenario:
            logger.info(f"Running scenario {args.scenario}...")
            runner.run_specific_scenario(args.scenario)
        elif args.all:
            logger.info("Running all scenarios...")
            runner.run_all_scenarios()
        else:
            logger.info("Running all scenarios...")
            runner.run_all_scenarios()
        
        # Save and print results
        runner.save_results_json()
        runner.print_summary()
        
        # Exit with appropriate code
        summary = runner.generate_summary_report()
        if summary['failed'] > 0 or summary['errors'] > 0:
            sys.exit(1)
        else:
            sys.exit(0)
    
    except Exception as e:
        logger.error(f"Test execution failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
