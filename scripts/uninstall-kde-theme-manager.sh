#!/usr/bin/env bash
# uninstall-kde-theme-manager.sh — remove the GUI, its launcher and its desktop
# entry. Profiles, backups and settings in ~/.config/theme-profile/ are left
# alone (uninstall-theme-profile-kit.sh removes those).

set -euo pipefail

say() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }

BINDIR="${XDG_BIN_HOME:-$HOME/.local/bin}"
DATADIR="${XDG_DATA_HOME:-$HOME/.local/share}"
APPDIR="$DATADIR/kde-theme-manager"
LEGACY_APPDIR="$DATADIR/theme-profile-manager"
APPSDIR="$DATADIR/applications"
ICON="$DATADIR/icons/hicolor/scalable/apps/ktm-theme-manager.svg"
# Name used before the rename (KDE's icon loader mangled "kde-*" names).
LEGACY_ICON="$DATADIR/icons/hicolor/scalable/apps/kde-theme-manager.svg"
MARKER=".installed-by-theme-profile-kit"

usage() {
  cat <<'EOF'
Usage: uninstall-kde-theme-manager.sh [OPTIONS]

Remove the KDE Theme Manager GUI, its launcher and its desktop entry.

Options:
  -f, --force    Skip the confirmation prompt.
  -h, --help     Show this help message and exit.

Removed:
  ~/.local/share/kde-theme-manager/
  ~/.local/bin/kde-theme-manager
  ~/.local/share/applications/kde-theme-manager.desktop
  ~/.local/share/icons/hicolor/scalable/apps/ktm-theme-manager.svg

Kept: ~/.config/theme-profile/ (profiles, backups, settings) and the
theme-profile / wallpaper-* scripts.
EOF
}

FORCE=0
while [ $# -gt 0 ]; do
  case "$1" in
    -h | --help)
      usage
      exit 0
      ;;
    -f | --force) FORCE=1 ;;
    *)
      say "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

if [ "$FORCE" -eq 0 ]; then
  printf 'Remove the KDE Theme Manager app from %s? [y/N] ' "$APPDIR"
  read -r reply
  case "$reply" in
    [yY]*) ;;
    *)
      say "Aborted."
      exit 0
      ;;
  esac
fi

say "Removing launcher"
rm -f "$BINDIR/kde-theme-manager"

say "Removing desktop entry and icon"
rm -f "$APPSDIR/kde-theme-manager.desktop"
rm -f "$ICON"
rm -f "$LEGACY_ICON"

# Only delete directories this installer created: a wrong XDG_DATA_HOME must
# not turn into `rm -rf` of somebody else's tree.
remove_appdir() { # dir label
  [ -e "$1" ] || return 0
  if [ ! -f "$1/$MARKER" ] && [ ! -f "$1/src/__main__.py" ]; then
    say "Skipping $1 (does not look like an app install)"
    return 0
  fi
  say "Removing $2 ($1)"
  rm -rf "$1"
}

remove_appdir "$APPDIR" "application"
remove_appdir "$LEGACY_APPDIR" "obsolete application copy"

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$APPSDIR" 2>/dev/null || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
  gtk-update-icon-cache -f -t "$DATADIR/icons/hicolor" >/dev/null 2>&1 || true
fi

say "Done. Данные профилей в ~/.config/theme-profile/ не тронуты."
