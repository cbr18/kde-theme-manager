"""
System Tray & Global Hotkey Controller.

Provides:
- System tray icon with context menu (if available)
- Global hotkey (Meta+T by default) to show/hide window
- Minimize to tray instead of close
"""

from __future__ import annotations

import os
from PySide6.QtCore import QObject, Signal, Slot, Property, QTimer, QCoreApplication
from PySide6.QtGui import QGuiApplication, QIcon, QAction
from PySide6.QtDBus import QDBusConnection, QDBusMessage

# Make system tray optional - import lazily
QSystemTrayIcon = None
QMenu = None

def _import_widgets():
    """Lazy import of QtWidgets to avoid segfault on Wayland."""
    global QSystemTrayIcon, QMenu
    if QSystemTrayIcon is None:
        try:
            from PySide6.QtWidgets import QSystemTrayIcon as _QSystemTrayIcon, QMenu as _QMenu
            QSystemTrayIcon = _QSystemTrayIcon
            QMenu = _QMenu
        except Exception:
            QSystemTrayIcon = None
            QMenu = None


class SystemTrayController(QObject):
    """Управляет системным треем и глобальными хоткеями."""

    trayIconVisibleChanged = Signal(bool)
    hotkeyPressed = Signal()

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

        self._tray_icon = None
        self._tray_menu = None
        self._main_window = None
        self._hotkey_enabled = True
        self._hotkey_sequence = "Meta+T"
        self._minimize_to_tray = False
        self._native_filter = None

    @classmethod
    def instance(cls) -> "SystemTrayController":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def set_main_window(self, window) -> None:
        """Установить главное окно для управления видимостью."""
        self._main_window = window

    @Property(bool, notify=trayIconVisibleChanged)
    def trayIconVisible(self) -> bool:
        return self._tray_icon is not None and self._tray_icon.isVisible()

    @Property(bool, notify=hotkeyPressed)
    def hotkeyEnabled(self) -> bool:
        return self._hotkey_enabled

    @hotkeyEnabled.setter
    def hotkeyEnabled(self, value: bool) -> None:
        if self._hotkey_enabled != value:
            self._hotkey_enabled = value
            if value:
                self._register_hotkey()
            else:
                self._unregister_hotkey()

    @Property(str, notify=hotkeyPressed)
    def hotkeySequence(self) -> str:
        return self._hotkey_sequence

    @hotkeySequence.setter
    def hotkeySequence(self, value: str) -> None:
        if self._hotkey_sequence != value:
            self._hotkey_sequence = value
            if self._hotkey_enabled:
                self._register_hotkey()

    @Property(bool)
    def minimizeToTray(self) -> bool:
        return self._minimize_to_tray

    @minimizeToTray.setter
    def minimizeToTray(self, value: bool) -> None:
        self._minimize_to_tray = value

    def initialize(self) -> None:
        """Инициализировать трей и хоткей."""
        try:
            self._create_tray_icon()
        except Exception as e:
            print(f"System tray not available: {e}")
            self._tray_icon = None
        
        if self._hotkey_enabled:
            self._register_hotkey()

    def _create_tray_icon(self) -> None:
        """Создать иконку в системном трее."""
        _import_widgets()
        if QSystemTrayIcon is None:
            raise RuntimeError("QtWidgets not available")

        if self._tray_icon is not None:
            return

        # Check if system tray is available
        try:
            if not QSystemTrayIcon.isSystemTrayAvailable():
                raise RuntimeError("System tray not available")
        except Exception:
            raise RuntimeError("System tray not available")

        # System tray requires QApplication (QWidget), not just QGuiApplication
        from PySide6.QtWidgets import QApplication
        if not QApplication.instance():
            raise RuntimeError("QApplication required for system tray")

        try:
            self._tray_icon = QSystemTrayIcon()
        except Exception as e:
            raise RuntimeError(f"Failed to create system tray icon: {e}")

        self._tray_icon.setIcon(QIcon.fromTheme("preferences-desktop-theme"))
        self._tray_icon.setToolTip("KDE Theme Manager")

        # Контекстное меню
        _import_widgets()
        self._tray_menu = QMenu()

        show_action = QAction("Показать", self._tray_menu)
        show_action.triggered.connect(self._show_window)
        self._tray_menu.addAction(show_action)

        # Быстрое переключение профилей
        self._tray_menu.addSeparator()
        profiles_action = self._tray_menu.addAction("Профили")
        profiles_action.setEnabled(False)  # Заголовок

        self._tray_icon.setContextMenu(self._tray_menu)

        # Двойной клик — показать/скрыть
        self._tray_icon.activated.connect(self._on_tray_activated)

        self._tray_icon.show()
        self.trayIconVisibleChanged.emit(True)

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Обработка кликов по иконке трея."""
        if reason == QSystemTrayIcon.DoubleClick:
            self._toggle_window_visibility()

    def _show_window(self) -> None:
        """Показать главное окно."""
        if self._main_window:
            self._main_window.show()
            self._main_window.raise_()
            self._main_window.requestActivate()

    def _hide_window(self) -> None:
        """Скрыть главное окно."""
        if self._main_window:
            self._main_window.hide()

    def _toggle_window_visibility(self) -> None:
        """Переключить видимость окна."""
        if self._main_window:
            if self._main_window.isVisible():
                self._main_window.hide()
            else:
                self._main_window.show()
                self._main_window.raise_()
                self._main_window.requestActivate()

    @Slot()
    def toggle_window(self) -> None:
        """Слот для вызова из QML (global hotkey)."""
        self._toggle_window_visibility()
        self.hotkeyPressed.emit()

    def _register_hotkey(self) -> None:
        """Зарегистрировать глобальный хоткей через KGlobalAccel (KWin)."""
        try:
            # Через KGlobalAccel D-Bus
            bus = QDBusConnection.sessionBus()
            msg = QDBusMessage.createMethodCall(
                "org.kde.kglobalaccel",
                "/kglobalaccel",
                "org.kde.kglobalaccel",
                "setShortcut"
            )
            msg.setArguments([
                "org.kde.theme-manager",  # component name
                "toggle_window",           # action name
                self._hotkey_sequence      # shortcut
            ])
            QDBusConnection.sessionBus().asyncCall(msg)
        except Exception:
            pass

    def _unregister_hotkey(self) -> None:
        """Отменить регистрацию хоткея."""
        try:
            bus = QDBusConnection.sessionBus()
            msg = QDBusMessage.createMethodCall(
                "org.kde.kglobalaccel",
                "/kglobalaccel",
                "org.kde.kglobalaccel",
                "removeShortcut"
            )
            msg.setArguments(["org.kde.theme-manager", "toggle_window"])
            QDBusConnection.sessionBus().asyncCall(msg)
        except Exception:
            pass

    def set_hotkey(self, sequence: str) -> None:
        """Установить новый хоткей."""
        self._hotkey_sequence = sequence
        self._register_hotkey()


def register_system_tray(engine, main_window) -> None:
    """Зарегистрировать SystemTrayController в QML."""
    from PySide6.QtWidgets import QApplication
    if not QApplication.instance():
        # QGuiApplication (QtQuick/QML only) - skip system tray to avoid QWidget crash
        print("System tray skipped: QApplication not available (pure QML mode)")
        return None

    controller = SystemTrayController.instance()
    controller.set_main_window(main_window)
    controller.initialize()
    engine.rootContext().setContextProperty("trayController", controller)
    return controller