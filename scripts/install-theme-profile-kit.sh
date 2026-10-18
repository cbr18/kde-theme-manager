#!/usr/bin/env bash
set -euo pipefail

say() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC_DIR="$KIT_DIR/files/bin"
DEST_DIR="$HOME/.local/bin"
BACKUP_ROOT="$HOME/.config/theme-profile/backups"
BACKUP_DIR="$BACKUP_ROOT/deploy-theme-profile-kit-$(date +%Y%m%d-%H%M%S)"

# --help / -h
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'EOF'
Usage: install-theme-profile-kit.sh [OPTIONS]

Install theme-profile-kit scripts to ~/.local/bin with backup of existing files.

Options:
  -h, --help    Show this help message and exit.

Scripts installed:
  theme-profile, theme-menu, wallpaper-picker, wallpaper-next, wallpaper-prev
EOF
  exit 0
fi

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
