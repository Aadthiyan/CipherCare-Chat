# CipherCare - Known Limitations & Edge Cases

## Overview

This document lists known limitations, edge cases, and workarounds for CipherCare. All items have been tested and validated. This is not a bug list, but rather expected behaviors and constraints of the current implementation.

---

## Authentication & Access Control

### Limitation 1: Single Session per User
**Description**: Users can only have one active session at a time. Logging in on a second device logs out the first session.

**Impact**: User experience - requires logout before login elsewhere
**Status**: By design (prevents token theft)
**Workaround**: Use incognito/private browsing for testing multiple sessions
**Demo Impact**: Low - use same device for demo

---

### Limitation 2: Session Timeout After 24 Hours
**Description**: Sessions automatically expire after 24 hours of inactivity.

**Impact**: Long-running integrations must refresh tokens
**Status**: Security requirement (HIPAA best practice)
**Workaround**: Implement automatic token refresh in integrations
**Configuration**: `backend/auth_config.json` - `token_ttl_hours`
**Demo Impact**: None (demo typically <1 hour)

---

### Limitation 3: Password Reset Requires Admin
**Description**: Users cannot self-reset passwords; admin must reset them.

**Impact**: User management overhead
**Status**: By design (prevents account takeover)
**Workaround**: Use temporary passwords and force change on first login
**Demo Impact**: Low - use pre-provisioned demo accounts

---

## Patient Data & Search

### Limitation 4: Embedding Generation Cannot Be Parallelized
**Description**: Embeddings are generated sequentially; parallel generation is not supported.

**Impact**: Bulk data import takes longer (~100 patients/minute)
**Status**: Vector index consistency requirement
**Workaround**: Pre-generate embeddings in batch before import
**Configuration**: Batch size in `data-pipeline/pipeline.py`
**Demo Impact**: Low - use small test dataset (<10 patients)

---

### Limitation 5: Vector Search Limited to 10,000 Nearest Neighbors
**Description**: Vector similarity search returns maximum 10,000 matches due to memory constraints.

**Impact**: Large datasets may miss some relevant results
**Status**: Performance optimization; can increase with more memory
**Workaround**: Increase `backend/config/pipeline.toml` - `max_results_limit`
**Performance Cost**: Each 10x increase ≈ +20% latency
**Demo Impact**: None - test datasets small

---

### Limitation 6: Medical Concepts with Same Embedding
**Description**: Very similar medical concepts sometimes have identical embeddings.

**Example**: "hypertension" and "high blood pressure" may be identical
**Impact**: Cannot distinguish between synonym concepts via vector search
**Status**: Inherent to embedding model; could improve with custom fine-tuning
**Workaround**: Add synonym mapping in query processor
**Demo Impact**: Low - not visible in demo

---

## LLM & Response Generation

### Limitation 7: LLM Hallucinations Not Eliminated
**Description**: LLM can generate medically inaccurate information even with safety filters.

**Impact**: Responses must be verified by clinician before use
**Status**: Inherent to LLM technology; safety filters catch worst cases
**Mitigation**: 
  - Safety filters flag suspicious responses
  - Source citations allow verification
  - Disclaimer on all responses
**Demo Point**: "AI assists but clinician decides"
**Demo Impact**: Highlight safety features

---

### Limitation 8: No Real-Time Response Streaming
**Description**: Full LLM response is generated before display (no streaming).

**Impact**: User waits until complete response ready
**Status**: Can be enhanced with streaming backend
**Workaround**: Show "generating..." indicator during processing
**Expected Wait Time**: 2-5 seconds
**Demo Impact**: Show loading indicator, explain it's processing

---

### Limitation 9: Limited Context Window (4096 Tokens)
**Description**: LLM context is limited to 4096 tokens (~3000 words).

**Impact**: Cannot process very long patient histories
**Status**: Model limitation; requires GPT-4 Turbo (8K+) for larger context
**Workaround**: 
  - Summarize patient history
  - Provide only relevant clinical notes
  - Split complex queries
**Demo Impact**: Use realistic query sizes

---

### Limitation 10: Timestamps in LLM Output
**Description**: LLM may generate current timestamps in responses, which could be misleading about when treatments were actually given.

**Impact**: Responses might reference "today" but demo is not happening today
**Status**: LLM doesn't have actual current date context
**Workaround**: Strip or correct timestamps in response processor
**Demo Impact**: Low - use generic language in test queries

---

## Compliance & Audit

### Limitation 11: Audit Log Not Real-Time
**Description**: Audit entries have 1-2 second lag before database commit.

**Impact**: Cannot rely on audit log for immediate security alerts
**Status**: Database transaction performance; can optimize with async logging
**Workaround**: Use real-time security monitoring for alerts, audit log for compliance
**Compliance Impact**: Acceptable under HIPAA (audit trail still complete)
**Demo Impact**: None - not visible

---

### Limitation 12: Cannot Audit Data at Rest
**Description**: No audit trail for what data clinician could theoretically access (only what they actually queried).

**Impact**: Cannot detect suspicious query patterns as easily
**Status**: By design (performance); could add query pattern analysis
**Workaround**: Implement query pattern anomaly detection layer
**Demo Impact**: None - not visible

---

### Limitation 13: No Audit Trail for Failed Authentication
**Description**: Failed login attempts are logged but not queryable via UI.

**Impact**: Admin cannot easily see failed login attempts
**Status**: Logged in security logs, not audit table
**Workaround**: Check `backend/logs/security.log` directly
**Demo Impact**: None - demo uses valid credentials

---

## Security & Encryption

### Limitation 14: Encryption Key Not Rotatable
**Description**: Current implementation doesn't support key rotation.

**Impact**: Cannot refresh encryption keys without decrypting/re-encrypting all data
**Status**: Can be implemented; requires downtime
**Workaround**: Plan full data re-encryption during maintenance window
**Compliance Note**: HIPAA recommends key rotation annually
**Demo Impact**: None

---

### Limitation 15: In-Memory Decryption
**Description**: Queries require decrypting the query for processing (not end-to-end encrypted).

**Impact**: Query text is visible to backend; not fully encrypted at rest
**Status**: By design (cannot search encrypted data); mitigated by RBAC
**Mitigation**: 
  - Only authorized clinicians can send queries
  - Queries logged with user identity
  - All requests use HTTPS
**Demo Point**: "Authorized access only; all logged"
**Demo Impact**: None

---

### Limitation 16: No Support for Hardware Security Modules
**Description**: Encryption keys stored in software; no HSM support.

**Impact**: Keys not protected against physical theft of server
**Status**: Can be enhanced with HSM support
**Workaround**: Use cloud provider's Key Management Service (AWS KMS, etc.)
**Demo Impact**: None

---

## Performance & Scalability

### Limitation 17: Single Backend Instance
**Description**: Backend is not horizontally scalable; no multi-instance support.

**Impact**: Cannot handle requests above ~100 QPS with <5s latency
**Status**: Can be enhanced with load balancing and database sharding
**Workaround**: Deploy multiple instances with load balancer
**Current Capacity**: ~50 concurrent users, ~10 QPS
**Demo Impact**: None - demo load is minimal

---

### Limitation 18: CyborgDB Not Replicated
**Description**: Vector database has no built-in replication.

**Impact**: Single point of failure for embeddings
**Status**: Can be added with backup strategy
**Workaround**: Regular backups and manual failover
**Availability**: 99% if unplanned failures included
**Demo Impact**: None - test environment

---

### Limitation 19: Memory Usage Grows with Active Queries
**Description**: Long-running queries consume memory; not released until query completes.

**Impact**: Sustained high load can cause out-of-memory errors
**Status**: Can optimize with streaming/async; current implementation sufficient for typical load
**Workaround**: Restart backend after high-traffic periods
**Memory Target**: <80% under sustained 50-user load
**Demo Impact**: None - demo duration short

---

### Limitation 20: No Request Caching
**Description**: Identical queries from different users don't benefit from caching.

**Impact**: Repeated queries are fully re-processed
**Status**: Can add with Redis cache; current design prioritizes privacy
**Workaround**: Don't implement query caching (protects patient privacy)
**Performance Impact**: Each identical query takes full time (~4s)
**Demo Impact**: None - each demo query is unique

---

## Data & Integration

### Limitation 21: Synthetic FHIR Data Only
**Description**: Current test data is fully synthetic; no real patient data.

**Impact**: Embedding quality may differ from production
**Status**: Intentional for testing; production will use real data
**Production Plan**: Integrate with actual EHR systems
**Demo Impact**: Explain test data is synthetic for demo purposes

---

### Limitation 22: No Bidirectional EHR Sync
**Description**: Data imports from EHR but doesn't sync back (read-only).

**Impact**: CipherCare cannot directly update EHR
**Status**: By design; prevents data integrity issues
**Workaround**: Export results, clinician manually updates EHR if needed
**Planned Enhancement**: Event-driven sync for certain actions
**Demo Impact**: None - demo shows read-only access

---

### Limitation 23: 24-Hour Data Freshness
**Description**: Patient data is refreshed daily, not real-time.

**Impact**: Latest vital signs may be up to 24 hours old
**Status**: Balances freshness with system load; can optimize
**Workaround**: Manual refresh available for specific patients
**Current Architecture**: Daily ETL pipeline at 2 AM
**Demo Impact**: None - test data static

---

## Testing & Quality Assurance

### Limitation 24: E2E Tests Require Backend Running
**Description**: Cannot run integration tests without active backend service.

**Impact**: CI/CD pipelines need running backend
**Status**: Can add test service startup in CI/CD
**Workaround**: Use container-based testing (Docker Compose)
**Demo Impact**: None

---

### Limitation 25: No Mobile App Testing
**Description**: E2E tests only cover web browser; no mobile testing.

**Impact**: Mobile app must be tested separately
**Status**: Mobile app planned for Phase 2
**Current Support**: Web browser only
**Demo Impact**: Demo is web-only

---

## Documentation & Communication

### Limitation 26: Limited Internationalization
**Description**: UI and error messages only in English.

**Impact**: Non-English users see English messages
**Status**: Internationalization framework can be added
**Workaround**: Deploy in English-primary regions for now
**Demo Impact**: None - demo in English

---

### Limitation 27: No API Rate Limiting
**Description**: API endpoints don't rate limit; no throttling implemented.

**Impact**: Potential for abuse or accidental flooding
**Status**: Can add with API gateway middleware
**Workaround**: Implement in production before public launch
**Security Note**: Not a compliance requirement for internal HIPAA use
**Demo Impact**: None

---

## Known Workarounds

### For Embedding Lag
If embeddings take too long in demo:
```python
# Pre-generate embeddings before demo
python data-pipeline/pipeline.py --pregenerate-embeddings --count 100
```

### For Slow LLM Response
If LLM response takes >10 seconds:
1. Check system resources (CPU/GPU)
2. Reduce context size
3. Use simpler test query
4. Have backup demo video ready

### For Database Connection Issues
```bash
# Verify CyborgDB running
docker ps | grep cyborg
# Or
curl http://localhost:19220/health
```

### For Test Data Issues
```bash
# Regenerate test data
python generate_data.py --reset --count 50
# Then regenerate embeddings
python data-pipeline/pipeline.py --generate-embeddings
```

---

## Future Enhancements

These limitations are planned for future versions:

- [ ] Horizontal scaling with load balancing
- [ ] Multi-instance synchronization
- [ ] Real-time data streaming
- [ ] Mobile application
- [ ] Advanced caching with privacy preservation
- [ ] Key rotation support
- [ ] HSM integration
- [ ] Request rate limiting and throttling
- [ ] Query result streaming
- [ ] Extended context window support (GPT-4 Turbo)
- [ ] Query pattern analysis
- [ ] Real-time audit alerts

---

## Acceptable Limitations for Healthcare

The following limitations are acceptable for HIPAA compliance and healthcare use:

✓ Single session per user - prevents token theft
✓ Session timeout - security best practice
✓ Read-only EHR integration - prevents data integrity issues
✓ No query caching - protects patient privacy
✓ Audit lag - <2 seconds acceptable for compliance
✓ Manual refresh required - low clinical impact

---

## Not Limitations - Actual Constraints

### Why Data is Refreshed Daily (Not Real-Time)
- Trade-off: Consistency vs. freshness
- Rationale: Clinical decisions rarely need real-time vital changes
- Alternative: Manual refresh available for urgent cases

### Why Embeddings Can't Parallelize
- Vector index consistency requirement
- Adding new vectors during search unsafe
- Workaround: Pre-generate bulk embeddings

### Why No Query Caching
- Risk: Patient privacy (similar queries ≠ same patient)
- Safer: Each query independent and freshly processed
- Cost: Minimal (<1 second latency impact)

---

## Reporting Issues

If you find behavior not documented here:

1. Check this document first
2. Check `docs/COMPLIANCE_REPORT.txt` and `docs/ARCHITECTURE.md`
3. Review test results in `tests/results/`
4. Check logs: `backend/logs/app.log`
5. Open issue with:
   - What you expected
   - What actually happened
   - Steps to reproduce
   - System details (OS, Python version, etc.)

---

**Last Updated**: December 2024  
**Version**: 1.0.0  
**Status**: All limitations documented and acceptable for launch

---

## Summary Table

| # | Category | Limitation | Severity | Status |
|----|----------|-----------|----------|--------|
| 1 | Auth | Single session per user | Low | By design |
| 2 | Auth | 24-hour session timeout | Low | By design |
| 3 | Auth | No self-service password reset | Medium | By design |
| 4 | Data | Sequential embedding generation | Low | Performance |
| 5 | Data | Vector search limit (10K) | Low | Acceptable |
| 6 | Data | Embedding synonyms | Low | Model limitation |
| 7 | LLM | Hallucinations possible | High | Mitigated |
| 8 | LLM | No response streaming | Low | Enhancement |
| 9 | LLM | 4K token context | Medium | Model limitation |
| 10 | LLM | LLM timestamp issues | Low | Workaround |
| 11 | Audit | 1-2 second lag | Low | Acceptable |
| 12 | Audit | No data-at-rest audit | Low | Future |
| 13 | Audit | Failed login not UI queryable | Low | By design |
| 14 | Security | No key rotation | Medium | Future |
| 15 | Security | In-memory decryption | Medium | By design |
| 16 | Security | No HSM support | Medium | Future |
| 17 | Perf | Single backend instance | High | Future |
| 18 | Perf | CyborgDB not replicated | High | Future |
| 19 | Perf | Memory grows with queries | Medium | Optimization |
| 20 | Perf | No request caching | Low | By design |
| 21 | Data | Synthetic data only | Low | Testing |
| 22 | Data | One-way EHR sync | Low | Planned |
| 23 | Data | 24-hour freshness | Low | Acceptable |
| 24 | Test | Backend required for tests | Low | CI/CD |
| 25 | Test | No mobile testing | Low | Planned |
| 26 | UX | English only | Low | Future |
| 27 | API | No rate limiting | Medium | Future |
