"""
Component Benchmarking Script for CipherCare
==============================================

Measures individual component performance:
1. Query Embedding Generation: <200ms
2. CyborgDB Search: <500ms
3. LLM Inference: <5 seconds
4. API Response Time: <100ms (excluding LLM)
5. End-to-End Query: <5 seconds

Usage:
    python component_benchmarks.py [--component all|embedding|search|llm|api|e2e] [--iterations 100]
"""

import os
import sys
import time
import json
import logging
import argparse
import statistics
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
import threading
import psutil

import numpy as np


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class BenchmarkResult:
    """Single benchmark measurement"""
    component: str
    iteration: int
    duration_ms: float
    success: bool
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class BenchmarkStats:
    """Aggregated benchmark statistics"""
    component: str
    iterations: int
    min_ms: float
    max_ms: float
    mean_ms: float
    median_ms: float
    stdev_ms: float
    p95_ms: float
    p99_ms: float
    success_rate: float
    total_duration_sec: float


# ============================================================================
# Configuration
# ============================================================================

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
EMBEDDING_MODEL = "MiniLM-L6-v2"  # 384-dimensional
VECTOR_DIMENSION = 384
MOCK_EMBEDDINGS = True  # Use mock data if backend unavailable


# Sample clinical data
SAMPLE_QUESTIONS = [
    "What are the recent vital signs for this patient?",
    "Are there any drug interactions I should be aware of?",
    "What is the patient's medication history?",
    "What are the current lab results?",
    "Is there a history of allergies?",
]

SAMPLE_DOCUMENTS = [
    "Patient presented with hypertension, currently on lisinopril 10mg daily.",
    "Recent lab work shows elevated creatinine levels, may indicate kidney function decline.",
    "Allergy to penicillin documented in records.",
    "Diabetes type 2 diagnosed 5 years ago, managed with metformin.",
    "Recent echocardiogram shows normal ejection fraction.",
]


# ============================================================================
# Embedding Benchmarking
# ============================================================================

class EmbeddingBenchmark:
    """Benchmark embedding generation"""
    
    def __init__(self):
        self.results: List[BenchmarkResult] = []
        
        # Try to import embedding service
        try:
            sys.path.insert(0, '/app')
            from embeddings.embedder import ClinicalEmbedder
            self.embedder = ClinicalEmbedder()
            self.use_mock = False
            logging.info("Using real ClinicalEmbedder")
        except Exception as e:
            logging.warning(f"Failed to load ClinicalEmbedder: {e}, using mock")
            self.embedder = None
            self.use_mock = True
    
    def _generate_mock_embedding(self) -> np.ndarray:
        """Generate mock embedding for testing"""
        return np.random.randn(VECTOR_DIMENSION).astype(np.float32)
    
    def run(self, iterations: int = 100) -> List[BenchmarkResult]:
        """Run embedding benchmarks"""
        logging.info(f"Running embedding benchmark ({iterations} iterations)")
        
        for i in range(iterations):
            text = SAMPLE_QUESTIONS[i % len(SAMPLE_QUESTIONS)]
            
            try:
                start_time = time.time()
                
                if self.use_mock:
                    embedding = self._generate_mock_embedding()
                else:
                    embedding = self.embedder.generate_embedding(text)
                
                duration_ms = (time.time() - start_time) * 1000
                
                result = BenchmarkResult(
                    component="embedding",
                    iteration=i + 1,
                    duration_ms=duration_ms,
                    success=True,
                    metadata={
                        "text_length": len(text),
                        "embedding_dim": len(embedding),
                        "embedding_norm": float(np.linalg.norm(embedding)),
                    }
                )
                self.results.append(result)
                
            except Exception as e:
                result = BenchmarkResult(
                    component="embedding",
                    iteration=i + 1,
                    duration_ms=0,
                    success=False,
                    error=str(e)
                )
                self.results.append(result)
        
        return self.results


# ============================================================================
# Search Benchmarking
# ============================================================================

class SearchBenchmark:
    """Benchmark vector search performance"""
    
    def __init__(self):
        self.results: List[BenchmarkResult] = []
        
        # Try to import CyborgDB service
        try:
            sys.path.insert(0, '/app')
            from backend.cyborg_manager import CyborgManager
            self.cyborg_manager = CyborgManager()
            self.use_mock = False
            logging.info("Using real CyborgManager")
        except Exception as e:
            logging.warning(f"Failed to load CyborgManager: {e}, using mock")
            self.cyborg_manager = None
            self.use_mock = True
    
    def _generate_mock_search_results(self, query_vector, k: int) -> List[Dict]:
        """Generate mock search results"""
        results = []
        for i in range(min(k, 5)):
            results.append({
                "document_id": f"doc_{i}",
                "content": SAMPLE_DOCUMENTS[i % len(SAMPLE_DOCUMENTS)],
                "similarity_score": 0.9 - (i * 0.05),
                "metadata": {"source": f"patient_record_{i}"},
            })
        return results
    
    def run(self, iterations: int = 100, vector_count: int = 500) -> List[BenchmarkResult]:
        """Run search benchmarks"""
        logging.info(f"Running search benchmark ({iterations} iterations, {vector_count} vectors)")
        
        # Generate random query vectors
        query_vectors = [np.random.randn(VECTOR_DIMENSION) for _ in range(iterations)]
        
        for i, query_vector in enumerate(query_vectors):
            k = 5 + (i % 6)  # Vary k from 5 to 10
            
            try:
                start_time = time.time()
                
                if self.use_mock:
                    results = self._generate_mock_search_results(query_vector, k)
                else:
                    results = self.cyborg_manager.search(
                        query_vector=query_vector,
                        patient_id=f"PAT_{i % 10:03d}",
                        top_k=k
                    )
                
                duration_ms = (time.time() - start_time) * 1000
                
                result = BenchmarkResult(
                    component="search",
                    iteration=i + 1,
                    duration_ms=duration_ms,
                    success=True,
                    metadata={
                        "k": k,
                        "results_count": len(results) if results else 0,
                        "vector_count": vector_count,
                    }
                )
                self.results.append(result)
                
            except Exception as e:
                result = BenchmarkResult(
                    component="search",
                    iteration=i + 1,
                    duration_ms=0,
                    success=False,
                    error=str(e),
                    metadata={"k": k, "vector_count": vector_count}
                )
                self.results.append(result)
        
        return self.results


# ============================================================================
# LLM Inference Benchmarking
# ============================================================================

class LLMBenchmark:
    """Benchmark LLM inference performance"""
    
    def __init__(self):
        self.results: List[BenchmarkResult] = []
        
        # Try to import LLM service
        try:
            sys.path.insert(0, '/app')
            from backend.llm import LLMService
            self.llm_service = LLMService()
            self.use_mock = False
            logging.info("Using real LLMService")
        except Exception as e:
            logging.warning(f"Failed to load LLMService: {e}, using mock")
            self.llm_service = None
            self.use_mock = True
    
    def _generate_mock_response(self, prompt: str, max_tokens: int) -> str:
        """Generate mock LLM response"""
        return "This is a simulated clinical response based on the patient data and context provided."
    
    def run(self, iterations: int = 50, max_tokens: int = 100) -> List[BenchmarkResult]:
        """Run LLM inference benchmarks"""
        logging.info(f"Running LLM benchmark ({iterations} iterations, max_tokens={max_tokens})")
        
        prompts = [
            f"Summarize the patient's condition: {SAMPLE_DOCUMENTS[i % len(SAMPLE_DOCUMENTS)]}"
            for i in range(iterations)
        ]
        
        for i, prompt in enumerate(prompts):
            try:
                start_time = time.time()
                
                if self.use_mock:
                    response = self._generate_mock_response(prompt, max_tokens)
                    # Simulate inference time
                    time.sleep(np.random.uniform(2, 4))  # 2-4 seconds
                else:
                    response = self.llm_service.generate(
                        prompt=prompt,
                        max_tokens=max_tokens
                    )
                
                duration_ms = (time.time() - start_time) * 1000
                
                result = BenchmarkResult(
                    component="llm",
                    iteration=i + 1,
                    duration_ms=duration_ms,
                    success=True,
                    metadata={
                        "prompt_length": len(prompt),
                        "response_length": len(response),
                        "max_tokens": max_tokens,
                        "tokens_per_second": len(response.split()) / (duration_ms / 1000),
                    }
                )
                self.results.append(result)
                
            except Exception as e:
                result = BenchmarkResult(
                    component="llm",
                    iteration=i + 1,
                    duration_ms=0,
                    success=False,
                    error=str(e),
                    metadata={"max_tokens": max_tokens}
                )
                self.results.append(result)
        
        return self.results


# ============================================================================
# API Response Time Benchmarking
# ============================================================================

class APIBenchmark:
    """Benchmark API response times (excluding LLM inference)"""
    
    def __init__(self):
        self.results: List[BenchmarkResult] = []
    
    def run(self, iterations: int = 100) -> List[BenchmarkResult]:
        """Run API benchmarks"""
        try:
            import requests
        except ImportError:
            logging.error("requests library required for API benchmarking")
            return self.results
        
        logging.info(f"Running API benchmark ({iterations} iterations)")
        
        for i in range(iterations):
            try:
                payload = {
                    "username": "test_user",
                    "password": "test_password"
                }
                
                start_time = time.time()
                response = requests.post(
                    f"{BACKEND_URL}/login",
                    json=payload,
                    timeout=10
                )
                duration_ms = (time.time() - start_time) * 1000
                
                result = BenchmarkResult(
                    component="api",
                    iteration=i + 1,
                    duration_ms=duration_ms,
                    success=response.status_code == 200,
                    metadata={
                        "status_code": response.status_code,
                        "response_size": len(response.content),
                    }
                )
                self.results.append(result)
                
            except Exception as e:
                result = BenchmarkResult(
                    component="api",
                    iteration=i + 1,
                    duration_ms=0,
                    success=False,
                    error=str(e)
                )
                self.results.append(result)
        
        return self.results


# ============================================================================
# End-to-End Query Benchmarking
# ============================================================================

class EndToEndBenchmark:
    """Benchmark complete query workflow"""
    
    def __init__(self):
        self.results: List[BenchmarkResult] = []
        self.embedding_bench = EmbeddingBenchmark()
        self.search_bench = SearchBenchmark()
        self.llm_bench = LLMBenchmark()
    
    def run(self, iterations: int = 50) -> List[BenchmarkResult]:
        """Run end-to-end benchmarks"""
        logging.info(f"Running end-to-end benchmark ({iterations} iterations)")
        
        for i in range(iterations):
            try:
                # Step 1: Generate embedding
                text = SAMPLE_QUESTIONS[i % len(SAMPLE_QUESTIONS)]
                embedding_start = time.time()
                if self.embedding_bench.use_mock:
                    embedding = self.embedding_bench._generate_mock_embedding()
                else:
                    embedding = self.embedding_bench.embedder.generate_embedding(text)
                embedding_time = time.time() - embedding_start
                
                # Step 2: Search
                search_start = time.time()
                if self.search_bench.use_mock:
                    search_results = self.search_bench._generate_mock_search_results(embedding, 5)
                else:
                    search_results = self.search_bench.cyborg_manager.search(
                        query_vector=embedding,
                        patient_id=f"PAT_{i % 10:03d}",
                        top_k=5
                    )
                search_time = time.time() - search_start
                
                # Step 3: LLM inference
                context = " ".join([doc.get("content", "") for doc in search_results])
                prompt = f"Based on: {context}\nAnswer: {text}"
                
                llm_start = time.time()
                if self.llm_bench.use_mock:
                    response = self.llm_bench._generate_mock_response(prompt, 100)
                    time.sleep(np.random.uniform(2, 4))  # Simulate LLM time
                else:
                    response = self.llm_bench.llm_service.generate(prompt, max_tokens=100)
                llm_time = time.time() - llm_start
                
                total_duration = (embedding_time + search_time + llm_time) * 1000
                
                result = BenchmarkResult(
                    component="e2e",
                    iteration=i + 1,
                    duration_ms=total_duration,
                    success=True,
                    metadata={
                        "embedding_ms": embedding_time * 1000,
                        "search_ms": search_time * 1000,
                        "llm_ms": llm_time * 1000,
                        "results_count": len(search_results) if search_results else 0,
                    }
                )
                self.results.append(result)
                
            except Exception as e:
                result = BenchmarkResult(
                    component="e2e",
                    iteration=i + 1,
                    duration_ms=0,
                    success=False,
                    error=str(e)
                )
                self.results.append(result)
        
        return self.results


# ============================================================================
# Results Analysis
# ============================================================================

def analyze_results(results: List[BenchmarkResult]) -> BenchmarkStats:
    """Analyze benchmark results and compute statistics"""
    if not results:
        raise ValueError("No results to analyze")
    
    successful_results = [r for r in results if r.success]
    durations = [r.duration_ms for r in successful_results]
    
    if not durations:
        success_rate = 0
        stats = {
            'min': 0, 'max': 0, 'mean': 0, 'median': 0,
            'stdev': 0, 'p95': 0, 'p99': 0
        }
    else:
        success_rate = len(successful_results) / len(results) * 100
        stats = {
            'min': min(durations),
            'max': max(durations),
            'mean': statistics.mean(durations),
            'median': statistics.median(durations),
            'stdev': statistics.stdev(durations) if len(durations) > 1 else 0,
            'p95': np.percentile(durations, 95),
            'p99': np.percentile(durations, 99),
        }
    
    component = results[0].component
    total_duration = sum(r.duration_ms for r in results) / 1000
    
    return BenchmarkStats(
        component=component,
        iterations=len(results),
        min_ms=stats['min'],
        max_ms=stats['max'],
        mean_ms=stats['mean'],
        median_ms=stats['median'],
        stdev_ms=stats['stdev'],
        p95_ms=stats['p95'],
        p99_ms=stats['p99'],
        success_rate=success_rate,
        total_duration_sec=total_duration
    )


def print_stats(stats: BenchmarkStats):
    """Print benchmark statistics"""
    print("\n" + "=" * 80)
    print(f"BENCHMARK RESULTS: {stats.component.upper()}")
    print("=" * 80)
    print(f"Iterations:           {stats.iterations}")
    print(f"Success Rate:         {stats.success_rate:.2f}%")
    print(f"Total Duration:       {stats.total_duration_sec:.2f} seconds")
    print()
    print("Latency Statistics (milliseconds):")
    print(f"  Min:                {stats.min_ms:10.2f} ms")
    print(f"  Median:             {stats.median_ms:10.2f} ms")
    print(f"  Mean:               {stats.mean_ms:10.2f} ms")
    print(f"  StDev:              {stats.stdev_ms:10.2f} ms")
    print(f"  p95:                {stats.p95_ms:10.2f} ms")
    print(f"  p99:                {stats.p99_ms:10.2f} ms")
    print(f"  Max:                {stats.max_ms:10.2f} ms")
    print("=" * 80)


def save_results(stats: BenchmarkStats, filename: str):
    """Save benchmark results to JSON"""
    os.makedirs("benchmarks/results", exist_ok=True)
    filepath = f"benchmarks/results/{filename}"
    
    with open(filepath, 'w') as f:
        json.dump(asdict(stats), f, indent=2)
    
    logging.info(f"Results saved to {filepath}")


# ============================================================================
# Main Entry Point
# ============================================================================

def setup_logging():
    """Configure logging"""
    os.makedirs("benchmarks/logs", exist_ok=True)
    
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    log_file = f"benchmarks/logs/benchmarks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(),
        ]
    )


def main():
    """Run benchmarks"""
    parser = argparse.ArgumentParser(
        description="Component benchmarking for CipherCare",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python component_benchmarks.py --component all --iterations 100
  python component_benchmarks.py --component embedding --iterations 200
  python component_benchmarks.py --component e2e --iterations 50
        """
    )
    
    parser.add_argument(
        "--component",
        choices=["all", "embedding", "search", "llm", "api", "e2e"],
        default="all",
        help="Which component to benchmark (default: all)"
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=100,
        help="Number of iterations per component (default: 100)"
    )
    
    args = parser.parse_args()
    setup_logging()
    
    logging.info(f"Starting benchmark: component={args.component}, iterations={args.iterations}")
    
    all_results = {}
    
    # Run benchmarks
    if args.component in ["all", "embedding"]:
        logging.info("\n>>> Benchmarking Embedding Generation")
        bench = EmbeddingBenchmark()
        results = bench.run(iterations=args.iterations)
        stats = analyze_results(results)
        print_stats(stats)
        save_results(stats, "embedding_results.json")
        all_results["embedding"] = stats
    
    if args.component in ["all", "search"]:
        logging.info("\n>>> Benchmarking Vector Search")
        bench = SearchBenchmark()
        results = bench.run(iterations=args.iterations)
        stats = analyze_results(results)
        print_stats(stats)
        save_results(stats, "search_results.json")
        all_results["search"] = stats
    
    if args.component in ["all", "llm"]:
        logging.info("\n>>> Benchmarking LLM Inference")
        bench = LLMBenchmark()
        results = bench.run(iterations=max(20, args.iterations // 2))
        stats = analyze_results(results)
        print_stats(stats)
        save_results(stats, "llm_results.json")
        all_results["llm"] = stats
    
    if args.component in ["all", "api"]:
        logging.info("\n>>> Benchmarking API Response Time")
        bench = APIBenchmark()
        results = bench.run(iterations=args.iterations)
        stats = analyze_results(results)
        print_stats(stats)
        save_results(stats, "api_results.json")
        all_results["api"] = stats
    
    if args.component in ["all", "e2e"]:
        logging.info("\n>>> Benchmarking End-to-End Query")
        bench = EndToEndBenchmark()
        results = bench.run(iterations=max(20, args.iterations // 2))
        stats = analyze_results(results)
        print_stats(stats)
        save_results(stats, "e2e_results.json")
        all_results["e2e"] = stats
    
    # Print summary
    logging.info("\n" + "=" * 80)
    logging.info("BENCHMARK SUMMARY")
    logging.info("=" * 80)
    for component, stats in all_results.items():
        logging.info(f"{component.upper():15} - p99: {stats.p99_ms:10.2f}ms, p95: {stats.p95_ms:10.2f}ms, success: {stats.success_rate:6.2f}%")


if __name__ == "__main__":
    main()
