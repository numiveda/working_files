# Complete Server Hardening Playbook
**For:** numiVeda VPS on Vultr (currently 65.20.75.166 — Astro Engine + Kaaliyo)
**Goal:** (1) Serious backup, (2) Health monitoring, (3) Kaaliyo migration prep
**Time:** ~2 hours total, broken into clean phases

---

## What you're getting after this playbook

By the end, you'll have:
- **Vultr automatic backups enabled** (image-level, restorable in clicks)
- **Manual snapshots** before risky operations (free to create, $0.05/GB/month to store)
- **Daily/weekly file backups** to your local disk + Google Drive (offsite)
- **Health monitoring** with Telegram alerts every 5 min, daily heartbeat, auto-restart
- **External uptime monitoring** via UptimeRobot (catches if VPS itself is offline)
- **Clean migration plan** for Kaaliyo when you redeploy on a fresh server

Estimated cost increase per month: ~$2-5 (Vultr backups premium, depending on VPS size + snapshot storage)

---

## PHASE 1 — Vultr-side Backup (10 minutes, browser-only)

This is the **most important** layer. Vultr can take image-level snapshots that restore your entire server with a few clicks — including OS, configs, code, everything. Two flavors:

**Vultr Automatic Backups** = recurring, automated, daily/weekly. Costs 20% of your VPS price.
**Vultr Manual Snapshots** = on-demand, you trigger them. Costs $0.05/GB/month per snapshot.

You need BOTH. Automatic for routine safety; manual for "I'm about to do something risky."

### Step 1.1 — Log into Vultr

1. Go to https://my.vultr.com
2. Log in with your Vultr account
3. Click on your VPS (the one running at 65.20.75.166)

### Step 1.2 — Enable Automatic Backups

1. On the VPS detail page, find the **Settings** tab (or **Backups** tab, depending on Vultr's current layout)
2. Click **Enable Backups**
3. Vultr will show the price (20% of your monthly VPS cost — e.g. if your VPS is $24/month, backups add ~$4.80/month)
4. Choose backup schedule:
   - **Daily** at a low-traffic hour (recommended: 02:00 UTC = 07:30 IST morning)
   - Vultr keeps the most recent 2 backups by default
5. Click **Enable**

Vultr will run the first backup within ~24 hours. From then on, automatic.

### Step 1.3 — Create your first MANUAL snapshot RIGHT NOW

This is your "before the playbook" safety net. Critical to do before anything else.

1. From the VPS detail page, find **Snapshots** tab
2. Click **Take Snapshot**
3. Label it: `pre_playbook_2026_05_19`
4. Click **Take Snapshot**
5. Wait ~3-5 minutes (Vultr shows progress)
6. Verify the snapshot appears in the list with status **Complete**

This snapshot will cost ~$0.50-$2/month depending on your VPS disk usage. You can delete it after the playbook completes if you want to save that cost — or keep it as a long-term "known good" baseline.

### What you now have on Vultr-side

- One manual snapshot you can restore from in 5 minutes if anything goes wrong
- Automatic daily backups will start within 24 hours
- Both are stored on Vultr infrastructure (geographically separate from your VPS itself)

**This alone is already better than 90% of small-business backup setups.**

---

## PHASE 2 — Google Drive Offsite Backup (30 minutes)

Vultr backups protect against most things, but not "what if Vultr loses your account" or "what if your account gets compromised." Offsite-to-different-provider is the gold standard.

We'll use **rclone** to push backups to your Google Drive. Free for up to 15GB on personal Google account.

### Step 2.1 — Decide which Google account to use

Use a Google account that you control and won't lose access to. Options:
- Your numiVeda Workspace account (e.g. [email protected])
- A dedicated backup account
- Your personal Gmail (works but mixes personal + business)

For this playbook I'll assume you're using your numiVeda account.

### Step 2.2 — Install rclone on local machine AND on VPS

**Why both:** rclone's Google Drive auth requires a browser. Your VPS has no browser. So you authenticate on your local machine and copy the token to the VPS.

**On your LOCAL machine (Mac/Windows/Linux):**

Mac:
```bash
brew install rclone
```

Windows (PowerShell as admin):
```powershell
winget install Rclone.Rclone
```

Linux:
```bash
curl https://rclone.org/install.sh | sudo bash
```

Verify:
```bash
rclone version
```

**On the VPS (SSH in as root):**
```bash
ssh root@65.20.75.166
curl https://rclone.org/install.sh | sudo bash
rclone version
```

The versions on local and VPS should match (or be very close).

### Step 2.3 — Configure rclone on your LOCAL machine first

On your **local** machine (with browser available):

```bash
rclone config
```

Walk through the prompts:
```
n/s/q> n                                    # New remote
name> gdrive                                # Name it 'gdrive'
Storage> drive                              # Type 'drive' (Google Drive)
client_id>                                  # Press Enter (use rclone's default)
client_secret>                              # Press Enter (use rclone's default)
scope> 1                                    # Full access
service_account_file>                       # Press Enter (skip)
Edit advanced config? n
Use auto config? y                          # YES — opens browser
```

A browser tab opens. Log in with your Google account → click Allow.

You'll see "Success!" in the browser. Back in terminal:
```
Configure this as a Shared Drive? n        # NO unless you want a Shared Drive
Yes this is OK? y
q                                           # Quit config
```

Test it works:
```bash
rclone lsd gdrive:
```

Should list your Google Drive folders.

### Step 2.4 — Copy the rclone config to the VPS

The auth token is in `~/.config/rclone/rclone.conf` on your local machine. Copy it to the VPS:

**On your local machine:**
```bash
# Mac/Linux
scp ~/.config/rclone/rclone.conf root@65.20.75.166:/root/.config/rclone/rclone.conf

# Windows (PowerShell)
scp $env:APPDATA\rclone\rclone.conf root@65.20.75.166:/root/.config/rclone/
```

If the directory doesn't exist on the VPS:
```bash
ssh root@65.20.75.166 "mkdir -p /root/.config/rclone"
# Then run the scp again
```

### Step 2.5 — Verify rclone works on the VPS

SSH into the VPS:
```bash
ssh root@65.20.75.166
rclone lsd gdrive:
```

Should list your Google Drive folders (same as on your local machine).

### Step 2.6 — Create a dedicated backup folder in Google Drive

```bash
# On the VPS
rclone mkdir gdrive:numiveda_backups
rclone mkdir gdrive:numiveda_backups/astro_vps
rclone mkdir gdrive:numiveda_backups/astro_vps/daily
rclone mkdir gdrive:numiveda_backups/astro_vps/weekly
rclone mkdir gdrive:numiveda_backups/astro_vps/monthly
```

Verify:
```bash
rclone lsd gdrive:numiveda_backups/astro_vps
```

You should see 3 directories: daily, weekly, monthly.

---

## PHASE 3 — File-Level Backups on the VPS (15 minutes)

Vultr backups capture the whole disk image. File-level backups give you faster, more granular recovery — and easier inspection of what's in each backup.

### Step 3.1 — Upload the backup setup script

I'll create a Google-Drive-aware version of the production backup script. On your **local** machine:

Download `setup_production_backups_gdrive.sh` from this conversation (created below this guide), then:

```bash
scp setup_production_backups_gdrive.sh root@65.20.75.166:/root/
```

### Step 3.2 — Run the setup script

```bash
ssh root@65.20.75.166
chmod +x /root/setup_production_backups_gdrive.sh

# Edit it first if you want to change any defaults
nano /root/setup_production_backups_gdrive.sh
# Look at the CONFIGURATION section at top
# Default Google Drive path is "gdrive:numiveda_backups/astro_vps"
# Most defaults should be fine.

# Run it
/root/setup_production_backups_gdrive.sh
```

This will:
- Create `/usr/local/bin/astro_backup.sh` (the backup engine)
- Create `/usr/local/bin/astro_restore.sh` (the restore tool)
- Set up cron jobs: daily 02:00, weekly Sunday 03:00, monthly day 1 at 04:00
- Push backups to Google Drive automatically
- Auto-cleanup: keeps 7 days local + 14 days on Drive (daily), 28 days (weekly), 180 days (monthly)
- Run the first backup immediately

### Step 3.3 — Verify the first backup worked

```bash
# Check local backups
ls -la /root/backups/daily/

# Check Google Drive backups
rclone ls gdrive:numiveda_backups/astro_vps/daily/

# Read the backup log
tail -50 /var/log/astro_backup.log
```

You should see a `.tar.gz` file in both places.

### Step 3.4 — Test the restore script (dry run)

```bash
# List available backups
/usr/local/bin/astro_restore.sh

# Dry-run restore from the most recent
/usr/local/bin/astro_restore.sh /root/backups/daily/astro_daily_*.tar.gz --dry-run
```

The dry-run shows what WOULD be restored without actually doing it. If output looks reasonable, you have a working restore path.

---

## PHASE 4 — Health Monitoring + Telegram Alerts (20 minutes)

You want to know if the server stops responding. Three layers:

1. **Local watchdog** on the VPS (every 5 min) — catches service crashes, alerts via Telegram
2. **External monitor** (UptimeRobot) — catches if the entire VPS is offline
3. **Daily heartbeat** — confirms monitoring itself is alive

### Step 4.1 — Create a Telegram bot

1. Open Telegram, search for `@BotFather`, start chat
2. Send: `/newbot`
3. Name it: `numiVeda VPS Watchdog`
4. Username: pick anything ending in `bot`, e.g. `numiveda_watchdog_bot`
5. BotFather replies with a token like `123456789:ABCdef-GHIjkl-MNOpqr_STUvwx-YZ`
6. **Copy this token — you'll need it**

### Step 4.2 — Get your Telegram chat ID

1. In Telegram, search for `@userinfobot`, start chat
2. Send any message (e.g. "hi")
3. It replies with your numeric ID, like `987654321`
4. **Copy this ID — you'll need it**

### Step 4.3 — Activate the bot (one-time)

Telegram bots can't message you until YOU message them first. So:

1. In Telegram, search for the bot username you created (e.g. `@numiveda_watchdog_bot`)
2. Click **Start** or send `/start`

Now the bot can send you messages.

### Step 4.4 — Upload and configure the monitoring script

Download `setup_health_monitoring.sh` from this conversation, then:

```bash
# On local machine
scp setup_health_monitoring.sh root@65.20.75.166:/root/

# On VPS
ssh root@65.20.75.166
chmod +x /root/setup_health_monitoring.sh

# Edit the config section at top — fill in your Telegram credentials
nano /root/setup_health_monitoring.sh
```

In the script, find these lines and fill them in:
```bash
TELEGRAM_BOT_TOKEN="123456789:ABCdef..."   # from BotFather
TELEGRAM_CHAT_ID="987654321"               # from @userinfobot
```

Save (Ctrl+X, Y, Enter).

### Step 4.5 — Run the monitoring setup

```bash
/root/setup_health_monitoring.sh
```

This installs the watchdog, sets up cron (every 5 min), configures systemd auto-restart, and sends an initial test alert.

You should receive a Telegram message within ~1 minute. If you don't:
```bash
# Test Telegram manually
curl -s -X POST "https://api.telegram.org/bot$YOUR_TOKEN/sendMessage" \
  -d chat_id=$YOUR_CHAT_ID \
  -d text="test from VPS"
```

### Step 4.6 — Verify monitoring is running

```bash
# Check cron
crontab -l | grep watchdog

# Run watchdog manually to test
/usr/local/bin/astro_watchdog.sh

# Check the log
tail -30 /var/log/astro_watchdog.log

# Watch for next scheduled run
journalctl -t astro_watchdog --since "1 hour ago"
```

### Step 4.7 — Set up External Uptime Monitoring (5 min)

The local watchdog only works if the VPS itself is alive. If Vultr has a network issue or the entire VPS crashes, you need an external check.

**UptimeRobot.com — free, recommended:**

1. Go to https://uptimerobot.com
2. Sign up (free)
3. Click **+ Add New Monitor**
4. Settings:
   - Monitor Type: **HTTP(s)**
   - Friendly Name: `numiVeda Astro Engine`
   - URL: `http://65.20.75.166:8001/astro/openapi.json` (or your public URL)
   - Monitoring Interval: **5 minutes** (free tier limit)
5. Click **Create Monitor**
6. Repeat for `https://trade.kaaliyo.com/` (or whichever URL serves Kaaliyo)
7. Go to **My Settings → Add Alert Contact** → add Telegram (uses same bot)

UptimeRobot pings every 5 min from external locations. If your VPS is offline, you get an alert WITHIN 5 MINUTES.

---

## PHASE 5 — Kaaliyo Migration Prep (when you're ready to redeploy)

This is independent of the above and can wait. When you're ready to spin up Kaaliyo on a fresh server (new Vultr instance), follow these steps.

### Step 5.1 — Run the migration audit (does not change anything)

On the current VPS:
```bash
scp kaaliyo_migration_audit.sh root@65.20.75.166:/root/
ssh root@65.20.75.166
chmod +x /root/kaaliyo_migration_audit.sh
/root/kaaliyo_migration_audit.sh

# Or specify path if auto-detect fails:
# /root/kaaliyo_migration_audit.sh /opt/kaaliyo
```

This produces `/root/kaaliyo_migration_audit_TIMESTAMP/` with:
- `1_detection.txt` — what was found
- `2_size_breakdown.txt` — what's actually big
- `3_dead_weight.txt` — what should NOT migrate
- `4_secrets.txt` — credentials inventory (transfer separately)
- `5_dependencies.txt` — Python + Node deps
- `6_data_state.txt` — DBs and state files
- `7_external_connections.txt` — what Kaaliyo connects to
- `8_migration_manifest.md` — the checklist
- `9_clean_export.sh` — the actual export script (run when ready)

### Step 5.2 — Provision the new server

In Vultr panel:
1. Click **Deploy Server**
2. Choose:
   - Server Type: **Cloud Compute** (Regular Performance or AMD High Performance)
   - Location: same as current for low latency
   - OS: **Ubuntu 24.04 LTS** (match current OS for parity)
   - Server Size: match current (or upsize if needed)
   - Auto-Backups: **Enable**
   - Add SSH Key
3. Hostname: `kaaliyo-fresh`
4. Deploy

Get its IP, SSH in, harden:
```bash
ssh root@NEW_IP

# Update system
apt update && apt upgrade -y

# Install basics
apt install -y python3.12 python3.12-venv python3-pip nodejs npm nginx certbot ufw fail2ban

# Firewall
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable

# Create non-root user
adduser kaaliyo
usermod -aG sudo kaaliyo
```

### Step 5.3 — Transfer code (clean export)

On the OLD VPS:
```bash
/root/kaaliyo_migration_audit_*/9_clean_export.sh
```

This creates 3 tarballs in `/root/kaaliyo_clean_export/`:
- `kaaliyo_migration_<TS>_code.tar.gz` — code (excludes cruft)
- `kaaliyo_migration_<TS>_envs.tar.gz` — .env files (restricted)
- `kaaliyo_migration_<TS>_data.tar.gz` — databases

Transfer:
```bash
# From old VPS to new VPS
scp /root/kaaliyo_clean_export/kaaliyo_migration_*.tar.gz root@NEW_IP:/root/
```

### Step 5.4 — Restore on new server + verify

```bash
# On NEW VPS
ssh root@NEW_IP
cd /
tar -xzf /root/kaaliyo_migration_*_code.tar.gz
tar -xzf /root/kaaliyo_migration_*_envs.tar.gz   # securely if relevant
tar -xzf /root/kaaliyo_migration_*_data.tar.gz   # if present

# Recreate Python venv
cd /opt/kaaliyo   # or wherever
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Install Node deps
npm install

# Set up systemd service (mirror old service file)
scp root@OLD_IP:/etc/systemd/system/kaaliyo*.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable kaaliyo.service
systemctl start kaaliyo.service

# Verify
systemctl status kaaliyo.service
curl http://localhost:PORT/health
```

### Step 5.5 — DNS cutover (ONLY when fully validated)

1. Test the new server thoroughly — same domain pointed at new IP via /etc/hosts override on your local machine for testing
2. Once verified, in Cloudflare (or wherever DNS is) update the A record for `trade.kaaliyo.com` → new IP
3. Wait for DNS propagation (usually 5-30 min with low TTL)
4. Verify production traffic flowing
5. **Keep the old server running for 7 days minimum** in case rollback is needed

### Step 5.6 — Decommission old server (after 7 days of stable new server)

1. Take a final snapshot in Vultr panel of old server (kept as "archived")
2. Run final backup, transfer to Google Drive
3. Vultr panel → Destroy old VPS

---

## Summary checklist — print this and check off

### Today (Phase 1-4, ~90 min)
- [ ] 1.1 Logged into Vultr
- [ ] 1.2 Enabled Automatic Backups
- [ ] 1.3 Created manual pre-playbook snapshot
- [ ] 2.1-2.6 rclone configured + Google Drive folder set up
- [ ] 3.1-3.4 File-level backup script installed + first backup run + Google Drive sync verified
- [ ] 4.1-4.6 Telegram bot created + watchdog installed + test alert received
- [ ] 4.7 UptimeRobot configured for 2 URLs with Telegram alerts

### When ready to migrate Kaaliyo (Phase 5)
- [ ] 5.1 Migration audit script run
- [ ] 5.2 New Vultr instance provisioned + hardened
- [ ] 5.3 Clean export tarballs created + transferred
- [ ] 5.4 New server validated
- [ ] 5.5 DNS cutover
- [ ] 5.6 Old server decommissioned

### Ongoing
- [ ] Weekly: glance at Telegram (no news = good news; daily heartbeat at 09:00 UTC confirms monitoring alive)
- [ ] Monthly: verify backup chain by listing recent backups locally + on Google Drive
- [ ] Quarterly: test a restore on a scratch Vultr instance (don't wait until you actually need it)

---

## Troubleshooting

**Telegram alerts not arriving:**
- Did you send `/start` to your bot first?
- Check token + chat ID in `/etc/astro_watchdog.conf`
- Test manually: `curl -X POST "https://api.telegram.org/bot$TOKEN/sendMessage" -d chat_id=$ID -d text=test`

**rclone "Access blocked: Rclone's request is invalid":**
- You need to use the auto-config method on local machine first, then copy the conf to VPS
- Don't try to do rclone config directly on the VPS

**Google Drive folder shows but uploads fail:**
- Check Google Drive storage quota
- Run `rclone about gdrive:` to see usage

**Backup script runs but tarball is tiny (<1MB):**
- Probably the source directory permission issue
- Check `tar` was reading `/opt/astro/` correctly

**Watchdog says service is down but it's actually fine:**
- Check `systemctl is-active astro.service` returns "active"
- Watchdog config might point to wrong service name

---

## Cost summary

| Item | Cost/month |
|---|---|
| Current VPS | (unchanged) |
| Vultr automatic backups | ~$2-5 (20% of VPS) |
| Manual snapshots (keep 1-2) | ~$0.50-2.00 |
| Google Drive storage (free tier) | $0 (until you exceed 15GB) |
| UptimeRobot free tier | $0 |
| Telegram | $0 |
| **Total monthly overhead** | **~$3-7** |

For a system running real-money trading + customer-facing reports, this is the cheapest "I won't lose my business overnight" insurance you can buy.

---

*Generated 2026-05-19. Source verified against Vultr docs (Jan 2026) and rclone docs.*
