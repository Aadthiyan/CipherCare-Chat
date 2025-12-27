#!/usr/bin/env python3
"""Smoke test: upsert a single dummy vector for one patient to CyborgDB to verify API key/auth."""
import os
import json
from backend.cyborg_lite_manager import get_cyborg_manager

def main():
    key = os.getenv('CYBORGDB_API_KEY')
    base = os.getenv('CYBORGDB_BASE_URL', 'http://localhost:8002')
    print('Using CYBORGDB_API_KEY:', key)
    print('Base URL:', base)

    mgr = get_cyborg_manager()
    print('Got Cyborg manager')

    # Create a single dummy record for PID-TEST
    patient_id = 'PID-TEST'
    dim = int(os.getenv('EMBEDDING_DIMENSION', '768'))
    dummy_vector = [0.0] * dim

    record = {
        'id': f'{patient_id}_smoke_1',
        'patient_id': patient_id,
        'vector': dummy_vector,
        'metadata': {
            'patient_id': patient_id,
            'record_type': 'smoke_test',
            'display': 'Smoke test record',
            'data_source': 'smoke'
        }
    }

    try:
        print('Attempting batch_upsert of 1 record...')
        result = mgr.batch_upsert([record], collection='patient_records')
        print('batch_upsert result:', result)
    except Exception as e:
        print('batch_upsert failed:', repr(e))

if __name__ == '__main__':
    main()
