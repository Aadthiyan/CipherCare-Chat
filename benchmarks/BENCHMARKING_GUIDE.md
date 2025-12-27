# CipherCare Performance Benchmarking Guide
## Comprehensive Testing, Analysis, and Optimization

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Performance Targets](#performance-targets)
4. [Load Testing Scenarios](#load-testing-scenarios)
5. [Component Benchmarking](#component-benchmarking)
6. [Running Tests](#running-tests)
7. [Monitoring & Metrics](#monitoring--metrics)
8. [Results Analysis](#results-analysis)
9. [Troubleshooting](#troubleshooting)
10. [Best Practices](#best-practices)
11. [Optimization Strategies](#optimization-strategies)

---

## Overview

CipherCare's performance benchmarking suite provides comprehensive testing and analysis tools to validate system behavior under various load conditions. The test suite measures:

- **Latency**: Response time at different percentiles (p50, p95, p99)
- **Throughput**: Requests per second and concurrent user capacity
- **Error Rates**: System reliability under load
- **Resource Utilization**: CPU, memory, GPU, and network usage
- **Scalability**: Behavior as load increases
- **Stability**: Consistent performance over extended periods

### Key Components

| Component | Purpose | Target |
|-----------|---------|--------|
| **Locustfile** | Load testing with realistic user behavior | 100+ concurrent users |
| **Component Benchmarks** | Individual component performance | <200ms embedding, <500ms search |
| **Monitoring** | Real-time metrics collection | Prometheus + Grafana |
| **Analysis** | Results interpretation and reporting | HTML reports with visualizations |
| **Profiling** | Code hotspot identification | py-spy flame graphs |

---

## Quick Start

### Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install locust psutil numpy

# Optional: Install profiling tools
pip install py-spy
```

### Run Tests in 5 Minutes

**Windows (PowerShell):**
```powershell
# Warm up system
.\benchmarks\run_performance_tests.ps1 -Scenario warmup

# Run component benchmarks
.\benchmarks\run_performance_tests.ps1 -Scenario components

# Run steady state test
.\benchmarks\run_performance_tests.ps1 -Scenario steady
```

**Linux/macOS (Bash):**
```bash
# Make script executable
chmod +x benchmarks/run_performance_tests.sh

# Run all tests
./benchmarks/run_performance_tests.sh all

# Or run specific scenario
./benchmarks/run_performance_tests.sh steady
```

### View Results

After tests complete:
1. Open `benchmarks/reports/performance_report.html` in browser
2. Check logs: `benchmarks/logs/`
3. Raw results: `benchmarks/results/`

---

## Performance Targets

### Component-Level Targets

| Component | Metric | Target | Notes |
|-----------|--------|--------|-------|
| **Embedding** | p99 latency | <200ms | Single question embedding |
| **Search** | p99 latency | <500ms | 500+ vector database |
| **LLM** | p99 latency | <5s | 100-token response |
| **API** | p99 latency | <100ms | Excluding LLM inference |
| **E2E Query** | p99 latency | <5s | Complete workflow |

### Load Testing Targets

| Metric | Steady State | Peak Load | Stress Test | Sustained |
|--------|--------------|-----------|-------------|-----------|
| **Users** | 5 | 50 | 100 | 20 |
| **Duration** | 10 min | 5 min | 2 min | 1 hour |
| **p95 Latency** | <5s | <7s | Graceful | <5s |
| **Error Rate** | <1% | <2% | Monitored | <1% |
| **CPU Usage** | <60% | <80% | <90% | <70% |
| **Memory** | <50% | <75% | <85% | <70% |
| **Uptime** | 100% | 100% | 100% | ≥99% |

---

## Load Testing Scenarios

### Scenario 1: Steady State (Baseline)

**Configuration:**
- 5 concurrent clinicians
- 10-minute duration
- Realistic think time (1-5 seconds)
- Consistent load throughout

**Expected Behavior:**
- Stable latency around 2-3 seconds
- <1% error rate
- CPU utilization 40-60%
- Memory stable

**Success Criteria:**
✅ p99 latency <5 seconds  
✅ Error rate <1%  
✅ CPU <80%  
✅ No memory leaks  

### Scenario 2: Peak Load

**Configuration:**
- 50 concurrent clinicians
- 5-minute duration
- Ramp up over 1 minute
- Higher request rate

**Expected Behavior:**
- Increased latency (3-5 seconds)
- <2% error rate
- CPU utilization 60-80%
- Memory increases but stable

**Success Criteria:**
✅ p99 latency <7 seconds  
✅ Error rate <2%  
✅ System remains responsive  

### Scenario 3: Stress Test

**Configuration:**
- 100 concurrent clinicians
- Ramp up over 5 minutes
- Hold for 2 minutes
- High sustained load

**Expected Behavior:**
- Higher latencies (5-10 seconds)
- <5% error rate acceptable
- Requests may queue
- Graceful degradation

**Success Criteria:**
✅ System doesn't crash  
✅ Recovers after load reduction  
✅ No cascading failures  

### Scenario 4: Sustained Load

**Configuration:**
- 20 concurrent clinicians
- 1-hour duration
- Realistic user patterns
- Monitor memory over time

**Expected Behavior:**
- Consistent p95 latency <5 seconds
- Flat memory usage over time
- No performance degradation
- Steady error rate <1%

**Success Criteria:**
✅ No memory leaks detected  
✅ p99 latency stable throughout  
✅ Uptime ≥99%  
✅ Error rate consistent  

---

## Component Benchmarking

### Running Component Benchmarks

```bash
# Benchmark all components
python benchmarks/component_benchmarks.py --component all --iterations 100

# Benchmark specific component
python benchmarks/component_benchmarks.py --component embedding --iterations 200
python benchmarks/component_benchmarks.py --component search --iterations 100
python benchmarks/component_benchmarks.py --component llm --iterations 50
python benchmarks/component_benchmarks.py --component api --iterations 100
python benchmarks/component_benchmarks.py --component e2e --iterations 50
```

### Interpreting Results

Each component test produces statistics:

```
BENCHMARK RESULTS: EMBEDDING
========================================================================================
Iterations:           100
Success Rate:         100.00%
Total Duration:       15.23 seconds

Latency Statistics (milliseconds):
  Min:                 45.32 ms
  Median:              82.15 ms
  Mean:                85.43 ms
  StDev:               12.67 ms
  p95:                142.56 ms
  p99:                167.89 ms
  Max:                195.42 ms
========================================================================================
```

**Key Metrics:**
- **Min/Max**: Range of latencies
- **Mean**: Average latency
- **Median (p50)**: 50th percentile
- **p95/p99**: 95th and 99th percentiles (important for user perception)
- **StDev**: Consistency (lower is better)

---

## Running Tests

### Using Run Scripts (Recommended)

**Windows PowerShell:**
```powershell
# Run all tests
.\benchmarks\run_performance_tests.ps1

# Run specific scenario
.\benchmarks\run_performance_tests.ps1 -Scenario steady
.\benchmarks\run_performance_tests.ps1 -Scenario peak
.\benchmarks\run_performance_tests.ps1 -Scenario stress
.\benchmarks\run_performance_tests.ps1 -Scenario sustained

# Custom backend URL
.\benchmarks\run_performance_tests.ps1 -BackendUrl http://192.168.1.100:8000
```

**Linux/macOS Bash:**
```bash
# Run all tests
./benchmarks/run_performance_tests.sh all

# Run specific scenario
./benchmarks/run_performance_tests.sh steady
./benchmarks/run_performance_tests.sh peak
./benchmarks/run_performance_tests.sh stress
./benchmarks/run_performance_tests.sh sustained

# Warm up system first
./benchmarks/run_performance_tests.sh warmup

# Profile components
./benchmarks/run_performance_tests.sh profile
```

### Using Locust Directly

```bash
# Interactive web UI (localhost:8089)
locust -f benchmarks/locustfile.py --host=http://localhost:8000

# Headless mode with specific parameters
locust -f benchmarks/locustfile.py \
  --host=http://localhost:8000 \
  --users=10 \
  --spawn-rate=1 \
  --run-time=5m \
  --headless \
  --csv=benchmarks/results/custom_test
```

---

## Monitoring & Metrics

### Prometheus Setup

1. **Start Prometheus:**
```bash
prometheus --config.file=benchmarks/prometheus.yml
```

2. **Access UI:** http://localhost:9090

3. **Check targets:** Status → Targets

### Grafana Setup

1. **Add Prometheus datasource:**
   - URL: http://localhost:9090
   - Access: Browser

2. **Import dashboard:**
   - Import JSON: `benchmarks/grafana_dashboard.json`

3. **View metrics in real-time**

### Key Metrics to Monitor

| Metric | Query | Target |
|--------|-------|--------|
| Query Latency p95 | `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{endpoint="/query"}[5m]))` | <5s |
| Query Latency p99 | `histogram_quantile(0.99, rate(http_request_duration_seconds_bucket{endpoint="/query"}[5m]))` | <5s |
| Error Rate | `(rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])) * 100` | <1% |
| Throughput | `rate(http_requests_total{endpoint="/query"}[1m])` | ≥2 RPS |
| CPU Usage | `(100 - (avg(irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100))` | <80% |
| Memory Usage | `(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100` | <80% |

---

## Results Analysis

### Automated Analysis

```bash
# Generate HTML report from results
python benchmarks/analyze_results.py \
  --results benchmarks/results \
  --output performance_report.html
```

### Report Contents

The generated report includes:

1. **Executive Summary**
   - Tests run
   - Overall health
   - Key metrics

2. **Performance Summary Table**
   - p95, p99 latencies
   - Error rates
   - Throughput
   - Status (Green/Yellow/Red)

3. **Bottleneck Analysis**
   - Components exceeding targets
   - Error rate spikes
   - Resource constraints

4. **Optimization Recommendations**
   - Specific improvements
   - Priority rankings
   - Estimated impact

5. **Resource Utilization Trends**
   - CPU/Memory over time
   - Peak usage patterns
   - Capacity headroom

6. **Detailed Metrics**
   - Full latency distribution
   - Percentile breakdown
   - Statistical analysis

---

## Troubleshooting

### Common Issues

**Issue: Backend connection refused**
```
❌ Backend is not responding at http://localhost:8000
```

**Solution:**
```bash
# Ensure backend is running
python backend/main.py

# Or check if port is correct
curl http://localhost:8000/health
```

**Issue: Locust not found**
```
locust: command not found
```

**Solution:**
```bash
pip install locust
# Or use python -m
python -m locust -f benchmarks/locustfile.py --host=http://localhost:8000
```

**Issue: Insufficient resources**
```
MemoryError or resource exhaustion during peak load test
```

**Solution:**
- Reduce concurrent users for peak scenario
- Close other applications
- Check available memory: `free -h` (Linux) or Task Manager (Windows)

**Issue: Inconsistent results**
```
Latency varies significantly between runs
```

**Solution:**
- Ensure consistent system state before testing
- Run warm-up scenario first
- Close background processes
- Run multiple times and average results
- Check for thermal throttling: `throttle`

### Debug Mode

Enable verbose logging:

```bash
# Component benchmarks
python benchmarks/component_benchmarks.py --component embedding --iterations 10 -v

# Locust
locust -f benchmarks/locustfile.py --host=http://localhost:8000 --loglevel=DEBUG
```

---

## Best Practices

### Before Testing

1. **System Preparation**
   - Close unnecessary applications
   - Disable sleep/screensaver
   - Ensure stable network
   - Check CPU/memory availability

2. **Baseline Recording**
   - Document hardware specs
   - Record OS and software versions
   - Note any system modifications
   - Create BASELINE_METRICS.yaml entry

3. **Warm-up**
   - Always run warm-up scenario first
   - Allow 5 minutes for system stabilization
   - Initialize connection pools

### During Testing

1. **Monitoring**
   - Watch Grafana dashboard
   - Monitor system resources
   - Check for alerts
   - Note any anomalies

2. **Documentation**
   - Record exact test conditions
   - Note any issues encountered
   - Capture timestamps
   - Monitor thermal conditions

### After Testing

1. **Results Collection**
   - Generate HTML report
   - Review bottleneck analysis
   - Compare to previous baselines
   - Archive results

2. **Analysis**
   - Identify root causes of bottlenecks
   - Prioritize optimizations
   - Plan improvements
   - Estimate impact

3. **Iteration**
   - Implement optimizations
   - Re-test to validate improvements
   - Update baselines
   - Document changes

---

## Optimization Strategies

### Embedding Generation (<200ms target)

**If exceeding target:**

1. **Caching Strategy**
   ```python
   # Cache embeddings for common questions
   @cache(ttl=3600)
   def generate_embedding(text):
       return embedder.generate(text)
   ```

2. **Model Optimization**
   - Use MiniLM instead of full BERT
   - Consider quantization (int8)
   - Batch generation when possible

3. **Infrastructure**
   - Add GPU acceleration
   - Increase inference batch size
   - Use model caching

### Vector Search (<500ms target)

**If exceeding target:**

1. **Indexing**
   ```python
   # Use HNSW or IVF indexing
   index = faiss.IndexIVFFlat(d, nlist, q)
   ```

2. **Database Optimization**
   - Index vector columns
   - Increase connection pool
   - Enable query caching

3. **Query Optimization**
   - Limit search scope (patient-specific)
   - Reduce top-k results if possible
   - Pre-filter before vector search

### LLM Inference (<5s target)

**If exceeding target:**

1. **Model Selection**
   - Use faster model (smaller, distilled)
   - Implement model quantization
   - Use model serving (vLLM, TensorRT)

2. **Batching**
   ```python
   # Batch multiple requests
   responses = llm.batch_generate(prompts, batch_size=8)
   ```

3. **Fallback Strategy**
   ```python
   # Use faster model as fallback
   try:
       response = llm.generate(prompt, model="gpt-4")
   except Timeout:
       response = llm.generate(prompt, model="gpt-3.5-turbo")
   ```

### API Response (<100ms target)

**If exceeding target:**

1. **Caching**
   ```python
   # Cache API responses
   from functools import lru_cache
   @lru_cache(maxsize=1000)
   def query_cache(patient_id, question):
       ...
   ```

2. **Async Processing**
   ```python
   # Async endpoints
   @app.post("/query")
   async def query(request: QueryRequest):
       ...
   ```

3. **Connection Pooling**
   ```python
   # Optimize database connections
   pool = create_pool(min_size=5, max_size=20)
   ```

### Horizontal Scaling

**For >50 concurrent users:**

1. **Load Balancing**
   - Deploy multiple backend instances
   - Use load balancer (nginx, HAProxy)
   - Session affinity if needed

2. **Database Scaling**
   - Read replicas for searches
   - Write replicas for embeddings
   - Connection pooling

3. **Caching Layer**
   - Redis for frequent queries
   - CDN for static content
   - Query result caching

---

## Reporting

### Performance Report Structure

```
performance_report.html (Auto-generated)
├── Executive Summary
├── Performance Summary Table
├── Bottleneck Analysis
├── Optimization Recommendations
├── Resource Utilization
├── Detailed Metrics
├── Key Findings
├── Scaling Recommendations
└── Success Criteria Assessment
```

### Key Metrics in Report

- **Latency Percentiles**: p50, p95, p99
- **Throughput**: Requests per second
- **Error Rates**: By endpoint
- **Resource Usage**: CPU, memory, disk I/O
- **Trends**: Over time during test
- **Health Status**: Green/Yellow/Red

---

## Advanced Topics

### Custom Load Patterns

Edit `benchmarks/locustfile.py` to add custom behavior:

```python
@task(4)  # Weight: 4x more likely
def custom_task(self):
    # Custom test logic
    ...
```

### Performance Profiling

```bash
# Profile with py-spy
py-spy record -o profile.svg -- python benchmarks/component_benchmarks.py --component all

# Analyze flame graph
# Open profile.svg in web browser
```

### Distributed Load Testing

For very high concurrency (>1000 users):

```bash
# Master
locust -f benchmarks/locustfile.py --master --host=http://target

# Workers (on other machines)
locust -f benchmarks/locustfile.py --worker --master-host=master_ip
```

---

## References

- [Locust Documentation](https://docs.locust.io/)
- [Prometheus Monitoring](https://prometheus.io/docs/)
- [Grafana Dashboards](https://grafana.com/grafana/dashboards/)
- [FastAPI Performance](https://fastapi.tiangolo.com/deployment/concepts/)
- [Python Profiling](https://docs.python.org/3/library/profiling.html)

---

## Support & Troubleshooting

For issues or questions:

1. Check [Troubleshooting](#troubleshooting) section
2. Review log files: `benchmarks/logs/`
3. Check Grafana dashboard for anomalies
4. Review generated HTML report

---

**Last Updated**: December 2024  
**Version**: 1.0  
**Maintainer**: CipherCare Team
