#!/usr/bin/env bash
# mac-security-check — chạy sau khi nghi ngờ chạy tool rác
# Usage: bash check.sh [--json]

set -euo pipefail

RED='\033[0;31m'; YEL='\033[1;33m'; GRN='\033[0;32m'; CYN='\033[0;36m'; NC='\033[0m'
JSON_MODE=false
[[ "${1:-}" == "--json" ]] && JSON_MODE=true

log()  { $JSON_MODE || echo -e "$1"; }
warn() { $JSON_MODE || echo -e "${YEL}[WARN]${NC} $1"; }
bad()  { $JSON_MODE || echo -e "${RED}[BAD] ${NC} $1"; }
ok()   { $JSON_MODE || echo -e "${GRN}[OK]  ${NC} $1"; }
head() { $JSON_MODE || echo -e "\n${CYN}=== $1 ===${NC}"; }

FINDINGS=()
add() { FINDINGS+=("$1"); }

# ── 1. System info ────────────────────────────────────────────────
head "SYSTEM INFO"
sw_vers 2>/dev/null || true
log "Kernel: $(uname -r)"

# ── 2. FileVault ──────────────────────────────────────────────────
head "DISK ENCRYPTION (FileVault)"
FV=$(fdesetup status 2>/dev/null || echo "unknown")
if echo "$FV" | grep -qi "on"; then
  ok "FileVault ON"
else
  bad "FileVault OFF — dữ liệu không được mã hóa"
  add "FileVault OFF"
fi

# ── 3. Firewall ───────────────────────────────────────────────────
head "FIREWALL"
FW=$(/usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate 2>/dev/null || echo "unknown")
if echo "$FW" | grep -qi "enabled"; then
  ok "Application Firewall ON"
else
  bad "Application Firewall OFF"
  add "Firewall OFF"
fi

# stealth mode
SM=$(/usr/libexec/ApplicationFirewall/socketfilterfw --getstealthmode 2>/dev/null || echo "unknown")
echo "  Stealth mode: $SM"

# ── 4. SIP (System Integrity Protection) ─────────────────────────
head "SYSTEM INTEGRITY PROTECTION"
SIP=$(csrutil status 2>/dev/null || echo "unknown")
if echo "$SIP" | grep -qi "enabled"; then
  ok "SIP enabled"
else
  bad "SIP DISABLED — nguy hiểm!"
  add "SIP disabled"
fi

# ── 5. Listening ports ────────────────────────────────────────────
head "LISTENING PORTS (TCP)"
lsof -nP -iTCP -sTCP:LISTEN 2>/dev/null | head -40 || true

# ── 6. Suspicious processes ───────────────────────────────────────
head "SUSPICIOUS PROCESSES"
SUSPECT_PATTERNS="ngrok|frp|ncat|netcat|socat|meterpreter|cobalt|beacon|reverse_shell|cryptominer|xmrig|minerd"
PROCS=$(ps aux | grep -iE "$SUSPECT_PATTERNS" | grep -v grep || true)
if [[ -n "$PROCS" ]]; then
  bad "Tìm thấy process khả nghi:"
  echo "$PROCS"
  add "Suspicious process found"
else
  ok "Không có process khả nghi"
fi

# ── 7. LaunchAgents / LaunchDaemons (persistence) ─────────────────
head "LAUNCH AGENTS & DAEMONS (startup persistence)"
LAUNCH_DIRS=(
  "$HOME/Library/LaunchAgents"
  "/Library/LaunchAgents"
  "/Library/LaunchDaemons"
)
RECENT_PLIST=()
for dir in "${LAUNCH_DIRS[@]}"; do
  if [[ -d "$dir" ]]; then
    # files modified in last 7 days
    while IFS= read -r f; do
      RECENT_PLIST+=("$f")
    done < <(find "$dir" -name "*.plist" -newer /tmp -mtime -7 2>/dev/null || true)
    COUNT=$(find "$dir" -name "*.plist" 2>/dev/null | wc -l | tr -d ' ')
    log "  $dir: $COUNT items"
  fi
done

if [[ ${#RECENT_PLIST[@]} -gt 0 ]]; then
  warn "Plist mới (7 ngày qua) — kiểm tra thủ công:"
  for p in "${RECENT_PLIST[@]}"; do warn "  $p"; done
  add "New LaunchAgent/Daemon plist found"
else
  ok "Không có plist mới gần đây"
fi

# ── 8. Login items ────────────────────────────────────────────────
head "LOGIN ITEMS"
osascript -e 'tell application "System Events" to get the name of every login item' 2>/dev/null || echo "  (cần quyền Accessibility hoặc Full Disk Access)"

# ── 9. Network interfaces & unusual connections ───────────────────
head "ACTIVE NETWORK CONNECTIONS (ESTABLISHED)"
lsof -nP -iTCP -sTCP:ESTABLISHED 2>/dev/null | head -30 || true

# ── 10. Recently modified files in sensitive areas ────────────────
head "FILES MODIFIED IN LAST 24H (sensitive paths)"
SENSITIVE_DIRS=(
  "$HOME/.ssh"
  "$HOME/.bash_profile" "$HOME/.zshrc" "$HOME/.zprofile"
  "/etc/hosts"
  "/etc/crontab"
)
for f in "${SENSITIVE_DIRS[@]}"; do
  if [[ -e "$f" ]] && find "$f" -newer /tmp -mtime -1 2>/dev/null | grep -q .; then
    warn "Modified recently: $f"
    add "Sensitive file modified: $f"
  fi
done

# crontab
CRON=$(crontab -l 2>/dev/null || true)
if [[ -n "$CRON" ]]; then
  warn "Crontab có entries — kiểm tra:"
  echo "$CRON"
  add "Crontab not empty"
else
  ok "Crontab trống"
fi

# ── 11. Sudoers / privilege escalation ───────────────────────────
head "SUDO ACCESS"
sudo -l 2>/dev/null | head -20 || echo "  (không có quyền hoặc không config)"

# ── 12. Auto-update ───────────────────────────────────────────────
head "AUTO SOFTWARE UPDATE"
AU=$(defaults read /Library/Preferences/com.apple.SoftwareUpdate AutomaticCheckEnabled 2>/dev/null || echo "unknown")
if [[ "$AU" == "1" ]]; then
  ok "Auto-update check: ON"
else
  warn "Auto-update check: OFF — nên bật"
  add "Auto-update OFF"
fi

# ── Summary ───────────────────────────────────────────────────────
echo ""
echo -e "${CYN}══════════════════════════════════════${NC}"
echo -e "${CYN}          SUMMARY${NC}"
echo -e "${CYN}══════════════════════════════════════${NC}"
if [[ ${#FINDINGS[@]} -eq 0 ]]; then
  echo -e "${GRN}✓ Không tìm thấy vấn đề rõ ràng${NC}"
else
  echo -e "${RED}Cần chú ý (${#FINDINGS[@]} items):${NC}"
  for f in "${FINDINGS[@]}"; do echo -e "  ${RED}•${NC} $f"; done
fi
echo ""
echo "Chạy xong: $(date)"
echo "Nếu thấy bất thường, backup ngay và đổi password quan trọng."

# JSON output
if $JSON_MODE; then
  echo "{"
  echo "  \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\","
  echo "  \"findings\": ["
  for i in "${!FINDINGS[@]}"; do
    [[ $i -gt 0 ]] && echo ","
    echo -n "    \"${FINDINGS[$i]}\""
  done
  echo ""
  echo "  ]"
  echo "}"
fi
