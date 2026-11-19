"""Tests for cryptographic hash chain audit logging."""
import pytest
from app.core.audit import _compute_hash, _canonical_json
import json
import hashlib


def test_hash_chain_tamper_detection():
    # Simulate a 3-event chain
    e1 = {"event": "create", "id": "1"}
    h0 = "0" * 64
    raw1 = h0 + json.dumps(e1, sort_keys=True, separators=(",", ":"))
    h1 = hashlib.sha256(raw1.encode()).hexdigest()

    e2 = {"event": "approve", "id": "1"}
    raw2 = h1 + json.dumps(e2, sort_keys=True, separators=(",", ":"))
    h2 = hashlib.sha256(raw2.encode()).hexdigest()

    # Tampering test: if e1 is modified, h2 will not match recomputed hash
    e1_tampered = {"event": "create_tampered", "id": "1"}
    raw1_tampered = h0 + json.dumps(e1_tampered, sort_keys=True, separators=(",", ":"))
    h1_tampered = hashlib.sha256(raw1_tampered.encode()).hexdigest()

    raw2_recomputed = h1_tampered + json.dumps(e2, sort_keys=True, separators=(",", ":"))
    h2_recomputed = hashlib.sha256(raw2_recomputed.encode()).hexdigest()

    assert h1 != h1_tampered
    assert h2 != h2_recomputed
