"""
Theme Controller — Dogfooding: применяет активный профиль к самому приложению.

Поддерживает: glass (прозрачность + KWin blur), paper, dark, light, system.
"""

import os
import subprocess
from PySide6.QtCore import QObject, Signal, Slot, Property, QTimer, Qt
from PySide6.QtGui import QGuiApplication, QWindow
from PySide6.QtQml import qmlRegisterSingletonInstance


class ThemeController(QObject):
    """Singleton для управления темой приложения."""

    themeChanged = Signal(str)
    glassEffectChanged = Signal(bool)
    windowBlurChanged = Signal(bool)

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
        self._window = None
        self._update_timer = QTimer(self)
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._apply_theme)

    @classmethod
    def instance(cls) -> "ThemeController":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @Slot(QWindow)
    def set_window(self, window: QWindow) -> None:
        """Установить главное окно для применения эффектов."""
        self._window = window

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

    @Property(bool, notify=windowBlurChanged)
    def blurEnabled(self) -> bool:
        return self._blur_enabled

    def _schedule_apply(self) -> None:
        self._update_timer.start(50)

    @Slot()
    def _apply_theme(self) -> None:
        """Применить тему к приложению."""
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

        palette = QGuiApplication.palette()
        bg = palette.color(palette.ColorRole.Window)
        luminance = (0.299 * bg.red() + 0.587 * bg.green() + 0.114 * bg.blue()) / 255
        return "dark" if luminance < 0.5 else "light"

    def _apply_glass_theme(self) -> None:
        """Glass theme: прозрачность окна + KWin blur."""
        self._is_glass = True
        self._blur_enabled = True
        self.glassEffectChanged.emit(True)
        self.windowBlurChanged.emit(True)

        if self._window:
            self._enable_window_blur()

    def _enable_window_blur(self) -> None:
        """Включить прозрачность окна (без изменения флагов)."""
        if not self._window:
            return

        # Включить прозрачность фона (без изменения window flags)
        self._window.setAttribute(Qt.WA_TranslucentBackground, True)
        self._window.setAttribute(Qt.WA_NoSystemBackground, True)

        # Для Wayland: запрашиваем blur через KWin (non-blocking)
        QTimer.singleShot(100, self._request_kwin_blur)

    def _request_kwin_blur(self) -> None:
        """Запросить KWin blur через D-Bus (works on Wayland)."""
        try:
            # Попытка через qdbus6
            subprocess.run([
                "qdbus6", "org.kde.KWin", "/KWin",
                "org.kde.KWin.loadEffect", "blur"
            ], capture_output=True, timeout=1)
        except Exception:
            pass

    def _apply_paper_theme(self) -> None:
        """Paper theme: светлая, без прозрачности."""
        self._is_glass = False
        self._blur_enabled = False
        self.glassEffectChanged.emit(False)
        self.windowBlurChanged.emit(False)
        self._disable_window_blur()
        self._apply_light_theme()

    def _disable_window_blur(self) -> None:
        """Отключить прозрачность и blur."""
        if self._window:
            self._window.setAttribute(Qt.WA_TranslucentBackground, False)
            self._window.setAttribute(Qt.WA_NoSystemBackground, False)

    def _apply_dark_theme(self) -> None:
        """Тёмная тема."""
        self._is_glass = False
        self._blur_enabled = False
        self.glassEffectChanged.emit(False)
        self.windowBlurChanged.emit(False)
        self._disable_window_blur()
        os.environ["QT_QUICK_CONTROLS_MATERIAL_THEME"] = "Dark"
        os.environ["QT_QUICK_CONTROLS_STYLE"] = "Material"

    def _apply_light_theme(self) -> None:
        """Светлая тема."""
        self._is_glass = False
        self._blur_enabled = False
        self.glassEffectChanged.emit(False)
        self.windowBlurChanged.emit(False)
        self._disable_window_blur()
        os.environ["QT_QUICK_CONTROLS_MATERIAL_THEME"] = "Light"
        os.environ["QT_QUICK_CONTROLS_STYLE"] = "Material"

    def _apply_system_theme(self) -> None:
        """Системная тема (follow system)."""
        self._is_glass = False
        self._blur_enabled = False
        self.glassEffectChanged.emit(False)
        self.windowBlurChanged.emit(False)
        self._disable_window_blur()
        os.environ.pop("QT_QUICK_CONTROLS_MATERIAL_THEME", None)
        os.environ.pop("QT_QUICK_CONTROLS_STYLE", None)

    @Slot(str)
    def sync_with_active_profile(self, profile_name: str) -> None:
        """Синхронизировать тему приложения с активным профилем."""
        if profile_name in ("glass", "paper"):
            self.currentTheme = profile_name
        else:
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
    engine.rootContext().setContextProperty("themeController", controller)
    return controller