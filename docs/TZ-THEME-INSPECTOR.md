# TZ: Theme Inspector — экран «Тема»

> **Статус**: готова к работе
> **Приоритет**: P1 (после текущих багфиксов)
> **Оценка**: Phase 0 — 1 ч · Phase 1 — 1.5–2 дня · Phase 2 — 2–3 дня · Phase 3 — ~2 дня
> **Дизайн и обоснование**: [THEME_INSPECTOR.md](THEME_INSPECTOR.md)
> **Ветка**: `main` (репозиторий `github.com/cbr18/kde-theme-manager`)

---

## 1. Цель

Дать пользователю один экран, который отвечает на вопросы:

1. **Что внутри моей темы?** — accent, схема, Kvantum, blur, прозрачность, шрифты, иконки, курсоры, обои.
2. **Чем профиль отличается от live?** — diff по полям, а не по 4000 строк.
3. **Что сломано?** — несуществующие пакеты/темы/шрифты, конфликты эффектов.
4. **Можно ли поправить здесь?** — да, безопасные поля: пикеры, слайдеры, цвета.

## 2. Границы

**Входит:**
- новая страница `Theme` в drawer;
- read-only инспектор ~60 полей в 6 секциях;
- валидация («Theme Doctor»);
- редактирование live-значений с мгновенным применением, Undo и снимком сессии;
- поиск по полям, diff live↔profile, ссылки в System Settings и «Open file».

**Не входит:**
- замена System Settings, редактор панелей/виджетов, полный редактор `.colors`;
- пиксель-точный предпросмотр темы;
- автоудаление бэкапов;
- Rust-реализация инспектора (Phase 3, после стабилизации схемы).

## 3. Результат

| Артефакт | Где |
|---|---|
| Схема полей | `gui/qt-app/src/core/theme_schema.py` |
| Ядро инспектора (read/write/hooks/validate) | `gui/qt-app/src/core/theme_core.py` |
| Контракты | `gui/qt-app/src/core/protocol.py` (`ThemeCore`, `ThemeSection`, `ThemeFieldInfo`, `ThemeValue`, `ThemeIssue`, `Choice`) |
| Контроллер | `gui/qt-app/src/controllers/__init__.py` (`ThemeController`) |
| UI | `qml/pages/ThemePage.qml`, `qml/pages/ThemeSectionPage.qml`, `qml/Components/ThemeSectionCard.qml`, `ThemeFieldRow.qml`, `ColorSwatch.qml`, `ValueBadge.qml` |
| Тесты | `gui/qt-app/tests/test_theme_inspector.py` |

---

## 4. Phase 0 — блокирующие багфиксы

### T0.1. Починить `LookAndFeelPackage` в `apply_live_hooks`

`files/bin/theme-profile`:

```bash
# было (лишний позиционный аргумент → kreadconfig6 печатает --help):
look_and_feel="$(kreadconfig6 --file kdeglobals --group KDE --key LookAndFeelPackage "$source/.config/kdeglobals" ...)"

# стало:
look_and_feel="$(kreadconfig6 --file "$source/.config/kdeglobals" --group KDE --key LookAndFeelPackage ...)"
```

- [ ] Исправить вызов.
- [ ] Проверить, что `kreadconfig6 --file <abs path>` отдаёт значение, а не usage.
- [ ] Добавить регрессионный тест в `tests/test-scripts.sh`: `theme-profile` не пишет в `kdeglobals` текст, содержащий `Usage:`/`Options:`.

### T0.2. Восстановить испорченное значение

Сейчас в live и в профиле `glass` лежит текст `--help`.

- [ ] Бэкап: `cp ~/.config/kdeglobals ~/.config/kdeglobals.bak-$(date +%F)` (и то же для профиля).
- [ ] Записать `LookAndFeelPackage=glass` в live и в `profiles/glass/.config/kdeglobals`.
- [ ] Проверить: `kreadconfig6 --file kdeglobals --group KDE --key LookAndFeelPackage` → `glass`.
- [ ] Убедиться, что `plasma-apply-lookandfeel --list` содержит `glass`.

### T0.3. Починить `theme-profile status`

- [ ] `zed_*`: вытаскивать значения без `"light":` / `"mode":` (парсить JSON, а не awk).
- [ ] `code_theme` / `cursor_theme`: только значение в кавычках, без имени ключа.
- [ ] `obsidian_appearance`: если `{}` — писать пусто, а не мусор.
- [ ] Не ломать существующий формат `key=value` (его читают тесты и GUI).

### T0.4. Курсорная тема (решение)

`kcminputrc` не входит в `COMPONENT_PATHS`, поэтому KDE-курсор не сохраняется в профиль.

- [ ] Решить: добавлять компонент `cursor` (меняет состав профилей) или оставить read-only в инспекторе.
- [ ] Если добавляем — обновить `COMPONENT_PATHS` в `theme-profile`, `TRACKED_APPS` в Python и Rust, тесты паритета.

**Acceptance Phase 0:** `theme-profile status` больше не содержит `Usage:`, L&F = `glass`, тесты зелёные.

---

## 5. Phase 1 — read-only инспектор

### T1.1. Схема полей

`gui/qt-app/src/core/theme_schema.py`:

```python
ThemeField(
    id="accent_color",
    section="colors",
    label="Accent color",
    source=IniSource(".config/kdeglobals", "General", "AccentColor", type="color"),
    default=None,
    choices=None,
    apply=CmdApply(["plasma-apply-colorscheme", "-a", "$VALUE", "$ColorScheme"]),
    badge="live",
    summary=True,
    description="Selection/accent color used by Plasma and Qt apps",
    keywords=("accent", "выделение", "цвет"),
)
```

- [ ] Dataclasses: `ThemeField`, `IniSource`, `JsonSource`, `TomlSource`, `CssSource`, `UserJsSource`, `CmdApply`, `ConfigApply`.
- [ ] Секции: `colors`, `typography`, `windows`, `assets`, `apps`, `advanced`.
- [ ] Набор полей — по таблицам [THEME_INSPECTOR.md §3.3](THEME_INSPECTOR.md#33-кураторский-набор-полей-mvp) (~60).
- [ ] `summary=True` — для карточки обзора и строки «DNA».

### T1.2. Чтение

`gui/qt-app/src/core/theme_core.py`:

- [ ] INI через `kreadconfig6` (абсолютный путь) с fallback на свой парсер.
- [ ] JSON/JSONC — чтение с вырезанием комментариев.
- [ ] TOML — `tomllib`.
- [ ] CSS — `@define-color`.
- [ ] `user.js` — переиспользовать логику `zen_user_pref`.
- [ ] «Не задано» ≠ пустая строка: `is_default=True` и понятный display.
- [ ] Кэш значений + инвалидация по mtime.

### T1.3. Choices-провайдеры

- [ ] Color schemes: `plasma-apply-colorscheme --list-schemes`, группировка User/System.
- [ ] Plasma theme: `plasma-apply-desktoptheme --list-themes`.
- [ ] L&F / cursor: `--list` / `--list-themes`.
- [ ] Kvantum: `*.kvconfig` (варианты внутри каталогов! `Orchis/OrchisDark.kvconfig`).
- [ ] Icons: каталоги с `index.theme`.
- [ ] GTK themes: `/usr/share/themes`, `~/.themes`, `~/.local/share/themes`.
- [ ] Fonts: `Qt.fontFamilies()`.
- [ ] Если текущее значение не в списке — пункт «Custom: <value>» (не терять его).

### T1.4. Валидация

- [ ] Цветовая схема существует.
- [ ] L&F-пакет существует (ловит текущий баг).
- [ ] Plasma theme / icons / cursor / GTK theme существуют.
- [ ] Kvantum-тема существует (с учётом вариантов).
- [ ] Шрифт есть в системе (`fc-match`).
- [ ] Конфликт: `blurEnabled` и `better_blur_dxEnabled` одновременно.
- [ ] Конфиг configured vs loaded (`org.kde.KWin /Effects loadedEffects`).
- [ ] `ThemeIssue(severity, field_id, message, fix_action)`.

### T1.5. Контракт и контроллер

- [ ] `ThemeCore` ABC в `protocol.py`:
  `sections()`, `fields(section)`, `value(field_id, scope)`, `choices(field_id)`, `validate()`, `set_value()`, `reset()`, `snapshot()`, `revert()`.
- [ ] `CoreFactory.theme_core()` → Python-реализация (не зависит от `--core`; задокументировать в Settings).
- [ ] `ThemeController` (QObject): `Properties` секций/полей, сигналы `busyChanged`, `valueChanged(fieldId)`, `toastRequested(text)`.
- [ ] Регистрация в `register_controllers(engine)`; держать Python-ссылку (иначе QML видит `null`).
- [ ] Async-обёртки: чтение и запись не блокируют GUI.

### T1.6. UI

- [ ] `ThemePage.qml`: scope-переключатель `Live | <profile>`, карточка обзора (обои, палитра, 4 факта, issues), 6 карточек секций, Advanced.
- [ ] `ThemeSectionPage.qml`: `Kirigami.FormLayout`, группы, поиск по секции, бейджи, контекстное меню (Reset/Copy/Open file/Raw).
- [ ] `ThemeSectionCard.qml`, `ThemeFieldRow.qml`, `ColorSwatch.qml`, `ValueBadge.qml`.
- [ ] Добавить типы в `qml/Components/qmldir`.
- [ ] Drawer: `Profiles · Theme · Settings`.
- [ ] Карточка профиля: действие «Inspect» + строка DNA (`#808e47 · OrchisDark · blur 11 · r10`).
- [ ] Advanced: поиск по всем полям, Validation report, diff live↔profile по полям.
- [ ] «Open in System Settings»: `kcmshell6 kcm_colors|kcm_fonts|kcm_icons|kcm_cursortheme|kcm_kwindecoration|kcm_kwin_effects|kcm_kwinrules|kcm_style`.
- [ ] «Open file»: `xdg-open` (fallback: показать путь).
- [ ] Glass-режим: страница следует `themeController.isGlass` (как `Main.qml`).
- [ ] Без `ToolTip.text` → `tooltip:` (есть тест).

### T1.7. Тесты

- [ ] `test_theme_inspector.py`: схема (уникальные id, валидные секции, у каждого поля есть source).
- [ ] Golden-паритет с `theme-profile status` там, где значения пересекаются.
- [ ] Валидация на синтетическом `$HOME` (подмена `Path.home`): битый L&F, отсутствующая схема, Kvantum-вариант.
- [ ] QML: файлы существуют, `qmldir` содержит новые типы, offscreen-рендер страницы без QML-предупреждений.
- [ ] «Не блокирует GUI»: чтение секции не дольше N мс на кэше (мягкий тест).
- [ ] Обновить `ALL_PY_FILES`-совместимость (новые файлы компилируются).

**Acceptance Phase 1:** страница открывается, все поля заполнены, Validation находит испорченный L&F, diff по полям работает, `pytest` зелёный, 0 QML-warning offscreen.

---

## 6. Phase 2 — редактирование

### T2.1. Запись

- [ ] `kwriteconfig6 --notify` (+ `--type bool`) для KDE/Kvantum INI.
- [ ] Точечная запись JSON/TOML/CSS (regex по ключу, без переформатирования файла).
- [ ] Атомарная запись (tmp + rename), сохранение прав.
- [ ] Хуки: `kwin-reconfigure`, `kwin-effect`, `kbuildsycoca`, `kitty-live`, `plasmashell`.
- [ ] Best-effort: ошибка хука → тост «сохранено, перезапустите приложение», запись не откатывается.

### T2.2. Снимок / Undo

- [ ] Снимок затронутых файлов при первой записи в сессии + `backups/inspector-<ts>/`.
- [ ] Стек Undo (до 50): файл, байты до, поле, старое значение.
- [ ] `Ctrl+Z`, «Undo last», «Revert all».
- [ ] Проверка mtime/хеша перед записью: «файл изменён вне приложения — перечитать?».

### T2.3. Контролы

- [ ] ColorDialog (accent, роли палитры), hex + alpha.
- [ ] Слайдеры с дебаунсом 250 мс (blur, contrast, opacity, радиус, анимация).
- [ ] ComboBox из choices + «Custom…».
- [ ] FontDialog: family + size, сохранять weight/style в составной строке.
- [ ] Confirm для тяжёлых: L&F, иконки, рестарт plasmashell.

### T2.4. Набор редактируемых полей

Colors: accent, accentFromWallpaper, scheme, window/view/button/text/selection/link, contrast, frameContrast, widgetStyle.
Typography: UI/fixed/small/menu/toolbar/title, GTK font.
Windows: decoration library/theme/border, Klassy opacity ×2 + radius + shadow, bbdx enabled/strength/contrast/decorations/docks/menus, legacy blur, contrast, translucency + 6 процентов, animation factor.
Assets: Plasma theme, L&F (confirm), icons, cursor + size, splash, GTK theme/dark/icons, Kvantum theme + translucent/blurring/popup blurring.
Apps: kitty opacity/blur (live), alacritty opacity/blur, btop theme/rounded corners, zed mode/light/dark, vscode/cursor colorTheme, zen prefs.

### T2.5. Тесты

- [ ] Roundtrip на temp `$HOME`: для каждого writable-поля `set → value` совпадает.
- [ ] Undo восстанавливает байты файла.
- [ ] Внешнее изменение файла → warning, без потери данных.
- [ ] Хуки вызываются с ожидаемыми аргументами (mock subprocess/D-Bus).
- [ ] Confirm-диалоги не ломают offscreen-тесты.

**Acceptance Phase 2:** accent, Kvantum, radius, blur и opacity меняются из UI; Undo/Revert работают; ни один файл не повреждён; тесты зелёные.

---

## 7. Phase 3 — продвинутое

- [ ] Raw-таблица по файлам + глобальный поиск по ключам.
- [ ] «Restore field from profile» (частичное применение).
- [ ] Validation report UI с Fix-кнопками.
- [ ] Экспорт снимка темы в JSON.
- [ ] Per-app advanced: zed/vscode/zen/obsidian.
- [ ] Rust-паритет инспектора (или явное «inspector is Python-only» в Settings и docs).

---

## 8. Контракты (минимальный вид)

```python
@dataclass(frozen=True)
class ThemeSection:
    id: str; title: str; summary: str; issue_count: int

@dataclass(frozen=True)
class ThemeFieldInfo:
    id: str; section: str; label: str; type: str
    value: object; display: str; default: object | None
    is_default: bool; is_modified: bool
    badge: str            # live | new | app | shell | warning | error
    choices: tuple[Choice, ...]
    file: str; key: str; description: str

@dataclass(frozen=True)
class ThemeIssue:
    severity: str         # error | warning | info
    field_id: str; message: str; fix: str | None

class ThemeCore(ABC):
    def sections(self) -> list[ThemeSection]: ...
    def fields(self, section: str, scope: str = "live") -> list[ThemeFieldInfo]: ...
    def value(self, field_id: str, scope: str = "live") -> ThemeFieldInfo: ...
    def choices(self, field_id: str) -> list[Choice]: ...
    def validate(self) -> list[ThemeIssue]: ...
    def set_value(self, field_id: str, value: object) -> Result: ...
    def reset(self, field_id: str, to: str = "default") -> Result: ...
    def snapshot(self) -> Result: ...
    def revert(self) -> Result: ...
```

`scope` = `"live"` или `"profile:<name>"` (для последнего `set_value` → `Result.err("profile scope is read-only")`).

---

## 9. Проверки перед коммитом

```bash
# Python
cd gui/qt-app && QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ -q

# Bash
bash tests/test-scripts.sh
shellcheck files/bin/* scripts/*.sh

# Rust (если трогали ядро)
cd gui/qt-app/src/core/rust_core && cargo build --release

# Живой запуск / скриншот
cd gui/qt-app && KTM_SCREENSHOT=/tmp/theme-page.png .venv/bin/kde-theme-manager
```

Установка и деплой — только из исходников:

```bash
scripts/install-theme-profile-kit.sh
scripts/install-kde-theme-manager.sh
```

---

## 10. Definition of Done

- [ ] Phase 0 смержен, испорченный L&F восстановлен, есть регрессионный тест.
- [ ] Theme-страница открывается из drawer и с карточки профиля.
- [ ] Read-only инспектор: ≥50 полей, 6 секций, поиск, diff live↔profile.
- [ ] Validation находит битые значения (проверено на реальном кейсе L&F).
- [ ] Редактирование: accent, Kvantum, Klassy radius/opacity, blur, translucency, kitty opacity.
- [ ] Undo/Revert работают; после тестов ни один реальный конфиг не изменён (temp HOME).
- [ ] `pytest`, `test-scripts.sh`, `shellcheck` — зелёные; 0 QML-предупреждений offscreen.
- [ ] README + `docs/CURRENT_APP.md` + `docs/ROADMAP.md` обновлены.
- [ ] Коммит и пуш в `origin/main`.

---

## 11. Риски

| Риск | Митигация |
|---|---|
| KConfig-экранирование | только `kwriteconfig6`, не свой INI-writer |
| Составные строки шрифтов | менять family/size, остальное сохранять |
| `plasmashell` перезаписывает appletsrc | не редактировать live, только read-only |
| Kvantum-варианты | список по `*.kvconfig`, а не по каталогам |
| Эффекты: configured ≠ loaded | показывать оба, предупреждать |
| Долгие D-Bus/файловые операции | async-контроллер, не блокировать GUI |
| Случайная порча конфигов | снимок + Undo + бэкап в `backups/inspector-*` |
| Расползание в System Settings | глубокое — ссылками `kcmshell6` |

---

## 12. Открытые решения

1. Модель применения: **instant + Undo** (рекомендация) или черновик + Apply.
2. Scope: **только live** (рекомендация) или ещё файлы профилей.
3. Курсор: добавлять в отслеживаемые компоненты или read-only (T0.4).
4. Язык UI: английский (как сейчас) или добавляем русские строки.
