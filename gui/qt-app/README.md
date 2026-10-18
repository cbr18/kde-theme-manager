# KDE Theme Manager — Qt/QML Application (v0.2.0)

Native KDE Plasma application for managing theme profiles and wallpapers.

## Features

- **Native KDE UI** — Built with Kirigami/QML, follows KDE HIG
- **Profile Management** — Apply/save/diff profiles (glass, paper, custom)
- **Select, then Apply** — clicking a profile only *selects* it; an explicit
  **Apply** button commits it (switching profiles is slow, so nothing happens
  until you ask for it)
- **Granular Control** — Choose which components to apply per profile
- **Wallpaper Management** — Picker with previews, next/prev navigation
- **App Detection** — Automatically detects installed/configured apps
- **Dogfooding** — App themes itself from the *active* profile
- **Clean Architecture** — Core protocol ready for Rust rewrite

## Theming (dogfooding)

The application styles itself from the active profile:

| Active profile | App look |
|----------------|----------|
| `glass` | Translucent dark "glass panel", dark controls, light text, KWin blur requested |
| `paper` | Light panel, light controls, dark text |
| `dark` / `light` | Plain dark / light palette |
| `system` | Follows the system colour scheme |

Implementation notes:

- The whole **application palette** is switched (`ThemeController._apply_palette`)
  so Qt Quick Controls (buttons, chips, check boxes…) match the custom QML
  colours. Without this the window looked "half dark".
- `Kirigami.Page` paints `Platform.Theme.backgroundColor` behind its content;
  `Main.qml` overrides the page `background` so glass mode shows the translucent
  glass panel instead of an opaque light rectangle.
- `Kirigami.Theme` colour roles can be invalid with PySide6's bundled Qt, so every
  QML file defines a `safeColor(role, fallback)` helper.
- Window transparency is owned by QML (`color:` binding) — the Python side must
  **not** call `QWindow.setColor()`, as that overrides the QML binding.

## Screenshots

| Main Page | Settings Page |
|-----------|---------------|
| Profiles + Wallpaper | Granular component toggles |

## Requirements

- **KDE Plasma 6** (Wayland or X11)
- **Python 3.11+**
- **PySide6 6.7+**
- **Existing bash tools** — `theme-profile`, `wallpaper-picker/next/prev` (from `theme-profile-kit` v0.1.0)

## Installation

```bash
# From theme-profile-kit root
cd qt-app
uv pip install -e ".[dev]"  # or pip install -e ".[dev]"

# Or install system-wide (requires PySide6)
pip install -e .
```

## Development

```bash
# Run from source
cd qt-app
python -m src

# Run with uv
uv run python -m src

# Lint
ruff check src/
mypy src/

# Tests
pytest

# Visual smoke test: render the window to a PNG and exit (dev helper)
KTM_SCREENSHOT=/tmp/win.png python -m src
```

## Architecture

```
src/
├── core/
│   ├── protocol.py       # Abstract Base Classes (CONTRACT)
│   ├── python_core.py    # Python implementation (wraps bash)
│   └── tracked_apps.py   # App registry with detection
├── controllers/          # PySide6 QObject controllers
│   ├── ProfileController
│   ├── WallpaperController
│   ├── TrackedAppsController
│   ├── SettingsController
│   └── MainController    # Aggregate
├── theme_controller.py   # Dogfooding: app theming
└── __main__.py           # Entry point

qml/
├── Main.qml              # Main page (active profile, profiles, wallpaper)
├── pages/
│   └── SettingsPage.qml  # Settings with component toggles
└── Components/
    ├── ProfileCardDelegate.qml      # Available-profile card
    ├── ProfileRadioButton.qml       # Active-profile select card
    ├── ComponentCategoryGroup.qml   # Collapsible component category
    └── ComponentCheckbox.qml        # Single component toggle
```

> Note: `ScrollablePage` must contain a **single layout** child — its children are
> only anchored left/right, never laid out, so bare cards collapse to zero height.

## Core Protocol (Replaceable)

The `core/protocol.py` defines **Abstract Base Classes** for:
- `ProfileCore` — profile operations
- `WallpaperCore` — wallpaper operations
- `TrackedAppsCore` — app detection
- `SettingsCore` — app preferences

**PythonCore** implements these by wrapping bash scripts.
**RustCore** (future) will implement the same protocol natively.

## Tracked Applications (19)

| Category | Apps |
|----------|------|
| KDE/Plasma | KWin, Plasma Shell, KDE Globals |
| GTK/Qt | GTK3, GTK4, Qt5/Qt6 |
| Window Deco | Klassy, Kvantum |
| Terminals | Kitty (live reload), Alacritty |
| Launchers | Wofi |
| Monitors | btop |
| Sysinfo | Fastfetch |
| Editors | Zed, VS Code, Cursor |
| Browser | Zen Browser |
| Notes | Obsidian |
| System | Color Schemes, Look & Feel |

## Configuration

Settings stored in `~/.config/theme-profile/app-preferences.json`:

```json
{
  "default_components_mode": "all",
  "custom_components": [],
  "wallpaper_linked_to_profile": false,
  "wallpaper_directory": "~/Изображения/Wallpaper",
  "theme": "system",
  "show_not_installed_warning": true,
  "auto_apply_on_startup": false,
  "minimize_to_tray": false,
  "global_hotkey": "",
  "confirm_before_apply": true,
  "create_backup_before_apply": true,
  "notify_on_success": true
}
```

## Building

### Desktop Entry

Installed via `theme-profile-kit/scripts/install-theme-profile-kit.sh`:
- `~/.local/bin/kde-theme-manager` — wrapper script
- `~/.local/share/applications/kde-theme-manager.desktop`

### Standalone Binary (future)

```bash
# With Nuitka (Python)
uv pip install nuitka
python -m nuitka --standalone --enable-plugin=PySide6 src/__main__.py

# Or with Rust core (future)
cargo build --release
```

## Roadmap

- [ ] System tray integration
- [ ] Global hotkey (Meta+T)
- [ ] Profile preview before apply
- [ ] Auto-sync with system theme changes
- [ ] Rust core implementation
- [ ] Plasma applet version

## License

MIT — see LICENSE in parent directory.