# AGENTS.md — theme-profile-kit

Instructions for AI agents and contributors working in this repository.

## What this repository is

`theme-profile-kit` is the **source of truth** for:

| Area | Source |
|---|---|
| Bash CLI | `files/bin/theme-profile`, `theme-menu`, `wallpaper-picker`, `wallpaper-next`, `wallpaper-prev` |
| Qt/QML GUI ("KDE Theme Manager") | `gui/qt-app/` |
| Install / update / uninstall | `scripts/*.sh` |
| Tests | `tests/test-scripts.sh`, `gui/qt-app/tests/` |

Deployed copies live in `~/.local/bin/`, `~/.local/share/kde-theme-manager/`
and `~/.local/share/applications/`. **Never edit deployed copies directly** —
edit the kit and re-run the installer.

The end-user data directory (`profiles/`, `backups/`, `manifests/`,
`active-profile`, `app-preferences.json`) is separate from the code and is never
touched by install/update.

## Documentation rule (mandatory)

**Every code change must be reflected in the documentation in the same task.**
A change is not done until the docs agree with the code. At minimum:

1. Update the doc(s) that describe the changed behaviour. See the map below.
2. If a user-visible behaviour, path, default, CLI flag, setting, or contract
   changed, update the relevant README/docs text and any code example.
3. If a documented test count, file path, or architecture diagram becomes stale,
   fix it in the same task.
4. Keep code comments and docstrings in sync when they explain *why* something
   is done — stale rationale is worse than none.

### Where documentation lives

| Document | Covers |
|---|---|
| `README.md` | Install/usage, wallpapers, profiles, Theme Inspector, update/uninstall, rollback |
| `docs/CURRENT_APP.md` | Current app, tracked paths, directory layout, known limits |
| `docs/THEME_INSPECTOR.md` | Theme Inspector UX + architecture |
| `docs/ROLLBACK.md` | Backup layout and recovery |
| `docs/ROADMAP.md` | Direction and completed work |
| `docs/TZ-QT-APP.md`, `docs/TZ-THEME-INSPECTOR.md` | Original specifications |
| `gui/qt-app/README.md` | GUI details: cores, tray, theming, wallpapers, architecture, dev commands |

## Contracts that must not drift

- **Profile-name validation**: `^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$`, implemented
  identically in `gui/qt-app/src/core/paths.py` (`validate_profile_name`), bash
  `files/bin/theme-profile`, and the Rust core (`src/paths.rs`). Names are single
  path components; reject anything else (traversal, separators, leading dot).
- **XDG-aware paths**: live files resolve through `XDG_CONFIG_HOME` /
  `XDG_DATA_HOME` / `XDG_CACHE_HOME`. The data root prefers an existing
  `$XDG_CONFIG_HOME/theme-profile`, then an existing legacy
  `~/.config/theme-profile`, then the XDG path. Profile *snapshots* keep the
  historical `.config/...` layout — do not change that without a migration.
- **Wallpaper list ordering**: shared by bash, Python and Rust — follow symlinks,
  extensions `jpg jpeg png webp bmp` (case-insensitive), byte/code-point order
  (`LC_ALL=C sort` / `sorted()` / `Vec::sort()`). See the table in
  `gui/qt-app/README.md`.
- **Profile scopes are read-only snapshots** in the Theme Inspector; only
  *Live* is editable. Mutating profile operations delegate to bash
  `theme-profile`.
- **`KTM_THEME_NO_APPLY=1`** disables external commands and D-Bus hooks (used by
  tests and dry runs).
- **JSONC files** (Zed / VS Code / Cursor / Obsidian / fastfetch) are patched by
  value position and never reserialised.
- **Two interchangeable cores**: Python (`gui/qt-app/src/core/python_core.py`) is
  the reference; Rust (`gui/qt-app/src/core/rust_core/`) must stay at parity
  (`tests/test_gui.py::TestCoreParity`). Select with `--core`, `$KTM_CORE` or
  *Settings → Core*.

## Verification (run before committing)

```bash
# Python tests (offscreen Qt; ~157 tests)
cd gui/qt-app && QT_QPA_PLATFORM=offscreen uv run --project . --extra dev pytest tests -q

# Bash tests (~96 assertions) — from the repo root
bash tests/test-scripts.sh

# Rust core
cd gui/qt-app/src/core/rust_core && cargo test && cargo clippy --all-targets -- -D warnings

# Shell static analysis
shellcheck files/bin/* scripts/*.sh tests/*.sh

# QML lint
find gui/qt-app/qml -name '*.qml' -print0 | xargs -0 qmllint
```

`ruff` / `mypy` configs exist but are **not** enforced by CI; do not churn the
codebase to satisfy them unless asked.

## Editing rules

1. Edit `files/bin/*` for the CLI; deploy with
   `scripts/install-theme-profile-kit.sh`.
2. Edit `gui/qt-app/**` for the GUI; deploy with
   `scripts/install-kde-theme-manager.sh` (or the kit installer).
3. Do **not** edit `~/.config/kwinrc`, `plasmashellrc`, `kdeglobals` without a
   backup; do **not** edit Zen `prefs.js` (use the profile `user.js`).
4. Prefer `uv` for Python and `cargo` for Rust on this machine.
5. Keep writes to config files atomic and permission-preserving
   (`gui/qt-app/src/core/fileutil.py`).

## License

MIT — see `LICENSE`. Remote: `github.com/cbr18/kde-theme-manager`.
