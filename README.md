# theme-profile-kit

Сохранение и применение профилей оформления KDE Plasma.

Позволяет переключаться между темами оформления **glass** (полупрозрачное стекло) и **paper** (светлая/solid тема) одной командой, сохраняя и восстанавливая десятки настроек: KWin эффекты, темы GTK/Qt, настройки терминалов, редакторов и браузера Zen.

## Состав

| Скрипт | Назначение |
|--------|------------|
| `theme-profile` | CLI: save/apply/list/diff профилей |
| `theme-menu` | wofi-меню для управления профилями |
| `wallpaper-picker` | выбор обоев через wofi с превью |
| `wallpaper-next` / `wallpaper-prev` | листание обоев |

## Зависимости

Всё стандартное для KDE Plasma 6:

| Пакет | Зачем |
|---|---|
| `wofi` | меню (`theme-menu`, `wallpaper-picker`) |
| `plasma-workspace` | `kreadconfig6`/`kwriteconfig6`/`kbuildsycoca6` |
| `plasma-workspace` | `plasma-apply-wallpaperimage` |
| `imagemagick` | генерация превью обоев (`wallpaper-picker`) |

Всё это ставится вместе с KDE Plasma из коробки. Дополнительно ничего качать не нужно.

Опционально:
- `kitty` — для live-перезагрузки темы терминала (если используете kitty)
- `dolphin` — для кнопки "Open profile folder" в `theme-menu`

## Установка

```bash
~/theme-profile-kit/scripts/install-theme-profile-kit.sh
```

Создаёт бэкап предыдущих версий в `~/.config/theme-profile/backups/`.

## Использование

```bash
theme-profile list               # список профилей
theme-profile apply glass        # применить профиль
theme-profile save my-profile    # сохранить текущее состояние
theme-menu                       # wofi-меню
wallpaper-picker                 # выбор обоев
```

## Профили

- `glass` — полупрозрачные окна с размытием, KWin glass enabled
- `paper` — светлая/solid тема, без прозрачностей

Профили хранятся в `~/.config/theme-profile/profiles/`.

## Правило редактирования

Править файлы в `~/theme-profile-kit/files/bin/`, затем запустить `install-theme-profile-kit.sh`.
Не редактировать `~/.local/bin/` напрямую (или сразу скопировать изменения обратно в kit).