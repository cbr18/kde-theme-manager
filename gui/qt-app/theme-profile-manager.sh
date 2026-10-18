#!/usr/bin/env bash
# Wrapper script for KDE Theme Manager (PySide6 Qt/QML app)
# Sets environment variables needed for system QML modules (Kirigami) to be
# found by PySide6's bundled Qt6.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# System Qt6 QML modules (Kirigami, org.kde.desktop) — needed because
# PySide6 bundles its own Qt that doesn't see system QML paths
export QML2_IMPORT_PATH="/usr/lib/qt6/qml:/usr/lib64/qt6/qml:${QML2_IMPORT_PATH:-}"
export QT_PLUGIN_PATH="/usr/lib/qt6/plugins:/usr/lib64/qt6/plugins:${QT_PLUGIN_PATH:-}"

# Ensure KDE platform theme is used (for icons, colors, etc.)
export QT_QPA_PLATFORMTHEME="${QT_QPA_PLATFORMTHEME:-KDE}"

# Run the app
exec python3 -m src "$@"
