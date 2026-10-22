"""
Tracked Applications Registry — полный список отслеживаемых приложений
на основе TRACKED_PATHS из bash-версии theme-profile.
"""

from dataclasses import dataclass
import shutil
import subprocess
from typing import Optional

from .paths import live_path
from .protocol import Component, AppStatus, TrackedAppsCore


# ──────────────────────────────────────────────────────────────
# Определение всех отслеживаемых компонентов
# ──────────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class TrackedAppDef:
    """Определение отслеживаемого приложения (статические метаданные)."""
    id: str
    name: str
    category: str
    config_paths: tuple[str, ...]
    detect_command: Optional[str] = None          # Команда для проверки установки
    flatpak_id: Optional[str] = None              # Flatpak ID если есть
    supports_live_reload: bool = False
    description: str = ""
    icon: str = ""
    docs_url: str = ""


# Порядок = порядок в UI
TRACKED_APPS: tuple[TrackedAppDef, ...] = (
    # === Базовые KDE/Plasma (всегда доступны) ===
    TrackedAppDef(
        id="kwin",
        name="KWin",
        category="KDE / Plasma",
        config_paths=(
            ".config/kwinrc",
            ".config/kwinrulesrc",
        ),
        description="KWin window manager: effects, rules, blur, glass",
        icon="preferences-system-windows",
    ),
    TrackedAppDef(
        id="plasma_shell",
        name="Plasma Shell",
        category="KDE / Plasma",
        config_paths=(
            ".config/plasmarc",
            ".config/plasmashellrc",
            ".config/plasma-org.kde.plasma.desktop-appletsrc",
        ),
        description="Plasma panels, widgets, desktop applets",
        icon="plasma",
    ),
    TrackedAppDef(
        id="kdeglobals",
        name="KDE Globals",
        category="KDE / Plasma",
        config_paths=(".config/kdeglobals",),
        description="Colors, accent, Look & Feel, color scheme, widget style",
        icon="preferences-desktop-theme",
    ),

    # === GTK ===
    TrackedAppDef(
        id="gtk3",
        name="GTK3",
        category="GTK / Qt",
        config_paths=(
            ".config/gtk-3.0/settings.ini",
            ".config/gtk-3.0/gtk.css",
            ".config/gtk-3.0/colors.css",
        ),
        description="GTK3 theme, custom CSS, colors",
        icon="preferences-desktop-theme-gtk",
    ),
    TrackedAppDef(
        id="gtk4",
        name="GTK4",
        category="GTK / Qt",
        config_paths=(
            ".config/gtk-4.0/settings.ini",
            ".config/gtk-4.0/gtk.css",
            ".config/gtk-4.0/colors.css",
        ),
        description="GTK4 theme, custom CSS, colors",
        icon="preferences-desktop-theme-gtk",
    ),

    # === Qt ===
    TrackedAppDef(
        id="qt5ct",
        name="Qt5/Qt6 Style",
        category="GTK / Qt",
        config_paths=(
            ".config/QtProject.conf",
            ".config/Trolltech.conf",
        ),
        description="Qt5/Qt6 widget style, font, icon theme",
        icon="qtlogo",
    ),

    # === Window Decorations ===
    TrackedAppDef(
        id="klassy",
        name="Klassy",
        category="Window Decorations",
        config_paths=(
            ".config/klassy/klassyrc",
            ".config/klassy/windecopresetsrc",
        ),
        detect_command="klassy",
        description="KWin decoration: titlebar opacity, corner radius, buttons",
        icon="preferences-system-windows",
        docs_url="https://github.com/paul-g/klassy",
    ),
    TrackedAppDef(
        id="kvantum",
        name="Kvantum",
        category="Window Decorations",
        config_paths=(
            ".config/Kvantum/kvantum.kvconfig",
            ".config/Kvantum/Sandstone",
        ),
        detect_command="kvantummanager",
        description="SVG-based theme engine for Qt/KDE",
        icon="preferences-system-windows",
        docs_url="https://github.com/tsujan/Kvantum",
    ),

    # === Terminals ===
    TrackedAppDef(
        id="kitty",
        name="Kitty",
        category="Terminals",
        config_paths=(".config/kitty/kitty.conf",),
        detect_command="kitty",
        supports_live_reload=True,
        description="GPU-accelerated terminal with live config reload",
        icon="utilities-terminal",
        docs_url="https://sw.kovidgoyal.net/kitty/",
    ),
    TrackedAppDef(
        id="alacritty",
        name="Alacritty",
        category="Terminals",
        config_paths=(
            ".config/alacritty/alacritty.toml",
            ".config/alacritty/themes/noctalia.toml",
        ),
        detect_command="alacritty",
        description="GPU-accelerated terminal, TOML config",
        icon="utilities-terminal",
        docs_url="https://github.com/alacritty/alacritty",
    ),

    # === Launchers / Menu ===
    TrackedAppDef(
        id="wofi",
        name="Wofi",
        category="Launchers / Menu",
        config_paths=(
            ".config/wofi/style.css",
            ".config/wofi/wallpaper.css",
        ),
        detect_command="wofi",
        description="Application launcher / menu (GTK)",
        icon="system-run",
        docs_url="https://hg.sr.ht/~scoopta/wofi",
    ),

    # === Monitors ===
    TrackedAppDef(
        id="btop",
        name="btop",
        category="Monitors",
        config_paths=(
            ".config/btop/btop.conf",
            ".config/btop/themes/noctalia.theme",
            ".config/btop/themes/paper.theme",
        ),
        detect_command="btop",
        description="Resource monitor with themes",
        icon="utilities-system-monitor",
        docs_url="https://github.com/aristocratos/btop",
    ),

    # === Sysinfo ===
    TrackedAppDef(
        id="fastfetch",
        name="Fastfetch",
        category="Sysinfo",
        config_paths=(
            ".config/fastfetch/config.jsonc",
            ".config/fastfetch/logo",
            ".config/fastfetch/cat-source.jpg",
        ),
        detect_command="fastfetch",
        description="System info tool with custom logo/config",
        icon="preferences-desktop-theme",
        docs_url="https://github.com/fastfetch-cli/fastfetch",
    ),

    # === Editors ===
    TrackedAppDef(
        id="zed",
        name="Zed",
        category="Editors",
        config_paths=(
            ".config/zed/settings.json",
            ".config/zed/themes",
        ),
        detect_command="zed",
        description="Code editor with native themes",
        icon="text-editor",
        docs_url="https://zed.dev/",
    ),
    TrackedAppDef(
        id="vscode",
        name="VS Code",
        category="Editors",
        config_paths=(".config/Code/User/settings.json",),
        detect_command="code",
        description="VS Code settings (theme, font, etc.)",
        icon="visual-studio-code",
        docs_url="https://code.visualstudio.com/",
    ),
    TrackedAppDef(
        id="cursor",
        name="Cursor",
        category="Editors",
        config_paths=(".config/Cursor/User/settings.json",),
        detect_command="cursor",
        description="Cursor editor settings",
        icon="text-editor",
        docs_url="https://cursor.sh/",
    ),

    # === Browser ===
    TrackedAppDef(
        id="zen",
        name="Zen Browser",
        category="Browser",
        config_paths=(
            ".zen/gp0y8wrv.Default (release)/user.js",
            ".zen/gp0y8wrv.Default (release)/chrome/userChrome.css",
            ".zen/gp0y8wrv.Default (release)/chrome/userContent.css",
            ".zen/gp0y8wrv.Default (release)/chrome/zen-themes.css",
        ),
        flatpak_id="app.zen_browser.zen",
        description="Firefox-based browser with user.js + userChrome.css theming",
        icon="web-browser",
        docs_url="https://zen-browser.app/",
    ),

    # === Notes ===
    TrackedAppDef(
        id="obsidian",
        name="Obsidian",
        category="Notes",
        config_paths=(
            ".config/obsidian/obsidian.json",
            ".config/obsidian/Preferences",
            "obsidian/vault/.obsidian/appearance.json",
        ),
        detect_command="obsidian",
        flatpak_id="md.obsidian.Obsidian",
        description="Markdown notes with theme/appearance settings",
        icon="x-office-note",
        docs_url="https://obsidian.md/",
    ),

    # === System Profiles ===
    TrackedAppDef(
        id="color_schemes",
        name="Color Schemes",
        category="System Profiles",
        config_paths=(".local/share/color-schemes/ThemeProfilePaper.colors",),
        description="KDE color scheme files",
        icon="preferences-desktop-color",
    ),
    TrackedAppDef(
        id="look_and_feel",
        name="Look & Feel",
        category="System Profiles",
        config_paths=(
            ".local/share/plasma/look-and-feel/glass",
            ".local/share/plasma/look-and-feel/paper",
        ),
        description="Plasma Look & Feel packages (glass/paper)",
        icon="preferences-desktop-theme",
    ),
)


# ──────────────────────────────────────────────────────────────
# Детекция статусов
# ──────────────────────────────────────────────────────────────

def _check_command(cmd: str) -> bool:
    """Проверить наличие команды в PATH."""
    return shutil.which(cmd.split()[0]) is not None


def _check_flatpak(flatpak_id: str) -> bool:
    """Проверить установлен ли Flatpak."""
    try:
        result = subprocess.run(
            ["flatpak", "list", "--app", "--columns=application"],
            capture_output=True, text=True, timeout=5
        )
        return flatpak_id in result.stdout
    except Exception:
        return False


def _check_configs_exist(paths: tuple[str, ...]) -> bool:
    """Проверить наличие хотя бы одного конфига (с учётом XDG)."""
    return any(live_path(p).exists() for p in paths)


def detect_app_status(app: TrackedAppDef) -> AppStatus:
    """Определить статус приложения."""
    # 1. Проверка команды установки
    if app.detect_command and not _check_command(app.detect_command):
        # 2. Проверка Flatpak
        if app.flatpak_id and not _check_flatpak(app.flatpak_id):
            return AppStatus.NOT_INSTALLED
        elif not app.flatpak_id:
            return AppStatus.NOT_INSTALLED

    # 3. Проверка конфигов
    if _check_configs_exist(app.config_paths):
        return AppStatus.AVAILABLE
    else:
        # Установлено, но конфигов ещё нет (первый запуск)
        return AppStatus.PARTIAL


def build_component(app: TrackedAppDef) -> Component:
    """Построить Component из определения + актуальный статус."""
    status = detect_app_status(app)
    return Component(
        id=app.id,
        name=app.name,
        category=app.category,
        config_paths=app.config_paths,
        status=status,
        supports_live_reload=app.supports_live_reload,
        description=app.description,
        icon=app.icon,
        docs_url=app.docs_url,
    )


def detect_all_apps() -> list[Component]:
    """Получить список всех компонентов с актуальными статусами."""
    return [build_component(app) for app in TRACKED_APPS]


# ──────────────────────────────────────────────────────────────
# Реализация TrackedAppsCore
# ──────────────────────────────────────────────────────────────

class PythonTrackedAppsCore(TrackedAppsCore):
    """Python реализация реестра отслеживаемых приложений."""

    def __init__(self):
        self._cache: Optional[list[Component]] = None

    def detect_all(self) -> list[Component]:
        """Свежий детект всех приложений."""
        self._cache = detect_all_apps()
        return self._cache

    def refresh(self) -> list[Component]:
        """Принудительный рефреш (очистка кэша)."""
        self._cache = None
        return self.detect_all()

    def get_all_components(self) -> list[Component]:
        """Все компоненты (из кэша или свежий детект)."""
        if self._cache is None:
            return self.detect_all()
        return self._cache

    def get_categories(self) -> list[str]:
        """Уникальные категории в порядке появления."""
        seen = set()
        categories = []
        for comp in self.get_all_components():
            if comp.category not in seen:
                seen.add(comp.category)
                categories.append(comp.category)
        return categories

    def get_components_by_category(self, category: str) -> list[Component]:
        """Компоненты по категории."""
        return [c for c in self.get_all_components() if c.category == category]


# Для обратной совместимости
__all__ = [
    "TRACKED_APPS",
    "TrackedAppDef",
    "detect_all_apps",
    "detect_app_status",
    "build_component",
    "PythonTrackedAppsCore",
]