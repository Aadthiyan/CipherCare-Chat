#!/usr/bin/env python3
"""Inspect records in index for patients and print counts + sample metadata."""
from backend.cyborg_lite_manager import get_cyborg_manager


def inspect(patients=None, collection='patient_records'):
    mgr = get_cyborg_manager()
    index = mgr.get_index(collection)
    top_k = 20000
    zero_embedding = [0.0] * 768
    try:
        results = index.query(query_vectors=[zero_embedding], top_k=top_k)
    except Exception as e:
        print('Index query failed:', e)
        return

    # Organize by patient_id
    by_pid = {}
    for rec in results:
        meta = rec.get('metadata', {})
        pid = meta.get('patient_id')
        if not pid:
            continue
        by_pid.setdefault(pid, []).append(meta)

    pids = sorted(by_pid.keys())
    if patients:
        pids = [p for p in pids if p in patients]

    print(f'Total patients in index (found by scan): {len(by_pid)}')
    for pid in pids:
        recs = by_pid[pid]
        print('\n---', pid, f'({len(recs)} records)')
        sample = recs[:3]
        for i, m in enumerate(sample,1):
            # Print a few metadata keys
            keys = list(m.keys())[:8]
            print(f'  Sample {i}:', {k: m.get(k) for k in keys})

if __name__ == '__main__':
    import sys
    # If args passed, treat as patient IDs
    args = sys.argv[1:]
    inspect(patients=args if args else None)
