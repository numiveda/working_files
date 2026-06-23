# Tech Handbook T5 — Debugging Runbook

**numiVeda Astro Engine · Internal Reference · v1.0**

When something breaks at 11pm. This doc is for you — present-day or future you, panicking, on a phone, with the production engine misbehaving.

Structured to be **searchable by symptom**, not by theory. Find your symptom in Section 1, jump to the diagnosis.

Companion docs:
- **T1** — Architecture (system topology)
- **T7** — Deployment & operations
- `BACKUP_RECOVERY_OPERATIONS.md` — recovery procedures

---

## 1. Symptom Index

Jump to whichever matches what you're seeing:

- [1.1 Service won't start](#11-service-wont-start)
- [1.2 Service starts but endpoints return 500](#12-service-starts-but-endpoints-return-500)
- [1.3 Specific endpoint(s) return 404](#13-specific-endpoints-return-404)
- [1.4 All endpoints return 401](#14-all-endpoints-return-401)
- [1.5 422 Unprocessable Entity on valid-looking input](#15-422-unprocessable-entity)
- [1.6 Endpoint hangs / times out](#16-endpoint-hangs--times-out)
- [1.7 Wrong values returned](#17-wrong-values-returned)
- [1.8 Memory keeps growing](#18-memory-keeps-growing)
- [1.9 Disk full](#19-disk-full)
- [1.10 Telegram alerts firing constantly](#110-telegram-alerts-firing-constantly)
- [1.11 Backups failing](#111-backups-failing)
- [1.12 Can't SSH in](#112-cant-ssh-in)

---

## 2. The Three-Step Triage

Before diving into specifics, do these in order. They cover 80% of issues.

### Step 1: Is the service running?

```bash
ssh root@65.20.75.166
systemctl status astro.service --no-pager
```

Look for:
- `Active: active (running)` ✅ — service alive, problem is in code/data
- `Active: failed` ❌ — service crashed, look at logs
- `Active: inactive` ❌ — service stopped, restart it

### Step 2: Can it serve a basic request?

```bash
curl -s http://localhost:8001/openapi.json | head -c 200
```

- Returns JSON with `"openapi":"3..."` ✅ — engine is alive and accepting connections
- Connection refused ❌ — service isn't listening on port 8001
- Times out ❌ — service is wedged

### Step 3: What does the journal say?

```bash
journalctl -u astro.service --since "30 min ago" --no-pager | tail -100
```

The latest errors point at the problem. Common patterns:
- `ImportError` → missing Python dependency
- `FileNotFoundError` → missing Swiss Ephemeris data file
- `MemoryError` → ran out of memory
- `Address already in use` → another process on port 8001

If none of the above three steps tell you what's wrong, jump to the specific symptom section.

---

## 3. By-Symptom Diagnostics

### 1.1 Service won't start

```bash
# Confirm it's not running
systemctl status astro.service --no-pager

# Look at startup attempts in journal
journalctl -u astro.service --since "10 min ago" --no-pager

# Try a manual start to see immediate error
systemctl start astro.service
sleep 3
systemctl status astro.service --no-pager
```

**Common causes:**

**(a) Python syntax error in code**
```
File "/opt/astro/main.py", line 4521
    def some_handler(...
                     ^
SyntaxError: ...
```
**Fix:** Either revert to a working commit, or fix the syntax.
```bash
cd /opt/astro
git status                          # see what's uncommitted
git checkout v1.0-f11                # revert to known-good baseline
systemctl restart astro.service
```

**(b) Missing Python module**
```
ModuleNotFoundError: No module named 'pyswisseph'
```
**Fix:** Install missing dep.
```bash
pip install --break-system-packages pyswisseph
systemctl restart astro.service
```

**(c) Port 8001 already in use**
```
[Errno 98] Address already in use
```
**Fix:** Find and kill the zombie.
```bash
ss -tlnp | grep 8001
kill -9 <PID>
systemctl restart astro.service
```

**(d) Permissions issue**
```
PermissionError: [Errno 13] Permission denied: '/opt/astro/...'
```
**Fix:** Restore ownership.
```bash
chown -R trading:trading /opt/astro
systemctl restart astro.service
```

**(e) Swiss Ephemeris data files missing**
```
swisseph.Error: SwissEph file 'sepl_18.se1' not found
```
**Fix:** Restore ephemeris files (they're not in git). Options:
1. Restore from a daily tarball backup
2. Re-download from astro.com/swisseph
3. Restore from Vultr backup

---

### 1.2 Service starts but endpoints return 500

Service is running. Specific endpoint hits = `500 Internal Server Error`.

```bash
# Capture the failing request's stack trace in journal
journalctl -u astro.service --since "10 min ago" --no-pager | grep -A 30 "Internal Server Error"

# Or watch live
journalctl -u astro.service -f
# (in another terminal, retry the request that fails)
```

You'll see a Python traceback. Common patterns:

**(a) KeyError / IndexError in a handler**
```
KeyError: 'd9_sign'
  File "/opt/astro/yogas.py", line 142, in detect_yogas
    sign = chart['lagna']['d9_sign']
```
The handler expects a field that isn't present. Usually means input was missing or a recent patch broke an invariant.

**Fix path:**
1. Save the exact input that triggers it
2. `git log -- yogas.py | head -10` — see recent changes to the module
3. If recent change is suspect: `git revert <commit>` or `git checkout v1.0-f11 -- yogas.py`
4. Restart service
5. File a proper bug fix later

**(b) DivisionByZero / NaN / Math error**
```
ZeroDivisionError: float division by zero
  File "/opt/astro/strength.py", line 287, in shadbala_calc
```
Usually edge case: planet at exact 0° or 30° boundary, midnight = 24:00 issue, polar latitude with no Ascendant.

**Fix:** Patch the edge case in the relevant module.

**(c) Pyswisseph error**
```
swisseph.Error: ayanamsa = ...
```
Usually means an unsupported ayanamsha or date out of ephemeris range.

**Fix:** Check input. If valid, may need to extend ephemeris coverage.

---

### 1.3 Specific endpoint(s) return 404

The endpoint exists in the docs but returns `{"detail":"Not Found"}`.

**Causes:**

**(a) Typo in URL path**
The 16 endpoint docs use `/astro/...` prefix. Make sure you're hitting that exact path including the leading slash.

Verify endpoint exists:
```bash
curl -s http://localhost:8001/openapi.json | jq -r '.paths | keys[]' | grep -i <part-of-endpoint-name>
```

**(b) FastAPI route registration missing**
If a new module was added but never imported into main.py, its endpoints won't exist.

Check:
```bash
grep -n "import.*<module_name>" /opt/astro/main.py
grep -n "from .*<module_name> import" /opt/astro/main.py
```

**(c) Endpoint was removed in a recent commit**
```bash
cd /opt/astro
git log --oneline -- main.py | head -5
git diff HEAD~3 -- main.py | grep "@app.post"
```

---

### 1.4 All endpoints return 401

Authentication failing across the board.

**Diagnostics:**

```bash
# What's the engine using for API key?
ssh root@65.20.75.166
systemctl show astro.service | grep -i environ
# Or check the .env if used
env | grep ASTRO_API_KEY
```

**Common causes:**

**(a) Client sending wrong key**
Check client's env var: `echo $ASTRO_API_KEY`. Compare with engine's expected value.

**(b) Engine env var got cleared**
```bash
# Test with default fallback
curl -X POST http://localhost:8001/astro/chart \
  -H "X-API-Key: numiveda-astro-secret-2026" \
  -H "Content-Type: application/json" \
  -d '{"dob":"1990-04-15","time":"14:30","lat":28.6,"lon":77.2,"timezone":"Asia/Kolkata"}'
```
If this works but the production key doesn't, the env var override was set but is now broken. Inspect systemd unit and `/etc/environment`.

**(c) Header name typo on client**
`x-api-key`, `X-Api-Key`, `X-API-Key` should all work (HTTP headers are case-insensitive). But `X_API_KEY` or `XAPIKey` won't.

---

### 1.5 422 Unprocessable Entity

Pydantic validation rejecting the request.

```bash
# Response includes detail with exact issue
curl -X POST http://localhost:8001/astro/chart \
  -H "X-API-Key: numiveda-astro-secret-2026" \
  -d '{"dob":"1990-04-15"}'
```

Returns something like:
```json
{
  "detail": [
    {"loc":["body","time"], "msg":"field required", "type":"value_error.missing"},
    {"loc":["body","lat"],  "msg":"field required", "type":"value_error.missing"}
  ]
}
```

The `detail` array tells you exactly what's wrong. Fix the client input.

**Common gotchas:**
- `time` sent as `HH:MM:SS` instead of `HH:MM`
- `lat`/`lon` sent as string instead of number
- `dob` in wrong format (DD-MM-YYYY instead of YYYY-MM-DD)
- `timezone` as offset (`+05:30`) instead of IANA name (`Asia/Kolkata`)
- Missing required field

---

### 1.6 Endpoint hangs / times out

Request never returns (or eventually times out).

**Step 1: Is it the engine, or downstream?**

```bash
# Watch what the engine is doing while request is hanging
journalctl -u astro.service -f
# (in another terminal, send the request)
```

If you see the request arrive but no completion log: engine is wedged or thinking really hard.

**Step 2: Common slow endpoints**

These are KNOWN slow:
| Endpoint | Expected | Caveat |
|---|---|---|
| `/rectification/master` | ~1157ms | Can spike to 5-10s under contention |
| `/rectification/event_based` | ~663ms | |
| `/rectification/kp_based` | ~628ms | |
| `/rectification/tattva` | ~206ms | |
| `/rectification/nadi_amshas` | ~109ms | |

Set client timeout to 60s for rectification endpoints.

**Step 3: Check for infinite loops**

```bash
# Top of process
top -bn 1 | head -20
# Or:
ps aux | grep uvicorn
```

If a worker is at 100% CPU for >30s on a request that should be fast, there's a probable infinite loop.

**Recovery:** Restart the service.
```bash
systemctl restart astro.service
```

**Long-term fix:** Reproduce locally with the offending input, debug.

**Step 4: Check thread/process exhaustion**

```bash
# Count current processes
ps -ef | wc -l
# Worker count check
pgrep -c uvicorn
```

Should see 2 uvicorn workers (or whatever `--workers` is set to). If 0, service is dead.

---

### 1.7 Wrong values returned

Service runs, endpoint succeeds (200), but the data is wrong.

**Common causes:**

**(a) Wrong ayanamsha**
Default is Lahiri. If your client sends `ayanamsha: "Raman"`, planet positions shift slightly. Sanity-check.

**(b) Wrong timezone**
Most common. If birth was at "11:00 AM Mumbai" but you send `timezone: "UTC"`, the chart is computed for 11:00 UTC = 4:30 PM IST. Lagna will be completely wrong.

**(c) Wrong lat/lon sign**
Northern/Southern hemisphere mixed up, Eastern/Western longitude swapped.

**(d) Recent patch broke something**

```bash
cd /opt/astro
git log --oneline -- <module>.py | head -10
# Compare current vs previous
git diff HEAD~1 -- <module>.py
```

If recent commit suspect, revert.

**(e) Bug in classical rule implementation**

Cross-check with a manual chart or another astrological tool. If our engine says "Gajakesari Yoga present" but verified sources disagree, the rule may be wrong.

**To investigate:**
- Find the yoga in `yogas_catalog_*.py`
- Check the rule against a classical source (Brihat Parashara Hora Shastra, etc.)
- Fix the rule, commit with reference

---

### 1.8 Memory keeps growing

Worker memory creeping up over time = memory leak.

**Diagnostics:**

```bash
# Watch memory of uvicorn workers
ps aux | grep uvicorn
# Or:
systemctl status astro.service | grep Memory
```

Normal: each worker ~65 MB. If you see 500+ MB and climbing, there's a leak.

**Common causes:**

**(a) Module-level caches growing**
```python
_cache = {}
def some_helper(input):
    if input not in _cache:
        _cache[input] = compute(...)  # never evicted
    return _cache[input]
```
If unique inputs flow through, the cache grows unbounded.

**Fix:** Replace with `functools.lru_cache(maxsize=N)`.

**(b) Logging accumulator**
Some custom logger appending to a list in-memory.

**Fix:** Find it via `grep -rn "append.*log" /opt/astro/`.

**(c) Swiss Ephemeris not releasing data files**
Less common, but pyswisseph holds some state. Worker restart releases.

**Workaround (any leak):** Restart workers periodically.
```bash
# Daily restart via cron (low-traffic time)
echo "0 4 * * * systemctl restart astro.service" | crontab -
```

---

### 1.9 Disk full

```bash
df -h /
```

If `/` is >90% full:

```bash
# Top 20 biggest directories
du -h --max-depth=2 / 2>/dev/null | sort -rh | head -20

# Where logs typically accumulate:
du -sh /var/log/journal/      # systemd journal
du -sh /var/log/astro_backup.log
du -sh /root/backups/         # our backup tarballs
du -sh /opt/astro/__pycache__ # Python cache
```

**Fixes:**

**(a) Journal too large**
```bash
journalctl --vacuum-time=14d           # delete journal older than 14 days
# Or by size:
journalctl --vacuum-size=500M
```

**(b) Old backups not cleaned**
```bash
# Our backup script keeps 7 daily / 28 weekly / 180 monthly
ls -la /root/backups/daily/ | wc -l
# If way more than expected, run cleanup manually:
find /root/backups/daily/ -mtime +7 -delete
find /root/backups/weekly/ -mtime +28 -delete
find /root/backups/monthly/ -mtime +180 -delete
```

**(c) Pycache growing**
```bash
find /opt/astro -name __pycache__ -type d -exec rm -rf {} +
```

**(d) Old archive tarball still around**
```bash
ls -la /root/astro_archive_pre_git_*.tar.gz
# Already pushed to Google Drive, safe to delete local copy
rm -f /root/astro_archive_pre_git_*.tar.gz
# And the unpacked archive dir
rm -rf /root/astro_archive/
```

---

### 1.10 Telegram alerts firing constantly

Watchdog is alerting more than expected.

```bash
# What's it complaining about?
tail -50 /var/log/astro_watchdog.log
```

**Common causes:**

**(a) Wrong endpoint URL in config**
We hit this — `/astro/openapi.json` returns 404 because FastAPI serves at root `/openapi.json`. Fixed in current config:
```bash
grep ENDPOINTS /etc/astro_watchdog.conf
# Should show: ENDPOINTS="http://localhost:8001/openapi.json"
```

If wrong, fix:
```bash
sed -i 's|/astro/openapi.json|/openapi.json|' /etc/astro_watchdog.conf
rm -f /var/lib/astro_watchdog/fail_ep_*
```

**(b) Service genuinely flapping**
The service crashes, restarts, crashes again. Look at:
```bash
journalctl -u astro.service --since "1 hour ago" --no-pager | grep -E "Started|Stopped|Failed"
```

If many cycles, find root cause via Step 1.1 above.

**(c) Disk/memory alarms**
```bash
tail -50 /var/log/astro_watchdog.log | grep -i "disk\|memory"
```

Then handle 1.8 or 1.9 above.

**(d) Telegram bot itself broken**
```bash
source /etc/astro_watchdog.conf
curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getMe"
```

If `{"ok":false}`, token revoked or bot deleted. Create new one via BotFather, update config.

**Temporarily silence:**
```bash
# Disable watchdog cron temporarily
crontab -l | sed '/astro_watchdog/s/^/#/' | crontab -
# Re-enable when fixed:
crontab -l | sed '/astro_watchdog/s/^#//' | crontab -
```

---

### 1.11 Backups failing

```bash
# Recent backup log
tail -100 /var/log/astro_backup.log

# Did cron actually fire?
journalctl -t astro_backup --since "1 day ago" --no-pager
```

**Common causes:**

**(a) rclone authentication expired**
```bash
rclone lsd gdrive:
# If error mentions OAuth, re-authenticate (see playbook Phase 2)
```

**(b) Google Drive full**
```bash
rclone about gdrive:
# Look at "Used" and "Free"
```
Free tier is 15GB. If hit, clear old archives or upgrade Drive.

**(c) Disk full on VPS**
Handle 1.9 above. The backup script needs space to create tarball before uploading.

**(d) Cron not running**
```bash
systemctl status cron
# If inactive:
systemctl start cron
systemctl enable cron
```

---

### 1.12 Can't SSH in

You're locked out of the VPS.

**Recovery paths:**

**(a) Vultr Console**
1. Vultr panel → your VPS → **View Console**
2. Browser-based serial console
3. Log in as root (use the password from Vultr panel — Server Information section)
4. Fix whatever broke SSH (usually `/etc/ssh/sshd_config` mistake, firewall rule, or fail2ban ban)

**(b) Restart from Vultr panel**
If the VM is just hung, Vultr panel → Server Actions → Restart.

**(c) Restore from Vultr backup**
If SSH config is genuinely broken and you can't get console working:
- Vultr panel → Backups → Restore most recent good backup
- Takes ~10 min

**(d) Reset root password**
Vultr panel → your VPS → Settings → there should be a password reset option. Then access via console.

**Common SSH issues:**

```bash
# In Vultr console, check SSH service
systemctl status ssh

# Check firewall — common cause of lockout
ufw status

# If your IP got blocked by fail2ban:
fail2ban-client status sshd
fail2ban-client set sshd unbanip <your-ip>
```

---

## 4. Common Operational Tasks

### Restart the engine cleanly

```bash
systemctl restart astro.service
sleep 5
systemctl is-active astro.service
curl http://localhost:8001/openapi.json | head -c 100
```

### Reload nginx after config change

```bash
nginx -t                # test config
systemctl reload nginx  # reload if test passes
```

### Pull latest code from GitHub

```bash
cd /opt/astro
git status              # ensure clean state
git pull origin main
systemctl restart astro.service
```

### Roll back to F11 baseline

```bash
cd /opt/astro
git stash               # save any uncommitted changes
git checkout v1.0-f11
systemctl restart astro.service

# Verify endpoint count
curl -s http://localhost:8001/openapi.json | python3 -c "import sys, json; d=json.load(sys.stdin); print(f'Endpoints: {len(d.get(\"paths\", {}))}')"
# Should print: Endpoints: 327
```

### Restart specific watchdog or cron

```bash
# Trigger watchdog manually
/usr/local/bin/astro_watchdog.sh

# Trigger backup manually
/usr/local/bin/astro_backup.sh daily

# Reload all cron after edits
systemctl restart cron
```

### Force a fresh ephemeris file location

If Swiss Ephemeris is misbehaving:
```bash
# Find existing .se1 files
find / -name "*.se1" 2>/dev/null | head -10

# Set env var to override
export SE_EPHE_PATH=/path/to/ephe
systemctl restart astro.service
```

---

## 5. Log Locations Cheat Sheet

| Log | Location |
|---|---|
| Engine access + errors | `journalctl -u astro.service` |
| Nginx access | `/var/log/nginx/access.log` |
| Nginx errors | `/var/log/nginx/error.log` |
| Backup script | `/var/log/astro_backup.log` |
| Watchdog | `/var/log/astro_watchdog.log` |
| Cron firings | `journalctl -t astro_backup` or `-t astro_watchdog` |
| SSH attempts | `/var/log/auth.log` |
| Kernel | `dmesg` or `journalctl -k` |

---

## 6. Useful One-Liners

```bash
# Endpoint count
curl -s http://localhost:8001/openapi.json | python3 -c "import sys, json; d=json.load(sys.stdin); print(f'Endpoints: {len(d.get(\"paths\", {}))}')"

# Show all endpoints
curl -s http://localhost:8001/openapi.json | python3 -c "import sys, json; d=json.load(sys.stdin); [print(p) for p in sorted(d.get('paths', {}).keys())]"

# Test a specific endpoint
curl -s -X POST http://localhost:8001/astro/chart \
  -H "X-API-Key: numiveda-astro-secret-2026" \
  -H "Content-Type: application/json" \
  -d '{"dob":"1990-04-15","time":"14:30","lat":28.6,"lon":77.2,"timezone":"Asia/Kolkata"}' \
  | python3 -m json.tool | head -30

# Watch logs live during a test
journalctl -u astro.service -f &
TAIL_PID=$!
# ... run your test ...
kill $TAIL_PID

# Check current request load
journalctl -u astro.service --since "5 min ago" --no-pager | grep "POST /astro" | wc -l

# Find slow endpoints (>1s, search in journal)
journalctl -u astro.service --since "1 hour ago" --no-pager | grep "POST /astro" | tail -50

# Recent errors only
journalctl -u astro.service --since "1 hour ago" --no-pager | grep -E "ERROR|Exception|Traceback" | head -30

# Worker process state
ps aux | grep uvicorn | grep -v grep

# Memory per worker
for pid in $(pgrep -f "uvicorn.*main:app"); do
  ps -o pid,rss,cmd -p $pid
done

# Disk usage breakdown
du -h --max-depth=2 / 2>/dev/null | sort -rh | head -20

# Active TCP connections to engine
ss -an | grep ":8001"
```

---

## 7. Escalation: When to Worry

| Situation | Severity | Action |
|---|---|---|
| 1 endpoint failing intermittently | Low | Log it, investigate when convenient |
| All endpoints returning 500 | High | Restart service, then debug |
| Service in restart loop | High | Stop service, debug from clean state |
| Memory exhausted | Medium | Restart service immediately, schedule fix |
| Disk >95% full | High | Clean up immediately or service crashes |
| Engine unresponsive >5 min | Critical | Restart service, restore from backup if needed |
| Vultr panel inaccessible | Critical | Contact Vultr support, plan failover |
| All backups verified absent | Catastrophic | Stop all changes; investigate before risking more loss |

---

## 8. When You Genuinely Don't Know What's Wrong

Default fallback sequence:

```bash
# 1. Restart everything
systemctl restart astro.service nginx

# 2. Verify
sleep 5
systemctl is-active astro.service nginx
curl http://localhost:8001/openapi.json | head -c 100

# 3. If still broken, roll back to F11 baseline
cd /opt/astro
git stash
git checkout v1.0-f11
systemctl restart astro.service

# 4. If STILL broken, restore from yesterday's backup
/usr/local/bin/astro_restore.sh /root/backups/daily/astro_daily_<yesterday>.tar.gz

# 5. If STILL broken, restore from Vultr image backup
# (Vultr panel → Backups → Restore)
```

Each step is more drastic than the previous. Try least-drastic first.

---

## 9. After the Fire — Postmortem Discipline

When you fix something at 11pm and the engine is healthy again, do this **next morning**:

1. **Write what happened** in a short note. Date, symptom, root cause, fix.
2. **Add the symptom to this doc** if it's not already covered.
3. **Commit any temporary patches** properly to git.
4. **Test the fix didn't break something else** — run smoke tests.
5. **Update monitoring** if the symptom should have been caught earlier.

This prevents the same problem catching you off-guard twice.

---

**End of T5 Debugging Runbook.**
