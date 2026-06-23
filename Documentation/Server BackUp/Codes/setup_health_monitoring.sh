#!/bin/bash
# numiVeda Server Health Monitoring Setup
# Run on VPS 65.20.75.166 as root
#
# Installs THREE layers of monitoring:
#   1. Local watchdog (VPS-side, checks every 5 min, auto-restarts on failure)
#   2. Telegram alerts (sends to your phone when something breaks or recovers)
#   3. External uptime monitoring instructions (Hostinger-independent)

set -euo pipefail

# ============================================================================
# CONFIGURATION — EDIT BEFORE RUNNING
# ============================================================================

# Telegram bot for alerts
# Create a bot: message @BotFather on Telegram, /newbot
# Get your chat ID: message @userinfobot on Telegram
TELEGRAM_BOT_TOKEN="8517086841:AAGEke8bVFcxtTZedYvmXR4Xmh68Dp18CSo"                     # e.g. "123456789:ABCdef..."
TELEGRAM_CHAT_ID="7711160828"                       # e.g. "987654321" (your Telegram user ID)

# Services to monitor
SERVICES=(
  "astro.service"                         # The astro engine
  "nginx"                                 # Web server
)

# Endpoints to health-check
ENDPOINTS=(
  "http://localhost:8001/astro/openapi.json"
  # Add more endpoints here if needed
)

# Maximum allowed failures before alerting (avoid flapping)
FAILURE_THRESHOLD=2

# ============================================================================
# WRITE THE WATCHDOG SCRIPT
# ============================================================================
echo "Installing watchdog script..."

cat > /usr/local/bin/astro_watchdog.sh << 'WATCHDOG_SCRIPT'
#!/bin/bash
# Server watchdog — runs every 5 min via cron
# Checks services + endpoints + disk + memory; alerts on failure; auto-restarts

set -euo pipefail

# Load config from env file (so it can be edited without re-running setup)
CONFIG=/etc/astro_watchdog.conf
[ -f "$CONFIG" ] && source "$CONFIG"

STATE_DIR=/var/lib/astro_watchdog
mkdir -p "$STATE_DIR"
LOG_FILE=/var/log/astro_watchdog.log

# Logging helper
log() {
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" >> "$LOG_FILE"
}

# Telegram alert
alert() {
  local severity="$1"
  local message="$2"
  log "[$severity] $message"
  
  if [ -n "${TELEGRAM_BOT_TOKEN:-}" ] && [ -n "${TELEGRAM_CHAT_ID:-}" ]; then
    # Emoji based on severity
    local emoji="ℹ️"
    case "$severity" in
      "CRITICAL") emoji="🚨" ;;
      "WARNING")  emoji="⚠️"  ;;
      "RECOVERY") emoji="✅" ;;
      "INFO")     emoji="ℹ️"  ;;
    esac
    
    local payload="${emoji} *${severity}*: ${message}\n_$(hostname) at $(date -u +%H:%M:%SZ)_"
    
    curl -s --max-time 10 \
      -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
      -d "chat_id=${TELEGRAM_CHAT_ID}" \
      -d "text=${payload}" \
      -d "parse_mode=Markdown" \
      > /dev/null 2>&1 || log "Telegram alert failed"
  fi
}

# Track failures to debounce (only alert after FAILURE_THRESHOLD failures in a row)
incr_failure() {
  local check_name="$1"
  local file="$STATE_DIR/fail_$check_name"
  local count=$(cat "$file" 2>/dev/null || echo 0)
  count=$((count + 1))
  echo "$count" > "$file"
  echo "$count"
}

reset_failure() {
  local check_name="$1"
  local file="$STATE_DIR/fail_$check_name"
  local count=$(cat "$file" 2>/dev/null || echo 0)
  rm -f "$file"
  echo "$count"
}

# ============================================================================
# CHECK 1: Systemd services
# ============================================================================
SERVICES=${SERVICES:-"astro.service nginx"}
for svc in $SERVICES; do
  if systemctl is-active --quiet "$svc"; then
    prev=$(reset_failure "svc_$svc")
    if [ "$prev" -ge "${FAILURE_THRESHOLD:-2}" ]; then
      alert "RECOVERY" "$svc is back online after ${prev} failed checks"
    fi
  else
    count=$(incr_failure "svc_$svc")
    log "FAIL: $svc is not active (failure #$count)"
    
    # Attempt auto-restart on first failure
    if [ "$count" -eq 1 ]; then
      log "Attempting auto-restart of $svc..."
      systemctl restart "$svc" || true
      sleep 5
      if systemctl is-active --quiet "$svc"; then
        alert "WARNING" "$svc had failed; auto-restart succeeded"
        reset_failure "svc_$svc"
      fi
    elif [ "$count" -ge "${FAILURE_THRESHOLD:-2}" ] && [ "$count" -le $((${FAILURE_THRESHOLD:-2} + 1)) ]; then
      alert "CRITICAL" "$svc is DOWN — auto-restart failed (${count} consecutive failures). Manual intervention needed. \`systemctl status $svc\` for details."
    fi
  fi
done

# ============================================================================
# CHECK 2: Endpoint health
# ============================================================================
ENDPOINTS=${ENDPOINTS:-"http://localhost:8001/astro/openapi.json"}
for endpoint in $ENDPOINTS; do
  endpoint_key=$(echo "$endpoint" | md5sum | cut -c1-8)
  
  # Try the request
  http_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 15 \
    -H "X-API-Key: numiveda-astro-secret-2026" \
    "$endpoint" 2>/dev/null || echo "000")
  
  if [ "$http_code" = "200" ]; then
    prev=$(reset_failure "ep_$endpoint_key")
    if [ "$prev" -ge "${FAILURE_THRESHOLD:-2}" ]; then
      alert "RECOVERY" "Endpoint healthy again: $endpoint (HTTP 200)"
    fi
  else
    count=$(incr_failure "ep_$endpoint_key")
    log "FAIL: $endpoint returned HTTP $http_code (failure #$count)"
    
    if [ "$count" -ge "${FAILURE_THRESHOLD:-2}" ] && [ "$count" -le $((${FAILURE_THRESHOLD:-2} + 1)) ]; then
      alert "CRITICAL" "Endpoint failing: $endpoint returned HTTP $http_code (${count} consecutive failures)"
    fi
  fi
done

# ============================================================================
# CHECK 3: Disk space
# ============================================================================
DISK_THRESHOLD=85
disk_usage=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$disk_usage" -ge 95 ]; then
  alert "CRITICAL" "Disk usage at ${disk_usage}%. URGENT: free up space."
elif [ "$disk_usage" -ge "$DISK_THRESHOLD" ]; then
  # Only alert once per day on disk warnings
  last_alert_file="$STATE_DIR/last_disk_alert"
  today=$(date +%Y%m%d)
  last_alert=$(cat "$last_alert_file" 2>/dev/null || echo "")
  if [ "$today" != "$last_alert" ]; then
    alert "WARNING" "Disk usage at ${disk_usage}% (threshold: ${DISK_THRESHOLD}%)"
    echo "$today" > "$last_alert_file"
  fi
fi

# ============================================================================
# CHECK 4: Memory
# ============================================================================
mem_avail_pct=$(free | awk '/Mem:/ {printf "%.0f", $7/$2 * 100}')
if [ "$mem_avail_pct" -le 5 ]; then
  alert "CRITICAL" "Memory critically low: only ${mem_avail_pct}% available"
elif [ "$mem_avail_pct" -le 10 ]; then
  last_alert_file="$STATE_DIR/last_mem_alert"
  today=$(date +%Y%m%d)
  last_alert=$(cat "$last_alert_file" 2>/dev/null || echo "")
  if [ "$today" != "$last_alert" ]; then
    alert "WARNING" "Memory low: ${mem_avail_pct}% available"
    echo "$today" > "$last_alert_file"
  fi
fi

# ============================================================================
# CHECK 5: SSL cert expiry (if certificates exist)
# ============================================================================
if [ -d /etc/letsencrypt/live ]; then
  for cert_dir in /etc/letsencrypt/live/*/; do
    cert="$cert_dir/fullchain.pem"
    [ ! -f "$cert" ] && continue
    
    domain=$(basename "$cert_dir")
    days_left=$(echo $(($(date -d "$(openssl x509 -in "$cert" -noout -enddate | cut -d= -f2)" +%s) - $(date +%s))) / 86400 | bc 2>/dev/null || echo "999")
    
    if [ "$days_left" -le 7 ]; then
      alert "CRITICAL" "SSL cert for $domain expires in ${days_left} days"
    elif [ "$days_left" -le 14 ]; then
      last_alert_file="$STATE_DIR/last_ssl_alert_$domain"
      today=$(date +%Y%m%d)
      last_alert=$(cat "$last_alert_file" 2>/dev/null || echo "")
      if [ "$today" != "$last_alert" ]; then
        alert "WARNING" "SSL cert for $domain expires in ${days_left} days"
        echo "$today" > "$last_alert_file"
      fi
    fi
  done
fi

# ============================================================================
# Daily heartbeat (so you know monitoring is alive)
# ============================================================================
heartbeat_file="$STATE_DIR/last_heartbeat"
today=$(date +%Y%m%d)
last_heartbeat=$(cat "$heartbeat_file" 2>/dev/null || echo "")
if [ "$today" != "$last_heartbeat" ]; then
  # Only send heartbeat at 09:00 UTC daily
  hour=$(date +%H)
  if [ "$hour" = "09" ]; then
    # Gather a status summary
    summary="✅ Daily heartbeat
Services: $(systemctl is-active astro.service) astro, $(systemctl is-active nginx) nginx
Disk: ${disk_usage}% used
Memory: ${mem_avail_pct}% available
Uptime: $(uptime -p)"
    alert "INFO" "$summary"
    echo "$today" > "$heartbeat_file"
  fi
fi

WATCHDOG_SCRIPT
chmod +x /usr/local/bin/astro_watchdog.sh

# ============================================================================
# WRITE CONFIG FILE
# ============================================================================
echo "Writing config to /etc/astro_watchdog.conf..."

cat > /etc/astro_watchdog.conf << CONFIG_FILE
# numiVeda Server Watchdog Configuration
# Edit this file to update settings without re-running setup.

# Telegram alerts
TELEGRAM_BOT_TOKEN="$TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID="$TELEGRAM_CHAT_ID"

# Failure threshold (how many consecutive failed checks before alerting)
FAILURE_THRESHOLD=$FAILURE_THRESHOLD

# Services to monitor (space-separated)
SERVICES="${SERVICES[@]}"

# Endpoints to health-check (space-separated)
ENDPOINTS="${ENDPOINTS[@]}"

# Disk usage warning threshold (%)
DISK_THRESHOLD=85
CONFIG_FILE
chmod 600 /etc/astro_watchdog.conf

# ============================================================================
# INSTALL CRON JOB
# ============================================================================
echo "Installing cron job (every 5 minutes)..."

(crontab -l 2>/dev/null | grep -v "astro_watchdog"; \
  echo "*/5 * * * * /usr/local/bin/astro_watchdog.sh 2>&1 | logger -t astro_watchdog" \
  ) | crontab -

# ============================================================================
# SET UP LOG ROTATION
# ============================================================================
cat > /etc/logrotate.d/astro_watchdog << 'LOGROTATE'
/var/log/astro_watchdog.log {
    weekly
    rotate 4
    compress
    delaycompress
    missingok
    notifempty
    create 0644 root root
}
LOGROTATE

# ============================================================================
# CONFIGURE SYSTEMD AUTO-RESTART
# ============================================================================
echo "Configuring systemd auto-restart for astro.service..."

# Check if astro.service already has Restart= directive
if ! grep -q "^Restart=" /etc/systemd/system/astro.service 2>/dev/null; then
  cat > /etc/systemd/system/astro.service.d/override.conf << 'OVERRIDE'
[Service]
Restart=on-failure
RestartSec=10s
StartLimitInterval=10min
StartLimitBurst=5
OVERRIDE
  systemctl daemon-reload
  echo "  -> Added Restart=on-failure (kicks in after crashes)"
else
  echo "  -> astro.service already has Restart= configured (skipped)"
fi

# ============================================================================
# TEST RUN
# ============================================================================
echo ""
echo "Running initial check..."
/usr/local/bin/astro_watchdog.sh

# ============================================================================
# DONE
# ============================================================================
echo ""
echo "================================================================"
echo "MONITORING SETUP COMPLETE"
echo "================================================================"
echo ""
echo "Local watchdog: /usr/local/bin/astro_watchdog.sh"
echo "  - Runs every 5 minutes via cron"
echo "  - Checks services, endpoints, disk, memory, SSL"
echo "  - Auto-restarts services on first failure"
echo "  - Sends Telegram alerts after ${FAILURE_THRESHOLD} failed checks"
echo "  - Daily heartbeat at 09:00 UTC"
echo ""
echo "Config: /etc/astro_watchdog.conf"
echo "Logs:   /var/log/astro_watchdog.log"
echo "        journalctl -t astro_watchdog --since '1 hour ago'"
echo ""
echo "Test the watchdog manually:"
echo "  /usr/local/bin/astro_watchdog.sh"
echo "  tail -50 /var/log/astro_watchdog.log"
echo ""
echo "If Telegram alerts not working, check:"
echo "  - Bot token in /etc/astro_watchdog.conf"
echo "  - Send a message to your bot once to initiate the chat"
echo "  - Test manually:"
echo "    curl -X POST https://api.telegram.org/bot\$TOKEN/sendMessage \\"
echo "         -d chat_id=\$CHAT_ID -d text=test"
echo ""
echo "================================================================"
echo "EXTERNAL UPTIME MONITORING (set up separately)"
echo "================================================================"
echo ""
echo "Local watchdog only catches problems WITHIN the VPS."
echo "If the VPS itself goes offline (Hostinger issue, network issue),"
echo "you'd never know without an EXTERNAL check."
echo ""
echo "Set up at least one of these (all free tiers):"
echo ""
echo "1. UPTIMEROBOT.COM (recommended — 50 free monitors, 5-min checks)"
echo "   - Sign up at uptimerobot.com"
echo "   - Add monitor: HTTPS, https://trade.kaaliyo.com/"
echo "   - Add monitor: HTTPS, your astro engine URL"
echo "   - Notification: Telegram (same bot) or email"
echo ""
echo "2. BETTERSTACK.COM (better UX, 10 free monitors, 30-sec checks)"
echo "   - Includes status page (status.numiveda.com)"
echo "   - Incident management built-in"
echo ""
echo "3. HEALTHCHECKS.IO (for cron job monitoring — different paradigm)"
echo "   - Sends ping URLs that your cron jobs hit"
echo "   - Alerts if pings stop arriving (i.e. cron is dead)"
echo ""
echo "================================================================"
