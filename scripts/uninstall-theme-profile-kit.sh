#!/usr/bin/env bash
set -euo pipefail

say() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }

BINDIR="${XDG_BIN_HOME:-$HOME/.local/bin}"
THEMEDIR="$HOME/.config/theme-profile"

say "Удаление исполняемых файлов"
rm -f "$BINDIR/theme-profile"
rm -f "$BINDIR/theme-menu"
rm -f "$BINDIR/wallpaper-picker"
rm -f "$BINDIR/wallpaper-next"
rm -f "$BINDIR/wallpaper-prev"

say "Удаление профилей, бэкапов и метаданных"
rm -rf "$THEMEDIR"

say "Готово. theme-profile-kit полностью удалён."
say "Конфиги wofi (.config/wofi/*.css) и настройки приложений не тронуты."