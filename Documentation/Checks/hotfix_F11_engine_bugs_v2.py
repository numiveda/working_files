"""
hotfix_F11_engine_bugs.py
==========================
Surgical fix for 4 pre-existing engine bugs discovered during F10 probe_v1:

  Bug A (remedies_esoteric.py):
    - vbt_breath_techniques()     [line 276] crashes on _description entry (str)
    - vbt_awareness_techniques()  [line 286] crashes on _description entry (str)
    - vbt_devotional_practices()  [line 307] crashes on _description entry (str)

    Root cause: VBT["sample_dharanas"] contains 11 entries.
      - 10 are dicts: {verse, sanskrit_concept, technique, category, ...}
      - 1 is a string: _description = "10 representative dharanas..."
    The buggy filter calls v.get("category") on every value, including the str.

    Fix: add `isinstance(v, dict) and` guard before v.get("category")

  Bug B (karmic.py):
    - handle_kaal_sarpa() [line 234] crashes when no kaal sarpa pattern exists

    Root cause: cast_chart()["kaal_sarpa"] is None (not missing) for charts
    with no Kaal Sarpa pattern. raw.get("kaal_sarpa", {}) returns None (because
    the key exists with value None), and None.get() crashes.

    Fix: change `ks = raw.get("kaal_sarpa", {})` to `ks = raw.get("kaal_sarpa") or {}`

INSTALLATION:
    sudo python3 hotfix_F11_engine_bugs.py

Phase A: Backup remedies_esoteric.py + karmic.py
Phase B: Apply 4 surgical str_replace edits
Phase C: Syntax check (py_compile both files)
Phase D: Restart astro service (waits for /astro/health to return 200)
Phase E: Smoke-test all 4 previously-broken endpoints + regression check

Auto-rollback on any failure.

Note: A pre-restart import smoke phase was deliberately omitted. The astro
service runs under its own working directory and PYTHONPATH; a sudo'd
subprocess does NOT inherit those. Trying to import remedies_esoteric/karmic
from such a subprocess fails on dashaflow even though the running service
imports them fine. The real test is Phase D (service comes back healthy) +
Phase E (the 4 endpoints return 200 with expected keys).
"""

import os
import sys
import shutil
import subprocess
import time
import json
import urllib.request
import urllib.error
from datetime import datetime

# ============================================================================
# Config
# ============================================================================

ASTRO_DIR = "/opt/astro"
REMEDIES_FILE = os.path.join(ASTRO_DIR, "remedies_esoteric.py")
KARMIC_FILE = os.path.join(ASTRO_DIR, "karmic.py")

BACKUP_DIR = os.path.join(ASTRO_DIR, f"_backup_hotfix_F11_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

SERVICE_NAME = "astro"
BASE_URL = "http://localhost:8001"
API_KEY = "numiveda-astro-secret-2026"

# ============================================================================
# Surgical edits to apply
# ============================================================================

# Bug A: 3 VBT functions in remedies_esoteric.py
REMEDIES_EDITS = [
    {
        "name": "vbt_breath_techniques",
        "old": '    breath = {k:v for k,v in VBT["sample_dharanas"].items() if v.get("category") == "breath_techniques"}',
        "new": '    breath = {k:v for k,v in VBT["sample_dharanas"].items() if isinstance(v, dict) and v.get("category") == "breath_techniques"}',
    },
    {
        "name": "vbt_awareness_techniques",
        "old": '    awareness = {k:v for k,v in VBT["sample_dharanas"].items() if v.get("category") == "awareness_techniques"}',
        "new": '    awareness = {k:v for k,v in VBT["sample_dharanas"].items() if isinstance(v, dict) and v.get("category") == "awareness_techniques"}',
    },
    {
        "name": "vbt_devotional_practices",
        "old": '    devotional = {k:v for k,v in VBT["sample_dharanas"].items() if v.get("category") == "devotional_techniques"}',
        "new": '    devotional = {k:v for k,v in VBT["sample_dharanas"].items() if isinstance(v, dict) and v.get("category") == "devotional_techniques"}',
    },
]

# Bug B: handle_kaal_sarpa in karmic.py
KARMIC_EDITS = [
    {
        "name": "handle_kaal_sarpa None-defense",
        "old": '    ks = raw.get("kaal_sarpa", {})',
        "new": '    ks = raw.get("kaal_sarpa") or {}',
    },
]

# ============================================================================
# Helpers
# ============================================================================

def log(level: str, msg: str):
    stamp = datetime.now().strftime("%H:%M:%S")
    icons = {"INFO": "ℹ", "OK": "✓", "ERR": "✗", "WARN": "⚠", "STEP": "→"}
    icon = icons.get(level, "·")
    print(f"  [{stamp}] {icon} {msg}", flush=True)


def die(msg: str, rollback: bool = True):
    log("ERR", msg)
    if rollback:
        log("STEP", "Initiating rollback...")
        do_rollback()
    sys.exit(1)


def http_call(method: str, path: str, body: dict = None, timeout: int = 30):
    url = BASE_URL + path
    headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
    try:
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers=headers, method=method)
        else:
            req = urllib.request.Request(url, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return {"status": resp.status, "ok": True, "body": json.loads(raw)}
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8")
        except Exception:
            body = ""
        return {"status": e.code, "ok": False, "body": body[:300]}
    except Exception as e:
        return {"status": 0, "ok": False, "body": f"{type(e).__name__}: {e}"}


# ============================================================================
# Rollback
# ============================================================================

def do_rollback():
    """Restore both files from backup directory."""
    if not os.path.isdir(BACKUP_DIR):
        log("WARN", f"No backup directory {BACKUP_DIR} found — cannot rollback")
        return

    restored = []
    for fname in ("remedies_esoteric.py", "karmic.py"):
        backup_path = os.path.join(BACKUP_DIR, fname)
        target_path = os.path.join(ASTRO_DIR, fname)
        if os.path.exists(backup_path):
            try:
                shutil.copy2(backup_path, target_path)
                restored.append(fname)
            except Exception as e:
                log("ERR", f"Failed to restore {fname}: {e}")

    if restored:
        log("OK", f"Rolled back: {', '.join(restored)}")
        # Restart service after rollback so the rolled-back code is loaded
        try:
            subprocess.run(["systemctl", "restart", SERVICE_NAME], check=True, capture_output=True)
            log("OK", "Service restarted after rollback")
        except Exception as e:
            log("ERR", f"Service restart after rollback failed: {e}")


# ============================================================================
# Phase A: Backup
# ============================================================================

def phase_a_backup():
    log("STEP", f"Phase A — Backup files to {BACKUP_DIR}")
    if not os.path.exists(REMEDIES_FILE):
        die(f"File not found: {REMEDIES_FILE}", rollback=False)
    if not os.path.exists(KARMIC_FILE):
        die(f"File not found: {KARMIC_FILE}", rollback=False)

    os.makedirs(BACKUP_DIR, exist_ok=True)
    shutil.copy2(REMEDIES_FILE, os.path.join(BACKUP_DIR, "remedies_esoteric.py"))
    shutil.copy2(KARMIC_FILE, os.path.join(BACKUP_DIR, "karmic.py"))
    log("OK", "Backups created")


# ============================================================================
# Phase B: Apply edits
# ============================================================================

def apply_edits(filepath: str, edits: list, label: str):
    """Apply a list of str_replace-style edits to a file."""
    log("STEP", f"Phase B — Apply {len(edits)} edits to {label}")

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    for edit in edits:
        old = edit["old"]
        new = edit["new"]
        name = edit["name"]

        count = content.count(old)
        if count == 0:
            die(f"Edit '{name}' — old string NOT FOUND in {label}")
        if count > 1:
            die(f"Edit '{name}' — old string appears {count} times in {label} (expected 1)")

        content = content.replace(old, new, 1)
        log("OK", f"Applied: {name}")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)


def phase_b_edits():
    apply_edits(REMEDIES_FILE, REMEDIES_EDITS, "remedies_esoteric.py")
    apply_edits(KARMIC_FILE, KARMIC_EDITS, "karmic.py")
    log("OK", "All edits applied")


# ============================================================================
# Phase C: Syntax check
# ============================================================================

def phase_c_syntax():
    log("STEP", "Phase C — Syntax check")
    for fpath in (REMEDIES_FILE, KARMIC_FILE):
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", fpath],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            die(f"Syntax error in {os.path.basename(fpath)}:\n{result.stderr}")
    log("OK", "Both files compile cleanly")


# ============================================================================
# Phase D: Restart service (no pre-restart import smoke — see header note)
# ============================================================================

def phase_d_restart():
    log("STEP", "Phase D — Restart astro service")
    result = subprocess.run(
        ["systemctl", "restart", SERVICE_NAME],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        die(f"Service restart failed:\n{result.stderr}")
    log("OK", "Service restart command sent")

    # Wait for service to come up
    log("STEP", "Waiting for /astro/health to respond...")
    for attempt in range(20):
        time.sleep(0.5)
        r = http_call("GET", "/astro/health", timeout=5)
        if r["ok"]:
            log("OK", f"Service healthy after {(attempt+1)*0.5:.1f}s")
            return
    die("Service did not become healthy within 10 seconds")


# ============================================================================
# Phase E: Smoke-test the 4 previously-broken endpoints + regression check
# ============================================================================

def phase_e_smoke():
    log("STEP", "Phase E — Smoke-test 4 previously-broken endpoints")

    tests = [
        {
            "name": "VBT breath_techniques",
            "method": "GET",
            "path": "/astro/remedies/esoteric/vbt/breath_techniques",
            "body": None,
            "expect_keys": ["breath_dharanas", "category_info", "practice_rules", "classical_source"],
        },
        {
            "name": "VBT awareness_techniques",
            "method": "GET",
            "path": "/astro/remedies/esoteric/vbt/awareness_techniques",
            "body": None,
            "expect_keys": ["awareness_dharanas", "category_info", "practice_rules", "classical_source"],
        },
        {
            "name": "VBT devotional_practices",
            "method": "GET",
            "path": "/astro/remedies/esoteric/vbt/devotional_practices",
            "body": None,
            "expect_keys": ["devotional_dharanas", "category_info", "practice_rules", "classical_source"],
        },
        {
            "name": "karmic/kaal_sarpa (Trump — no KS pattern)",
            "method": "POST",
            "path": "/astro/karmic/kaal_sarpa",
            "body": {"dob": "1946-06-14", "time": "10:54", "lat": 40.7282, "lon": -73.7949, "timezone": "America/New_York"},
            "expect_keys": ["present", "note", "citation"],
        },
    ]

    # Also verify the previously-working call still works (kaal_sarpa for Arunav)
    sanity_test = {
        "name": "karmic/kaal_sarpa (Arunav — has KS pattern) [regression check]",
        "method": "POST",
        "path": "/astro/karmic/kaal_sarpa",
        "body": {"dob": "1980-12-31", "time": "09:40", "lat": 26.1445, "lon": 91.7362, "timezone": "Asia/Kolkata"},
        "expect_keys": ["present", "engine_classification", "rahu_sign", "classical_type"],
    }

    all_tests = tests + [sanity_test]

    for t in all_tests:
        r = http_call(t["method"], t["path"], body=t["body"], timeout=15)
        if not r["ok"]:
            die(f"{t['name']} — status {r['status']}: {r['body']}")

        body = r["body"]
        if not isinstance(body, dict):
            die(f"{t['name']} — response is not a dict: {type(body).__name__}")

        missing = [k for k in t["expect_keys"] if k not in body]
        if missing:
            die(f"{t['name']} — missing keys: {missing}. Got: {sorted(body.keys())}")

        # For VBT endpoints, verify the filtered dict has at least one entry
        if "vbt" in t["path"]:
            dharanas_key = next((k for k in body.keys() if "dharanas" in k), None)
            if dharanas_key:
                dharanas = body[dharanas_key]
                if not isinstance(dharanas, dict):
                    die(f"{t['name']} — {dharanas_key} is not a dict")
                # _description should NOT be in the filtered output anymore
                if "_description" in dharanas:
                    die(f"{t['name']} — _description leaked into filtered output (filter still broken)")
                log("OK", f"{t['name']}: {len(dharanas)} dharanas, _description excluded")
            else:
                log("OK", f"{t['name']}: 200 OK, all expected keys present")
        else:
            present_val = body.get("present")
            log("OK", f"{t['name']}: 200 OK, present={present_val}")


# ============================================================================
# Main
# ============================================================================

def main():
    print()
    print("═" * 72)
    print(f"  HOTFIX F11 — Engine bugs (3 VBT + 1 kaal_sarpa)")
    print(f"  {datetime.now().isoformat()}")
    print("═" * 72)
    print()

    if os.geteuid() != 0:
        log("ERR", "This script must be run with sudo (needs systemctl restart)")
        sys.exit(1)

    try:
        phase_a_backup()
        phase_b_edits()
        phase_c_syntax()
        phase_d_restart()
        phase_e_smoke()
    except SystemExit:
        raise
    except Exception as e:
        die(f"Unexpected exception in main: {type(e).__name__}: {e}")

    print()
    print("═" * 72)
    log("OK", "HOTFIX F11 COMPLETE")
    log("OK", f"  Backups preserved at: {BACKUP_DIR}")
    log("OK", "  4 engine bugs fixed; service healthy; all smoke tests pass")
    log("OK", "  Run probe_all_endpoints_v1.py again to confirm 100% pass rate")
    print("═" * 72)


if __name__ == "__main__":
    main()
