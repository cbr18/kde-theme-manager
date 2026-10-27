# Rollback / Recovery Guide

This document covers all rollback and recovery scenarios for `theme-profile-kit`.

> **Path note.** Examples below use `~/.config/theme-profile/` for brevity. The
> data root is XDG-aware: `$XDG_CONFIG_HOME/theme-profile/` is used when set,
> with an existing legacy `~/.config/theme-profile/` kept as a fallback.
> Profile snapshots themselves always keep the historical `.config/...` layout.

## Quick Summary

| Scenario | Command |
|---|---|
| Undo a profile application | See **Pre-apply backups** below |
| Restore old installer scripts | See **Installer backup restore** below |
| Plasma shell won't start | See **Emergency: Plasma Shell recovery** below |
| Fully remove the kit | `uninstall-theme-profile-kit.sh --force` |

---

## 1. Pre-apply backups

Every `theme-profile apply <name>` creates a timestamped backup of all
tracked config files **before** modifying anything:

```text
~/.config/theme-profile/backups/pre-apply-<name>-<YYYYMMDD-HHMMSS>/
```

This contains:
- `manifest.txt` — list of tracked paths and generation metadata
- `metadata/kde/summary.txt` — KDE effects state at time of save
- `metadata/kde/kwin-*.txt` — kwin support information
- A full copy of every tracked path from `$HOME` (kwinrc, kdeglobals, GTK configs, etc.)

### To restore a pre-apply backup:

```bash
# List available backups
ls ~/.config/theme-profile/backups/

# Find the backup you want (note the timestamp)
BACKUP="pre-apply-glass-20240115-103000"

# Restore all tracked files
theme-profile apply "$BACKUP"          # if backup is in profiles/
# OR manually copy back:
cp -a ~/.config/theme-profile/backups/$BACKUP/.config/kwinrc ~/.config/kwinrc
cp -a ~/.config/theme-profile/backups/$BACKUP/.config/kdeglobals ~/.config/kdeglobals
# ... repeat for each file you need to restore
```

Alternatively, if the backup is itself a valid profile, you can copy it
into the profiles directory:

```bash
cp -a ~/.config/theme-profile/backups/pre-apply-glass-20240115-103000 ~/.config/theme-profile/profiles/rollback-20240115
theme-profile apply rollback-20240115
```

---

## 2. Installer backup restore

When `install-theme-profile-kit.sh` replaces an existing `~/.local/bin/`
script, the old version is backed up:

```text
~/.config/theme-profile/backups/deploy-theme-profile-kit-<YYYYMMDD-HHMMSS>-<pid>/bin/
```

The GUI installer backs up everything it replaces (the previous app copy, the
launcher, the desktop entry) in a sibling directory:

```text
~/.config/theme-profile/backups/deploy-kde-theme-manager-<YYYYMMDD-HHMMSS>/
├── app/                              previous ~/.local/share/kde-theme-manager
├── legacy-theme-profile-manager/     the old hand-made copy, if it was there
├── bin/kde-theme-manager             previous launcher
└── applications/kde-theme-manager.desktop

```

### To restore a previous installer backup:

```bash
cp -a ~/.config/theme-profile/backups/deploy-theme-profile-kit-YYYYMMDD-HHMMSS/bin/. ~/.local/bin/
cp -a ~/.config/theme-profile/backups/deploy-kde-theme-manager-YYYYMMDD-HHMMSS/app/. ~/.local/share/kde-theme-manager/
```

Then verify:

```bash
theme-profile status
theme-profile list
```

### Rolling back the GUI core

The app can run on the Rust core (`libkde_theme_core.so`, the default) or the
Bash core. If the Rust core misbehaves, go back to Bash — no reinstall needed:

```bash
kde-theme-manager --core bash     # this run
KTM_CORE=bash kde-theme-manager   # or via the environment
# Settings → Core → bash persists the choice for the next start
```

`--core bash` is persisted too, so it survives restarts. The setting is stored
in `~/.config/theme-profile/app-preferences.json` (`"core_backend": "bash"`),
which can also be edited by hand while the app is closed:

```bash
python3 - <<'PY'
import json, os, pathlib
root = pathlib.Path(os.environ.get("XDG_CONFIG_HOME", pathlib.Path.home() / ".config"))
path = root / "theme-profile" / "app-preferences.json"
data = json.loads(path.read_text())
data["core_backend"] = "bash"
path.write_text(json.dumps(data, indent=2) + "\n")
PY
```

The legacy value `"python"` is still accepted as an alias for `"bash"`, so old
scripts and settings keep working.

If the library is the problem, remove it — the app then reports the Bash core
and keeps working:

```bash
rm ~/.local/share/kde-theme-manager/lib/libkde_theme_core.so
kde-theme-manager --list-cores   # → rust NOT AVAILABLE
```

Per-operation differences worth knowing when switching: profile writes
(apply/save/diff) go through the same `theme-profile` script in both cores; the
Rust core only takes over reading (profiles, components, wallpapers, app
detection, settings). `tests/test_gui.py::TestCoreParity` fails if that ever
drifts.

---

## 3. Emergency: Plasma Shell recovery

If `theme-profile apply` fails mid-execution and Plasma Shell does not
restart automatically, recover manually:

```bash
systemctl --user start plasma-plasmashell.service
systemctl --user reset-failed plasma-plasmashell.service
kquitapp6 plasmashell && kstart6 plasmashell &  # fallback if the above doesn't work
```

The `apply` command now uses `trap 'start_plasma_shell' ERR` to
automatically attempt recovery on any error after stopping Plasma. If
the session is already dead, the recovery trap may not fire — use the
commands above.

---

## 4. Full removal (complete rollback)

To completely remove `theme-profile-kit`:

```bash
~/theme-profile-kit/scripts/uninstall-theme-profile-kit.sh --force
```

Or interactively (confirms before deletion):

```bash
~/theme-profile-kit/scripts/uninstall-theme-profile-kit.sh
```

This removes:
- `~/.local/bin/theme-profile`, `theme-menu`, `wallpaper-picker`, `wallpaper-next`, `wallpaper-prev`
- the GUI: `~/.local/share/kde-theme-manager/`, `~/.local/bin/kde-theme-manager`,
  `~/.local/share/applications/kde-theme-manager.desktop`,
  `~/.local/share/icons/hicolor/scalable/apps/ktm-theme-manager.svg`
  (keep the app with `--no-gui`; remove only it with `uninstall-kde-theme-manager.sh`)

**But does NOT touch** — you must revert these manually if needed:
- `~/.config/wofi/*.css` — wofi styles
- `~/.config/kwinrc`, `~/.config/kdeglobals`, `~/.config/plasmashellrc` — KDE configs
- `~/.config/kitty/kitty.conf`, `~/.config/alacritty/...` — terminal configs
- Zen, VS Code, Cursor, Obsidian, btop, fastfetch configs

---

## 5. Troubleshooting

### Plasma won't start after `apply`

```bash
systemctl --user start plasma-plasmashell.service
```

### `kreadconfig6` / `kwriteconfig6` not found

These come from `plasma-workspace`. Install it:

```bash
sudo pacman -S plasma-workspace   # CachyOS / Arch
```

### wofi menu appears empty

Ensure `~/.config/wofi/style.css` exists. If not:

```bash
mkdir -p ~/.config/wofi
echo '* { background-color: #1e1e1e; }' > ~/.config/wofi/style.css
```

### `theme-profile list` shows nothing

Ensure `~/.config/theme-profile/profiles/` exists and contains profile
directories:

```bash
mkdir -p ~/.config/theme-profile/profiles
theme-profile save my-profile
```

### Wallpaper picker shows no images

The wallpaper directory defaults to `~/Изображения/Wallpaper` (or `~/Pictures/Wallpaper`
on English systems). Override with:

```bash
export WALLPAPER_DIR="$HOME/Pictures/MyWallpapers"
```

You can add this to your `~/.config/fish/config.fish` for persistence.
