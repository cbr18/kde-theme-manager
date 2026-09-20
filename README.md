# theme-profile-kit

Source-of-truth kit for local KDE theme/profile helper scripts.

Deployed scripts live in:

```text
~/.local/bin/
```

Source scripts live in:

```text
~/theme-profile-kit/files/bin/
```

## Scripts

- `theme-profile` - applies/saves KDE theme profiles from `~/.config/theme-profile/profiles`.
- `theme-menu` - Wofi menu for theme profiles.
- `wallpaper-picker` - Wofi wallpaper picker.
- `wallpaper-next` - next wallpaper helper.
- `wallpaper-prev` - previous wallpaper helper.
- `rgb-hyperion-sync` - Hyperion helper currently kept here because it has no matching source in `~/rgb-control-kit/files/bin`.

## Deploy

```bash
~/theme-profile-kit/scripts/install-theme-profile-kit.sh
```

The installer creates a timestamped backup in:

```text
~/.config/theme-profile/backups/deploy-theme-profile-kit-YYYYMMDD-HHMMSS
```

## Editing Rule

Edit files in `~/theme-profile-kit/files/bin/` first, then deploy with the installer.
Do not edit `~/.local/bin/theme-profile` or related deployed scripts directly unless it is an emergency hotfix that is copied back into this kit immediately.
