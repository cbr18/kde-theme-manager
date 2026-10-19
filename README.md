# theme-profile-kit / Тема‑профиль‑кит

> **Save and switch KDE Plasma themes with one command.**
> Переключайтесь между профилями оформления **glass** (полупрозрачное стекло) и **paper** (светлая/solid тема), сохраняя и восстанавливая десятки настроек.

---

## Table of Contents / Оглавление

- [Overview](#overview--обзор)
- [Contents](#contents--состав)
- [Dependencies](#dependencies--зависимости)
- [Installation](#installation--установка)
- [Usage](#usage--использование)
- [Profiles](#profiles--профили)
- [Update](#update--обновление)
- [Uninstall](#uninstall--удаление)
- [Rollback & Recovery](#rollback--восстановление)
- [Troubleshooting](#troubleshooting--устранение-неполадок)
- [Editing Rule](#editing-rule--правило-редактирования)
- [License](#license--лицензия)

---

## Overview / Обзор

Позволяет переключаться между темами оформления **glass** (полупрозрачное стекло с размытием) и **paper** (светлая/solid тема) одной командой, сохраняя и восстанавливая десятки настроек: KWin эффекты, темы GTK/Qt, настройки терминалов (kitty, Alacritty), редакторов (Zed, VS Code, Cursor), браузера Zen, Obsidian, btop, fastfetch, wofi, цветовые схемы Plasma и больше.

## Contents / Состав

### Bash Toolkit (core)

| Script | Purpose |
|--------|---------|
| `theme-profile` | CLI: save/apply/list/diff/status профилей |
| `theme-menu` | wofi‑menu for applying, saving, restarting Plasma, status |
| `wallpaper-picker` | Choose wallpaper via wofi with thumbnail preview |
| `wallpaper-next` / `wallpaper-prev` | Cycle wallpapers |

### GUI Application (optional)

| Component | Purpose |
|-----------|---------|
| `gui/qt-app/` | **KDE Theme Manager** — native Qt/QML + Kirigami desktop app with profile cards, wallpaper picker, settings, and system tray |

```bash
cd gui/qt-app
uv venv && uv pip install -e ".[dev]"
uv run kde-theme-manager  # or: python -m src
```

Requires KDE Plasma 6 + Kirigami. See `gui/qt-app/README.md` for details.

## Dependencies / Зависимости

Everything ships with KDE Plasma 6 — nothing extra to install:

| Package | Why |
|---|---|
| `wofi` | Menus (`theme-menu`, `wallpaper-picker`) |
| `plasma-workspace` | `kreadconfig6` / `kwriteconfig6` / `kbuildsycoca6` |
| `plasma-workspace` | `plasma-apply-wallpaperimage` |
| `imagemagick` (or `magick`) | Thumbnail generation (`wallpaper-picker`) |

Optional:
- `kitty` — live reload of terminal theme
- `dolphin` — "Open profile folder" button in `theme-menu`
- `rg` (ripgrep) — used in `status` for VS Code / Cursor theme detection (falls back gracefully)

## Installation / Установка

```bash
~/theme-profile-kit/scripts/install-theme-profile-kit.sh
```

Creates timestamped backups of existing scripts in `~/.config/theme-profile/backups/`.

Options:
```bash
install-theme-profile-kit.sh --help   # show help
```

## Usage / Использование

```bash
theme-profile list               # list available profiles
theme-profile apply glass        # apply a profile (creates a pre-apply backup)
theme-profile save my-profile    # save current state as a new profile
theme-profile diff glass paper   # show config differences
theme-profile status             # diagnostic: dump 30+ config values
theme-menu                       # interactive wofi menu
wallpaper-picker                 # pick wallpaper with thumbnails
wallpaper-next                   # next wallpaper
wallpaper-prev                   # previous wallpaper
```

All commands support `--help` / `-h` for usage info.

Profile names may only contain letters, numbers, dots, underscores, and hyphens (`[A-Za-z0-9._-]`).

### Wallpapers / Обои

`wallpaper-next` / `wallpaper-prev` step relative to the wallpaper Plasma is
**actually showing** (read from
`~/.config/plasma-org.kde.plasma.desktop-appletsrc`), so they stay correct even
after you add or remove files. `~/.cache/wallpaper_index` is only a fallback for
when that config cannot be read.

The list itself is a shared contract between all three scripts and the Qt app:
same extensions (`jpg`, `jpeg`, `png`, `webp`, `bmp`), symlinks followed, and
**byte order** (`LC_ALL=C sort`, i.e. `Path.is_file()` + `sorted()` in Python).
The cached index is a *position* in that list, so a locale-aware sort
(`ru_RU.UTF-8`, which folds case and ignores punctuation) made the GUI resolve
the index to a different image than the one applied. All three scripts must keep
enumerating identically — `tests/test-scripts.sh` (section 9) fails if they drift.

Environment overrides (also used by the GUI and the tests): `WALLPAPER_DIR`,
`WALLPAPER_STATE`, `PLASMA_APPLETSRC`, `WALLPAPER_DRY_RUN=1` (print the chosen
file instead of applying it).

## Profiles / Профили

- **`glass`** — полупрозрачные окна с размытием, KWin glass enabled
- **`paper`** — светлая/solid тема, без прозрачностей

Profiles live in `~/.config/theme-profile/profiles/`.

## Update / Обновление

```bash
~/theme-profile-kit/scripts/update-theme-profile-kit.sh
```

Fetches latest from git (`--ff-only`), then reinstalls scripts. Warns if you have uncommitted local changes.

## Uninstall / Удаление

```bash
~/theme-profile-kit/scripts/uninstall-theme-profile-kit.sh      # interactive (confirms)
~/theme-profile-kit/scripts/uninstall-theme-profile-kit.sh --force  # skip confirmation
```

Removes scripts from `~/.local/bin/` and wipes `~/.config/theme-profile/`. Does **not** touch your KDE config files, wofi styles, or application settings — those must be reverted manually. See [Rollback & Recovery](#rollback--восстановление).

## Rollback / Восстановление

See [`docs/ROLLBACK.md`](docs/ROLLBACK.md) for full instructions. Quick summary:

- **Undo profile apply**: pre-apply backups are at `~/.config/theme-profile/backups/pre-apply-<name>-<ts>/`
- **Restore old scripts**: `cp -a ~/.config/theme-profile/backups/deploy-*/bin/. ~/.local/bin/`
- **Plasma won't start**: `systemctl --user start plasma-plasmashell.service`
- **Full remove**: `uninstall-theme-profile-kit.sh --force`

## Troubleshooting / Устранение неполадок

| Problem | Fix |
|---|---|
| `command not found: kreadconfig6` | Install `plasma-workspace`: `sudo pacman -S plasma-workspace` |
| `command not found: wofi` | Install: `sudo pacman -S wofi` |
| wofi menu appears empty | Ensure `~/.config/wofi/style.css` exists |
| `theme-profile list` shows nothing | `mkdir -p ~/.config/theme-profile/profiles && theme-profile save my-profile` |
| Wallpaper picker shows no images | Default dir is `~/Изображения/Wallpaper`. Override with `export WALLPAPER_DIR="$HOME/Pictures/Wallpaper"` |
| Plasma won't start after `apply` | `systemctl --user start plasma-plasmashell.service` |

## Editing Rule / Правило редактирования

1. Edit files in `~/theme-profile-kit/files/bin/` first.
2. Re-run `install-theme-profile-kit.sh` to deploy.
3. Do **not** edit `~/.local/bin/` directly — copy changes back into the kit immediately.

## License / Лицензия

MIT — see [`LICENSE`](LICENSE).
