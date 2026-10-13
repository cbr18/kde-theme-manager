#!/usr/bin/env bash
set -euo pipefail

say() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }

BINDIR="${XDG_BIN_HOME:-$HOME/.local/bin}"
SHAREDIR="$HOME/.local/share"
DESKTOPDIR="$HOME/.local/share/applications"
THEMEDIR="$HOME/.config/theme-profile"

# ─── 1. Remove bash scripts ───
say "Removing bash scripts..."
rm -f "$BINDIR/theme-profile"
rm -f "$BINDIR/theme-menu"
rm -f "$BINDIR/wallpaper-picker"
rm -f "$BINDIR/wallpaper-next"
rm -f "$BINDIR/wallpaper-prev"

# ─── 2. Remove Qt app ───
say "Removing Qt application..."
rm -f "$BINDIR/kde-theme-manager"
rm -rf "$SHAREDIR/theme-profile-manager"
rm -f "$DESKTOPDIR/kde-theme-manager.desktop"

# ─── 3. Update desktop database ───
if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$DESKTOPDIR" 2>/dev/null || true
fi

# ─── 4. Remove profiles, backups, metadata ───
say "Removing profiles, backups, and metadata..."
rm -rf "$THEMEDIR"

say "Done. theme-profile-kit fully removed."
say "WoFi configs (.config/wofi/*.css) and app settings untouched."
say "User preferences: ~/.config/theme-profile/app-preferences.json (removed with THEMEDIR)"