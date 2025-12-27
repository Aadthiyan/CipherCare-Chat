"""
Locust Load Testing Script for CipherCare Healthcare Chatbot
=============================================================

Comprehensive load testing scenarios:
1. Steady State: 5 concurrent clinicians for 10 minutes
2. Peak Load: 50 concurrent clinicians for 5 minutes  
3. Stress Test: Ramp to 100 concurrent, hold 2 minutes
4. Sustained Load: 20 concurrent clinicians for 1 hour

Metrics tracked:
- Response latency (p50, p95, p99)
- Throughput (requests/sec)
- Error rates
- Resource utilization
"""

import os
import json
import time
import logging
import random
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import threading

from locust import HttpUser, task, events, between, TaskSet
import psutil
import numpy as np


# ============================================================================
# Configuration
# ============================================================================

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
API_TIMEOUT = 30  # seconds
THINK_TIME_MIN = 1  # Realistic think time between requests
THINK_TIME_MAX = 5

# Test users (simulated clinicians)
TEST_USERS = {
    "admin": {"username": "admin", "password": "admin123"},
    "resident_1": {"username": "resident_1", "password": "resident123"},
    "resident_2": {"username": "resident_2", "password": "resident123"},
    "nurse_1": {"username": "nurse_1", "password": "nurse123"},
    "nurse_2": {"username": "nurse_2", "password": "nurse123"},
}

# Patient IDs for testing
TEST_PATIENT_IDS = [
    "PAT001", "PAT002", "PAT003", "PAT004", "PAT005",
    "PAT006", "PAT007", "PAT008", "PAT009", "PAT010",
]

# Realistic clinical questions (10+ variations)
CLINICAL_QUESTIONS = [
    "What are the recent vital signs for this patient?",
    "Are there any drug interactions I should be aware of?",
    "What is the patient's medication history?",
    "What are the current lab results and their implications?",
    "Is there a history of allergies in the patient record?",
    "What previous diagnoses has this patient had?",
    "What is the patient's current treatment plan?",
    "Are there any pending procedures or appointments?",
    "What comorbidities does this patient have?",
    "Can you summarize the patient's recent clinical notes?",
    "What is the prognosis based on current conditions?",
    "Are there any red flags in the patient's recent data?",
]


# ============================================================================
# Metrics Collection
# ============================================================================

@dataclass
class MetricsSnapshot:
    """Snapshot of metrics at a point in time"""
    timestamp: str
    endpoint: str
    response_time_ms: float
    status_code: int
    error: Optional[str] = None
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    active_connections: int = 0


class MetricsCollector:
    """Collects and aggregates metrics during load testing"""
    
    def __init__(self):
        self.metrics: List[MetricsSnapshot] = []
        self.lock = threading.Lock()
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
        
    def add_metric(self, metric: MetricsSnapshot):
        """Add a metric snapshot"""
        with self.lock:
            self.metrics.append(metric)
            if metric.status_code >= 400:
                self.error_count += 1
            self.request_count += 1
    
    def get_latency_stats(self) -> Dict:
        """Calculate latency percentiles"""
        latencies = [m.response_time_ms for m in self.metrics]
        if not latencies:
            return {}
        
        latencies.sort()
        return {
            "p50": np.percentile(latencies, 50),
            "p75": np.percentile(latencies, 75),
            "p90": np.percentile(latencies, 90),
            "p95": np.percentile(latencies, 95),
            "p99": np.percentile(latencies, 99),
            "max": max(latencies),
            "min": min(latencies),
            "mean": np.mean(latencies),
        }
    
    def get_throughput_stats(self) -> Dict:
        """Calculate throughput metrics"""
        if not self.metrics:
            return {}
        
        elapsed_seconds = time.time() - self.start_time
        successful_requests = sum(1 for m in self.metrics if m.status_code < 400)
        
        return {
            "total_requests": self.request_count,
            "successful_requests": successful_requests,
            "failed_requests": self.error_count,
            "elapsed_seconds": elapsed_seconds,
            "requests_per_second": self.request_count / elapsed_seconds if elapsed_seconds > 0 else 0,
            "error_rate": (self.error_count / self.request_count * 100) if self.request_count > 0 else 0,
        }
    
    def get_resource_stats(self) -> Dict:
        """Calculate resource utilization stats"""
        if not self.metrics:
            return {}
        
        cpu_values = [m.cpu_percent for m in self.metrics if m.cpu_percent > 0]
        mem_values = [m.memory_percent for m in self.metrics if m.memory_percent > 0]
        conn_values = [m.active_connections for m in self.metrics if m.active_connections > 0]
        
        return {
            "cpu_mean": np.mean(cpu_values) if cpu_values else 0,
            "cpu_max": max(cpu_values) if cpu_values else 0,
            "memory_mean": np.mean(mem_values) if mem_values else 0,
            "memory_max": max(mem_values) if mem_values else 0,
            "connections_mean": np.mean(conn_values) if conn_values else 0,
            "connections_max": max(conn_values) if conn_values else 0,
        }
    
    def save_results(self, filename: str = "load_test_results.json"):
        """Save results to file"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "latency_stats": self.get_latency_stats(),
            "throughput_stats": self.get_throughput_stats(),
            "resource_stats": self.get_resource_stats(),
            "metrics_snapshots": [asdict(m) for m in self.metrics[:100]],  # Save first 100 samples
        }
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        logging.info(f"Results saved to {filename}")


# Global metrics collector
metrics_collector = MetricsCollector()


# ============================================================================
# System Monitoring
# ============================================================================

def get_system_metrics() -> Tuple[float, float, int]:
    """Get current CPU, memory, and connection count"""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory_percent = psutil.virtual_memory().percent
        # Count established connections (approximate)
        net_stats = psutil.net_connections()
        active_connections = len([c for c in net_stats if c.status == 'ESTABLISHED'])
        return cpu_percent, memory_percent, active_connections
    except Exception as e:
        logging.warning(f"Failed to get system metrics: {e}")
        return 0, 0, 0


# ============================================================================
# Locust Task Sets
# ============================================================================

class CipherCareQueryTasks(TaskSet):
    """Task set for realistic CipherCare query workflows"""
    
    def on_start(self):
        """Called when user starts - perform login"""
        self.token = None
        self.patient_id = None
        self.login()
    
    def login(self):
        """Authenticate user and obtain token"""
        # Select random user
        user_credentials = random.choice(list(TEST_USERS.values()))
        
        try:
            start_time = time.time()
            response = self.client.post(
                f"{BACKEND_URL}/login",
                json=user_credentials,
                timeout=API_TIMEOUT,
            )
            response_time = (time.time() - start_time) * 1000
            
            cpu, mem, conn = get_system_metrics()
            metric = MetricsSnapshot(
                timestamp=datetime.now().isoformat(),
                endpoint="/login",
                response_time_ms=response_time,
                status_code=response.status_code,
                cpu_percent=cpu,
                memory_percent=mem,
                active_connections=conn,
            )
            metrics_collector.add_metric(metric)
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                logging.debug(f"Login successful, token: {self.token[:20]}...")
            else:
                logging.warning(f"Login failed: {response.status_code}")
        except Exception as e:
            logging.error(f"Login error: {e}")
            metric = MetricsSnapshot(
                timestamp=datetime.now().isoformat(),
                endpoint="/login",
                response_time_ms=0,
                status_code=500,
                error=str(e),
                cpu_percent=0,
                memory_percent=0,
                active_connections=0,
            )
            metrics_collector.add_metric(metric)
    
    @task(3)
    def query_patient_data(self):
        """Perform a patient query - most common task"""
        if not self.token:
            self.login()
            if not self.token:
                return
        
        patient_id = random.choice(TEST_PATIENT_IDS)
        question = random.choice(CLINICAL_QUESTIONS)
        
        payload = {
            "patient_id": patient_id,
            "question": question,
            "retrieve_k": random.randint(3, 10),
            "temperature": random.uniform(0.3, 0.7),
        }
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            start_time = time.time()
            response = self.client.post(
                f"{BACKEND_URL}/query",
                json=payload,
                headers=headers,
                timeout=API_TIMEOUT,
            )
            response_time = (time.time() - start_time) * 1000
            
            cpu, mem, conn = get_system_metrics()
            metric = MetricsSnapshot(
                timestamp=datetime.now().isoformat(),
                endpoint="/query",
                response_time_ms=response_time,
                status_code=response.status_code,
                cpu_percent=cpu,
                memory_percent=mem,
                active_connections=conn,
            )
            
            if response.status_code != 200:
                try:
                    error_msg = response.json().get("detail", response.text)
                    metric.error = error_msg
                except:
                    metric.error = response.text
            
            metrics_collector.add_metric(metric)
            
        except Exception as e:
            logging.error(f"Query error: {e}")
            metric = MetricsSnapshot(
                timestamp=datetime.now().isoformat(),
                endpoint="/query",
                response_time_ms=0,
                status_code=500,
                error=str(e),
                cpu_percent=0,
                memory_percent=0,
                active_connections=0,
            )
            metrics_collector.add_metric(metric)
    
    @task(1)
    def query_different_patient(self):
        """Ensure different patients are tested"""
        self.query_patient_data()
    
    def wait_time(self):
        """Realistic think time between requests"""
        return random.uniform(THINK_TIME_MIN, THINK_TIME_MAX)


class CipherCareUser(HttpUser):
    """Simulated clinician user"""
    tasks = [CipherCareQueryTasks]
    wait_time = between(THINK_TIME_MIN, THINK_TIME_MAX)


# ============================================================================
# Event Listeners for Custom Logging
# ============================================================================

@events.request.add_listener
def log_request(request_type, name, response_time, response_length, response, context, exception, **kwargs):
    """Log individual requests"""
    if exception:
        logging.warning(f"Request failed: {name} - {exception}")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when load test starts"""
    logging.info("=" * 80)
    logging.info("LOAD TEST STARTED")
    logging.info(f"Target: {BACKEND_URL}")
    logging.info(f"Start time: {datetime.now().isoformat()}")
    logging.info("=" * 80)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when load test stops"""
    logging.info("=" * 80)
    logging.info("LOAD TEST STOPPED")
    logging.info(f"Stop time: {datetime.now().isoformat()}")
    
    # Print summary
    latency_stats = metrics_collector.get_latency_stats()
    throughput_stats = metrics_collector.get_throughput_stats()
    resource_stats = metrics_collector.get_resource_stats()
    
    logging.info("\n=== LATENCY STATS (ms) ===")
    for key, value in latency_stats.items():
        logging.info(f"{key:10s}: {value:10.2f}")
    
    logging.info("\n=== THROUGHPUT STATS ===")
    for key, value in throughput_stats.items():
        if isinstance(value, float):
            logging.info(f"{key:20s}: {value:10.2f}")
        else:
            logging.info(f"{key:20s}: {value:10}")
    
    logging.info("\n=== RESOURCE UTILIZATION ===")
    for key, value in resource_stats.items():
        logging.info(f"{key:20s}: {value:10.2f}")
    
    # Save results
    metrics_collector.save_results("benchmarks/load_test_results.json")
    logging.info("=" * 80)


# ============================================================================
# Custom Shape Classes for Advanced Scenarios
# ============================================================================

class SteadyStateShape:
    """
    Scenario 1: Steady State
    5 concurrent clinicians for 10 minutes
    """
    def tick(self):
        run_time = self.get_run_time()
        
        if run_time < 600:  # 10 minutes
            return (5, 1.0)  # 5 users, 1x spawn rate
        else:
            return None  # Stop


class PeakLoadShape:
    """
    Scenario 2: Peak Load
    50 concurrent clinicians for 5 minutes
    """
    def tick(self):
        run_time = self.get_run_time()
        
        if run_time < 60:  # Ramp up for 1 minute
            return (int(run_time / 12), 1.0)  # Gradually increase to 5
        elif run_time < 360:  # Hold for 5 minutes
            return (50, 1.0)  # 50 users
        else:
            return None  # Stop


class StressTestShape:
    """
    Scenario 3: Stress Test
    Ramp up to 100 concurrent, hold for 2 minutes
    """
    def tick(self):
        run_time = self.get_run_time()
        
        if run_time < 300:  # Ramp up for 5 minutes
            return (int(run_time / 3), 1.0)  # Gradually increase to 100
        elif run_time < 420:  # Hold for 2 minutes
            return (100, 1.0)  # 100 users
        else:
            return None  # Stop


class SustainedLoadShape:
    """
    Scenario 4: Sustained Load
    20 concurrent clinicians for 1 hour
    """
    def tick(self):
        run_time = self.get_run_time()
        
        if run_time < 60:  # Ramp up for 1 minute
            return (int(run_time / 3), 1.0)  # Gradually increase
        elif run_time < 3660:  # Hold for 1 hour
            return (20, 1.0)  # 20 users
        else:
            return None  # Stop


# ============================================================================
# Logging Configuration
# ============================================================================

def setup_logging():
    """Configure logging for the load test"""
    os.makedirs("benchmarks/logs", exist_ok=True)
    
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    log_file = f"benchmarks/logs/load_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(),
        ]
    )
    
    return log_file


if __name__ == "__main__":
    setup_logging()
