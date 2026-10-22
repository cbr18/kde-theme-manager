#!/usr/bin/env bash
set -euo pipefail

say() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }

# --help / -h
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'EOF'
Usage: uninstall-theme-profile-kit.sh [OPTIONS]

Uninstall theme-profile-kit: remove scripts and the GUI from the home
directory, plus the theme-profile data directory.

Options:
  --no-gui       Keep the GUI (remove scripts and data only)
  -f, --force    Skip confirmation prompt.
  -h, --help     Show this help message and exit.
EOF
  exit 0
fi

# --force / -f: auto-confirm
FORCE=0
WITH_GUI=1
for arg in "$@"; do
  case "$arg" in
    -f | --force) FORCE=1 ;;
    --no-gui) WITH_GUI=0 ;;
    *)
      printf 'Unknown option: %s\n' "$arg" >&2
      exit 2
      ;;
  esac
done

BINDIR="${XDG_BIN_HOME:-$HOME/.local/bin}"
CONFIGDIR="${XDG_CONFIG_HOME:-$HOME/.config}"
THEMEDIR="$CONFIGDIR/theme-profile"
# A pre-XDG installation may still live under ~/.config.
if [ ! -d "$THEMEDIR" ] && [ -n "${XDG_CONFIG_HOME:-}" ] && [ -d "${HOME}/.config/theme-profile" ]; then
  THEMEDIR="${HOME}/.config/theme-profile"
fi
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Ask before deleting anything.  The previous order removed the GUI first and
# only then asked, so answering "no" left a half-uninstalled application.
if [ "$FORCE" -eq 0 ] && [ -e "$THEMEDIR" ]; then
  read -r -p "This will remove all profiles, backups, and metadata in $THEMEDIR. Continue? [y/N] " resp
  case "$resp" in
    [yY]*) ;;
    *) say "Aborted."; exit 0 ;;
  esac
fi

if [ "$WITH_GUI" -eq 1 ] && [ -x "$SCRIPT_DIR/uninstall-kde-theme-manager.sh" ]; then
  "$SCRIPT_DIR/uninstall-kde-theme-manager.sh" --force
fi

say "Удаление исполняемых файлов"
rm -f "$BINDIR/theme-profile"
rm -f "$BINDIR/theme-menu"
rm -f "$BINDIR/wallpaper-picker"
rm -f "$BINDIR/wallpaper-next"
rm -f "$BINDIR/wallpaper-prev"

say "Removing: $THEMEDIR"
rm -rf "$THEMEDIR"

say "Готово. theme-profile-kit полностью удалён."
say "Конфиги wofi ($CONFIGDIR/wofi/*.css) и настройки приложений не тронуты."