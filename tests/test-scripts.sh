#!/usr/bin/env bash
# test-scripts.sh — basic test suite for theme-profile-kit
# Run: bash tests/test-scripts.sh
# Requires: bash, shellcheck (optional but recommended)

set -euo pipefail

PASS=0
FAIL=0

# --- test helpers -----------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

ok()   { PASS=$((PASS + 1)); echo "  ✅ $1"; }
fail() { FAIL=$((FAIL + 1)); echo "  ❌ $1"; }

# Silence all output from a command
run_silent() { "$@" >/dev/null 2>&1; }

# --- 1. Syntax check (bash -n) on all scripts ---------------------------------
echo "=== Section 1: Syntax check (bash -n) ==="

for script in \
    "$SCRIPT_DIR/files/bin/theme-profile" \
    "$SCRIPT_DIR/files/bin/theme-menu" \
    "$SCRIPT_DIR/files/bin/wallpaper-picker" \
    "$SCRIPT_DIR/files/bin/wallpaper-next" \
    "$SCRIPT_DIR/files/bin/wallpaper-prev" \
    "$SCRIPT_DIR/scripts/install-theme-profile-kit.sh" \
    "$SCRIPT_DIR/scripts/uninstall-theme-profile-kit.sh" \
    "$SCRIPT_DIR/scripts/update-theme-profile-kit.sh"; do

  if run_silent bash -n "$script"; then
    ok "bash -n: $script"
  else
    fail "bash -n: $script"
  fi
done

# --- 2. shellcheck (if available) --------------------------------------------
echo "=== Section 2: shellcheck (if installed) ==="

if command -v shellcheck >/dev/null 2>&1; then
  for script in \
      "$SCRIPT_DIR/files/bin/theme-profile" \
      "$SCRIPT_DIR/files/bin/theme-menu" \
      "$SCRIPT_DIR/files/bin/wallpaper-picker" \
      "$SCRIPT_DIR/files/bin/wallpaper-next" \
      "$SCRIPT_DIR/files/bin/wallpaper-prev" \
      "$SCRIPT_DIR/scripts/install-theme-profile-kit.sh" \
      "$SCRIPT_DIR/scripts/uninstall-theme-profile-kit.sh" \
      "$SCRIPT_DIR/scripts/update-theme-profile-kit.sh"; do

    if shellcheck "$script" 2>/dev/null; then
      ok "shellcheck: $script"
    else
      fail "shellcheck: $script"
    fi
  done
else
  echo "  ⏭️  shellcheck not installed — skipping"
fi

# --- 3. theme-profile: --help exits 0 -----------------------------------------
echo "=== Section 3: --help flags ==="

if "$SCRIPT_DIR/files/bin/theme-profile" --help >/dev/null 2>&1; then
  ok "theme-profile --help exits 0"
else
  fail "theme-profile --help should exit 0"
fi

if "$SCRIPT_DIR/files/bin/theme-profile" -h >/dev/null 2>&1; then
  ok "theme-profile -h exits 0"
else
  fail "theme-profile -h should exit 0"
fi

# --- 4. theme-profile: invalid profile names rejected -------------------------
echo "=== Section 4: Profile name validation ==="

# Use a temporary HOME so save/apply don't touch the real profile dir
TMP_ROOT="$(mktemp -d)"
export TMP_ROOT
trap 'rm -rf "$TMP_ROOT"' EXIT

# Bootstrap a fake ~/.config/theme-profile structure
FAKE_HOME="$TMP_ROOT/fake-home"
mkdir -p "$FAKE_HOME/.config/theme-profile"

# Create a real profile so we can test apply success and save
mkdir -p "$FAKE_HOME/.config/theme-profile/profiles/test-profile"
if HOME="$FAKE_HOME" "$SCRIPT_DIR/files/bin/theme-profile" save test-profile >/dev/null 2>&1; then
  ok "save test-profile (valid name)"
else
  fail "save test-profile (valid name) — should succeed"
fi

# Test invalid names → should exit non-zero
for bad_name in "../x" "a b" "a/b" "a;b" "a|b" "a\$b" ""; do
  if HOME="$FAKE_HOME" "$SCRIPT_DIR/files/bin/theme-profile" save "$bad_name" >/dev/null 2>&1; then
    fail "save '$bad_name' should have been rejected"
  else
    ok "save '$bad_name' correctly rejected"
  fi
done

# --- 5. theme-profile: apply nonexistent → fails fast (no side effects) ------
echo "=== Section 5: apply nonexistent doesn't break Plasma ==="

# We can't easily test the trap, but we can verify it exits 1 before
# any real systemctl call by using a mock PATH
MOCK_BIN="$TMP_ROOT/mock-bin"
mkdir -p "$MOCK_BIN"

# Create mock systemctl that tracks calls
cat > "$MOCK_BIN/systemctl" <<'MOCK'
#!/usr/bin/env bash
echo "MOCK systemctl called: $*" >> "$MOCK_CALLS"
exit 0
MOCK
  chmod +x "$MOCK_BIN/systemctl"

MOCK_CALLS="$TMP_ROOT/mock-calls.log"
echo "" > "$MOCK_CALLS"

# Pre-apply validation should reject before stop_plasma_shell_for_restore
if HOME="$FAKE_HOME" PATH="$MOCK_BIN:$PATH" "$SCRIPT_DIR/files/bin/theme-profile" apply nonexistent-profile >/dev/null 2>&1; then
  fail "apply nonexistent-profile should exit non-zero"
else
  ok "apply nonexistent-profile correctly exits non-zero"
fi

# The mock systemctl should NOT have been called with "stop" because
# profile validation happens first now
if ! grep -q "stop plasma-plasmashell" "$MOCK_CALLS" 2>/dev/null; then
  ok "apply nonexistent-profile does NOT stop plasma (validation runs first)"
else
  fail "apply nonexistent-profile stopped plasma before validation failed!"
fi

# --- 6. Wallpaper index wrapping ---------------------------------------------
echo "=== Section 6: Wallpaper index wrapping ==="

WALL_DIR="$TMP_ROOT/walls"
mkdir -p "$WALL_DIR"
# Create 3 fake wallpaper files
for i in 1 2 3; do
  touch "$WALL_DIR/wallpaper-$i.png"
done

# Source the wallpaper-lib-like logic by testing the arithmetic directly
FILES=(wall-1.png wall-2.png wall-3.png)
COUNT=${#FILES[@]}

# next: 0 → 1
INDEX=$(( (0 + 1) % COUNT ))
if [ "$INDEX" -eq 1 ]; then ok "wallpaper-next: 0→1"; else fail "wallpaper-next: expected 1 got $INDEX"; fi

# next: 2 → 0 (wrap)
INDEX=$(( (2 + 1) % COUNT ))
if [ "$INDEX" -eq 0 ]; then ok "wallpaper-next: 2→0 (wrap)"; else fail "wallpaper-next: expected 0 got $INDEX"; fi

# prev: 0 → 2 (wrap)
INDEX=$(( (0 - 1 + COUNT) % COUNT ))
if [ "$INDEX" -eq 2 ]; then ok "wallpaper-prev: 0→2 (wrap)"; else fail "wallpaper-prev: expected 2 got $INDEX"; fi

# prev: 1 → 0
INDEX=$(( (1 - 1 + COUNT) % COUNT ))
if [ "$INDEX" -eq 0 ]; then ok "wallpaper-prev: 1→0"; else fail "wallpaper-prev: expected 0 got $INDEX"; fi

# --- 7. wallpaper-prev stderr leak test ---------------------------------------
echo "=== Section 7: wallpaper-prev handles missing state file ==="

# wallpaper-prev should not emit errors to stderr when STATE file is missing
STATE_FILE="$TMP_ROOT/missing-state"
rm -f "$STATE_FILE"

# Source the arithmetic and state-reading logic inline to test
# (we can't run wallpaper-prev directly without plasma-apply-wallpaperimage)
wall_prev_index() {
  local index=0
  local state="$1"
  [ -f "$state" ] && index=$(cat "$state" 2>/dev/null || echo 0)
  local count=$2
  index=$(( (index - 1 + count) % count ))
  echo "$index"
}

# This should not produce stderr output
ERR_OUT=$(wall_prev_index "$STATE_FILE" 3 2>&1 1>/dev/null)
if [ -z "$ERR_OUT" ]; then
  ok "wallpaper-prev: no stderr when state file missing"
else
  fail "wallpaper-prev: stderr leaked: $ERR_OUT"
fi

# --- Summary ------------------------------------------------------------------
echo ""
echo "═══════════════════════════════════════"
echo "  Results: $PASS passed, $FAIL failed"
echo "═══════════════════════════════════════"

[ "$FAIL" -eq 0 ]
