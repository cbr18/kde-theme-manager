#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"

say() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }

say "Updating theme-profile-kit from git"

if [ -d "$PROJECT_DIR/.git" ]; then
  cd "$PROJECT_DIR"

  # Stash local changes if any
  if ! git diff --quiet || ! git diff --cached --quiet; then
    say "Local changes detected, stashing..."
    git stash push -m "pre-update-$(date +%Y%m%d-%H%M%S)"
    STASHED=1
  else
    STASHED=0
  fi

  git pull

  say "Running installation..."
  exec "$SCRIPT_DIR/install-theme-profile-kit.sh"
else
  say "Not a git repository. Running reinstallation..."
  exec "$SCRIPT_DIR/install-theme-profile-kit.sh"
fi