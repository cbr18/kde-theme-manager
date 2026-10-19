# KDE Theme Manager — Qt/QML Application (v0.2.0)

Native KDE Plasma application for managing theme profiles and wallpapers.

## Features

- **Native KDE UI** — Built with Kirigami/QML, follows KDE HIG
- **Profile Management** — Apply/save/diff profiles (glass, paper, custom)
- **Select, then Apply** — clicking a profile only *selects* it; an explicit
  **Apply** button commits it (switching profiles is slow, so nothing happens
  until you ask for it)
- **Preview & Diff** — see exactly which components a profile carries and how it
  differs from the active one *before* applying
- **Granular Control** — Choose which components to apply per profile
  (*Settings* page in the global drawer)
- **Wallpaper Management** — Picker with previews, next/prev navigation
- **App Detection** — Automatically detects installed/configured apps
- **Non-blocking** — apply/save/delete run off the GUI thread with a busy state
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
- **All colours live in one place**: `qml/Components/ThemeColors.qml`, a QML
  singleton of `glass`-parameterised accessors (`ThemeColors.cardBg(glassMode)`,
  `ThemeColors.fgColor(glassMode)`, …). It is the only file allowed to read
  `Kirigami.Theme` directly — those colour roles can be *invalid* with PySide6's
  bundled Qt, which is why it wraps every lookup in `safeColor(role, fallback)`.
  Previously every component copy-pasted that helper and the palettes drifted
  apart.
- **All font sizes come from** `qml/Components/TypeScale.qml` (also a singleton:
  `body`, `subtitle`, `title`, `caption`, derived from the platform font).
  Never bind `font.pointSize` to `Platform.Units.*Spacing` — those are spacing
  tokens (4 pt / 6 pt here) and rendered body text near-illegible.
- Window transparency is owned by QML (`color:` binding) — the Python side must
  **not** call `QWindow.setColor()`, as that overrides the QML binding.
- The global drawer is `modal: true` (the default). A non-modal `GlobalDrawer` is
  a *permanent* sidebar on desktop, which eats ~220 px and overlaps the header.

## Select, then Apply

Switching a profile runs `theme-profile apply`, which touches dozens of config
files and takes seconds. Two consequences shape the UI:

- Clicking a profile card (or its radio button, or pressing Space while it has
  focus) only sets `selectedProfile`. Nothing is written until the **Apply**
  button is pressed, and the button is disabled while the selection already
  matches the active profile.
- Apply/save/delete run on a `QThreadPool` worker (`ProfileController.busy`,
  `operationStarted` / `operationFinished`), so the window keeps repainting and
  the busy indicator animates while the work happens. The result is shown in an
  inline message that auto-clears after a few seconds.
- The radio/check-box `checked` state is model-driven. A Qt Quick control writes
  to `checked` on click, which destroys a plain `checked:` binding, so both
  components re-arm it with
  `Binding { restoreMode: Binding.RestoreBindingOrValue }`.

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

Normal use — one command installs the app, its launcher and the desktop entry
(with a backup of whatever it replaces):

```bash
# From the theme-profile-kit root
scripts/install-kde-theme-manager.sh

# Options
scripts/install-kde-theme-manager.sh --help       # paths and details
scripts/install-kde-theme-manager.sh --no-venv    # never build a venv
scripts/install-kde-theme-manager.sh --with-venv  # always build one

# Remove it again (profiles and data are kept)
scripts/uninstall-kde-theme-manager.sh
```

| Installed | Where |
|---|---|
| application copy | `~/.local/share/kde-theme-manager/` |
| launcher (`kde-theme-manager`) | `~/.local/bin/` |
| desktop entry | `~/.local/share/applications/kde-theme-manager.desktop` |
| icon | `~/.local/share/icons/hicolor/scalable/apps/kde-theme-manager.svg` |
| backups of replaced files | `~/.config/theme-profile/backups/deploy-kde-theme-manager-*/` |

`~/.local/share` and `~/.local/bin` follow `XDG_DATA_HOME` / `XDG_BIN_HOME`.
A venv is created inside the app copy **only** when the system Python cannot
`import PySide6`; with the distro `pyside6` the copy is ~650 KB and runs on it
directly. The launcher respects `KDE_THEME_MANAGER_DIR` if you keep the app
somewhere else.

Where the data lives (never touched by install/update):

```
~/.config/theme-profile/
├── profiles/<name>/     the profiles themselves (theme snapshots)
├── backups/             pre-apply + deploy backups
├── manifests/           what a profile covers
├── active-profile       currently applied profile
└── app-preferences.json GUI settings (created when you first save settings)
```

The theme itself is not stored by the app — applying a profile writes the usual
KDE configuration (`~/.config/kdeglobals`, `kwinrc`, `gtk-3.0/settings.ini`, …).
Wallpapers live in `~/Изображения/Wallpaper` (or `wallpaper_directory` from the
settings) with the index cache in `~/.cache/wallpaper_index`.

### Running from the source tree (development)

```bash
cd gui/qt-app
uv pip install -e ".[dev]"  # or pip install -e ".[dev]"
./theme-profile-manager.sh  # sets QML import paths, prefers ./.venv, then python -m src
```

## Development

```bash
# Run from source
cd gui/qt-app
python -m src

# Run with uv
uv run python -m src

# Lint (ruff/mypy come from the [dev] extra)
ruff check src/
mypy src/

# QML syntax/type lint (PySide6 6.12 ships its own qmllint)
.venv/bin/pyside6-qmllint -I qml -I /usr/lib/qt6/qml qml/Main.qml qml/pages/SettingsPage.qml qml/Components/*.qml

# Tests (Python: 73, from gui/qt-app)
.venv/bin/python -m pytest tests/ -q

# Tests (bash tooling: 79, from the repo root)
bash tests/test-scripts.sh

# Static shell analysis (repo root)
find . -name "*.sh" -not -path "*/.venv/*" -print0 | xargs -0 shellcheck -x

# Visual smoke test: render the window to a PNG and exit (dev helper)
KTM_SCREENSHOT=/tmp/win.png python -m src
```

Known, harmless `qmllint` output:

- `Unqualified access [unqualified]` for `profileController`, `themeController`,
  `settingsController`, `trackedAppsController` — they are context properties, so
  qmllint cannot resolve them. Expected.
- `Type ThemeColors/TypeScale not declared as singleton in qmldir but using pragma
  Singleton [import]` — only emitted when the singleton file itself is passed on
  the command line; the `qmldir` does declare both and the runtime resolves them.

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
├── Main.qml              # Main page (active profile, profiles, wallpaper) + dialogs
├── pages/
│   └── SettingsPage.qml  # Settings with component toggles (drawer → Settings)
└── Components/
    ├── ThemeColors.qml              # Singleton: the only colour source
    ├── TypeScale.qml                # Singleton: typography scale
    ├── ProfileCardDelegate.qml      # Available-profile card
    ├── ProfileRadioButton.qml       # Active-profile select card
    ├── ComponentCategoryGroup.qml   # Collapsible component category
    └── ComponentCheckbox.qml        # Single component toggle
```

> Note: `ScrollablePage` must contain a **single layout** child — its children are
> only anchored left/right, never laid out, so bare cards collapse to zero height.
> `Kirigami.Card` needs an explicit `contentItem:` for the same reason.

> Note: a `@Slot()` in `src/controllers/__init__.py` must declare **every**
> argument type. `@Slot(str, result=str) def diff_profiles(a, b)` makes Qt drop
> the second argument silently, and the call raises `missing 1 required positional
> argument` at runtime. `tests/test_gui.py::test_slots_declare_every_python_argument`
> guards this for every controller.

## Wallpapers

**What is currently shown** is read from Plasma itself
(`~/.config/plasma-org.kde.plasma.desktop-appletsrc`, group
`[Containments][N][Wallpaper][org.kde.image][General]`, key `Image`), with the
cached index `~/.cache/wallpaper_index` only as a fallback. The cache is a
*position* in the file list, so it silently points at another wallpaper as soon
as files are added or removed — or when the list order changes.

**The list order is a contract** shared by this app and
`files/bin/wallpaper-{picker,next,prev}`:

| rule | bash | Python | Rust |
|---|---|---|---|
| follow symlinks | `find -L` | `Path.is_file()` | `fs::is_file()` |
| extensions `jpg jpeg png webp bmp`, case-insensitive | `-iname` | `.suffix.lower()` | `to_lowercase()` |
| byte/code-point order | `LC_ALL=C sort` | `sorted(key=str)` | `Vec<String>::sort()` |

A locale-aware `sort` (`ru_RU.UTF-8` folds case and ignores punctuation) ordered
the files differently from `sorted()`, so the GUI resolved the index to a
different image than the one the scripts had applied. `next`/`prev` now also
step from the wallpaper Plasma is showing instead of the cached index, which
makes them self-healing. Guarded by
`tests/test_gui.py::TestWallpaperOrdering` (runs the real script and compares the
walked order) and `tests/test-scripts.sh` sections 8–9.

The app passes `WALLPAPER_DIR` to the scripts so that a custom
`wallpaper_directory` in the settings file cannot diverge from the scripts'
default.

`wallpaper-picker` passes `--define dmenu-print_line_num=true` to wofi and uses
the printed value as a **direct 0-based index** into the displayed list: wofi
numbers the lines from 0 in input order (`modes/dmenu.c`:
`uint16_t line_num = 0; … snprintf("%u", line_num++)`). The previous `-1`
correction applied the image above the clicked one and made the first image a
no-op.

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

Installed by `theme-profile-kit/scripts/install-kde-theme-manager.sh` (which
`install-theme-profile-kit.sh` runs by default):

- `~/.local/bin/kde-theme-manager` — launcher (execs the app's own
  `theme-profile-manager.sh`, which sets the QML import paths)
- `~/.local/share/kde-theme-manager/` — the app copy
- `~/.local/share/applications/kde-theme-manager.desktop`
- `~/.local/share/icons/hicolor/scalable/apps/kde-theme-manager.svg`

Both source files live in the repository, so edit them there:
`resources/kde-theme-manager.desktop` and
`resources/icons/kde-theme-manager.svg` (icon = dark/light disc with the Breeze
accent ring). After editing, re-run the installer to redeploy.

### Standalone Binary (future)

```bash
# With Nuitka (Python)
uv pip install nuitka
python -m nuitka --standalone --enable-plugin=PySide6 src/__main__.py

# Or with Rust core (future)
cargo build --release
```

## Roadmap

- [x] Profile preview before apply (Preview / Diff dialogs)
- [ ] System tray: quick profile switching (icon + show/hide exists; the
      "Profiles" submenu is still a placeholder)
- [ ] Global hotkey (Meta+T)
- [ ] Auto-sync with system theme changes
- [ ] Rust core implementation
- [ ] Plasma applet version

## License

MIT — see LICENSE in parent directory.