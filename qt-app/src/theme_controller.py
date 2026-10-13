"""
Theme Controller — Dogfooding: применяет активный профиль к самому приложению.

Читает активный профиль (glass/paper) и настраивает:
- Kirigami.Theme / QtQuick.Controls.Material
- Прозрачность окна + KWin blur для glass
- Цветовую схему
"""

from PySide6.QtCore import QObject, Signal, Slot, Property, QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import qmlRegisterSingletonInstance

from controllers import MainController
from core import CoreFactory


class ThemeController(QObject):
    """Singleton для управления темой приложения."""

    themeChanged = Signal(str)
    glassEffectChanged = Signal(bool)

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        super().__init__()
        self._initialized = True
        self._current_theme = "system"  # system, glass, paper, dark, light
        self._is_glass = False
        self._blur_enabled = False
        self._update_timer = QTimer(self)
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._apply_theme)

    @classmethod
    def instance(cls) -> "ThemeController":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @Property(str, notify=themeChanged)
    def currentTheme(self) -> str:
        return self._current_theme

    @currentTheme.setter
    def currentTheme(self, value: str) -> None:
        if self._current_theme != value:
            self._current_theme = value
            self.themeChanged.emit(value)
            self._schedule_apply()

    @Property(bool, notify=glassEffectChanged)
    def isGlass(self) -> bool:
        return self._is_glass

    @Property(bool, notify=glassEffectChanged)
    def blurEnabled(self) -> bool:
        return self._blur_enabled

    def _schedule_apply(self) -> None:
        self._update_timer.start(100)

    @Slot()
    def _apply_theme(self) -> None:
        """Применить тему к приложению."""
        app = QGuiApplication.instance()
        if not app:
            return

        # Определяем эффективную тему
        effective_theme = self._resolve_theme()

        if effective_theme == "glass":
            self._apply_glass_theme()
        elif effective_theme == "paper":
            self._apply_paper_theme()
        elif effective_theme == "dark":
            self._apply_dark_theme()
        elif effective_theme == "light":
            self._apply_light_theme()
        else:  # system
            self._apply_system_theme()

    def _resolve_theme(self) -> str:
        """Разрешить тему с учётом системной."""
        if self._current_theme != "system":
            return self._current_theme

        # Проверить системную тему
        palette = QGuiApplication.palette()
        bg = palette.color(palette.ColorRole.Window)
        # Простая эвристика: если фон темный — dark
        luminance = (0.299 * bg.red() + 0.587 * bg.green() + 0.114 * bg.blue()) / 255
        return "dark" if luminance < 0.5 else "light"

    def _apply_glass_theme(self) -> None:
        """Glass theme: прозрачность + blur."""
        self._is_glass = True
        self._blur_enabled = True
        self.glassEffectChanged.emit(True)

        # Настройка палитры для прозрачности
        app = QGuiApplication.instance()
        # TODO: настроить прозрачность окна через QML (ApplicationWindow.background)

    def _apply_paper_theme(self) -> None:
        """Paper theme: светлая, без прозрачности."""
        self._is_glass = False
        self._blur_enabled = False
        self.glassEffectChanged.emit(False)
        self._apply_light_theme()

    def _apply_dark_theme(self) -> None:
        """Тёмная тема."""
        self._is_glass = False
        self._blur_enabled = False
        self.glassEffectChanged.emit(False)
        # QtQuick.Controls.Material theme
        import os
        os.environ["QT_QUICK_CONTROLS_MATERIAL_THEME"] = "Dark"
        os.environ["QT_QUICK_CONTROLS_STYLE"] = "Material"

    def _apply_light_theme(self) -> None:
        """Светлая тема."""
        self._is_glass = False
        self._blur_enabled = False
        self.glassEffectChanged.emit(False)
        import os
        os.environ["QT_QUICK_CONTROLS_MATERIAL_THEME"] = "Light"
        os.environ["QT_QUICK_CONTROLS_STYLE"] = "Material"

    def _apply_system_theme(self) -> None:
        """Системная тема (follow system)."""
        import os
        os.environ.pop("QT_QUICK_CONTROLS_MATERIAL_THEME", None)
        os.environ.pop("QT_QUICK_CONTROLS_STYLE", None)

    @Slot(str)
    def sync_with_active_profile(self, profile_name: str) -> None:
        """Синхронизировать тему приложения с активным профилем."""
        if profile_name in ("glass", "paper"):
            self.currentTheme = profile_name
        else:
            # Для кастомных профилей проверяем kdeglobals
            self._detect_from_kdeglobals()

    def _detect_from_kdeglobals(self) -> None:
        """Определить тему из kdeglobals."""
        try:
            from pathlib import Path
            import configparser

            kdeglobals = Path.home() / ".config/kdeglobals"
            if kdeglobals.exists():
                config = configparser.ConfigParser()
                config.read(kdeglobals)
                # Проверить цветовую схему
                color_scheme = config.get("General", "ColorScheme", fallback="")
                if "dark" in color_scheme.lower():
                    self.currentTheme = "dark"
                elif "light" in color_scheme.lower():
                    self.currentTheme = "light"
        except Exception:
            pass

    @Slot()
    def toggle_glass(self) -> None:
        """Переключить glass эффект."""
        if self._is_glass:
            self.currentTheme = "paper"
        else:
            self.currentTheme = "glass"


def register_theme_controller(engine) -> ThemeController:
    """Зарегистрировать ThemeController в QML."""
    controller = ThemeController.instance()
    qmlRegisterSingletonInstance(
        "KDEThemeManager", 1, 0, "ThemeController", controller
    )
    return controller