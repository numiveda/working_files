# numiVeda Astro Engine — Backup & Recovery Operations

**Server:** Vultr VPS, IP `65.20.75.166`, hostname `trading-agent` (Vultr label: `numiveda-trading-agent`)
**Service:** astro.service (FastAPI/uvicorn on port 8001, 327 endpoints)
**Document version:** 2.0 — updated 2026-05-19 (added GitHub + archive tarball layers)
**Audience:** Whoever has to bring the server back from the dead (you, future ops person, emergency contractor)

---

## TL;DR — If the server just crashed and you're panicking

In order, try these:

1. **Service hung? Restart it.**
   ```bash
   ssh root@65.20.75.166
   systemctl restart astro.service
   curl http://localhost:8001/openapi.json   # should return JSON
   ```

2. **Whole VPS unreachable for >10 min?** Log into Vultr panel → restart server (forced reboot)

3. **VPS is hosed (won't boot)?** Restore from Vultr automatic backup. Vultr panel → Backups tab → Restore. Takes ~10 min.

4. **All Vultr backups corrupt or account compromised?** Three independent recovery paths:
   - **Path A (preferred):** Spin up a fresh Vultr VPS, `git clone git@github.com:numiveda/astro-engine.git /opt/astro`
   - **Path B:** Pull latest tarball from Google Drive (`gdrive:numiveda_backups/astro_vps/daily/`)
   - **Path C:** Restore from the pre-git archive tarball (`gdrive:numiveda_backups/astro_vps/archives/`) — this is the full historical state including patches

Detailed procedures below.

---

## 1. What backup infrastructure exists

You have **six independent backup layers**, each with different characteristics:

### Layer 1 — Vultr Automatic Backups (image-level)

**What:** Full disk image of the VPS, taken automatically by Vultr.
**Where stored:** Vultr's infrastructure (separate from your VPS itself).
**Frequency:** Daily (Vultr's default schedule).
**Retention:** Vultr keeps the most recent 2 automatic backups.
**Cost:** 20% of your VPS monthly price (≈$2-5/mo).
**Restore time:** ~10 minutes — entire OS + configs + code in one operation.
**Restore granularity:** All-or-nothing. You can't restore just one file.
**Status:** ✅ Enabled.
**Access:** Vultr panel → your VPS → Backups tab.

### Layer 2 — Vultr Manual Snapshots (image-level, on-demand)

**What:** Point-in-time disk image, triggered by you.
**Where stored:** Vultr's infrastructure.
**Frequency:** Whenever you trigger one.
**Retention:** Until you delete it.
**Cost:** $0.05/GB/month per snapshot stored (≈$0.50-2/mo for one).
**Restore time:** ~5-10 minutes.
**Existing snapshot:** `pre_playbook_2026_05_19` (taken 2026-05-19 07:37 UTC, before backup playbook started).
**Use case:** Before major operations (deployments, dedup, OS upgrades).
**Access:** Vultr panel → your VPS → Snapshots tab.

### Layer 3 — File-Level Backups (tarballs, local + Google Drive)

**What:** Compressed tarballs of:
- `/opt/astro/` — engine code (now ~78 files, post-cleanup)
- `/etc/systemd/system/astro.service` — service unit
- `/etc/nginx/sites-available/` + `sites-enabled/` — nginx config
- Plus journal logs from the last 7-30 days (depending on tier)

**Where stored:**
- **Local:** `/root/backups/{daily,weekly,monthly}/` on the VPS itself
- **Offsite:** `gdrive:numiveda_backups/astro_vps/{daily,weekly,monthly}/` (Google Drive of `[email protected]`)

**Frequency:**
- Daily at 02:00 UTC (07:30 IST)
- Weekly Sunday at 03:00 UTC (08:30 IST Sunday)
- Monthly day 1 at 04:00 UTC (09:30 IST)

**Retention:**

| Tier | Local VPS | Google Drive |
|---|---|---|
| Daily | 7 days | 14 days |
| Weekly | 28 days | 60 days |
| Monthly | 180 days | 365 days |

**Tarball size:** ~4.2 MB compressed.
**Each backup includes:** `.tar.gz` + `.sha256` checksum + `_state.txt` (system state at time of backup) + `_journal.log` (recent service logs).
**Restore time:** ~2 minutes if VPS is intact; ~30 minutes if migrating to fresh VPS.
**Restore granularity:** Per-file — you can extract any file from any backup.

### Layer 4 — GitHub Source Code Repository

**What:** Version-controlled source code (every commit + history).
**Where stored:** GitHub private repository at `git@github.com:numiveda/astro-engine.git`
**URL (browser):** https://github.com/numiveda/astro-engine
**Visibility:** Private (locked to your account).
**Baseline tag:** `v1.0-f11` (post-F11 hotfix, 2026-05-19, 327 endpoints).
**Frequency:** Whenever you commit + push.
**Retention:** Forever (GitHub's standard).
**Cost:** $0 (GitHub free tier covers unlimited private repos).
**Restore time:** 5 minutes for clone + dependency install on fresh server.
**Restore granularity:** Any commit, any tag, any file at any version.
**Does NOT include:** Swiss Ephemeris data files, `__pycache__`, `.env`, logs, backup snapshots.
**Status:** ✅ Active.
**SSH key:** Stored at `/root/.ssh/id_ed25519` on VPS (added to GitHub account).

### Layer 5 — Pre-Git Archive Tarball (historical lineage)

**What:** Compressed tarball of all the pre-git filesystem-versioned files we cleaned up before initial commit:
- 170 backup snapshots (`main.py.before_*`, `main.py.after_*`, `.PHASE_*_COMPLETE_*`, etc.)
- 69 patch/hotfix scripts (`patch_*.py`, `hotfix_*.py`, `main_patches_*.py`, `preflight_*.py`)
- 2 backup directories (`_backup_hotfix_F11_*`)

**Where stored:** 
- **Google Drive:** `gdrive:numiveda_backups/astro_vps/archives/astro_archive_pre_git_20260519.tar.gz`
- (Also temporarily on VPS at `/root/astro_archive_pre_git_20260519.tar.gz` — can be deleted to save space)

**Tarball size:** 3.7 MB compressed (241 files inside).
**Restore time:** 2-3 minutes (extract specific file as needed).
**Use case:** Forensic — "what did main.py look like before the F4 mundane patch?" Or recover a deleted module pattern. Or roll back to a pre-F11 state.
**Status:** ✅ Stored.
**Cost:** $0 (within Google Drive free tier).

### Layer 6 — Health Monitoring (not strictly backup, but related)

**Local watchdog:** `/usr/local/bin/astro_watchdog.sh` runs every 5 min via cron. Checks services, endpoints, disk, memory, SSL. Alerts via Telegram bot `@numiveda_watchdog_bot` (bot ID `8517086841`) to chat ID `7711160828`. Auto-restarts services on first failure.

**Daily heartbeat:** 09:00 UTC (14:30 IST) — confirms monitoring is alive.

**External uptime monitoring:** UptimeRobot pending setup (catches VPS-level outages local watchdog cannot detect).

---

## 2. File locations cheat sheet

| What | Where on VPS |
|---|---|
| Engine code | `/opt/astro/` (78 items: 76 .py + 2 data dirs + README.md + .gitignore) |
| Git repo metadata | `/opt/astro/.git/` |
| Systemd service unit | `/etc/systemd/system/astro.service` |
| Service override (auto-restart) | `/etc/systemd/system/astro.service.d/override.conf` |
| Nginx site configs | `/etc/nginx/sites-available/`, `/etc/nginx/sites-enabled/` |
| SSL certificates (if any) | `/etc/letsencrypt/live/<domain>/` |
| SSH key (GitHub auth) | `/root/.ssh/id_ed25519` (private, NEVER share) |
| SSH public key | `/root/.ssh/id_ed25519.pub` |
| **Backup tarballs (local)** | `/root/backups/daily/`, `weekly/`, `monthly/` |
| **Backup tarballs (Google Drive)** | `gdrive:numiveda_backups/astro_vps/` |
| **Pre-git archive (local)** | `/root/astro_archive_pre_git_20260519.tar.gz` |
| **Pre-git archive (Google Drive)** | `gdrive:numiveda_backups/astro_vps/archives/` |
| Backup engine script | `/usr/local/bin/astro_backup.sh` |
| Restore script | `/usr/local/bin/astro_restore.sh` |
| Backup status helper | `/usr/local/bin/astro_backup_status.sh` |
| Backup log | `/var/log/astro_backup.log` |
| Watchdog script | `/usr/local/bin/astro_watchdog.sh` |
| Watchdog config (Telegram creds) | `/etc/astro_watchdog.conf` |
| Watchdog log | `/var/log/astro_watchdog.log` |
| Watchdog state (failure counters) | `/var/lib/astro_watchdog/` |
| Cron jobs (root user) | `crontab -l` to view |
| rclone config | `/root/.config/rclone/rclone.conf` |

---

## 3. Verifying the backup system is healthy

### Daily check (30 seconds)

```bash
ssh root@65.20.75.166
/usr/local/bin/astro_backup_status.sh
```

This shows:
- Recent local backups across all tiers
- Recent Google Drive backups across all tiers
- Last 20 lines of backup log
- Active cron schedule

### GitHub repo health check

```bash
cd /opt/astro
git status                              # should show "clean" if nothing uncommitted
git log --oneline -5                    # recent commits
git tag -l                              # tags (v1.0-f11 should be there)
git remote -v                           # origin should show github.com:numiveda/astro-engine.git
```

### What "healthy" looks like

- Local `daily/` has 5-7 recent tarballs (one per day)
- Google Drive `daily/` mirrors that
- Local `weekly/` has 2-4 tarballs (one per Sunday)
- Local `monthly/` has 1-6 tarballs (one per month)
- Backup log shows "Backup complete" entries with sizes matching recent runs
- Cron shows the 3 scheduled jobs
- GitHub repo accessible: `git ls-remote origin` returns refs
- `gdrive:numiveda_backups/astro_vps/archives/` has the pre-git archive tarball

### Warning signs

- Backup log shows tarballs of vastly different sizes (suggests source changed unexpectedly)
- Google Drive entries missing while local entries are present (rclone authentication issue)
- No new backups for 2+ days (cron broken or system clock issue)
- Telegram daily heartbeat at 14:30 IST stopped arriving
- `git status` shows uncommitted changes that should be pushed
- `git push` fails ("permission denied (publickey)") — SSH key issue

### Quarterly drill — test a restore on a scratch VPS

Don't wait for a real emergency to find out your backups don't actually restore. Once a quarter:

1. Spin up a temporary $6/month Vultr instance (Ubuntu 24.04 LTS)
2. Install rclone, copy your rclone config
3. **Method A (GitHub):** `git clone git@github.com:numiveda/astro-engine.git /opt/astro`
4. **Method B (tarball):** `rclone copy gdrive:numiveda_backups/astro_vps/daily/<latest.tar.gz> /tmp/` then extract
5. Install Python deps (uvicorn, fastapi, pyswisseph, etc.)
6. Set up systemd service (copy from extracted `astro.service`)
7. Start service, verify endpoint count = 327
8. **Destroy test VPS** when done

If the drill succeeds, you know backups work. If it fails, you've learned this in a controlled environment, not when production is on fire.

---

## 4. Recovery procedures — by scenario

### Scenario A — Service hung but VPS is reachable

**Symptoms:** SSH works, `systemctl status astro.service` shows running but unresponsive, or shows "failed."

**Recovery:**
```bash
ssh root@65.20.75.166

# Restart the service
systemctl restart astro.service

# Wait a few seconds
sleep 5

# Verify
systemctl status astro.service --no-pager
curl -s http://localhost:8001/openapi.json | head -c 200
```

**Expected:** Service shows "active (running)", curl returns JSON.

**If still broken:** Check logs.
```bash
journalctl -u astro.service --since "10 min ago" --no-pager | tail -50
```

Common causes:
- Python dependency conflict (recent pip update broke something)
- Swiss Ephemeris data file missing
- Port 8001 already in use (zombie process)
- Out of memory

**Recovery time:** 1-2 minutes.

---

### Scenario B — VPS unresponsive but exists in Vultr panel

**Symptoms:** SSH times out, HTTPS unreachable, UptimeRobot alerts, but Vultr panel shows VPS is running.

**Recovery:**

1. Vultr panel → your VPS → **Server Actions** → **Restart**
2. Wait 2-3 minutes for boot
3. SSH back in, verify everything started:
   ```bash
   ssh root@65.20.75.166
   systemctl status astro.service nginx --no-pager
   ```

**If still unresponsive after restart:** Use Vultr's "View Console" (browser-based serial console) to look at boot messages. May need to boot into recovery mode.

**Recovery time:** 5-10 minutes.

---

### Scenario C — VPS won't boot or boot loops

**Symptoms:** Vultr panel shows VPS as running, but console shows boot failures (kernel panic, fsck errors, etc.) or repeated reboots.

**Recovery: Restore from Vultr Automatic Backup**

1. Vultr panel → your VPS → **Backups** tab
2. See list of automatic backups (most recent first)
3. Click **Restore** on the most recent good backup
4. **Important:** Restore is destructive — current disk state is replaced
5. Vultr does the restore (~10 min)
6. VPS reboots from the restored image
7. SSH in, verify:
   ```bash
   ssh root@65.20.75.166
   systemctl status astro.service --no-pager
   curl http://localhost:8001/openapi.json
   ```

**What you lose:** Anything that changed between the backup time and now. For minor losses, you may be able to pull the latest code from GitHub: `cd /opt/astro && git pull origin main`.

**Recovery time:** 10-15 minutes.

---

### Scenario D — Code/config corruption, VPS otherwise fine

**Symptoms:** Service won't start because of code issues (recent deploy broke something, or a config file got mangled).

**Three options, in order of preference:**

**Option D1 — Git revert (fastest, cleanest)**
```bash
ssh root@65.20.75.166
cd /opt/astro

# Roll back to F11 baseline
git checkout v1.0-f11

# Or roll back to a specific recent commit
git log --oneline -10
git checkout <commit-hash>

# Or revert just one file
git checkout v1.0-f11 -- main.py

# Restart
systemctl restart astro.service
```

**Option D2 — File-level restore from local tarball**
```bash
ssh root@65.20.75.166

# See available backups
ls -la /root/backups/daily/

# Dry-run first
/usr/local/bin/astro_restore.sh /root/backups/daily/astro_daily_<date>.tar.gz --dry-run

# Actual restore (requires typing YES)
/usr/local/bin/astro_restore.sh /root/backups/daily/astro_daily_<date>.tar.gz
```

The restore script:
1. Verifies checksum (.sha256 file)
2. Stops `astro.service`
3. Moves current `/opt/astro` to `/opt/astro.pre_restore.<timestamp>` (safety net)
4. Extracts tarball to root filesystem
5. Restarts `astro.service`
6. Verifies endpoint returns 200

**Option D3 — Fresh clone from GitHub**
```bash
ssh root@65.20.75.166
mv /opt/astro /opt/astro.broken
git clone git@github.com:numiveda/astro-engine.git /opt/astro
# Re-add Swiss Ephemeris data files if needed (NOT in git — see Layer 4 note)
systemctl restart astro.service
```

**Recovery time:** 2-3 minutes for Option D1/D3, similar for D2.

---

### Scenario E — Local backups also corrupt/missing

**Symptoms:** Local tarballs gone or corrupt, but Google Drive still has them.

**Recovery: Pull from Google Drive**

```bash
ssh root@65.20.75.166

# Method 1: Use the restore script's --from-gdrive flag
/usr/local/bin/astro_restore.sh --from-gdrive astro_daily_<date>

# Method 2: Manual pull
rclone copy gdrive:numiveda_backups/astro_vps/daily/astro_daily_<date>.tar.gz /tmp/
/usr/local/bin/astro_restore.sh /tmp/astro_daily_<date>.tar.gz
```

To see what's in Google Drive:
```bash
rclone ls gdrive:numiveda_backups/astro_vps/daily/ | sort -k2 -r | head -10
rclone ls gdrive:numiveda_backups/astro_vps/weekly/ | sort -k2 -r | head -10
rclone ls gdrive:numiveda_backups/astro_vps/monthly/ | sort -k2 -r | head -10
rclone ls gdrive:numiveda_backups/astro_vps/archives/                          # pre-git history
```

**Recovery time:** 5 minutes.

---

### Scenario F — Complete VPS loss (account compromise, accidental destroy, Vultr region outage)

**Symptoms:** VPS is gone. Vultr panel doesn't show it. Or you accidentally destroyed it.

**Recovery: Rebuild on a fresh VPS from GitHub + Google Drive**

1. **Provision new VPS in Vultr panel:**
   - Type: Cloud Compute (same tier as old one)
   - OS: Ubuntu 24.04 LTS
   - Add SSH key
   - Enable automatic backups
   - Deploy

2. **SSH into new VPS:**
   ```bash
   ssh root@<NEW_IP>
   ```

3. **Install system dependencies:**
   ```bash
   apt update
   apt install -y python3 python3-pip python3-venv nginx git
   pip3 install --break-system-packages uvicorn fastapi pydantic pyswisseph
   # Other deps as discovered during startup
   ```

4. **Set up SSH key for GitHub (you'll need a new one or restore the existing one):**

   Option a — Generate a fresh key:
   ```bash
   ssh-keygen -t ed25519 -C "[email protected]" -f /root/.ssh/id_ed25519 -N ""
   cat /root/.ssh/id_ed25519.pub
   # Add to GitHub: https://github.com/settings/keys
   ssh -T git@github.com           # type "yes" to fingerprint prompt
   ```

   Option b — If you have the old key backed up (recommended: store key in a password manager):
   ```bash
   mkdir -p /root/.ssh
   # Paste/scp the old id_ed25519 + id_ed25519.pub files into /root/.ssh/
   chmod 600 /root/.ssh/id_ed25519
   chmod 644 /root/.ssh/id_ed25519.pub
   ssh -T git@github.com
   ```

5. **Clone the repo:**
   ```bash
   mkdir -p /opt
   git clone git@github.com:numiveda/astro-engine.git /opt/astro
   cd /opt/astro
   git checkout v1.0-f11           # or HEAD/main for latest
   ```

6. **Install rclone + restore rclone config:**
   ```bash
   curl https://rclone.org/install.sh | sudo bash
   mkdir -p /root/.config/rclone
   # Paste/scp your rclone.conf from password manager / backup
   # OR reconfigure on local machine + scp the conf over
   ```

7. **Restore systemd service file** — it's in the daily backup tarball:
   ```bash
   rclone copy gdrive:numiveda_backups/astro_vps/daily/astro_daily_<latest>.tar.gz /tmp/
   tar -xzf /tmp/astro_daily_<latest>.tar.gz -C / etc/systemd/system/astro.service
   systemctl daemon-reload
   systemctl enable astro.service
   systemctl start astro.service
   ```

8. **Set up nginx config** (also from the daily tarball):
   ```bash
   tar -xzf /tmp/astro_daily_<latest>.tar.gz -C / etc/nginx/
   systemctl reload nginx
   ```

9. **Verify:**
   ```bash
   systemctl status astro.service --no-pager
   curl http://localhost:8001/openapi.json | python3 -c "import sys, json; d=json.load(sys.stdin); print(f'Endpoints: {len(d.get(\"paths\", {}))}')"
   ```
   Expected: 327 endpoints.

10. **DNS cutover** — point your domain at the new IP via DNS provider (Cloudflare etc.)

11. **Re-run backup + watchdog setup** on the new VPS (the original setup scripts you have).

12. **Update UptimeRobot** to point at new IP/domain.

**Recovery time:** 60-90 minutes if you've done it before. 2-3 hours first time.

---

### Scenario G — Need to investigate pre-git history (forensics)

**Symptoms:** You want to know what a specific file looked like at some point in the F1-F11 patch lineage. Or you need to recover a deleted file pattern.

**Recovery: Pull the pre-git archive**

```bash
ssh root@65.20.75.166

# Method 1: Use the local copy (if not deleted)
ls -la /root/astro_archive_pre_git_20260519.tar.gz
tar -tzf /root/astro_archive_pre_git_20260519.tar.gz | grep -i "what_you_need"

# Method 2: Pull from Google Drive
rclone copy gdrive:numiveda_backups/astro_vps/archives/astro_archive_pre_git_20260519.tar.gz /tmp/
tar -tzf /tmp/astro_archive_pre_git_20260519.tar.gz | grep -i "what_you_need"

# Extract a specific historical file
tar -xzf /tmp/astro_archive_pre_git_20260519.tar.gz -C /tmp astro_archive/snapshots/main.py.after_F10P3_rectification_20260518_113407
cat /tmp/astro_archive/snapshots/main.py.after_F10P3_rectification_20260518_113407
```

The archive contains:
- `astro_archive/snapshots/` — 170 backup snapshots (`main.py.before_*`, `.after_*`, etc.)
- `astro_archive/patches/` — 69 patch scripts from F1-F11 hotfix lineage
- `astro_archive/backup_dirs/` — 2 backup directories

**Recovery time:** 2-3 minutes.

---

### Scenario H — Critical config or secret loss (you forgot a password)

**Symptoms:** Service runs but you've lost a credential (database password, API key, etc.).

**Recovery: Extract just one file from a daily backup**

```bash
# Without extracting whole tarball, look inside
tar -tzf /root/backups/daily/astro_daily_<date>.tar.gz | grep -i config

# Extract just one file
tar -xzf /root/backups/daily/astro_daily_<date>.tar.gz \
  -C /tmp \
  opt/astro/main.py

# Inspect it
cat /tmp/opt/astro/main.py | grep -i secret
```

**Recovery time:** 1 minute.

---

## 5. Backup decision tree (which backup to use when)

```
Something's wrong with the engine
│
├── Is the VPS reachable via SSH?
│   │
│   ├── YES → Is the service crashed?
│   │   │
│   │   ├── YES → Recent code change?
│   │   │   ├── YES → Scenario D1 (git checkout v1.0-f11) — fastest
│   │   │   │      OR Scenario D2 (tarball restore)
│   │   │   │      OR Scenario D3 (fresh git clone)
│   │   │   └── NO  → Scenario A (just restart the service)
│   │   │
│   │   └── NO → Endpoints failing?
│   │       └── Scenario A (restart service)
│   │
│   └── NO → Is the VPS shown as running in Vultr panel?
│       │
│       ├── YES → Scenario B (force restart from panel)
│       │
│       └── NO  → Is your Vultr account intact?
│           │
│           ├── YES → Scenario C (restore from Vultr automatic backup)
│           │
│           └── NO  → Scenario F (rebuild on fresh VPS from GitHub + Google Drive)
│
└── Need to investigate historical patch lineage?
    └── Scenario G (pull pre-git archive from Google Drive)
```

---

## 6. Backup ownership & access

**Who can access what:**

- **Vultr panel** — [email protected] login + 2FA (if enabled). This is the single most important credential. Loss = lose all Vultr backups + snapshots + access to VPS.
- **Google Drive backups** — same Gmail account. Folder `numiveda_backups/astro_vps/`.
- **GitHub repository** — `numiveda` account. Repo is private. Loss of account = lose GitHub layer (but tarballs in Google Drive remain).
- **VPS SSH access** — root via SSH key. Loss of SSH key = need to use Vultr's console to add a new one.
- **VPS → GitHub SSH key** — stored at `/root/.ssh/id_ed25519` on VPS. If VPS dies, you can generate a new one on the recovery VPS and add it to GitHub.
- **rclone config** — stored at `/root/.config/rclone/rclone.conf` on VPS. If VPS dies, you need to regenerate this on the recovery VPS (browser auth required, instructions in original playbook).
- **Telegram bot token** — stored in `/etc/astro_watchdog.conf` on VPS. Revocable via @BotFather. Not on the critical recovery path.

**Single points of failure to address:**
- Vultr account access (enable 2FA if not already, save recovery codes offline)
- Google account access (same — 2FA + recovery codes)
- GitHub account access (same — 2FA + recovery codes)
- VPS SSH key (backup the key file in a password manager or encrypted vault)
- VPS → GitHub SSH key (backup the key file in a password manager — without this, the new VPS can't pull from GitHub during recovery)

---

## 7. Cost summary

| Item | Monthly cost |
|---|---|
| Vultr automatic backups | 20% of VPS price (~$2-5) |
| Vultr manual snapshots (keep 1-2 active) | ~$0.50-2.00 |
| Google Drive (free tier, <15 GB) | $0 |
| GitHub private repo (free tier) | $0 |
| UptimeRobot free tier | $0 |
| Telegram | $0 |
| **Total backup + monitoring overhead** | **~$3-7/month** |

For a production engine serving customer-facing reports + integrations, this is essentially the minimum responsible spend on operational safety.

---

## 8. What to do RIGHT NOW after reading this document

(Skip these if already done.)

- [ ] Save Vultr panel login credentials in a password manager
- [ ] Enable 2FA on Vultr account
- [ ] Save Google account credentials in a password manager
- [ ] Enable 2FA on Google account
- [ ] Save GitHub account credentials in a password manager
- [ ] Enable 2FA on GitHub account
- [ ] **Save SSH private key (`/root/.ssh/id_ed25519`) in a password manager or encrypted vault** — without this, GitHub recovery is harder
- [ ] **Save rclone config (`/root/.config/rclone/rclone.conf`) in a password manager or encrypted vault** — without this, Google Drive recovery requires re-authenticating from a machine with a browser
- [ ] Schedule the first quarterly restore drill (calendar reminder for 3 months from today)
- [ ] Bookmark this document somewhere you'll find it during an emergency (not just on the server it's documenting)
- [ ] Print or PDF this document — when the server is down, you may not be able to retrieve it from the server
- [ ] Set up UptimeRobot external monitoring (5 min, browser-only) — see playbook Phase 4b

---

## Appendix A — Useful command quick reference

### Backup & Restore commands

```bash
# Backup status check
/usr/local/bin/astro_backup_status.sh

# Manual backup
/usr/local/bin/astro_backup.sh daily
/usr/local/bin/astro_backup.sh weekly
/usr/local/bin/astro_backup.sh monthly

# Restore (dry-run first!)
/usr/local/bin/astro_restore.sh /root/backups/daily/<file>.tar.gz --dry-run
/usr/local/bin/astro_restore.sh /root/backups/daily/<file>.tar.gz

# Restore from Google Drive
/usr/local/bin/astro_restore.sh --from-gdrive <backup_label>

# Pull pre-git archive (forensics)
rclone copy gdrive:numiveda_backups/astro_vps/archives/astro_archive_pre_git_20260519.tar.gz /tmp/
```

### Git commands (for code-level restore)

```bash
# Inside /opt/astro
cd /opt/astro

# What's the current commit?
git log --oneline -5

# Available tags
git tag -l

# Rollback to F11 baseline
git checkout v1.0-f11

# Rollback single file
git checkout v1.0-f11 -- main.py

# Rollback to specific commit
git checkout <commit-hash>

# Pull latest from GitHub
git pull origin main

# Make changes + commit + push
git add .
git commit -m "Description of change"
git push origin main

# Fresh clone (e.g. on new VPS)
git clone git@github.com:numiveda/astro-engine.git /opt/astro
```

### Watchdog & monitoring

```bash
# Watchdog manual run
/usr/local/bin/astro_watchdog.sh

# Watchdog log
tail -30 /var/log/astro_watchdog.log

# Backup log
tail -30 /var/log/astro_backup.log

# Cron jobs
crontab -l

# Service status
systemctl status astro.service --no-pager

# Service logs
journalctl -u astro.service --since "1 hour ago" --no-pager | tail -50

# Restart service
systemctl restart astro.service

# Test the engine
curl http://localhost:8001/openapi.json | head -c 300

# Endpoint count check
curl -s http://localhost:8001/openapi.json | python3 -c "import sys, json; d=json.load(sys.stdin); print(f'Endpoints: {len(d.get(\"paths\", {}))}')"
```

### Google Drive (via rclone)

```bash
# List daily backups
rclone ls gdrive:numiveda_backups/astro_vps/daily/

# List archives (pre-git history)
rclone ls gdrive:numiveda_backups/astro_vps/archives/

# Copy a backup down
rclone copy gdrive:numiveda_backups/astro_vps/daily/<file> /tmp/

# Storage usage
rclone about gdrive:
```

---

## Appendix B — Setup scripts (in case you need to reinstall)

These scripts live in your local Downloads (and should be saved to a private GitHub repo too):

- `setup_production_backups_gdrive.sh` — sets up the file-level backup system
- `setup_health_monitoring.sh` — sets up the watchdog + Telegram alerts
- `pre_git_cleanup_audit.sh` — read-only audit of pre-git clutter
- `kaaliyo_migration_audit.sh` — for future Kaaliyo migrations (not relevant to current astro VPS)

The playbook document `COMPLETE_SERVER_PLAYBOOK.md` describes how to use all of them in sequence.

---

## Appendix C — Backup layer comparison table

| Layer | Type | Scope | Frequency | Retention | Restore time | Granularity |
|---|---|---|---|---|---|---|
| 1. Vultr Auto Backups | Image | Whole VPS | Daily | 2 backups | ~10 min | All-or-nothing |
| 2. Vultr Manual Snapshots | Image | Whole VPS | On-demand | Until deleted | ~5-10 min | All-or-nothing |
| 3. File-level tarballs (local) | File | `/opt/astro` + configs | Daily/Weekly/Monthly | 7/28/180 days | ~2 min | Per-file |
| 3b. File-level tarballs (GDrive) | File | Same as 3 | Same | 14/60/365 days | ~5 min | Per-file |
| 4. GitHub repo | Versioned source | `/opt/astro` code only | On commit | Forever | ~5 min | Any commit/file |
| 5. Pre-git archive | File | Historical patch lineage | One-shot | Until you delete | ~3 min | Per-file |
| 6. Health monitoring | Detection | Service + endpoints + system | Every 5 min | Real-time | Auto-restart | N/A |

---

## Appendix D — Recovery time targets

| Scenario | Target RTO* | Layers used |
|---|---|---|
| Service crash (single endpoint failing) | 2 min | Layer 6 (auto-restart) |
| Service won't start (recent deploy) | 3 min | Layer 4 (git checkout) |
| Whole VPS unresponsive | 10 min | Layer 1 or 2 (Vultr restore) |
| VPS file corruption | 5 min | Layer 3 or 4 (tarball or git) |
| VPS account loss | 90 min | Layer 4 + 3b (GitHub clone + tarball for configs) |
| Historical forensics | 5 min | Layer 5 (pre-git archive) |

*RTO = Recovery Time Objective

---

**Document end. Save this somewhere you can access without the server.**
