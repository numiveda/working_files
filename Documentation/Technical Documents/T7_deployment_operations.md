# Tech Handbook T7 — Deployment & Operations

**numiVeda Astro Engine · Internal Reference · v1.0**

This doc covers how the engine runs in production: systemd, nginx, environment variables, deployment workflows, and routine operations.

Read this when:
- You're deploying a code change
- Setting up a new server (production, staging, replica)
- Configuring nginx / SSL / DNS
- Debugging service-level (not code-level) issues
- Establishing operational procedures

Companion docs:
- **T1** — Architecture overview
- **T5** — Debugging runbook
- `BACKUP_RECOVERY_OPERATIONS.md` — recovery procedures

---

## 1. Current production topology

**Server:** Vultr VPS, Ubuntu 24.04 LTS x64
**IP:** `65.20.75.166`
**Hostname:** `trading-agent` (Vultr label: `numiveda-trading-agent`)
**Service:** `astro.service` (systemd-managed)
**Runtime:** uvicorn + FastAPI, 2 workers, port 8001
**User:** `trading:trading`
**Code location:** `/opt/astro/`
**Memory footprint:** ~131 MB total
**Currently active since:** 2026-05-18 14:10 UTC (F11 hotfix deploy)

---

## 2. systemd unit file

Location: `/etc/systemd/system/astro.service`

```ini
[Unit]
Description=numiVeda Astro Engine
After=network.target

[Service]
Type=simple
User=trading
Group=trading
WorkingDirectory=/opt/astro
ExecStart=/usr/bin/python3 /home/trading/.local/bin/uvicorn main:app \
  --host 0.0.0.0 --port 8001 --workers 2

[Install]
WantedBy=multi-user.target
```

**Override file** at `/etc/systemd/system/astro.service.d/override.conf` adds restart policy:

```ini
[Service]
Restart=on-failure
RestartSec=10s
StartLimitInterval=10min
StartLimitBurst=5
```

This means:
- Service restarts within 10 seconds of any failure
- Up to 5 restarts in 10 minutes
- After that, systemd gives up and waits for manual intervention

### Service management commands

```bash
# Status
systemctl status astro.service --no-pager

# Start / stop / restart
systemctl start astro.service
systemctl stop astro.service
systemctl restart astro.service

# Enable / disable on boot
systemctl enable astro.service
systemctl disable astro.service

# Reload unit file after editing
systemctl daemon-reload

# Logs
journalctl -u astro.service --since "1 hour ago" --no-pager
journalctl -u astro.service -f                    # live tail
journalctl -u astro.service --since today
```

---

## 3. Process model

When `astro.service` starts, the process tree looks like:

```
systemd
  └─ uvicorn (main process)
       ├─ Worker 1 (uvicorn worker process, ~65MB)
       └─ Worker 2 (uvicorn worker process, ~65MB)
```

Each worker is an independent Python process. They share no memory (Python multiprocessing). Requests are load-balanced across workers by the OS / uvicorn supervisor.

### Why 2 workers

- Trade-off: more workers = more concurrency, more memory
- 2 workers handles ~100-200 req/s for medium endpoints
- 4 workers = ~200-400 req/s, 260MB memory

To increase workers:

```bash
# Edit the unit file
nano /etc/systemd/system/astro.service
# Change --workers 2 to --workers 4

systemctl daemon-reload
systemctl restart astro.service
```

For the current load (single-VPS, limited app traffic), 2 workers is appropriate.

---

## 4. Environment variables

### Where env vars come from

Three sources, in priority order:

**(a) `/etc/environment`** (system-wide)
```bash
ASTRO_API_KEY=numiveda-astro-secret-2026
```

**(b) systemd unit Environment directives**
```ini
[Service]
Environment="ASTRO_API_KEY=numiveda-astro-secret-2026"
Environment="ASTRO_DEBUG=false"
```

**(c) Hardcoded fallback in code**
```python
API_KEY = os.getenv("ASTRO_API_KEY", "numiveda-astro-secret-2026")
```

### To set/update env vars

**Option A: Edit systemd unit** (recommended — keeps env per-service)

```bash
nano /etc/systemd/system/astro.service
# Add in [Service] section:
#   Environment="NEW_VAR=value"

systemctl daemon-reload
systemctl restart astro.service
```

**Option B: System-wide via `/etc/environment`**

```bash
echo "NEW_VAR=value" >> /etc/environment
# Then reboot, OR reload via:
source /etc/environment   # only affects current shell
systemctl restart astro.service
```

### Verifying env vars active in service

```bash
systemctl show astro.service | grep -i environment
```

Shows what env vars systemd is passing to the service.

### Known env vars

| Variable | Purpose | Default fallback |
|---|---|---|
| `ASTRO_API_KEY` | X-API-Key auth | `numiveda-astro-secret-2026` |
| `EPHEMERIS_PATH` | Swiss Ephemeris data location | engine-specific |

Search for more: `grep -rn "os.getenv" /opt/astro/`

---

## 5. nginx configuration

If/when nginx is configured to front the engine, the site config goes in `/etc/nginx/sites-available/astro` with a symlink to `/etc/nginx/sites-enabled/astro`.

### Typical nginx site

```nginx
server {
    listen 80;
    server_name api.numiveda.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.numiveda.com;

    ssl_certificate /etc/letsencrypt/live/api.numiveda.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.numiveda.com/privkey.pem;

    # Modern SSL config
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Rate limiting (optional)
    limit_req_zone $binary_remote_addr zone=astro_zone:10m rate=10r/s;

    # Logging
    access_log /var/log/nginx/astro_access.log;
    error_log  /var/log/nginx/astro_error.log;

    # Proxy to uvicorn
    location / {
        limit_req zone=astro_zone burst=20 nodelay;

        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 10s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;          # generous for rectification

        # Buffer
        proxy_buffering off;             # for streaming responses
        client_max_body_size 1M;         # input payload limit
    }
}
```

### Nginx management

```bash
# Test config before reloading
nginx -t

# Reload (zero downtime if test passes)
systemctl reload nginx

# Full restart (brief downtime, usually not needed)
systemctl restart nginx

# Status
systemctl status nginx --no-pager

# Logs
tail -50 /var/log/nginx/astro_access.log
tail -50 /var/log/nginx/astro_error.log
```

### Currently

The engine is reachable directly at `http://65.20.75.166:8001`. Nginx with TLS isn't required for internal use, but recommended for production-facing URLs. Setting it up = ~20 min including certbot for SSL.

---

## 6. SSL with Let's Encrypt

If/when you set up a public URL:

```bash
# Install certbot
apt install -y certbot python3-certbot-nginx

# Get cert + auto-configure nginx
certbot --nginx -d api.numiveda.com

# Test renewal
certbot renew --dry-run

# Auto-renewal is set up by default (systemd timer)
systemctl status certbot.timer
```

Cert renews every 60 days automatically. Watchdog alerts if expiry approaches.

---

## 7. UFW firewall

```bash
# Status
ufw status verbose

# Standard rules for this engine
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp                  # SSH
ufw allow 80/tcp                  # HTTP (for cert renewal + redirect)
ufw allow 443/tcp                 # HTTPS

# Engine itself stays internal — DON'T open 8001 externally
# (It's only accessible because there's currently no firewall rule blocking it.
#  When nginx is configured, block 8001 from external traffic:)
#   ufw deny 8001/tcp

ufw enable
```

---

## 8. Cron jobs in production

Current cron schedule (`crontab -l`):

```
# numiVeda Astro Engine backups
0 2 * * * /usr/local/bin/astro_backup.sh daily   2>&1 | logger -t astro_backup
0 3 * * 0 /usr/local/bin/astro_backup.sh weekly  2>&1 | logger -t astro_backup
0 4 1 * * /usr/local/bin/astro_backup.sh monthly 2>&1 | logger -t astro_backup

# Watchdog
*/5 * * * * /usr/local/bin/astro_watchdog.sh 2>&1 | logger -t astro_watchdog
```

Times are UTC. In IST (UTC+5:30):
- Daily backup: 07:30 IST
- Weekly backup: Sun 08:30 IST
- Monthly backup: Day 1, 09:30 IST
- Watchdog: every 5 min (24/7)

### Cron management

```bash
# View
crontab -l

# Edit
crontab -e

# Verify cron daemon is running
systemctl status cron

# Watch cron firing
journalctl -t astro_backup -t astro_watchdog -f
```

---

## 9. Deployment workflows

### Workflow A: Edit on VPS, commit, push

Current default. For solo work.

```bash
ssh root@65.20.75.166
cd /opt/astro

# Make changes (e.g. fix a bug)
nano <module>.py

# Test
systemctl restart astro.service
curl http://localhost:8001/astro/<endpoint>  # verify works

# Commit + push
git add .
git status   # review what changed
git commit -m "Description of change"
git push origin main
```

### Workflow B: Edit locally, push, VPS pulls

For multi-developer / safer testing.

```bash
# On dev machine
git clone git@github.com:numiveda/astro-engine.git
cd astro-engine

# Make changes, test locally (if you have a local dev env)
git add .
git commit -m "Description"
git push origin main

# On VPS
ssh root@65.20.75.166
cd /opt/astro
git pull origin main
systemctl restart astro.service

# Verify
curl http://localhost:8001/openapi.json | head -c 200
```

### Workflow C: Feature branch + merge

For risky / experimental changes.

```bash
# Dev machine
git checkout -b feature/new-yoga-detection
# ... make changes ...
git commit -am "Add new yoga detection rule"
git push -u origin feature/new-yoga-detection

# Test the feature branch on staging if available
# OR deploy to VPS for testing:
ssh root@65.20.75.166
cd /opt/astro
git fetch origin
git checkout feature/new-yoga-detection
systemctl restart astro.service
# ... test ...

# If good: merge to main
git checkout main
git merge feature/new-yoga-detection
git push origin main

# On VPS: pull latest main
git checkout main
git pull origin main
systemctl restart astro.service
```

### Pre-deploy checklist

Before any deploy:

- [ ] Code committed and pushed to GitHub
- [ ] Backup is up-to-date (`/usr/local/bin/astro_backup.sh daily`)
- [ ] If risky: take a Vultr manual snapshot
- [ ] Have a rollback plan: `git checkout v1.0-f11`

### Post-deploy verification

```bash
systemctl status astro.service --no-pager | head -10

# Endpoint count
curl -s http://localhost:8001/openapi.json | python3 -c "import sys, json; d=json.load(sys.stdin); print(f'Endpoints: {len(d.get(\"paths\", {}))}')"
# Expected: 327 (or 328 if you added an endpoint, etc.)

# Smoke test a known endpoint
curl -s -X POST http://localhost:8001/astro/chart \
  -H "X-API-Key: numiveda-astro-secret-2026" \
  -H "Content-Type: application/json" \
  -d '{"dob":"1990-04-15","time":"14:30","lat":28.6,"lon":77.2,"timezone":"Asia/Kolkata"}' \
  | python3 -m json.tool | head -20
```

### Rollback procedure

If a deploy breaks something:

```bash
# Fast: revert to F11 baseline
cd /opt/astro
git stash               # if you have uncommitted changes
git checkout v1.0-f11
systemctl restart astro.service

# Verify
curl -s http://localhost:8001/openapi.json | python3 -c "import sys, json; d=json.load(sys.stdin); print(f'Endpoints: {len(d.get(\"paths\", {}))}')"

# Then debug what went wrong on a non-prod branch
```

---

## 10. Setting up a new server (full provisioning)

If you ever need to spin up a fresh VPS (replica, replacement, staging):

### Step 1: Provision Vultr VPS

In Vultr panel:
- Type: Cloud Compute, Regular Performance or AMD High Performance
- Location: Mumbai (low latency for IN-based users)
- OS: Ubuntu 24.04 LTS
- Server Size: $24-40/month tier
- Add SSH key
- Enable Automatic Backups
- Hostname: `astro-engine-prod-2` or similar
- Deploy

### Step 2: Initial hardening

```bash
ssh root@<NEW_IP>

# Update system
apt update && apt upgrade -y

# Install basics
apt install -y python3 python3-pip python3-venv nginx git curl ufw fail2ban

# Configure firewall
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable

# Create user
adduser trading
# (note: skip password, use SSH keys)

# fail2ban
systemctl enable --now fail2ban
```

### Step 3: Install Python deps

```bash
pip install --break-system-packages fastapi uvicorn pyswisseph pytz
# Add any other deps from requirements (when documented)
```

### Step 4: Set up SSH key for GitHub

```bash
ssh-keygen -t ed25519 -C "[email protected]" -f /root/.ssh/id_ed25519 -N ""
cat /root/.ssh/id_ed25519.pub
# Add to GitHub: https://github.com/settings/keys

ssh -T git@github.com
# Expected: "Hi numiveda! You've successfully authenticated..."
```

### Step 5: Clone the repo

```bash
mkdir -p /opt
git clone git@github.com:numiveda/astro-engine.git /opt/astro
cd /opt/astro
git checkout v1.0-f11   # or main
```

### Step 6: Restore Swiss Ephemeris data files

These aren't in git. Three options:

(a) Copy from old VPS:
```bash
# From OLD VPS
scp /opt/astro/*.se1 root@<NEW_IP>:/opt/astro/
```

(b) From the daily backup tarball:
```bash
# On new VPS
rclone copy gdrive:numiveda_backups/astro_vps/daily/<latest>.tar.gz /tmp/
tar -xzf /tmp/<latest>.tar.gz -C / opt/astro/*.se1
```

(c) Fresh download from Swiss Ephemeris official source.

### Step 7: Create systemd unit

```bash
cat > /etc/systemd/system/astro.service << 'EOF'
[Unit]
Description=numiVeda Astro Engine
After=network.target

[Service]
Type=simple
User=trading
Group=trading
WorkingDirectory=/opt/astro
ExecStart=/usr/bin/python3 /home/trading/.local/bin/uvicorn main:app \
  --host 0.0.0.0 --port 8001 --workers 2

[Install]
WantedBy=multi-user.target
EOF

mkdir -p /etc/systemd/system/astro.service.d
cat > /etc/systemd/system/astro.service.d/override.conf << 'EOF'
[Service]
Restart=on-failure
RestartSec=10s
StartLimitInterval=10min
StartLimitBurst=5
EOF

systemctl daemon-reload
systemctl enable --now astro.service
```

### Step 8: Verify

```bash
systemctl status astro.service --no-pager | head -10
curl -s http://localhost:8001/openapi.json | python3 -c "import sys, json; d=json.load(sys.stdin); print(f'Endpoints: {len(d.get(\"paths\", {}))}')"
# Should print: Endpoints: 327
```

### Step 9: Set up backups + monitoring

Re-run the setup scripts from earlier sessions:
- `setup_production_backups_gdrive.sh` — daily/weekly/monthly tarballs to Google Drive
- `setup_health_monitoring.sh` — Telegram watchdog + auto-restart

(Both scripts need fresh rclone config + Telegram bot token configured.)

### Step 10: Configure nginx + SSL

```bash
# Get nginx config from old server or recreate (see Section 5)
# Then:
certbot --nginx -d <your-domain>
```

### Step 11: DNS cutover

In Cloudflare (or wherever DNS is hosted):
- A record for your domain → new IP
- Wait for propagation (5-30 min)

### Step 12: Smoke test from external

```bash
# From any external machine
curl https://<your-domain>/openapi.json | head -c 200
```

### Step 13: Decommission old server

After 7 days of stable new server:
- Take final Vultr snapshot of old server
- Run final backup to Google Drive
- Vultr panel → destroy old VPS

Total time for a full new-server provisioning: ~90 minutes once you've done it before.

---

## 11. Routine operations

### Daily

- Telegram watchdog runs every 5 min (silent unless issue)
- Daily heartbeat at 09:00 UTC / 14:30 IST (Telegram message confirming alive)
- Daily backup at 02:00 UTC / 07:30 IST (silent success)

### Weekly

- Check Vultr panel for any infra notifications
- Glance at `/var/log/astro_backup.log` for any failed backups
- Verify GitHub repo is in sync: `cd /opt/astro && git status`

### Monthly

- Review disk usage: `df -h`
- Review memory baseline: `free -h`
- Verify the SSL cert (if active) isn't approaching expiry
- Clean up old logs: `journalctl --vacuum-time=30d`
- Confirm latest backup is in Google Drive

### Quarterly

- Run a restore drill (see `BACKUP_RECOVERY_OPERATIONS.md` section 3)
- Update system packages: `apt update && apt upgrade -y; systemctl reboot`
- Rotate API key (recommended every 90-180 days)
- Review who has access to: Vultr account, GitHub account, Google account

### Annually

- Full code review (or skip and trust git diff)
- Renew Vultr instance (if not auto-renewed)
- Audit env vars + secrets in password manager
- Review monthly costs vs traffic and right-size VPS tier

---

## 12. Logs reference

| Log | Path | Rotation |
|---|---|---|
| Engine (uvicorn) | `journalctl -u astro.service` | systemd handles |
| Nginx access | `/var/log/nginx/*_access.log` | logrotate weekly |
| Nginx error | `/var/log/nginx/*_error.log` | logrotate weekly |
| Backup script | `/var/log/astro_backup.log` | logrotate weekly (8 weeks) |
| Watchdog | `/var/log/astro_watchdog.log` | logrotate weekly (4 weeks) |
| Cron firings | `journalctl -t astro_backup -t astro_watchdog` | systemd handles |
| Auth (SSH attempts) | `/var/log/auth.log` | logrotate |
| Kernel | `dmesg` / `journalctl -k` | persistent |

---

## 13. Cost & sizing

### Current monthly costs

| Item | Cost |
|---|---|
| Vultr VPS (current tier) | $24-40 (depending on plan) |
| Vultr automatic backups | 20% premium (~$5-8) |
| Vultr manual snapshots (1-2 kept) | $0.50-2 |
| Google Drive (within 15GB free tier) | $0 |
| GitHub private repo | $0 |
| UptimeRobot | $0 |
| Telegram | $0 |
| **Total monthly** | **~$30-50** |

### Right-sizing

Current VPS handles ~100-200 req/s comfortably with 2 workers + 131 MB memory used out of 8 GB.

**Headroom is large.** Realistic ceiling on current hardware: 500-1000 req/s with 4-8 workers (still well under memory limits).

**When to upgrade VPS tier:**
- Sustained CPU >70% for >30 min on most days
- Memory usage >60% baseline
- Disk consistently >70% used
- Network bandwidth hitting limits

**When to add a second VPS:**
- Above 1000 req/s sustained
- Need geographic distribution (US-East customers etc.)
- Need true high-availability (one VPS can fail without downtime)

For current numiVeda traffic (low-volume, customer-facing reports), a single VPS is fine for years.

---

## 14. Disaster recovery summary

(Full procedures in `BACKUP_RECOVERY_OPERATIONS.md`. Quick reference here:)

| Failure mode | Recovery layer | RTO |
|---|---|---|
| Service crash | systemd auto-restart | ~10 sec |
| Service stuck | Manual `systemctl restart` | ~30 sec |
| Recent code broke things | `git checkout v1.0-f11` | ~2 min |
| File corruption | `astro_restore.sh /root/backups/daily/<file>` | ~3 min |
| VPS unresponsive | Vultr panel restart | ~5 min |
| VPS won't boot | Vultr backup restore | ~10 min |
| Total VPS loss | Rebuild from GitHub + Google Drive | ~90 min |

---

## 15. What's intentionally NOT in production yet

- HTTPS via nginx + Let's Encrypt (engine still reachable via direct HTTP on port 8001)
- Application-level rate limiting (no rate limit code in engine)
- CORS (no `Access-Control-Allow-Origin` headers — clients must proxy)
- Multi-region deployment (single VPS in Mumbai region)
- Database for audit logs
- Sentry / Datadog / external observability
- Staging environment (changes go directly to production)
- CI/CD pipeline (no automated tests run on commit)

Each of these can be added incrementally. None is critical for current single-tenant internal use.

---

## 16. Quick command reference

```bash
# Service lifecycle
systemctl status astro.service --no-pager
systemctl restart astro.service
systemctl stop astro.service
systemctl start astro.service

# Logs
journalctl -u astro.service -f
journalctl -u astro.service --since "1 hour ago" --no-pager | tail -100
journalctl -t astro_backup --since "1 day ago"

# Code lifecycle (git)
cd /opt/astro
git pull origin main
git checkout v1.0-f11
git log --oneline -5
git tag -l

# Smoke test
curl -s http://localhost:8001/openapi.json | head -c 200

# Endpoint count check
curl -s http://localhost:8001/openapi.json | python3 -c "import sys, json; d=json.load(sys.stdin); print(f'Endpoints: {len(d.get(\"paths\", {}))}')"

# Manual backup
/usr/local/bin/astro_backup.sh daily

# Manual restore
/usr/local/bin/astro_restore.sh /root/backups/daily/<file>.tar.gz --dry-run
/usr/local/bin/astro_restore.sh /root/backups/daily/<file>.tar.gz

# Watchdog manual
/usr/local/bin/astro_watchdog.sh
tail -30 /var/log/astro_watchdog.log

# nginx
nginx -t
systemctl reload nginx

# Firewall
ufw status verbose

# System health
df -h
free -h
top -bn 1 | head -20
ss -tlnp
```

---

**End of T7 Deployment & Operations.**
