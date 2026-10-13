#!/usr/bin/env bash
set -euo pipefail

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC_DIR="$KIT_DIR/files/bin"
DEST_DIR="$HOME/.local/bin"
BACKUP_ROOT="$HOME/.config/theme-profile/backups"
BACKUP_DIR="$BACKUP_ROOT/deploy-theme-profile-kit-$(date +%Y%m%d-%H%M%S)"

SCRIPTS=(
  "theme-profile"
  "theme-menu"
  "wallpaper-picker"
  "wallpaper-next"
  "wallpaper-prev"
)

mkdir -p "$DEST_DIR" "$BACKUP_DIR/bin"

for script in "${SCRIPTS[@]}"; do
  if [ ! -f "$SRC_DIR/$script" ]; then
    echo "Missing source: $SRC_DIR/$script" >&2
    exit 1
  fi
done

for script in "${SCRIPTS[@]}"; do
  if [ -e "$DEST_DIR/$script" ]; then
    cp -a "$DEST_DIR/$script" "$BACKUP_DIR/bin/$script"
  fi
done

for script in "${SCRIPTS[@]}"; do
  cp -a "$SRC_DIR/$script" "$DEST_DIR/$script"
  chmod 0755 "$DEST_DIR/$script"
done

echo "Installed theme-profile-kit scripts to $DEST_DIR"
echo "Backup: $BACKUP_DIR"
