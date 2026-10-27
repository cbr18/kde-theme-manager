# KDE Theme Manager — Полный план разработки (Roadmap)

> **Версионирование:** актуальная линия — `0.4.0`. Экспериментальные теги
> `v1.0.0`–`v1.1.2` оставлены в истории, но публично откатаны: они не являются
> стабильной линией. Новые релизы продолжаются с `v0.4.0`.

---

## v0.4.0 — Qt/QML (текущий этап)

### ✅ Готово
- [x] Clean Architecture: `core/protocol.py` (ABC contracts)
- [x] BashCore: обёртки над bash (`theme-profile`, `wallpaper-*`); настройки и
  реестр приложений — локально
- [x] TrackedAppsCore: 20 приложений с авто-детектом
- [x] Controllers: Profile, Wallpaper, TrackedApps, Settings, Main
- [x] ThemeController: dogfooding (glass/paper/dark/light/system)
- [x] QML UI: MainPage (профили + обои), SettingsPage (гранулярные чекбоксы)
- [x] Theme Inspector: страница Theme, 69 полей, diff live↔profile, валидация, live-правки с Undo/Revert, экспорт JSON, ссылки в KCM
- [x] Components: ProfileCardDelegate, ProfileRadioButton, ComponentCategoryGroup, ComponentCheckbox
- [x] Install/Update/Uninstall скрипты для Qt app
- [x] pyproject.toml, README, .gitignore
- [x] Git tags: v0.1.0 (bash), v0.2.0-dev, v0.3.0, v0.4.0 (Qt)

### 🔄 В процессе / Нужно доделать

#### 1. Добавить `--components` в bash `theme-profile` (критично для гранулярности)
```bash
# В ~/theme-profile-kit/files/bin/theme-profile
# Добавить парсинг --components=kwin,gtk3,kitty
# Фильтровать TRACKED_PATHS по префиксам компонентов
```
**Оценка**: 30-60 мин

#### 2. Исправить QML баги и UX
- [ ] ProfileRadioButton: правильная группировка (ExclusiveGroup)
- [ ] ComponentCheckbox: связка с SettingsController.customComponents
- [ ] SettingsPage: ComponentCategoryGroup — передача selectionChanged
- [ ] Wallpaper preview: асинхронная загрузка, placeholder
- [ ] DiffDialog: моноширинный шрифт, синтаксис

#### 3. Dogfooding — полноценная темизация приложения
- [ ] Glass: прозрачность окна + KWin blur (Qt::WA_TranslucentBackground + FastBlur)
- [ ] Paper: светлая тема Material
- [ ] Dark/Light: переключение QtQuick.Controls.Material
- [ ] System: следование за системной темой (KDE color scheme)
- [ ] Сохранение выбранной темы в настройках

#### 4. System Tray
- [x] System tray icon (Kirigami.ApplicationWindow + QSystemTrayIcon)
- [x] Minimize to tray вместо закрытия
- [x] ~~Global hotkey: Meta+T → toggle window~~ — **убрано**: KGlobalAccel создаёт
  компонент только для `.desktop` с `X-KDE-GlobalAccel-CommandShortcut=true`, а
  голый `doRegister` не давал рабочего шортката. См. `gui/qt-app/README.md`.

#### 5. Авто-детект Zen Browser профиля
```python
# Вместо хардкода .zen/gp0y8wrv.Default (release)/
# Найти: find ~/.zen -name "user.js" -path "*/Default*" | head -1
```

#### 6. Тесты и CI
- [ ] pytest для core логики
- [ ] pytest-qt для контроллеров
- [ ] GitHub Actions: lint (ruff), typecheck (mypy), test

---

## v0.3.0 — Polish & Features (история)

### UX Improvements
- [ ] **Profile Preview**: показывать diff перед apply (модальное окно)
- [ ] **Wallpaper Grid**: полноценный пикер в приложении (не wofi)
- [ ] **Profile Import/Export**: JSON/YAML бэкапы профилей
- [ ] **Auto-sync**: следить за изменениями в системе, предлагать сохранить
- [ ] **Notifications**: KNotification при успехе/ошибке apply

### Wallpaper Integration
- [ ] Опция "Link wallpaper to profile" — сохранять выбранные обои в профиль
- [ ] При apply профиля — автоматически ставить сохранённые обои (если включено)
- [ ] Поддержка нескольких мониторов (кнопка "Configure per screen")

### Settings
- [ ] Редактор путей к конфигам (advanced mode)
- [ ] Кастомные категории компонентов
- [ ] Профиль "Auto" — переключение glass↔paper по времени/системной теме

---

## v0.5.0 — Rust Core polish & Single Binary

> **Статус: Phase 1–2 сделаны** (выбор ядра флагом, паритет с Bash покрыт
> тестами). Файлы Rust-крейта: `src/core/rust_core/src/{lib,ffi,types,profile,
> wallpaper,tracked_apps,settings,config_parser}.rs`; Python-биндинг —
> `src/core/rust_core.py`. Мутирующие операции профилей (`apply`/`save`/`diff`)
> делегируются bash-скрипту `theme-profile` — он владеет картой
> «компонент → конфиг» и бэкапами; нативное переписывание один раз уже
> скопировало `kwinrc` в `~/kwin` и перезапускало plasmashell на каждый apply.
> Переключение: `--core rust|bash|auto`, `$KTM_CORE`, *Settings → Core*;
> Rust — по умолчанию, без собранной библиотеки приложение работает на
> Bash-ядре.

### Архитектура
```
src/
├── core/
│   ├── protocol.py       # ABC (остаётся)
│   ├── bash_core.py      # Bash adapter (theme-profile / wallpaper-*)
│   └── rust_core/        # Новый Rust crate
│       ├── Cargo.toml
│       ├── src/
│       │   ├── lib.rs       # FFI interface (cdylib)
│       │   ├── profile.rs   # Profile operations
│       │   ├── wallpaper.rs # Wallpaper operations
│       │   ├── tracked.rs   # App detection
│       │   ├── config.rs    # Config parsing (kwinrc, kdeglobals, etc.)
│       │   └── settings.rs  # Settings
│       └── build.rs
├── controllers/          # Python (unchanged)
│   └── ...
```

### Rust Implementation Plan

#### Phase 1: Core Library (cdylib + C FFI)
- [ ] `cargo new --lib kde_theme_core`
- [ ] FFI функции:
  ```rust
  // profile
  extern "C" fn list_profiles() -> *mut ProfileList
  extern "C" fn apply_profile(name: *const c_char, components: *const ComponentArray) -> ResultCode
  extern "C" fn save_profile(name: *const c_char, components: *const ComponentArray) -> ResultCode
  extern "C" fn diff_profiles(a: *const c_char, b: *const c_char) -> *mut c_char
  
  // wallpaper
  extern "C" fn pick_wallpaper() -> *mut c_char
  extern "C" fn next_wallpaper() -> ResultCode
  extern "C" fn prev_wallpaper() -> ResultCode
  extern "C" fn list_wallpapers() -> *mut WallpaperList
  extern "C" fn set_wallpaper(path: *const c_char) -> ResultCode
  
  // tracked apps
  extern "C" fn detect_apps() -> *mut ComponentList
  extern "C" fn refresh_apps() -> *mut ComponentList
  
  // settings
  extern "C" fn load_settings() -> Settings
  extern "C" fn save_settings(settings: Settings) -> ResultCode
  ```
- [ ] Memory management: `free_profile_list`, `free_component_list`, etc.
- [ ] Build: `cargo build --release` → `libkde_theme_core.so`

#### Phase 2: Python Bindings (cffi / pyo3)
- [ ] Вариант A: `cffi` — загрузка `.so` через `ctypes`/`cffi`, сохраняем Python controllers
- [ ] Вариант B: `pyo3` — нативный Python модуль, быстрее, но сложнее сборка
- [x] Обновить `CoreFactory` для выбора `RustCore` vs `BashCore`

#### Phase 3: Standalone Binary
- [ ] `cargo build --release --bin kde-theme-manager`
- [ ] Встроить QML ресурсы (`qrc` или `qt_resource`)
- [ ] Single binary ~10-15 MB
- [ ] Убрать Python dependency

#### Phase 4: Config Parsing (Native)
- [ ] Парсинг INI (kwinrc, kdeglobals, gtk settings.ini) — `configparser` crate
- [ ] Парсинг TOML (alacritty) — `toml` crate
- [ ] Парсинг JSON/JSONC (vscode, zed, fastfetch) — `serde_json`
- [ ] Парсинг CSS (gtk.css, wofi) — свой парсер или `cssparser`
- [ ] Парсинг user.js (Zen) — regex-based

---

## v1.0.0 — Plasma Applet (Native Integration)

### C++/Qt6 Plasma Plugin
```
plasma-applet/
├── CMakeLists.txt
├── metadata.json
├── src/
│   ├── ThemeManagerApplet.cpp/.h    # Plasma::Applet
│   ├── ProfileModel.cpp/.h          # QAbstractListModel
│   ├── WallpaperModel.cpp/.h
│   └── SettingsDialog.cpp/.h        # KConfigDialog
├── qml/
│   ├── main.qml                     # Compact representation
│   ├── FullRepresentation.qml       # Expanded panel
│   └── Settings.qml
└── contents/
    └── ui/
        └── main.qml
```

### Features
- [ ] Встроен в панель (system tray или отдельный апплет)
- [ ] Compact view: текущий профиль + клик → меню профилей
- [ ] Hover/click → переключение профилей без открытия окна
- [ ] Right-click → настройки, wallpaper next/prev
- [ ] KConfigXT для настроек (интеграция с System Settings)
- [ ] DBus API для внешних скриптов

### Distribution
- [ ] AUR package: `kde-theme-manager-applet`
- [ ] Flatpak: `org.kde.ThemeManager`
- [ ] KDE Store: store.kde.org

---

## v2.0.0 — Ecosystem & Advanced

### RGB Integration
- [ ] Синхронизация с `rgb-control-kit` (Hyperion, OpenRazer, AULA)
- [ ] Профиль темы → RGB режим (glass=slow_cycle, paper=accent)
- [ ] UI для управления RGB в приложении

### Cloud Sync
- [ ] Экспорт профилей в GitHub Gist / Git repo
- [ ] Синхронизация между машинами
- [ ] Community profiles marketplace

### Advanced Theming
- [ ] Генерация тем из wallpaper (matugen / pywal интеграция)
- [ ] Редактор цветовых схем в-app
- [ ] Поддержка GTK4 libadwaita themes

---

## Зависимости по версиям

| Версия | Runtime | Build | Packaging |
|--------|---------|-------|-----------|
| v0.2.x | Python 3.11+, PySide6, uv | pip/uv | GitHub Releases |
| v0.3.0 | + KNotification | | |
| v0.4.0 | Python 3.11+, PySide6, Rust 1.75+ (default) | uv, cargo | GitHub Releases |
| v0.5.0 | Rust polish, single binary | cargo + pip | Single binary |
| v1.0.0 | C++17, Qt6, KDE Frameworks 6 | CMake, ECM | AUR, Flatpak, KDE Store |

---

## Команда / Ресурсы

| Задача | Навыки | Оценка |
|--------|--------|--------|
| `--components` в bash | Bash, KDE config | 1ч |
| QML полировка | QML, Kirigami | 4-8ч |
| Dogfooding (glass blur) | Qt Wayland, KWin | 2-4ч |
| System Tray | QSystemTrayIcon | 4-6ч |
| Rust Core FFI | Rust, C FFI, cffi/pyo3 | 20-40ч |
| Config parsers (Rust) | Rust, serde, toml, ini | 10-20ч |
| Plasma Applet | C++, Qt6, KDE Frameworks | 30-60ч |

---

## Приоритеты (MoSCoW для 0.3.x, история)

| Must Have | Should Have | Could Have | Won't (v0.3) |
|-----------|-------------|------------|--------------|
| `--components` в bash | Profile Preview | Wallpaper Grid | Rust Core |
| QML багфиксы | Import/Export | Auto-sync | Plasma Applet |
| Dogfooding (basic) | Notifications | Multi-monitor | Cloud Sync |
| System Tray | Zen profile autodetect | | |

> Глобальный хоткей (Meta+T) снят с плана: без desktop-entry с
> `X-KDE-GlobalAccel-CommandShortcut=true` KGlobalAccel не создаёт компонент, а
> для toggle-семантики нужен ещё и single-instance слой.
>
> Профиль `default` (baseline текущей темы) отложен. Если делать — только
> вручную, кнопкой «Сохранить как default», без автосоздания при запуске. Имя
> `system` не используем, чтобы не путать с `AppSettings.theme = "system"`
> (внешний вид приложения, а не профиль).

---

## Команды для разработки

```bash
# Разработка Qt app
cd ~/theme-profile-kit/qt-app
uv pip install -e ".[dev]"
python -m src

# Линтинг
ruff check src/
mypy src/

# Тесты
pytest

# Сборка Rust core (v0.4)
cd ~/projects/kde_mods/theme-profile-kit/gui/qt-app/src/core/rust_core
cargo build --release

# Запуск с Rust core
python -m src --core rust     # или: KTM_CORE=rust python -m src

# Установка в систему
cd ~/theme-profile-kit
./scripts/install-theme-profile-kit.sh
```

---

## Риски и митигация

| Риск | Вероятность | Влияние | Митигация |
|------|-------------|---------|-----------|
| KWin blur не работает на Wayland | Высокая | Среднее | Fallback на прозрачность без blur, документация |
| PySide6 версия в дистре старая | Средняя | Высокое | uv venv + uv pip install PySide6@latest |
| Rust FFI сложности | Средняя | Высокое | Начать с cffi (проще), pyo3 позже |
| Plasma 6 API изменения | Низкая | Среднее | Тестировать на Plasma 6.1+, пинить версии |
| Zen Browser путь меняется | Высокая | Низкое | Автодетект через find, настройка в UI |

---

*Последнее обновление: v0.4.0*
*Репозиторий: https://github.com/cbr18/kde-theme-manager*