#!/usr/bin/env bash
set -euo pipefail

say() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }

# --help / -h
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  cat <<'EOF'
Usage: uninstall-theme-profile-kit.sh [OPTIONS]

Uninstall theme-profile-kit: remove scripts from ~/.local/bin and theme-profile data directory.

Options:
  -f, --force    Skip confirmation prompt.
  -h, --help     Show this help message and exit.
EOF
  exit 0
fi

# --force / -f: auto-confirm
FORCE=0
if [ "${1:-}" = "--force" ] || [ "${1:-}" = "-f" ]; then
  FORCE=1
fi

BINDIR="${XDG_BIN_HOME:-$HOME/.local/bin}"
THEMEDIR="$HOME/.config/theme-profile"

say "Удаление исполняемых файлов"
rm -f "$BINDIR/theme-profile"
rm -f "$BINDIR/theme-menu"
rm -f "$BINDIR/wallpaper-picker"
rm -f "$BINDIR/wallpaper-next"
rm -f "$BINDIR/wallpaper-prev"

if [ "$FORCE" -eq 0 ]; then
  read -r -p "This will remove all profiles, backups, and metadata in $THEMEDIR. Continue? [y/N] " resp
  case "$resp" in
    [yY]*) ;;
    *) say "Aborted."; exit 0 ;;
  esac
fi

say "Removing: $THEMEDIR"
rm -rf "$THEMEDIR"

say "Готово. theme-profile-kit полностью удалён."
say "Конфиги wofi (.config/wofi/*.css) и настройки приложений не тронуты."