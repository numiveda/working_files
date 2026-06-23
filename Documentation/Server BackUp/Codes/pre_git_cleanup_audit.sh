#!/bin/bash
# Astro Engine pre-git cleanup
# Run on VPS as root in /opt/astro
# 
# DOES NOT DELETE ANYTHING — only catalogs what would be cleaned.
# Generates a report so you can decide what to keep.

set -euo pipefail

cd /opt/astro

REPORT="/tmp/git_cleanup_report.txt"

{
  echo "=================================================="
  echo "Pre-git cleanup audit for /opt/astro"
  echo "Generated: $(date -u)"
  echo "=================================================="
  echo ""
  
  echo "## SUMMARY"
  echo ""
  TOTAL=$(find . -type f -not -path "./__pycache__/*" -not -path "./_backup*/*" -not -path "./remedies_data/*" -not -path "./remedies_esoteric/*" | wc -l)
  PROD=$(find . -maxdepth 1 -name "*.py" -type f ! -name "*.py.*" ! -name "main_patches_*" ! -name "patch_*" ! -name "hotfix_*" ! -name "preflight_*" | wc -l)
  BACKUPS=$(find . -maxdepth 1 -name "*.py.*" -type f | wc -l)
  PATCHES=$(find . -maxdepth 1 \( -name "patch_*.py" -o -name "hotfix_*.py" -o -name "preflight_*.py" -o -name "main_patches_*.py" \) -type f | wc -l)
  BACKUP_DIRS=$(find . -maxdepth 1 -type d -name "_backup*" | wc -l)
  
  echo "  Total files (excluding pycache/data dirs): $TOTAL"
  echo "  Production .py files:    $PROD"
  echo "  Backup snapshot files:   $BACKUPS    (e.g. main.py.before_xyz_*)"
  echo "  Patch/hotfix files:      $PATCHES    (development artifacts)"
  echo "  Backup directories:      $BACKUP_DIRS  (_backup_hotfix_*)"
  echo ""
  
  echo "## CATEGORY 1: PRODUCTION CODE (KEEP IN GIT) — $PROD files"
  echo "These are the live working modules currently used by the engine."
  echo ""
  find . -maxdepth 1 -name "*.py" -type f ! -name "*.py.*" ! -name "main_patches_*" ! -name "patch_*" ! -name "hotfix_*" ! -name "preflight_*" \
    | sort \
    | while read f; do
      printf "  %s  (%s)\n" "$f" "$(du -h "$f" | cut -f1)"
    done
  echo ""
  
  echo "## CATEGORY 2: DATA DIRECTORIES (KEEP IN GIT)"
  echo ""
  find . -maxdepth 1 -type d ! -name "." ! -name "__pycache__" ! -name "_backup*" \
    | sort \
    | while read d; do
      printf "  %s  (%s, %s files)\n" "$d" "$(du -sh "$d" | cut -f1)" "$(find "$d" -type f | wc -l)"
    done
  echo ""
  
  echo "## CATEGORY 3: BACKUP SNAPSHOTS (EXCLUDE FROM GIT) — $BACKUPS files"
  echo "These are filesystem-based versioning. Git replaces this entirely."
  echo "Recommendation: archive to a tarball, then remove."
  echo ""
  echo "  Sample (showing first 20):"
  find . -maxdepth 1 -name "*.py.*" -type f | sort | head -20 | while read f; do
      printf "    %s  (%s)\n" "$f" "$(du -h "$f" | cut -f1)"
  done
  echo "  ... and $((BACKUPS - 20)) more"
  echo ""
  TOTAL_BACKUP_SIZE=$(find . -maxdepth 1 -name "*.py.*" -type f -exec du -b {} \; | awk '{sum+=$1} END {print sum}')
  TOTAL_BACKUP_SIZE_MB=$((TOTAL_BACKUP_SIZE / 1024 / 1024))
  echo "  Total size of all backup snapshots: ${TOTAL_BACKUP_SIZE_MB} MB"
  echo ""
  
  echo "## CATEGORY 4: PATCH/HOTFIX SCRIPTS (DECIDE PER FILE) — $PATCHES files"
  echo "These are F1-F11 hotfix development artifacts."
  echo "Options:"
  echo "  (a) Keep in repo for historical reference"
  echo "  (b) Move to a /legacy/ subdirectory"
  echo "  (c) Archive separately and exclude"
  echo ""
  find . -maxdepth 1 \( -name "patch_*.py" -o -name "hotfix_*.py" -o -name "preflight_*.py" -o -name "main_patches_*.py" \) -type f \
    | sort \
    | while read f; do
      printf "  %s  (%s)\n" "$f" "$(du -h "$f" | cut -f1)"
    done
  echo ""
  
  echo "## CATEGORY 5: BACKUP DIRECTORIES (EXCLUDE FROM GIT) — $BACKUP_DIRS dirs"
  echo "Recommendation: archive separately and remove."
  echo ""
  find . -maxdepth 1 -type d -name "_backup*" | sort | while read d; do
      printf "  %s  (%s, %s files)\n" "$d" "$(du -sh "$d" | cut -f1)" "$(find "$d" -type f | wc -l)"
  done
  echo ""
  
  echo "## CATEGORY 6: ZERO-BYTE / WEIRD FILES (REVIEW)"
  echo ""
  find . -maxdepth 1 -size 0 -type f 2>/dev/null | while read f; do
      echo "  $f  (zero bytes)"
  done
  echo ""
  
  echo "=================================================="
  echo "## RECOMMENDED ACTIONS"
  echo "=================================================="
  echo ""
  echo "BEFORE git init, run these steps:"
  echo ""
  echo "1. Archive all backups + patches to /root/astro_archive/ (so you keep history):"
  echo "   mkdir -p /root/astro_archive"
  echo "   cd /opt/astro"
  echo "   mv *.py.* /root/astro_archive/                  # all backup snapshots"
  echo "   mv _backup* /root/astro_archive/                # backup directories"
  echo "   mv patch_*.py hotfix_*.py preflight_*.py main_patches_*.py /root/astro_archive/  # patches"
  echo "   rm -f scp                                       # zero-byte file"
  echo ""
  echo "2. Tarball the archive:"
  echo "   cd /root"
  echo "   tar -czf astro_archive_pre_git_$(date +%Y%m%d).tar.gz astro_archive/"
  echo "   # rclone copy astro_archive_pre_git_*.tar.gz gdrive:numiveda_backups/astro_vps/archives/"
  echo ""
  echo "3. NOW you have a clean /opt/astro/ ready for git init."
  echo ""
} > "$REPORT"

cat "$REPORT"
echo ""
echo "Report saved to: $REPORT"
