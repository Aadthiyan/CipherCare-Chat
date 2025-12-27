"""Parse clinical_text fields and enrich patient JSON with structured fields.

Creates `*_ready.json` files for each source file found in the `files` list.
"""
import re
import json
import os
from tqdm import tqdm

files = [
    ('mimic_patients_100.json', 'MIMIC-III'),
    ('synthea_patients_221.json', 'Synthea')
]

def extract_sections(text: str):
    sections = {}
    if not text:
        return sections
    # Normalize line endings
    lines = [l.rstrip() for l in text.splitlines()]

    current = None
    buffer = []
    for line in lines:
        s = line.strip()
        if not s:
            continue

        # Section headings heuristics
        heading = None
        if re.match(r'^(Diagnoses|Diagnoses:|Diagnoses\b)', s, re.I):
            heading = 'diagnoses'
        elif re.match(r'^(Medications|Medications:|Medications\b)', s, re.I):
            heading = 'medications'
        elif re.match(r'^(Medications:|Medications List|Meds)\b', s, re.I):
            heading = 'medications'
        elif re.match(r'^(Observations|Labs|Observations:|Clinical Observations)\b', s, re.I):
            heading = 'observations'
        elif re.match(r'^(Allergies|Adverse Reactions)\b', s, re.I):
            heading = 'allergies'
        elif re.match(r'^(Patient ID:|Gender:|Status:|DOB:|Birth|Birth Date|Birthdate)\b', s, re.I):
            heading = 'demographics'

        if heading:
            if current and buffer:
                sections.setdefault(current, []).extend(buffer)
            current = heading
            buffer = []
            # If line contains both heading and content (e.g. "Diagnoses: - A - B")
            parts = re.split(r':\s*', s, maxsplit=1)
            if len(parts) > 1 and parts[1].strip():
                buffer.append(parts[1].strip())
            continue

        # Items often start with '-' or '•'
        if s.startswith('-') or s.startswith('•') or s.startswith('*'):
            item = re.sub(r'^[-•*]\s*', '', s).strip()
            buffer.append(item)
        else:
            # Sometimes items are comma separated in a single line
            if current in ('diagnoses', 'medications') and (',' in s):
                parts = [p.strip() for p in s.split(',') if p.strip()]
                buffer.extend(parts)
            else:
                # free text line - include as-is
                buffer.append(s)

    if current and buffer:
        sections.setdefault(current, []).extend(buffer)

    return sections

def parse_demographics(text: str):
    demo = {}
    if not text:
        return demo
    # Find Gender
    m = re.search(r'Gender:\s*(male|female|other|unknown)', text, re.I)
    if m:
        demo['gender'] = m.group(1).lower()
    # DOB or Birth
    m2 = re.search(r'(Birth Date|DOB|birthDate|Born):\s*([0-9\-/]{4,10})', text, re.I)
    if m2:
        demo['birthDate'] = m2.group(2)
    return demo

def enrich_patient(patient: dict):
    # If already structured, skip heavy changes but still normalize
    text = patient.get('clinical_text') or ''
    sections = extract_sections(text)

    # demographics
    demo = patient.get('demographics', {}) or {}
    demo.update(parse_demographics(text))
    patient['demographics'] = demo

    # conditions
    conds = patient.get('conditions') or []
    if 'diagnoses' in sections and not conds:
        for d in sections.get('diagnoses', []):
            conds.append({'display': d})
    patient['conditions'] = conds

    # medications
    meds = patient.get('medications') or []
    if 'medications' in sections and not meds:
        for m in sections.get('medications', []):
            meds.append({'display': m})
    patient['medications'] = meds

    # observations
    obs = patient.get('observations') or []
    if 'observations' in sections and not obs:
        for o in sections.get('observations', []):
            obs.append({'display': o})
    patient['observations'] = obs

    # allergies
    allergies = patient.get('allergies') or []
    if 'allergies' in sections and not allergies:
        for a in sections.get('allergies', []):
            allergies.append({'display': a})
    if allergies:
        patient['allergies'] = allergies

    return patient


def main():
    for filename, source in files:
        if not os.path.exists(filename):
            print(f"Skipping missing file: {filename}")
            continue

        print(f"Processing {filename} ({source})...")
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # data can be dict of patient_id->patient or list
        if isinstance(data, dict):
            patients = list(data.values())
        else:
            patients = data

        enriched = {}
        for p in tqdm(patients, desc=f"Enriching {filename}"):
            pid = p.get('patient_id') or p.get('id') or p.get('patientId')
            enriched_p = enrich_patient(p)
            if pid:
                enriched[pid] = enriched_p
            else:
                # fallback to name key
                key = p.get('name') or str(len(enriched)+1)
                enriched[key] = enriched_p

        outname = filename.replace('.json', '.ready.json')
        with open(outname, 'w', encoding='utf-8') as out:
            json.dump(enriched, out, indent=2)

        print(f"Wrote enriched file: {outname} ({len(enriched)} patients)")

if __name__ == '__main__':
    main()
