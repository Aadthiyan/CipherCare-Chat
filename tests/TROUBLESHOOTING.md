# CipherCare E2E Testing - Troubleshooting Guide

## Quick Reference

### Test Execution Issues

#### Backend Not Responding
**Problem**: Tests fail with "Cannot connect to backend"

**Solution**:
1. Verify backend is running:
   ```bash
   curl http://localhost:8000/health
   ```
2. Start backend if not running:
   ```bash
   python backend/main.py
   ```
3. Check port 8000 is not blocked:
   ```bash
   # Windows
   netstat -ano | findstr :8000
   
   # Unix
   lsof -i :8000
   ```

#### Tests Timeout
**Problem**: "Test execution timed out"

**Solution**:
1. Increase timeout in runner (default: 300s)
   - Edit `run_e2e_tests.py` line ~110
   - Change `timeout=300` to `timeout=600`
2. Check system resources:
   - CPU usage (target: <80%)
   - Memory usage (target: <80%)
3. Kill competing processes
4. Run on quieter system

#### Missing Dependencies
**Problem**: "ModuleNotFoundError" for pytest, requests, etc.

**Solution**:
```bash
pip install pytest requests pytest-asyncio pytest-benchmark
pip install -r requirements.txt
```

---

### Scenario-Specific Issues

#### Scenario 1: Happy Path Fails

**Login fails**:
- Verify test credentials in `conftest.py`
- Check authentication service running
- Clear any cached session tokens

**Query fails**:
- Verify backend has test patient data
- Check embedding service is accessible
- Verify LLM service responding

**Audit log not found**:
- Verify database connection
- Check audit table exists
- Verify audit logging middleware enabled

#### Scenario 2: Access Control Always Passes

**Problem**: 403 should be returned but isn't

**Solution**:
1. Verify RBAC middleware is enabled
2. Check patient-clinician assignment in database
3. Verify test users have different roles
4. Check authentication tokens are separate

#### Scenario 3: Data Security Fails

**Problem**: "Cannot verify encryption"

**Solution**:
1. Verify CyborgDB is running and configured
2. Check encryption keys are loaded
3. Verify vectors are actually encrypted on disk
4. Check vector storage path is correct

**Query returns no results**:
- Verify test embeddings were generated
- Check vector index is populated
- Verify similarity threshold settings

#### Scenario 4: Audit Log Incomplete

**Problem**: Some actions not in audit log

**Solution**:
1. Verify audit logging is enabled in `backend/auth.py`
2. Check all endpoints have logging decorators
3. Verify database commits are happening
4. Check audit table for truncation

#### Scenario 5: Error Handling Doesn't Fail Gracefully

**Problem**: Service crash instead of graceful error

**Solution**:
1. Verify error handlers are in place (`backend/main.py`)
2. Check exception types are caught properly
3. Verify health check endpoint returns 500 when down
4. Test recovery by restarting service

**Cannot restore service**:
- Check for stuck database connections
- Clear any temporary files
- Restart all services cleanly

#### Scenario 6: Safety Guardrails Bypass

**Problem**: Unsafe responses not flagged

**Solution**:
1. Verify safety filters are enabled in `backend/llm.py`
2. Check filter keywords list is comprehensive
3. Verify response is actually checked before return
4. Test with known unsafe prompts first

---

## Performance Issues

### Scenario Runs Very Slowly

**Diagnosis**:
```bash
# Monitor resource usage while running
# Windows
Get-Process python | Select-Object Name, CPU, Memory

# Unix
top -p $(pgrep python)
```

**Solutions**:
1. Reduce concurrent users in stress test
2. Use quick mode: `./run_e2e_tests.sh quick`
3. Check network latency: `ping backend-host`
4. Increase backend server resources

### High Memory Usage

**Problem**: Tests fail with Out of Memory

**Solution**:
1. Clear pytest cache: `pytest --cache-clear`
2. Reduce iterations in component tests
3. Clear test results: `rm -rf tests/results/*`
4. Run scenarios sequentially, not parallel

---

## Database Issues

### "Connection Refused" to CyborgDB

**Check CyborgDB status**:
```bash
# Verify service running
curl http://localhost:19220/health

# Check Docker container (if containerized)
docker ps | grep cyborg
docker logs cyborg
```

**Solutions**:
1. Restart CyborgDB service
2. Check database file permissions
3. Verify connection string in config
4. Check firewall rules

### Audit Log Table Missing

**Verify table exists**:
```sql
SELECT * FROM audit_log LIMIT 1;
```

**Create if missing**:
```sql
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255),
    action VARCHAR(255),
    resource VARCHAR(255),
    result VARCHAR(50),
    timestamp DATETIME,
    details JSON
);
```

---

## Network/Environment Issues

### Cannot Run on Different Machine

**Problem**: Tests pass locally but fail on CI/CD

**Solutions**:
1. Verify backend URL is correct
   ```bash
   export BACKEND_URL="http://ci-backend:8000"
   ./tests/run_e2e_tests.sh all
   ```
2. Check network connectivity between machines
3. Verify firewall allows port 8000
4. Use `--headless` flag for CI environments

### SSL Certificate Errors

**Problem**: "SSL certificate verify failed"

**Solution** (for testing only):
```python
# In test code
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
```

Or use:
```bash
export PYTHONHTTPSVERIFY=0
python -m pytest tests/e2e/
```

---

## Result Analysis Problems

### No HTML Report Generated

**Verify results file exists**:
```bash
ls -la tests/results/e2e_results_*.json
```

**Generate report manually**:
```bash
python tests/analyze_e2e_results.py \
  --results-dir tests/results \
  --results-file e2e_results_latest.json \
  --output tests/results/report.html
```

### Report Shows All Tests Failed

**Likely causes**:
1. Backend was down during tests
2. Test database not populated
3. Authentication failed
4. Configuration mismatch

**Verify recent logs**:
```bash
tail -100 tests/results/e2e_execution.log
```

---

## Platform-Specific Issues

### Windows PowerShell Script Won't Run

**Enable script execution**:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Run with python instead**:
```powershell
python tests/run_e2e_tests.py --backend-url http://localhost:8000
```

### Bash Script Permission Denied

**Make executable**:
```bash
chmod +x tests/run_e2e_tests.sh
```

**Run with bash explicitly**:
```bash
bash tests/run_e2e_tests.sh all
```

---

## Debugging Techniques

### Enable Verbose Logging

```bash
# All platforms
python tests/run_e2e_tests.py --verbose

# Bash
VERBOSE=1 ./tests/run_e2e_tests.sh all

# PowerShell
.\tests\run_e2e_tests.ps1 -Verbose
```

### Capture Screenshots/Videos

```bash
# With browser screenshots
./tests/run_e2e_tests.sh all --screenshots

# In headless mode
./tests/run_e2e_tests.sh all --headless
```

### Run Single Scenario

```bash
# Run only happy path
./tests/run_e2e_tests.sh scenario1

# Run only compliance
./tests/run_e2e_tests.sh scenario4

# Direct pytest
pytest tests/e2e/test_scenario_1_happy_path.py -v
```

### Check Individual Component Health

```bash
# Backend health
curl http://localhost:8000/health

# Embedding service
curl http://localhost:8001/health

# Vector search
curl http://localhost:19220/health

# Authentication
curl -X POST http://localhost:8000/auth/login -d '{"username":"test","password":"test"}'
```

---

## Common Failure Patterns

### All Tests Fail Immediately

**Likely cause**: Backend not running or misconfigured

**Fix**:
```bash
python backend/main.py
# Wait 5 seconds for startup
sleep 5
# Run tests
python tests/run_e2e_tests.py
```

### Tests Pass Locally, Fail on CI

**Likely causes**:
- Different environment variables
- Missing test data
- Network configuration differences

**Fix**:
```bash
# Export all configuration
export BACKEND_URL=...
export DB_CONNECTION=...
export DEBUG=true

# Then run tests
./tests/run_e2e_tests.sh all
```

### Intermittent Failures

**Likely causes**:
- Race conditions in timing
- Database not committed before next test
- Insufficient wait time for async operations

**Fix**:
- Add explicit waits in test code
- Increase timeouts
- Add database commits between scenarios
- Check for async operations not awaited

### Memory Leaks During Long Tests

**Diagnosis**:
```bash
ps aux | grep python  # Check memory growth
```

**Fix**:
- Run sustained test separately
- Clear test cache between runs
- Check for unclosed connections in code
- Increase garbage collection frequency

---

## Getting Help

### View Recent Logs

```bash
# Last 50 lines
tail -50 tests/results/e2e_execution.log

# Search for errors
grep ERROR tests/results/e2e_execution.log
grep FAIL tests/results/e2e_execution.log
```

### Run Test with Debug Info

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Then run tests
pytest tests/e2e/ -vv --tb=long
```

### Test Component in Isolation

```bash
# Test just the API
curl -v http://localhost:8000/api/query -d '{...}'

# Test just authentication
python backend/auth.py --test

# Test just embeddings
python -c "from backend.llm import EmbeddingService; e = EmbeddingService(); print(e.embed('test'))"
```

---

## Prevention & Best Practices

1. **Always check backend health first**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Run quick tests before full suite**
   ```bash
   ./tests/run_e2e_tests.sh quick
   ```

3. **Keep logs for reference**
   ```bash
   cp tests/results/e2e_execution.log tests/results/e2e_execution_backup.log
   ```

4. **Test in isolation before running full suite**
   ```bash
   ./tests/run_e2e_tests.sh scenario1
   ```

5. **Monitor resource usage during tests**
   - CPU should stay <80%
   - Memory should stay <80%
   - No disk space issues

6. **Document any workarounds used**
   - Keep notes on what worked
   - Share with team
   - Update guide with findings

---

## Support Resources

- **Backend Logs**: `backend/logs/`
- **Test Logs**: `tests/results/e2e_execution.log`
- **Configuration**: `backend/config.yaml`, `backend/auth_config.json`
- **Test Code**: `tests/e2e/`
- **API Documentation**: `API_SPEC.md`

---

**Last Updated**: December 2024  
**For Issues**: Check logs, enable verbose mode, run isolated tests, restart services in order: Backend → Database → Tests
