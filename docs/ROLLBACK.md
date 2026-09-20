# Rollback

Installer backups are stored in:

```text
~/.config/theme-profile/backups/deploy-theme-profile-kit-YYYYMMDD-HHMMSS
```

To restore one backup manually:

```bash
cp -a ~/.config/theme-profile/backups/deploy-theme-profile-kit-YYYYMMDD-HHMMSS/bin/. ~/.local/bin/
```

Then verify:

```bash
theme-profile status
theme-profile list
```
