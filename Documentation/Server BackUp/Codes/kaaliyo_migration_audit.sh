#!/bin/bash
# Kaaliyo Migration Audit
# Run on the CURRENT Kaaliyo VPS (presumably the same 65.20.75.166 or wherever)
#
# This produces an audit of what's actually needed for a clean redeployment.
# It does NOT modify anything — read-only inspection.

set -euo pipefail

TIMESTAMP=$(date -u +"%Y%m%d_%H%M%S")
AUDIT_DIR="/root/kaaliyo_migration_audit_${TIMESTAMP}"
mkdir -p "$AUDIT_DIR"
cd "$AUDIT_DIR"

echo "================================================================"
echo "Kaaliyo Migration Audit: $TIMESTAMP"
echo "Output: $AUDIT_DIR"
echo "================================================================"

# ============================================================================
# AUTO-DETECT KAALIYO INSTALLATION
# ============================================================================
echo ""
echo "[1/9] Detecting Kaaliyo installation..."

# Search common locations
CANDIDATES=()
for path in /opt /root /home /var/www /srv; do
  if [ -d "$path" ]; then
    while IFS= read -r dir; do
      CANDIDATES+=("$dir")
    done < <(find "$path" -maxdepth 3 -type d \
      \( -iname "*kaaliyo*" -o -iname "*openalgo*" -o -iname "*trade*" \) \
      2>/dev/null)
  fi
done

{
  echo "=== Detected Kaaliyo / OpenAlgo / trading directories ==="
  for d in "${CANDIDATES[@]}"; do
    echo "$d ($(du -sh "$d" 2>/dev/null | cut -f1))"
  done
  echo ""
  echo "=== Running processes (search: trade/kaaliyo/openalgo) ==="
  ps aux | grep -iE "kaaliyo|openalgo|trade" | grep -v grep || echo "(none)"
  echo ""
  echo "=== Listening ports ==="
  ss -tlnp 2>/dev/null | grep -v "127.0.0.1" || netstat -tlnp 2>/dev/null
  echo ""
  echo "=== Systemd services matching kaaliyo/openalgo/trade ==="
  systemctl list-units --type=service --all | grep -iE "kaaliyo|openalgo|trade" || echo "(none)"
} > "1_detection.txt"

echo "  -> 1_detection.txt"

# Use the first candidate, or prompt
if [ ${#CANDIDATES[@]} -gt 0 ]; then
  KAALIYO_DIR="${CANDIDATES[0]}"
  echo "  Auto-selected: $KAALIYO_DIR"
else
  echo "  WARNING: No Kaaliyo directory detected. Pass it as arg 1: $0 /path/to/kaaliyo"
  KAALIYO_DIR="${1:-/opt/kaaliyo}"
fi

# Allow override via command-line arg
[ -n "${1:-}" ] && KAALIYO_DIR="$1"

if [ ! -d "$KAALIYO_DIR" ]; then
  echo "ERROR: $KAALIYO_DIR not found"
  exit 1
fi

echo "  Auditing: $KAALIYO_DIR"

# ============================================================================
# DIRECTORY SIZE BREAKDOWN
# ============================================================================
echo ""
echo "[2/9] Directory size breakdown..."

{
  echo "=== Total Kaaliyo footprint ==="
  du -sh "$KAALIYO_DIR"
  echo ""
  echo "=== Top-level subdirectories by size ==="
  du -sh "$KAALIYO_DIR"/* 2>/dev/null | sort -rh | head -30
  echo ""
  echo "=== Largest 30 files ==="
  find "$KAALIYO_DIR" -type f -exec du -h {} + 2>/dev/null | sort -rh | head -30
  echo ""
  echo "=== File count by extension ==="
  find "$KAALIYO_DIR" -type f 2>/dev/null \
    | awk -F. '{print tolower($NF)}' \
    | sort | uniq -c | sort -rn | head -30
} > "2_size_breakdown.txt"

echo "  -> 2_size_breakdown.txt"

# ============================================================================
# DEAD WEIGHT IDENTIFICATION
# ============================================================================
echo ""
echo "[3/9] Identifying dead weight (cruft that shouldn't migrate)..."

{
  echo "=== Files/dirs that should NOT migrate to new server ==="
  echo ""
  echo "--- Log files (regenerate on new server) ---"
  find "$KAALIYO_DIR" \( -name "*.log" -o -name "*.log.*" -o -path "*/logs/*" \) -type f 2>/dev/null \
    | xargs du -h 2>/dev/null | sort -rh | head -20
  echo ""
  echo "--- Cache directories ---"
  find "$KAALIYO_DIR" -type d \( -name "__pycache__" -o -name ".cache" -o -name "node_modules" -o -name ".pytest_cache" -o -name ".mypy_cache" \) 2>/dev/null \
    | head -20
  echo ""
  echo "--- Compiled Python ---"
  find "$KAALIYO_DIR" -name "*.pyc" 2>/dev/null | wc -l | xargs echo ".pyc files:"
  echo ""
  echo "--- Virtual environments ---"
  find "$KAALIYO_DIR" -type d \( -name "venv" -o -name ".venv" -o -name "env" \) 2>/dev/null
  echo ""
  echo "--- Database dumps / SQLite (need separate handling) ---"
  find "$KAALIYO_DIR" -type f \( -name "*.db" -o -name "*.sqlite" -o -name "*.sqlite3" -o -name "*.dump" -o -name "*.sql" \) 2>/dev/null \
    | xargs ls -lh 2>/dev/null
  echo ""
  echo "--- Backup / old files ---"
  find "$KAALIYO_DIR" -type f \( -name "*.bak" -o -name "*.old" -o -name "*~" -o -name "*.orig" -o -name "*_backup*" -o -name "*_old*" \) 2>/dev/null
  echo ""
  echo "--- Git directories (decide: include or not) ---"
  find "$KAALIYO_DIR" -type d -name ".git" 2>/dev/null
  echo ""
  echo "--- Files modified > 90 days ago (potential orphans) ---"
  find "$KAALIYO_DIR" -type f -mtime +90 ! -path "*/node_modules/*" ! -path "*/.git/*" 2>/dev/null \
    | head -20
} > "3_dead_weight.txt"

echo "  -> 3_dead_weight.txt"

# ============================================================================
# SECRETS & ENVIRONMENT
# ============================================================================
echo ""
echo "[4/9] Identifying secrets and environment files..."

{
  echo "=== CRITICAL: Secrets that need careful handling ==="
  echo "These must be transferred securely (NEVER through git, even private)"
  echo ""
  echo "--- .env files ---"
  find "$KAALIYO_DIR" -name ".env*" -type f 2>/dev/null | xargs ls -la 2>/dev/null
  echo ""
  echo "--- Config files mentioning api/key/secret/token ---"
  find "$KAALIYO_DIR" -type f \( -name "*.conf" -o -name "*.cfg" -o -name "*.ini" -o -name "*.yaml" -o -name "*.yml" -o -name "*.toml" -o -name "*.json" \) 2>/dev/null \
    | xargs grep -lE "api[_-]?key|secret|password|token|credential" 2>/dev/null \
    | head -20
  echo ""
  echo "--- Files with hardcoded credentials (scan code) ---"
  grep -rnE "(api[_-]?key|secret|password|access[_-]?token)\s*=\s*['\"][^'\"]{8,}" \
    "$KAALIYO_DIR" \
    --include="*.py" --include="*.js" --include="*.ts" \
    --exclude-dir=node_modules --exclude-dir=__pycache__ --exclude-dir=.git --exclude-dir=venv \
    2>/dev/null | head -10 || echo "(none found in code)"
  echo ""
  echo "--- API keys patterns (AliceBlue, broker creds) ---"
  grep -rlE "alice[_-]?blue|aliceblue|broker[_-]?api" "$KAALIYO_DIR" \
    --include="*.py" --include="*.js" --include="*.env*" \
    --exclude-dir=node_modules --exclude-dir=.git 2>/dev/null | head -10
} > "4_secrets.txt"

chmod 600 "4_secrets.txt"  # Only root can read
echo "  -> 4_secrets.txt (restricted to root)"

# ============================================================================
# DEPENDENCIES
# ============================================================================
echo ""
echo "[5/9] Cataloging dependencies..."

{
  echo "=== Python dependencies ==="
  find "$KAALIYO_DIR" -maxdepth 3 -name "requirements*.txt" -o -name "Pipfile" -o -name "pyproject.toml" 2>/dev/null | while read -r f; do
    echo "--- $f ---"
    cat "$f"
    echo ""
  done
  echo ""
  echo "=== Node.js dependencies ==="
  find "$KAALIYO_DIR" -maxdepth 3 -name "package.json" ! -path "*/node_modules/*" 2>/dev/null | while read -r f; do
    echo "--- $f ---"
    cat "$f" | python3 -c "import sys, json; d=json.load(sys.stdin); print('deps:', list(d.get('dependencies', {}).keys())); print('devDeps:', list(d.get('devDependencies', {}).keys()))" 2>/dev/null || cat "$f"
    echo ""
  done
  echo ""
  echo "=== System packages (apt) — guess from imports ==="
  echo "Common system deps used by trading apps: python3-dev, build-essential, libssl-dev, libffi-dev, postgresql-client, redis-tools"
} > "5_dependencies.txt"

echo "  -> 5_dependencies.txt"

# ============================================================================
# DATA / STATE
# ============================================================================
echo ""
echo "[6/9] Identifying data and state files..."

{
  echo "=== Data and state that needs migration ==="
  echo ""
  echo "--- Database files ---"
  find "$KAALIYO_DIR" -type f \( -name "*.db" -o -name "*.sqlite*" \) 2>/dev/null \
    | xargs ls -lh 2>/dev/null
  echo ""
  echo "--- CSV / JSON data files ---"
  find "$KAALIYO_DIR" -type f \( -name "*.csv" -o -name "*.json" \) ! -name "package*.json" ! -name "tsconfig*.json" 2>/dev/null \
    | head -20
  echo ""
  echo "--- Trade history / portfolio files ---"
  find "$KAALIYO_DIR" -type f \( -iname "*trade*" -o -iname "*portfolio*" -o -iname "*positions*" -o -iname "*orders*" \) 2>/dev/null \
    | head -20
  echo ""
  echo "--- Custom config (separate from secrets) ---"
  find "$KAALIYO_DIR" -maxdepth 3 -type f \( -name "config.*" -o -name "settings.*" \) ! -name "*.example" 2>/dev/null
  echo ""
  echo "--- Persistent state directories ---"
  find "$KAALIYO_DIR" -type d \( -iname "data" -o -iname "state" -o -iname "storage" -o -iname "uploads" \) 2>/dev/null
} > "6_data_state.txt"

echo "  -> 6_data_state.txt"

# ============================================================================
# EXTERNAL CONNECTIONS
# ============================================================================
echo ""
echo "[7/9] Mapping external connections..."

{
  echo "=== External services Kaaliyo connects to ==="
  echo "(These need verification on new server)"
  echo ""
  echo "--- URLs / hostnames in code ---"
  grep -rhE "https?://[a-zA-Z0-9.-]+" "$KAALIYO_DIR" \
    --include="*.py" --include="*.js" --include="*.ts" --include="*.env*" \
    --exclude-dir=node_modules --exclude-dir=__pycache__ --exclude-dir=.git --exclude-dir=venv 2>/dev/null \
    | grep -oE "https?://[a-zA-Z0-9.-]+" \
    | sort -u | head -30
  echo ""
  echo "--- Database connection strings ---"
  grep -rhnE "(postgres|mysql|mongodb|redis)://" "$KAALIYO_DIR" \
    --include="*.py" --include="*.js" --include="*.env*" \
    --exclude-dir=node_modules --exclude-dir=.git 2>/dev/null \
    | sed 's/:[^:@]*@/:****@/g' | head -10
  echo ""
  echo "--- Webhook URLs / callback URLs ---"
  grep -rhE "webhook|callback" "$KAALIYO_DIR" \
    --include="*.py" --include="*.js" --include="*.env*" \
    --exclude-dir=node_modules --exclude-dir=.git 2>/dev/null | head -10
} > "7_external_connections.txt"

echo "  -> 7_external_connections.txt"

# ============================================================================
# WHAT TO MIGRATE — CLEAN MANIFEST
# ============================================================================
echo ""
echo "[8/9] Generating clean migration manifest..."

{
  echo "# Kaaliyo Clean Migration Manifest"
  echo ""
  echo "Generated: $(date -u)"
  echo "Source: $KAALIYO_DIR"
  echo ""
  echo "## What to INCLUDE in migration tarball"
  echo ""
  echo "### Code"
  find "$KAALIYO_DIR" -maxdepth 4 -type f \( -name "*.py" -o -name "*.js" -o -name "*.ts" -o -name "*.html" -o -name "*.css" \) \
    ! -path "*/node_modules/*" ! -path "*/__pycache__/*" ! -path "*/.git/*" ! -path "*/venv/*" \
    2>/dev/null | wc -l | xargs echo "Code files:"
  echo ""
  echo "### Config (sanitized)"
  echo "- requirements.txt / package.json / Pipfile"
  echo "- All *.example config files"
  echo "- Templates and example envs (.env.example)"
  echo ""
  echo "### Data (decide case-by-case)"
  find "$KAALIYO_DIR" -type f \( -name "*.db" -o -name "*.sqlite*" \) 2>/dev/null \
    | xargs ls -lh 2>/dev/null | head -10
  echo ""
  echo "## What to EXCLUDE from migration tarball"
  echo ""
  echo "- venv/, .venv/, env/ (recreate on new server)"
  echo "- node_modules/ (recreate via npm install)"
  echo "- __pycache__, *.pyc, .pytest_cache (regenerable)"
  echo "- logs/, *.log (start fresh on new server)"
  echo "- .git/ (optional — if using git deploy, get from GitHub instead)"
  echo "- Trading history files older than retention requirement"
  echo ""
  echo "## What to TRANSFER SEPARATELY (NOT in tarball)"
  echo ""
  echo "- .env files (secure transfer: scp directly, or set up via secrets manager)"
  echo "- API keys (AliceBlue, broker credentials, Claude API key)"
  echo "- SSL certificates (use Let's Encrypt fresh on new server)"
  echo "- Database backups (separate logical dump, not file-level copy)"
  echo ""
  echo "## New server setup checklist"
  echo ""
  echo "- [ ] Provision VPS with same OS family (Ubuntu 24 recommended for parity)"
  echo "- [ ] Install Python 3.12 + Node.js (versions match current)"
  echo "- [ ] Install system deps: build-essential, libssl-dev, libffi-dev, etc."
  echo "- [ ] Create user: kaaliyo:kaaliyo (don't run as root)"
  echo "- [ ] Set up systemd service file"
  echo "- [ ] Set up nginx with SSL via Let's Encrypt"
  echo "- [ ] Configure UFW firewall (allow 22, 80, 443)"
  echo "- [ ] Transfer .env separately via scp"
  echo "- [ ] Verify connections to OpenAlgo, AliceBlue, Claude API"
  echo "- [ ] Set up monitoring (next section)"
  echo "- [ ] DNS cutover only after full validation"
} > "8_migration_manifest.md"

echo "  -> 8_migration_manifest.md"

# ============================================================================
# CLEAN-EXPORT SCRIPT TEMPLATE
# ============================================================================
echo ""
echo "[9/9] Generating clean-export script (for actual migration)..."

cat > "9_clean_export.sh" << EXPORT_SCRIPT
#!/bin/bash
# Clean Kaaliyo Export — generated by migration audit
# Review this script before running.
# It creates a tarball with ONLY what's needed for migration.

set -euo pipefail

KAALIYO_DIR="$KAALIYO_DIR"
EXPORT_DIR="/root/kaaliyo_clean_export"
TIMESTAMP=\$(date -u +"%Y%m%d_%H%M%S")
LABEL="kaaliyo_migration_\${TIMESTAMP}"

mkdir -p "\$EXPORT_DIR"

echo "Creating clean export tarball (excludes cruft)..."
tar --exclude='*/node_modules' \\
    --exclude='*/__pycache__' \\
    --exclude='*/.pytest_cache' \\
    --exclude='*/.mypy_cache' \\
    --exclude='*/venv' \\
    --exclude='*/.venv' \\
    --exclude='*/env' \\
    --exclude='*.pyc' \\
    --exclude='*.log' \\
    --exclude='*.log.*' \\
    --exclude='*/logs' \\
    --exclude='*/.git' \\
    --exclude='*.bak' \\
    --exclude='*.old' \\
    --exclude='*~' \\
    --exclude='.env' \\
    --exclude='.env.local' \\
    --exclude='.env.production' \\
    -czf "\$EXPORT_DIR/\${LABEL}_code.tar.gz" \\
    -C "\$(dirname \$KAALIYO_DIR)" \\
    "\$(basename \$KAALIYO_DIR)"

# Separately tarball .env files (KEEP RESTRICTED)
echo "Tarball .env files separately (restricted)..."
find "\$KAALIYO_DIR" -name ".env*" -type f -print0 2>/dev/null \\
  | tar --null -czf "\$EXPORT_DIR/\${LABEL}_envs.tar.gz" --files-from -
chmod 600 "\$EXPORT_DIR/\${LABEL}_envs.tar.gz"

# Tarball databases separately
echo "Tarball databases separately..."
find "\$KAALIYO_DIR" -type f \( -name "*.db" -o -name "*.sqlite*" \) -print0 2>/dev/null \\
  | tar --null -czf "\$EXPORT_DIR/\${LABEL}_data.tar.gz" --files-from - 2>/dev/null \\
  || echo "(no databases found)"

# Generate checksums
cd "\$EXPORT_DIR"
sha256sum \${LABEL}_*.tar.gz > "\${LABEL}.sha256"

# Generate manifest
{
  echo "Migration package: \$LABEL"
  echo "Source: \$KAALIYO_DIR"
  echo "Generated: \$(date -u)"
  echo ""
  echo "Contents:"
  ls -lh \${LABEL}_*.tar.gz
  echo ""
  echo "Checksums:"
  cat "\${LABEL}.sha256"
} > "\${LABEL}_manifest.txt"

cat "\${LABEL}_manifest.txt"

echo ""
echo "Export complete: \$EXPORT_DIR/\$LABEL*"
echo ""
echo "Transfer to new server:"
echo "  scp \$EXPORT_DIR/\${LABEL}_* root@NEW_SERVER:/root/"
echo ""
echo "On new server, transfer .env SEPARATELY through a secure channel."
EXPORT_SCRIPT
chmod +x "9_clean_export.sh"

echo "  -> 9_clean_export.sh"

# ============================================================================
# DONE
# ============================================================================
echo ""
echo "================================================================"
echo "AUDIT COMPLETE: $AUDIT_DIR"
echo "================================================================"
ls -la "$AUDIT_DIR"
echo ""
echo "Review the audit files, then when ready run:"
echo "  $AUDIT_DIR/9_clean_export.sh"
echo ""
echo "Download to local:"
echo "  scp -r root@SERVER:$AUDIT_DIR ~/Downloads/"
echo "================================================================"
