#!/usr/bin/env bash
set -euo pipefail

say() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC_DIR="$KIT_DIR/files/bin"
DEST_DIR="${XDG_BIN_HOME:-$HOME/.local/bin}"
CONFIGDIR="${XDG_CONFIG_HOME:-$HOME/.config}"
BACKUP_ROOT="$CONFIGDIR/theme-profile/backups"
BACKUP_DIR="$BACKUP_ROOT/deploy-theme-profile-kit-$(date +%Y%m%d-%H%M%S)-$$"

# --help / -h
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'EOF'
Usage: install-theme-profile-kit.sh [OPTIONS]

Install theme-profile-kit: the command line scripts and (by default) the
KDE Theme Manager GUI with its launcher and desktop entry.

Options:
  --no-gui      Install only the scripts, skip the Qt/QML application
  --with-venv   Always build a venv inside the installed app (passed through)
  --no-venv     Never build a venv — use the system PySide6 (passed through)
  -h, --help    Show this help message and exit.

Scripts installed to ${XDG_BIN_HOME:-~/.local/bin}:
  theme-profile, theme-menu, wallpaper-picker, wallpaper-next, wallpaper-prev

The GUI is installed by scripts/install-kde-theme-manager.sh (see its --help
for paths, --with-venv/--no-venv and what gets installed).
EOF
  exit 0
fi

WITH_GUI=1
GUI_ARGS=()
for arg in "$@"; do
  case "$arg" in
    --no-gui) WITH_GUI=0 ;;
    --with-venv | --no-venv) GUI_ARGS+=("$arg") ;;
    *)
      say "Unknown option: $arg" >&2
      exit 2
      ;;
  esac
done

SCRIPTS=(
  "theme-profile"
  "theme-menu"
  "wallpaper-picker"
  "wallpaper-next"
  "wallpaper-prev"
)

say "Installing theme-profile-kit scripts"
mkdir -p "$DEST_DIR" "$BACKUP_DIR/bin"

# Validate all source files exist before doing anything
for script in "${SCRIPTS[@]}"; do
  if [ ! -f "$SRC_DIR/$script" ]; then
    say "Missing source: $SRC_DIR/$script" >&2
    exit 1
  fi
done

# Back up existing files
say "Backing up existing scripts..."
for script in "${SCRIPTS[@]}"; do
  if [ -e "$DEST_DIR/$script" ]; then
    cp -a "$DEST_DIR/$script" "$BACKUP_DIR/bin/$script"
  fi
done

# Install new scripts
for script in "${SCRIPTS[@]}"; do
  say "Installing $script"
  cp -a "$SRC_DIR/$script" "$DEST_DIR/$script"
  chmod 0755 "$DEST_DIR/$script"
done

say "Installed theme-profile-kit scripts to $DEST_DIR"
say "Backup: $BACKUP_DIR"

# ── GUI (Qt/QML app + launcher + desktop entry) ─────────────────────────────
if [ "$WITH_GUI" -eq 1 ]; then
  if [ -x "$KIT_DIR/scripts/install-kde-theme-manager.sh" ]; then
    "$KIT_DIR/scripts/install-kde-theme-manager.sh" ${GUI_ARGS[@]+"${GUI_ARGS[@]}"}
  else
    say "GUI installer not found — skipping the app (scripts only)."
  fi
else
  say "Skipped the GUI (--no-gui)."
fi
