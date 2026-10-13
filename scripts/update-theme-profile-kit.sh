#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"

say() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }

say "Обновление theme-profile-kit из git"
if [ -d "$PROJECT_DIR/.git" ]; then
  cd "$PROJECT_DIR"
  git pull
  say "Запуск установки"
  exec "$SCRIPT_DIR/install-theme-profile-kit.sh"
else
  say "Не git-репозиторий. Просто переустановка."
  exec "$SCRIPT_DIR/install-theme-profile-kit.sh"
fi