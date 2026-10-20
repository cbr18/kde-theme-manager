# Текущее приложение: theme-profile-kit (Bash Version)

> **Статус**: Рабочая версия на Bash, деплоится в `~/.local/bin/`
> **Планируемая замена**: Qt/QML приложение (см. [TZ-QT-APP.md](TZ-QT-APP.md))

---

## Обзор

`theme-profile-kit` — набор Bash-скриптов для сохранения и применения профилей оформления KDE Plasma. Позволяет переключаться между темами **glass** (прозрачное стекло с размытием) и **paper** (светлая solid тема) одной командой.

---

## Состав

| Скрипт | Назначение |
|--------|------------|
| `theme-profile` | CLI: `save`, `apply`, `list`, `diff`, `status` профилей |
| `theme-menu` | Wofi-меню для управления профилями (apply/save/status/open folder) |
| `wallpaper-picker` | Выбор обоев через wofi с превью (ImageMagick) |
| `wallpaper-next` / `wallpaper-prev` | Листание обоев по циклу |

---

## Установка

```bash
~/theme-profile-kit/scripts/install-theme-profile-kit.sh
```

Создаёт бэкап предыдущих версий в `~/.config/theme-profile/backups/`.
Деплоит скрипты в `~/.local/bin/` (должно быть в PATH) и GUI:

| Что | Куда |
|-----|------|
| `theme-profile`, `theme-menu`, `wallpaper-*` | `~/.local/bin/` |
| KDE Theme Manager (копия приложения) | `~/.local/share/kde-theme-manager/` |
| обёртка `kde-theme-manager` | `~/.local/bin/` |
| ярлык | `~/.local/share/applications/kde-theme-manager.desktop` |
| иконка | `~/.local/share/icons/hicolor/scalable/apps/ktm-theme-manager.svg` |

Только скрипты: `install-theme-profile-kit.sh --no-gui`.
Отдельно GUI: `scripts/install-kde-theme-manager.sh` (venv создаётся лишь
если в системе нет PySide6) и `scripts/uninstall-kde-theme-manager.sh`.

Данные (профили, бэкапы, настройки) живут отдельно, в
`~/.config/theme-profile/`, и установкой не затрагиваются.

---

## Использование

```bash
theme-profile list               # список профилей
theme-profile apply glass        # применить профиль
theme-profile save my-profile    # сохранить текущее состояние
theme-profile status             # текущее состояние
theme-profile diff glass paper   # сравнить профили

theme-menu                       # wofi-меню
wallpaper-picker                 # выбор обоев
wallpaper-next                   # следующие обои
wallpaper-prev                   # предыдущие обои
```

---

## Профили

- **glass** — полупрозрачные окна с размытием, KWin glass enabled, blur, better-blur-dx для выбранных классов окон (zen, code, kitty, zed)
- **paper** — светлая/solid тема, без прозрачностей

Профили хранятся в `~/.config/theme-profile/profiles/`.
Активный профиль — маркер `~/.config/theme-profile/active-profile`.

---

## Что отслеживается (TRACKED_PATHS)

### KDE/Plasma (базовые, всегда)
- `.config/kwinrc` — KWin эффекты, правила
- `.config/kwinrulesrc` — правила окон
- `.config/kdeglobals` — цвета, акцент, Look & Feel, цветовая схема
- `.config/plasmarc` — настройки Plasma
- `.config/plasma-org.kde.plasma.desktop-appletsrc` — панель, виджеты, обои (весь конфиг)
- `.config/plasmashellrc` — поведение оболочки

### GTK
- `.config/gtk-3.0/settings.ini`, `gtk.css`, `colors.css`
- `.config/gtk-4.0/settings.ini`, `gtk.css`, `colors.css`

### Qt
- `.config/QtProject.conf`
- `.config/Trolltech.conf`

### Window Decorations (опционально)
- `.config/klassy/klassyrc`, `windecopresetsrc`
- `.config/Kvantum/kvantum.kvconfig`, `Sandstone/`

### Terminals (опционально)
- `.config/alacritty/alacritty.toml`, `themes/noctalia.toml`
- `.config/kitty/kitty.conf` — с live reload через `kitty @`

### Launchers/Menu (опционально)
- `.config/wofi/style.css`, `wallpaper.css`

### Monitors (опционально)
- `.config/btop/btop.conf`, `themes/noctalia.theme`, `paper.theme`

### Sysinfo (опционально)
- `.config/fastfetch/config.jsonc`, `logo`, `cat-source.jpg`

### Editors (опционально)
- `.config/zed/settings.json`, `themes/`
- `.config/Code/User/settings.json`
- `.config/Cursor/User/settings.json`

### Browser (опционально)
- `.zen/gp0y8wrv.Default (release)/user.js`
- `.zen/gp0y8wrv.Default (release)/chrome/userChrome.css`
- `.zen/gp0y8wrv.Default (release)/chrome/userContent.css`
- `.zen/gp0y8wrv.Default (release)/chrome/zen-themes.css`

### Notes (опционально)
- `.config/obsidian/obsidian.json`, `Preferences`
- `obsidian/vault/.obsidian/appearance.json`

### System Profiles
- `.local/share/color-schemes/ThemeProfilePaper.colors`
- `.local/share/plasma/look-and-feel/glass/`
- `.local/share/plasma/look-and-feel/paper/`

---

## Зависимости

| Пакет | Зачем |
|-------|-------|
| `wofi` | меню (`theme-menu`, `wallpaper-picker`) |
| `plasma-workspace` | `kreadconfig6`/`kwriteconfig6`/`kbuildsycoca6`/`plasma-apply-wallpaperimage` |
| `imagemagick` | генерация превью обоев (`wallpaper-picker`) |
| `kitty` | опционально, для live-reload темы терминала |
| `dolphin` | опционально, кнопка "Open profile folder" в `theme-menu` |

Всё базовое ставится с KDE Plasma из коробки.

---

## Правило редактирования

1. Править файлы в `~/theme-profile-kit/files/bin/`
2. Запустить `~/theme-profile-kit/scripts/install-theme-profile-kit.sh`
3. **Не редактировать** `~/.local/bin/` напрямую (или сразу скопировать изменения обратно в kit)

---

## GUI: Theme Inspector

Qt/QML-приложение (`gui/qt-app/`) уже ставится установщиком рядом с Bash-скриптами. Помимо профилей и обоев в нём есть страница **Theme**:

- 69 live-полей в секциях Colors, Typography, Windows & Effects, Desktop & Assets, Applications + Advanced;
- переключатель scope `Live | <profile>` и diff по полям;
- валидация (схемы, L&F, иконки, Kvantum, шрифты, конфликт blur) с кнопкой **Fix**;
- редактирование с мгновенным применением, Undo/Revert и снимком в `~/.config/theme-profile/backups/inspector-<ts>/`;
- экспорт снимка в JSON, ссылки в `kcmshell6`, открытие папки конфигов.

Инспектор всегда работает на Python-ядре (`CoreFactory.theme_core()`), независимо от `--core`. Подробности: [THEME_INSPECTOR.md](THEME_INSPECTOR.md), ТЗ: [TZ-THEME-INSPECTOR.md](TZ-THEME-INSPECTOR.md).

---

## Известные ограничения

1. **Обои не в профиле** — `theme-profile save/apply` не сохраняет/не применяет обои. Обои управляются отдельно через `wallpaper-*` скрипты.
2. **Нет гранулярности** — `apply` применяет ВСЁ сразу. Нельзя выбрать только KWin или только GTK.
3. **Wofi UI** — GTK-приложение, выглядит чужеродно в KDE, нет нативного интегрированного интерфейса.
4. **Нет детекта приложений** — если приложение не установлено, конфиги просто не копируются (тихо), но пользователь не видит, что доступно, а чего нет.
5. **Нет превью профилей** — нельзя посмотреть, что изменится до применения.
6. **Жёсткие пути** — папка обоев `~/Изображения/Wallpaper` захардкожена в скриптах.
7. **Zen Browser** — путь к профилю хардкоднут (`.zen/gp0y8wrv.Default (release)/`).

---

## Структура директорий

```
~/.config/theme-profile/
├── active-profile          # имя активного профиля
├── profiles/
│   ├── glass/              # профиль glass
│   │   ├── .config/kwinrc
│   │   ├── .config/kdeglobals
│   │   └── ...
│   ├── paper/              # профиль paper
│   └── custom/             # пользовательские профили
├── backups/                # авто-бэкапы перед apply
│   └── pre-apply-glass-20260115-120000/
└── manifests/              # манифесты сохранения (опционально)
```

---

## Интеграция с RGB Control

Отдельная система: `~/rgb-control-kit/` → `rgb-control`, `rgb-menu`.
Синхронизирует Hyperion, OpenRazer, AULA F108 Pro, ASUS keyboard, OpenRGB.
Читает акцент из `~/.config/kdeglobals` (меняется при смене профиля через `theme-profile`).

---

## Связанные проекты

| Проект | Путь | Описание |
|--------|------|----------|
| `rgb-control-kit` | `~/rgb-control-kit/` | Управление RGB устройствами |
| `theme-profile-kit` | `~/theme-profile-kit/` | **Этот проект** (bash версия) |
| `taskmanager-newinstance` | `~/projects/kde_mods/taskmanager-newinstance/` | KWin таскбар мод (C++) |
| `mdock` | `~/projects/mdock/` | Markdown vault server (Go) |

---

## Планы (v2 — Qt/QML)

См. [TZ-QT-APP.md](TZ-QT-APP.md) — полное техническое задание на переписывание:
- Native KDE UI на Kirigami/QML — **сделано** (`gui/qt-app/`, см. `gui/qt-app/README.md`)
- Гранулярный выбор компонентов (галочки) — **сделано**
- Детект установленных приложений — **сделано**
- Dogfooding (приложение само темизируется) — **сделано**
- Clean Architecture для замены Core на Rust — **сделано**: два взаимозаменяемых
  ядра, выбор через `--core python|rust|auto`, `$KTM_CORE` или
  *Settings → Core*; Rust-библиотека `libkde_theme_core.so` ставится в
  `~/.local/share/kde-theme-manager/lib/`, при её отсутствии приложение
  откатывается на Python-ядро. Паритет ядер проверяется
  `tests/test_gui.py::TestCoreParity`.
