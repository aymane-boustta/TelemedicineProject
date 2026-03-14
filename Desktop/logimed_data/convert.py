#!/usr/bin/env python3
"""
Logimed database converter: .FIC files → CSV
Converts Conpatient.FIC (patients) and ConBase *.FIC (consultations),
and produces linked_consultations.csv joining patients with consultations.
"""

import csv
import struct
import os
import sys

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(DATA_DIR, "csv_output")


def read_text(record, offset, max_len):
    """Extract null-terminated Latin-1 text from fixed-width field."""
    raw = record[offset:offset + max_len]
    end = raw.find(b'\x00')
    if end >= 0:
        raw = raw[:end]
    return raw.decode('latin-1', errors='replace').strip()


# ─── PATIENTS (Conpatient.FIC) ────────────────────────────────────────────────
# Record layout (685 bytes):
#   0-1    : flags (0xFF 0xFF)
#   2-5    : patient_id (uint32 LE)
#   10-19  : registration_date (DD/MM/YYYY text, 10 chars)
#   61-111 : surname (51 bytes, null-padded)
#   112-162: first_name (51 bytes, null-padded)
#   163-172: date_of_birth (10 chars)
#   265-417: address / insurance code (153 bytes)
#   418-468: contact_name (51 bytes)
#   469-519: insurance_type (51 bytes)
#   520-572: marital_status (53 bytes, Latin-1 incl. accented chars)

PATIENT_RECORD_SIZE = 685
PATIENT_HEADER_SIZE = 2591  # bytes before first record


def parse_patients(fic_path, out_path):
    print(f"Parsing {os.path.basename(fic_path)} …", flush=True)
    with open(fic_path, 'rb') as f:
        data = f.read()

    total = (len(data) - PATIENT_HEADER_SIZE) // PATIENT_RECORD_SIZE
    print(f"  Records found: {total:,}")

    with open(out_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=[
            'patient_id', 'registration_date',
            'surname', 'first_name', 'date_of_birth',
            'address', 'contact_name', 'insurance_type', 'marital_status',
        ])
        writer.writeheader()

        written = 0
        for idx in range(total):
            base = PATIENT_HEADER_SIZE + idx * PATIENT_RECORD_SIZE
            rec = data[base:base + PATIENT_RECORD_SIZE]

            if len(rec) < PATIENT_RECORD_SIZE:
                break

            patient_id = struct.unpack_from('<I', rec, 2)[0]
            reg_date   = read_text(rec, 10, 10)
            surname    = read_text(rec, 61, 51)
            first_name = read_text(rec, 112, 51)
            dob        = read_text(rec, 163, 12)  # may have leading space
            address    = read_text(rec, 265, 153)
            contact    = read_text(rec, 418, 51)
            insurance  = read_text(rec, 469, 51)
            marital    = read_text(rec, 520, 53)

            # Skip completely empty records
            if not surname and not first_name:
                continue

            writer.writerow({
                'patient_id':       patient_id,
                'registration_date': reg_date,
                'surname':          surname,
                'first_name':       first_name,
                'date_of_birth':    dob,
                'address':          address,
                'contact_name':     contact,
                'insurance_type':   insurance,
                'marital_status':   marital,
            })
            written += 1

        print(f"  Written: {written:,} rows → {out_path}")


# ─── CONSULTATIONS (ConBase *.FIC) ────────────────────────────────────────────
# Record layout (1061 bytes):
#   Binary header (16 bytes):
#     0      : 0x40 ('@')
#     1      : day (uint8)
#     2      : month (uint8)
#     3-4    : year (uint16 LE)
#     5-15   : internal metadata (skipped)
#   Content block (1045 bytes):
#     16-271 : chief_complaint (256 bytes, starts with '@', null-padded)
#     272-527: clinical_notes  (256 bytes, null-padded)
#     528-783: prescription    (256 bytes, null-padded)
#     784-1039: duration       (256 bytes, null-padded)
#     1040-1060: binary footer (skipped)

CONSULT_RECORD_SIZE = 1061
CONSULT_HEADER_SIZE = 2709  # default bytes before first record (ConBase T.FIC)
CONSULT_HEADER_SIZES = {
    "ConBase T.FIC":      2709,
    "ConBase MOIS 3.FIC": 2720,
}


def parse_consultations(fic_path, out_path, header_size=None):
    print(f"Parsing {os.path.basename(fic_path)} …", flush=True)
    with open(fic_path, 'rb') as f:
        data = f.read()

    if header_size is None:
        header_size = CONSULT_HEADER_SIZE
    total = (len(data) - header_size) // CONSULT_RECORD_SIZE
    print(f"  Records found: {total:,}")

    with open(out_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=[
            'consultation_date',
            'chief_complaint', 'clinical_notes', 'prescription', 'duration',
        ])
        writer.writeheader()

        written = 0
        for idx in range(total):
            base = header_size + idx * CONSULT_RECORD_SIZE
            rec = data[base:base + CONSULT_RECORD_SIZE]

            if len(rec) < CONSULT_RECORD_SIZE:
                break

            # Binary date header
            day   = rec[1]
            month = rec[2]
            year  = struct.unpack_from('<H', rec, 3)[0]

            if not (1 <= day <= 31 and 1 <= month <= 12 and 1900 <= year <= 2100):
                continue  # malformed date, skip

            consult_date = f"{day:02d}/{month:02d}/{year}"

            # Content fields (at content offsets 0, 257, 513, 769)
            content = rec[16:]
            chief      = read_text(content, 0,   257).lstrip('@').strip()
            notes      = read_text(content, 257, 256)
            prescript  = read_text(content, 513, 256)
            duration   = read_text(content, 769, 256)

            # Skip empty records
            if not chief and not notes and not prescript:
                continue

            writer.writerow({
                'consultation_date': consult_date,
                'chief_complaint':   chief,
                'clinical_notes':    notes,
                'prescription':      prescript,
                'duration':          duration,
            })
            written += 1

        print(f"  Written: {written:,} rows → {out_path}")


# ─── PATIENT–CONSULTATION LINKING ─────────────────────────────────────────────
# Each consultation record has a 21-byte footer at bytes 1040-1060:
#   [0-1]  : 00 10  (flags)
#   [2-3]  : uint16 LE — low 16 bits of NEXT consultation's DB_ID
#   [4-9]  : timestamp / internal
#   [10-13]: uint32 LE — this record's own DB_ID
#   [14-20]: internal
#
# Each patient record has:
#   [673-676]: uint32 LE — DB_ID of patient's first (registered) consultation
#
# Algorithm:
#   1. Build db_id → cidx reverse lookup from all consultation footers
#   2. Collect all "first consultation" DB_IDs from patient records (offset 673)
#   3. Pass 1: directly assign cidx → patient_id for each patient's first consult
#   4. Pass 2: walk each patient's forward-linked chain, assigning unvisited cidx
#      Stop walking when: already visited, DB_ID unknown, or next DB_ID is
#      another patient's first consultation (guards against default next=own+2
#      accidentally crossing into an unrelated patient's records)


def _build_db_to_cidx(cdata, header_size):
    """Return {db_id: cidx} from consultation footer bytes 10-13."""
    crec = CONSULT_RECORD_SIZE
    total = (len(cdata) - header_size) // crec
    db_to_cidx = {}
    for cidx in range(total):
        base = header_size + cidx * crec
        footer = cdata[base + 1040: base + 1061]
        if len(footer) >= 14:
            own_db = struct.unpack_from('<I', footer, 10)[0]
            if own_db > 0:
                db_to_cidx[own_db] = cidx
    return db_to_cidx


def _walk_chain(first_db, db_to_cidx, first_consult_db_ids, crec, cdata, header_size, max_steps=5000):
    """Follow the forward-linked chain starting at first_db; return list of cidx."""
    chain = []
    current_db = first_db
    visited = set()
    for _ in range(max_steps):
        if current_db in visited or current_db not in db_to_cidx:
            break
        visited.add(current_db)
        cidx = db_to_cidx[current_db]
        base = header_size + cidx * crec
        footer = cdata[base + 1040: base + 1061]
        if len(footer) < 14:
            break
        own_db   = struct.unpack_from('<I', footer, 10)[0]
        next_low = struct.unpack_from('<H', footer, 2)[0]
        own_high = own_db >> 16
        own_low  = own_db & 0xffff
        # Reconstruct full 32-bit next DB_ID (handle 16-bit wrap)
        if next_low >= own_low:
            next_full = (own_high << 16) | next_low
        else:
            next_full = ((own_high + 1) << 16) | next_low
        chain.append(cidx)
        if next_full == own_db:
            break  # self-pointer = end of chain
        if next_full in first_consult_db_ids:
            break  # would enter another patient's records
        current_db = next_full
    return chain


def link_consultations(patient_fic, consult_fic, out_path, consult_header_size=None):
    """Write linked_consultations.csv: all consultations with patient_id where known."""
    print(f"Linking patients → consultations …", flush=True)

    with open(patient_fic, 'rb') as f:
        pdata = f.read()
    with open(consult_fic, 'rb') as f:
        cdata = f.read()

    if consult_header_size is None:
        consult_header_size = CONSULT_HEADER_SIZE

    crec  = CONSULT_RECORD_SIZE
    prec  = PATIENT_RECORD_SIZE
    phead = PATIENT_HEADER_SIZE

    total_c = (len(cdata) - consult_header_size) // crec
    total_p = (len(pdata) - phead) // prec
    print(f"  Consultations: {total_c:,}  |  Patients: {total_p:,}")

    # Step 1: db_id → cidx
    db_to_cidx = _build_db_to_cidx(cdata, consult_header_size)

    # Step 2: patient records — collect pid, first_db (offset 673)
    patient_first = {}  # pidx → (patient_id, first_db)
    first_consult_db_ids = set()
    for pidx in range(total_p):
        base = phead + pidx * prec
        prec_data = pdata[base: base + prec]
        if len(prec_data) < prec:
            break
        pid      = struct.unpack_from('<I', prec_data, 2)[0]
        surname  = read_text(prec_data, 61, 51)
        fname    = read_text(prec_data, 112, 51)
        if not surname and not fname:
            continue
        first_db = struct.unpack_from('<I', prec_data, 673)[0]
        patient_first[pidx] = (pid, first_db)
        if first_db > 0:
            first_consult_db_ids.add(first_db)

    # Step 3 + 4: build cidx → patient_id via direct link then chain walk
    cidx_to_pid = {}

    # Pass 1: direct assignment
    for pidx, (pid, first_db) in patient_first.items():
        if first_db and first_db in db_to_cidx:
            cidx = db_to_cidx[first_db]
            if cidx not in cidx_to_pid:
                cidx_to_pid[cidx] = pid

    # Pass 2: chain walking
    for pidx, (pid, first_db) in patient_first.items():
        if not first_db or first_db not in db_to_cidx:
            continue
        chain = _walk_chain(first_db, db_to_cidx, first_consult_db_ids,
                            crec, cdata, consult_header_size)
        for cidx in chain:
            if cidx not in cidx_to_pid:
                cidx_to_pid[cidx] = pid

    linked = sum(1 for v in cidx_to_pid.values() if v)
    print(f"  Linked cidx entries: {linked:,}")

    # Write output
    with open(out_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=[
            'patient_id', 'consultation_date',
            'chief_complaint', 'clinical_notes', 'prescription', 'duration',
        ])
        writer.writeheader()

        written = with_pid = 0
        for cidx in range(total_c):
            base = consult_header_size + cidx * crec
            rec  = cdata[base: base + crec]
            if len(rec) < crec:
                break

            day   = rec[1]
            month = rec[2]
            year  = struct.unpack_from('<H', rec, 3)[0]
            if not (1 <= day <= 31 and 1 <= month <= 12 and 1900 <= year <= 2100):
                continue

            content   = rec[16:]
            chief     = read_text(content, 0,   257).lstrip('@').strip()
            notes     = read_text(content, 257, 256)
            prescript = read_text(content, 513, 256)
            duration  = read_text(content, 769, 256)

            if not chief and not notes and not prescript:
                continue

            pid = cidx_to_pid.get(cidx, '')
            writer.writerow({
                'patient_id':        pid,
                'consultation_date': f"{day:02d}/{month:02d}/{year}",
                'chief_complaint':   chief,
                'clinical_notes':    notes,
                'prescription':      prescript,
                'duration':          duration,
            })
            written += 1
            if pid:
                with_pid += 1

    pct = 100 * with_pid / written if written else 0
    print(f"  Written: {written:,} rows ({with_pid:,} with patient_id, {pct:.1f}%) → {out_path}")


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    # Patients
    patient_fic = os.path.join(DATA_DIR, "Conpatient.FIC")
    if os.path.exists(patient_fic):
        parse_patients(patient_fic, os.path.join(OUT_DIR, "patients.csv"))
    else:
        print(f"Not found: {patient_fic}")

    # Consultations – main archive
    for name, out in [
        ("ConBase T.FIC",     "consultations_all.csv"),
        ("ConBase MOIS 3.FIC","consultations_mois3.csv"),
    ]:
        fic = os.path.join(DATA_DIR, name)
        if os.path.exists(fic):
            hdr = CONSULT_HEADER_SIZES.get(name, CONSULT_HEADER_SIZE)
            parse_consultations(fic, os.path.join(OUT_DIR, out), header_size=hdr)
        else:
            print(f"Skipping (not found): {name}")

    # Linked consultations (ConBase T.FIC × Conpatient.FIC)
    consult_fic = os.path.join(DATA_DIR, "ConBase T.FIC")
    if os.path.exists(patient_fic) and os.path.exists(consult_fic):
        hdr = CONSULT_HEADER_SIZES.get("ConBase T.FIC", CONSULT_HEADER_SIZE)
        link_consultations(
            patient_fic, consult_fic,
            os.path.join(OUT_DIR, "linked_consultations.csv"),
            consult_header_size=hdr,
        )
    else:
        print("Skipping linked_consultations.csv (missing patient or consult file)")

    print("\nDone. Output files are in:", OUT_DIR)


if __name__ == "__main__":
    main()
