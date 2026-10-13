#!/usr/bin/env bash
set -euo pipefail

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC_DIR="$KIT_DIR/files/bin"
DEST_DIR="$HOME/.local/bin"
BACKUP_ROOT="$HOME/.config/theme-profile/backups"
BACKUP_DIR="$BACKUP_ROOT/deploy-theme-profile-kit-$(date +%Y%m%d-%H%M%S)"

# Bash scripts (v0.1.0)
SCRIPTS=(
  "theme-profile"
  "theme-menu"
  "wallpaper-picker"
  "wallpaper-next"
  "wallpaper-prev"
)

# Qt app (v0.2.0+)
QT_APP_DIR="$KIT_DIR/qt-app"
QT_APP_DEST_DIR="$HOME/.local/share/theme-profile-manager"
QT_APP_BIN="$DEST_DIR/kde-theme-manager"
QT_DESKTOP_DIR="$HOME/.local/share/applications"
QT_DESKTOP_FILE="$QT_DESKTOP_DIR/kde-theme-manager.desktop"

say() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }

# ─── 1. Backup existing ───
mkdir -p "$DEST_DIR" "$BACKUP_DIR/bin" "$QT_DESKTOP_DIR"

for script in "${SCRIPTS[@]}"; do
  if [ -e "$DEST_DIR/$script" ]; then
    cp -a "$DEST_DIR/$script" "$BACKUP_DIR/bin/$script"
  fi
done

if [ -e "$QT_APP_BIN" ]; then
  cp -a "$QT_APP_BIN" "$BACKUP_DIR/bin/kde-theme-manager"
fi
if [ -e "$QT_DESKTOP_FILE" ]; then
  cp -a "$QT_DESKTOP_FILE" "$BACKUP_DIR/kde-theme-manager.desktop"
fi
if [ -d "$QT_APP_DEST_DIR" ]; then
  cp -a "$QT_APP_DEST_DIR" "$BACKUP_DIR/theme-profile-manager"
fi

say "Backup created: $BACKUP_DIR"

# ─── 2. Install bash scripts ───
for script in "${SCRIPTS[@]}"; do
  if [ ! -f "$SRC_DIR/$script" ]; then
    echo "Missing source: $SRC_DIR/$script" >&2
    exit 1
  fi
done

for script in "${SCRIPTS[@]}"; do
  cp -a "$SRC_DIR/$script" "$DEST_DIR/$script"
  chmod 0755 "$DEST_DIR/$script"
done

say "Installed bash scripts to $DEST_DIR"

# ─── 3. Install Qt app ───
if [ -d "$QT_APP_DIR" ]; then
  say "Installing Qt application..."

  # Copy source to ~/.local/share
  mkdir -p "$QT_APP_DEST_DIR"
  rsync -a --delete \
    --exclude='.venv' --exclude='venv' --exclude='env' \
    --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' \
    --exclude='.pytest_cache' --exclude='.mypy_cache' --exclude='.ruff_cache' \
    --exclude='dist' --exclude='build' --exclude='*.egg-info' \
    "$QT_APP_DIR/" "$QT_APP_DEST_DIR/"

  # Create wrapper script
  cat > "$QT_APP_BIN" <<'EOF'
#!/usr/bin/env bash
# kde-theme-manager wrapper
# Auto-installs dependencies via uv if needed

QT_APP_DIR="$HOME/.local/share/theme-profile-manager"
VENV_DIR="$QT_APP_DIR/.venv"

cd "$QT_APP_DIR"

# Check if uv is available
if command -v uv >/dev/null 2>&1; then
  # Use uv to run with dependencies
  if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..." >&2
    uv venv "$VENV_DIR" >&2
    uv pip install -e ".[dev]" --python "$VENV_DIR/bin/python" >&2
  fi
  exec "$VENV_DIR/bin/python" -m src "$@"
else
  # Fallback: assume system python with PySide6
  exec python3 -m src "$@"
fi
EOF
  chmod 0755 "$QT_APP_BIN"

  # Create .desktop file
  cat > "$QT_DESKTOP_FILE" <<'EOF'
[Desktop Entry]
Type=Application
Name=KDE Theme Manager
GenericName=Theme Profile Manager
Comment=Manage KDE Plasma theme profiles and wallpapers
Exec=kde-theme-manager
Icon=preferences-desktop-theme
Terminal=false
Categories=Settings;DesktopSettings;Qt;KDE;X-KDE-SystemSettings;
StartupNotify=true
Keywords=theme;profile;wallpaper;plasma;kde;glass;paper;
X-KDE-Weight=50
EOF

  say "Installed Qt app wrapper to $QT_APP_BIN"
  say "Created desktop entry: $QT_DESKTOP_FILE"
else
  say "Qt app source not found at $QT_APP_DIR, skipping Qt installation"
fi

# ─── 4. Update desktop database ───
if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
fi

say "Installation complete."
say "Run 'kde-theme-manager' to start the Qt application."
say "Bash tools: theme-profile, theme-menu, wallpaper-picker/next/prev"