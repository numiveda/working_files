#!/bin/bash
# numiVeda Astro Engine — Production Backup System (Google Drive edition)
# Run on Vultr VPS as root
# 
# Sets up: daily automated backups + Google Drive offsite push + monthly snapshots
# 
# PREREQUISITES:
#   1. rclone installed (curl https://rclone.org/install.sh | sudo bash)
#   2. rclone config copied from local machine to /root/.config/rclone/rclone.conf
#   3. Google Drive remote named 'gdrive' configured
#   4. Folder gdrive:numiveda_backups/astro_vps/{daily,weekly,monthly} exists

set -euo pipefail

# ============================================================================
# CONFIGURATION — edit these if needed
# ============================================================================
BACKUP_ROOT="/root/backups"                  # Local backup directory on VPS
GDRIVE_PATH="gdrive:numiveda_backups/astro_vps"  # Google Drive backup root

# Retention (kept on VPS local disk)
LOCAL_DAILY_RETENTION_DAYS=7
LOCAL_WEEKLY_RETENTION_DAYS=28
LOCAL_MONTHLY_RETENTION_DAYS=180

# Retention (kept in Google Drive)
GDRIVE_DAILY_RETENTION_DAYS=14
GDRIVE_WEEKLY_RETENTION_DAYS=60
GDRIVE_MONTHLY_RETENTION_DAYS=365

# What to back up (relative or absolute paths)
# Edit this list to match your VPS layout
SOURCES=(
  "/opt/astro"                              # The astro engine code
  "/etc/systemd/system/astro.service"       # systemd unit for astro
  "/etc/nginx/sites-available"              # nginx configs
  "/etc/nginx/sites-enabled"
  # Add other paths here as needed:
  # "/opt/kaaliyo"                          # uncomment when Kaaliyo is on this VPS
  # "/etc/letsencrypt"                      # SSL certs
)

# ============================================================================
# PRE-FLIGHT CHECKS
# ============================================================================
echo "================================================================"
echo "Setting up production backup system on VPS (Google Drive edition)"
echo "Backup root:  $BACKUP_ROOT"
echo "GDrive path:  $GDRIVE_PATH"
echo "================================================================"

# Check rclone is installed
if ! command -v rclone &>/dev/null; then
  echo "ERROR: rclone not installed."
  echo "Install: curl https://rclone.org/install.sh | sudo bash"
  exit 1
fi

# Check rclone is configured for gdrive
if ! rclone listremotes | grep -q "^gdrive:"; then
  echo "ERROR: rclone remote 'gdrive' not configured."
  echo ""
  echo "On your LOCAL machine, run: rclone config"
  echo "Then copy /root/.config/rclone/rclone.conf from local to this VPS."
  echo "See PLAYBOOK Phase 2 for full instructions."
  exit 1
fi

# Test Google Drive accessible
echo "Testing Google Drive connectivity..."
if ! rclone lsd "${GDRIVE_PATH%/*}" >/dev/null 2>&1; then
  echo "WARNING: Can't list parent of $GDRIVE_PATH"
  echo "Will attempt to create the path on first backup."
fi

mkdir -p "$BACKUP_ROOT"/{daily,weekly,monthly,logs}

# ============================================================================
# WRITE THE BACKUP SCRIPT
# ============================================================================
echo ""
echo "Installing /usr/local/bin/astro_backup.sh..."

cat > /usr/local/bin/astro_backup.sh << 'BACKUP_SCRIPT'
#!/bin/bash
# Production backup script — runs daily/weekly/monthly via cron
# Usage: astro_backup.sh [daily|weekly|monthly]

set -euo pipefail

TIER="${1:-daily}"
TIMESTAMP=$(date -u +"%Y%m%d_%H%M%S")
HOSTNAME_=$(hostname)
BACKUP_ROOT="/root/backups"
GDRIVE_PATH="gdrive:numiveda_backups/astro_vps"
LOG_FILE="$BACKUP_ROOT/logs/${TIER}_${TIMESTAMP}.log"
MAIN_LOG="/var/log/astro_backup.log"
LABEL="astro_${TIER}_${TIMESTAMP}"

# Local retention (days)
LOCAL_RETENTION_DAILY=7
LOCAL_RETENTION_WEEKLY=28
LOCAL_RETENTION_MONTHLY=180

# Google Drive retention (days)
GDRIVE_RETENTION_DAILY=14
GDRIVE_RETENTION_WEEKLY=60
GDRIVE_RETENTION_MONTHLY=365

# Sources to backup (must match setup script)
SOURCES=(
  "/opt/astro"
  "/etc/systemd/system/astro.service"
  "/etc/nginx/sites-available"
  "/etc/nginx/sites-enabled"
)
[ -d "/etc/letsencrypt" ] && SOURCES+=("/etc/letsencrypt")
[ -d "/opt/kaaliyo" ] && SOURCES+=("/opt/kaaliyo")

# Output to both per-tier log and main log
exec > >(tee -a "$LOG_FILE" "$MAIN_LOG") 2>&1

echo "================================================================"
echo "Backup start: $TIMESTAMP (tier: $TIER)"
echo "================================================================"

# ----------------------------------------------------------------------------
# 1. Capture pre-backup state
# ----------------------------------------------------------------------------
{
  echo "=== Service state ==="
  systemctl is-active astro.service 2>/dev/null || echo "WARNING: astro.service not active"
  systemctl is-active nginx 2>/dev/null || echo "WARNING: nginx not active"
  echo ""
  echo "=== Disk space ==="
  df -h /root /opt 2>/dev/null
  echo ""
  echo "=== Memory ==="
  free -h
  echo ""
  echo "=== Endpoint count ==="
  curl -s --max-time 10 -H "X-API-Key: numiveda-astro-secret-2026" \
    http://localhost:8001/astro/openapi.json 2>/dev/null \
    | python3 -c "import sys, json; d=json.load(sys.stdin); print(f'Endpoints: {len(d.get(\"paths\", {}))}')" \
    2>/dev/null || echo "Endpoint check failed (non-fatal)"
} > "$BACKUP_ROOT/${TIER}/${LABEL}_state.txt"

# ----------------------------------------------------------------------------
# 2. Create tarball
# ----------------------------------------------------------------------------
echo "Creating tarball..."
TARBALL="$BACKUP_ROOT/${TIER}/${LABEL}.tar.gz"

tar --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='*/venv' \
    --exclude='*/.venv' \
    --exclude='*/node_modules' \
    --exclude='*/logs/*.log' \
    --exclude='*.tmp' \
    -czf "$TARBALL" \
    "${SOURCES[@]}" 2>&1 | tail -5

# ----------------------------------------------------------------------------
# 3. Capture journal logs (last N days based on tier)
# ----------------------------------------------------------------------------
JOURNAL_DAYS=7
[ "$TIER" = "weekly" ] && JOURNAL_DAYS=14
[ "$TIER" = "monthly" ] && JOURNAL_DAYS=30
journalctl -u astro.service --since "${JOURNAL_DAYS} days ago" --no-pager \
  > "$BACKUP_ROOT/${TIER}/${LABEL}_journal.log" 2>/dev/null || true

# ----------------------------------------------------------------------------
# 4. Generate checksum
# ----------------------------------------------------------------------------
sha256sum "$TARBALL" > "${TARBALL%.tar.gz}.sha256"

# ----------------------------------------------------------------------------
# 5. Verify tarball integrity
# ----------------------------------------------------------------------------
echo "Verifying tarball integrity..."
if tar -tzf "$TARBALL" > /dev/null 2>&1; then
  echo "OK: tarball integrity verified"
else
  echo "FAIL: tarball is corrupt"
  exit 2
fi

SIZE=$(du -h "$TARBALL" | cut -f1)
echo "Backup size: $SIZE"

# ----------------------------------------------------------------------------
# 6. Push to Google Drive
# ----------------------------------------------------------------------------
echo "Pushing to Google Drive: $GDRIVE_PATH/$TIER/"

if rclone copy "$TARBALL" "$GDRIVE_PATH/$TIER/" --quiet 2>&1; then
  echo "Google Drive upload: OK ($SIZE)"
  rclone copy "${TARBALL%.tar.gz}.sha256" "$GDRIVE_PATH/$TIER/" --quiet 2>&1
  rclone copy "$BACKUP_ROOT/${TIER}/${LABEL}_state.txt" "$GDRIVE_PATH/$TIER/" --quiet 2>&1
  if [ -f "$BACKUP_ROOT/${TIER}/${LABEL}_journal.log" ]; then
    rclone copy "$BACKUP_ROOT/${TIER}/${LABEL}_journal.log" "$GDRIVE_PATH/$TIER/" --quiet 2>&1
  fi
else
  echo "WARNING: Google Drive upload failed (local backup retained)"
fi

# ----------------------------------------------------------------------------
# 7. Local retention cleanup
# ----------------------------------------------------------------------------
case "$TIER" in
  daily)   RETENTION=$LOCAL_RETENTION_DAILY ;;
  weekly)  RETENTION=$LOCAL_RETENTION_WEEKLY ;;
  monthly) RETENTION=$LOCAL_RETENTION_MONTHLY ;;
esac

echo "Cleaning local backups older than $RETENTION days..."
find "$BACKUP_ROOT/$TIER" -type f -mtime +$RETENTION -delete 2>/dev/null || true

# ----------------------------------------------------------------------------
# 8. Google Drive retention cleanup (delete old files)
# ----------------------------------------------------------------------------
case "$TIER" in
  daily)   GDRIVE_RETENTION=$GDRIVE_RETENTION_DAILY ;;
  weekly)  GDRIVE_RETENTION=$GDRIVE_RETENTION_WEEKLY ;;
  monthly) GDRIVE_RETENTION=$GDRIVE_RETENTION_MONTHLY ;;
esac

echo "Cleaning Google Drive backups older than $GDRIVE_RETENTION days..."
rclone delete "$GDRIVE_PATH/$TIER/" --min-age "${GDRIVE_RETENTION}d" --quiet 2>&1 || true

# ----------------------------------------------------------------------------
# 9. Summary
# ----------------------------------------------------------------------------
echo "================================================================"
echo "Backup complete: $LABEL"
echo "Size: $SIZE"
echo "Local:   $BACKUP_ROOT/$TIER/$LABEL.tar.gz"
echo "GDrive:  $GDRIVE_PATH/$TIER/$LABEL.tar.gz"
echo "================================================================"

BACKUP_SCRIPT
chmod +x /usr/local/bin/astro_backup.sh

# ============================================================================
# WRITE THE RESTORE SCRIPT
# ============================================================================
echo "Installing /usr/local/bin/astro_restore.sh..."

cat > /usr/local/bin/astro_restore.sh << 'RESTORE_SCRIPT'
#!/bin/bash
# Restore from a backup
# Usage: astro_restore.sh <backup_file.tar.gz> [--dry-run]
# Or:    astro_restore.sh --from-gdrive <label> [--dry-run]

set -euo pipefail

GDRIVE_PATH="gdrive:numiveda_backups/astro_vps"

# ----------------------------------------------------------------------------
# Parse args
# ----------------------------------------------------------------------------
if [ "${1:-}" = "--from-gdrive" ]; then
  LABEL="${2:-}"
  DRY_RUN="${3:-}"
  if [ -z "$LABEL" ]; then
    echo "Usage: $0 --from-gdrive <backup_label> [--dry-run]"
    echo ""
    echo "Recent backups in Google Drive:"
    for tier in daily weekly monthly; do
      echo "--- $tier ---"
      rclone ls "$GDRIVE_PATH/$tier/" 2>/dev/null | sort -k2 -r | head -10
    done
    exit 1
  fi
  
  # Find which tier has it
  for tier in daily weekly monthly; do
    if rclone lsl "$GDRIVE_PATH/$tier/" 2>/dev/null | grep -q "$LABEL"; then
      echo "Downloading $LABEL from $tier..."
      mkdir -p /tmp/astro_restore
      rclone copy "$GDRIVE_PATH/$tier/${LABEL}.tar.gz" /tmp/astro_restore/
      rclone copy "$GDRIVE_PATH/$tier/${LABEL}.sha256" /tmp/astro_restore/ 2>/dev/null || true
      BACKUP_FILE="/tmp/astro_restore/${LABEL}.tar.gz"
      break
    fi
  done
  
  if [ -z "${BACKUP_FILE:-}" ]; then
    echo "ERROR: $LABEL not found in Google Drive"
    exit 1
  fi
else
  BACKUP_FILE="${1:-}"
  DRY_RUN="${2:-}"
fi

# ----------------------------------------------------------------------------
# Validate
# ----------------------------------------------------------------------------
if [ -z "$BACKUP_FILE" ] || [ ! -f "$BACKUP_FILE" ]; then
  echo "Usage: $0 <backup_file.tar.gz> [--dry-run]"
  echo "  or:  $0 --from-gdrive <backup_label> [--dry-run]"
  echo ""
  echo "Available local backups:"
  ls -la /root/backups/{daily,weekly,monthly}/*.tar.gz 2>/dev/null | tail -20 || echo "  (none)"
  exit 1
fi

echo "================================================================"
echo "RESTORE FROM: $BACKUP_FILE"
echo "DRY RUN: ${DRY_RUN:-no}"
echo "================================================================"

# ----------------------------------------------------------------------------
# Verify checksum if available
# ----------------------------------------------------------------------------
CHECKSUM_FILE="${BACKUP_FILE%.tar.gz}.sha256"
if [ -f "$CHECKSUM_FILE" ]; then
  echo "Verifying checksum..."
  cd "$(dirname $BACKUP_FILE)"
  sha256sum -c "$(basename $CHECKSUM_FILE)" || { echo "CHECKSUM FAILED — aborting"; exit 2; }
  cd /
fi

# ----------------------------------------------------------------------------
# Show contents
# ----------------------------------------------------------------------------
echo ""
echo "Tarball contents preview (first 20 entries):"
tar -tzf "$BACKUP_FILE" | head -20

if [ "$DRY_RUN" = "--dry-run" ]; then
  echo ""
  echo "DRY RUN — no files restored. Re-run without --dry-run to actually restore."
  exit 0
fi

# ----------------------------------------------------------------------------
# Confirm + restore
# ----------------------------------------------------------------------------
echo ""
echo "WARNING: This will overwrite /opt/astro and other config paths."
echo "Old /opt/astro will be saved as /opt/astro.pre_restore.<timestamp>"
read -p "Type YES to proceed: " CONFIRM
if [ "$CONFIRM" != "YES" ]; then
  echo "Aborted."
  exit 0
fi

# Stop services
echo "Stopping services..."
systemctl stop astro.service 2>/dev/null || true

# Save current /opt/astro as safety net
if [ -d /opt/astro ]; then
  TS=$(date +%s)
  mv /opt/astro "/opt/astro.pre_restore.$TS"
  echo "Saved current /opt/astro as /opt/astro.pre_restore.$TS"
fi

# Extract
echo "Extracting..."
tar -xzf "$BACKUP_FILE" -C /

# Reload + start
systemctl daemon-reload
systemctl start astro.service

sleep 5

# Verify
if systemctl is-active --quiet astro.service; then
  echo "OK: astro.service is active"
  curl -s --max-time 10 -H "X-API-Key: numiveda-astro-secret-2026" \
    http://localhost:8001/astro/openapi.json 2>/dev/null \
    | python3 -c "import sys, json; d=json.load(sys.stdin); print(f'Endpoints live: {len(d.get(\"paths\", {}))}')" \
    2>/dev/null || echo "Service started but endpoint check failed"
else
  echo "FAIL: astro.service did not start"
  systemctl status astro.service --no-pager
  exit 3
fi

echo "================================================================"
echo "Restore complete from: $BACKUP_FILE"
echo "Rollback available at: /opt/astro.pre_restore.$TS"
echo "================================================================"
RESTORE_SCRIPT
chmod +x /usr/local/bin/astro_restore.sh

# ============================================================================
# WRITE A QUICK-CHECK SCRIPT
# ============================================================================
cat > /usr/local/bin/astro_backup_status.sh << 'STATUS_SCRIPT'
#!/bin/bash
# Quick status check of backups
GDRIVE_PATH="gdrive:numiveda_backups/astro_vps"

echo "==================== Local backups ===================="
for tier in daily weekly monthly; do
  echo "--- $tier ---"
  ls -lh "/root/backups/$tier/"*.tar.gz 2>/dev/null | tail -5 || echo "  (none)"
done

echo ""
echo "==================== Google Drive backups ===================="
for tier in daily weekly monthly; do
  echo "--- $tier ---"
  rclone ls "$GDRIVE_PATH/$tier/" 2>/dev/null | grep -v "\.sha256\|_state\|_journal" | sort -k2 -r | head -5 || echo "  (none / rclone error)"
done

echo ""
echo "==================== Recent backup log ===================="
tail -20 /var/log/astro_backup.log 2>/dev/null || echo "  (no log yet)"

echo ""
echo "==================== Cron schedule ===================="
crontab -l 2>/dev/null | grep -i backup
STATUS_SCRIPT
chmod +x /usr/local/bin/astro_backup_status.sh

# ============================================================================
# CRON SETUP
# ============================================================================
echo ""
echo "Installing cron jobs..."

(crontab -l 2>/dev/null | grep -v "astro_backup.sh"; \
  echo "# numiVeda Astro Engine backups"; \
  echo "0 2 * * * /usr/local/bin/astro_backup.sh daily   2>&1 | tail -5 | logger -t astro_backup"; \
  echo "0 3 * * 0 /usr/local/bin/astro_backup.sh weekly  2>&1 | tail -5 | logger -t astro_backup"; \
  echo "0 4 1 * * /usr/local/bin/astro_backup.sh monthly 2>&1 | tail -5 | logger -t astro_backup"; \
  ) | crontab -

echo "Cron installed:"
echo "  - Daily backup at 02:00 UTC"
echo "  - Weekly backup at 03:00 UTC Sundays"
echo "  - Monthly backup at 04:00 UTC on day 1"

# ============================================================================
# LOGROTATE
# ============================================================================
cat > /etc/logrotate.d/astro_backup << 'LOGROTATE'
/var/log/astro_backup.log {
    weekly
    rotate 8
    compress
    delaycompress
    missingok
    notifempty
    create 0644 root root
}
LOGROTATE

# ============================================================================
# RUN FIRST BACKUP NOW
# ============================================================================
echo ""
echo "================================================================"
echo "Running first backup now..."
echo "================================================================"
/usr/local/bin/astro_backup.sh daily

# ============================================================================
# DONE
# ============================================================================
echo ""
echo "================================================================"
echo "SETUP COMPLETE"
echo "================================================================"
echo ""
echo "Commands available:"
echo "  Manual backup:    /usr/local/bin/astro_backup.sh [daily|weekly|monthly]"
echo "  Restore:          /usr/local/bin/astro_restore.sh <file.tar.gz> [--dry-run]"
echo "  Restore from GD:  /usr/local/bin/astro_restore.sh --from-gdrive <label>"
echo "  Status:           /usr/local/bin/astro_backup_status.sh"
echo ""
echo "Backup schedule:"
echo "  Daily:   /root/backups/daily/   + GDrive (kept 7d local / 14d GDrive)"
echo "  Weekly:  /root/backups/weekly/  + GDrive (kept 28d local / 60d GDrive)"
echo "  Monthly: /root/backups/monthly/ + GDrive (kept 180d local / 365d GDrive)"
echo ""
echo "Logs: /var/log/astro_backup.log"
echo "      journalctl -t astro_backup --since '1 day ago'"
echo "================================================================"
