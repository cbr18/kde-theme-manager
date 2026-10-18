"""
KDE Theme Profile Manager — Qt/QML Application Entry Point.

v0.2.0 — Native KDE UI with Kirigami, Clean Architecture.
"""

import sys
from pathlib import Path

# Добавляем src в путь для импортов
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtCore import QUrl, QCoreApplication, Qt
from PySide6.QtQuickControls2 import QQuickStyle

# Импорт контроллеров
from controllers import MainController, register_controllers
from theme_controller import register_theme_controller
from system_tray import register_system_tray

# Регистрация мета-типов для QML (not needed in PySide6, Python types auto-registered)
from core.protocol import Result, ProfileInfo, Component, AppStatus, AppSettings


def _show_help() -> int:
    """Show help via QMessageBox.about (requires QtWidgets/QGuiApplication)."""
    from PySide6.QtWidgets import QMessageBox

    app = QGuiApplication(sys.argv)
    QMessageBox.about(
        None,
        "KDE Theme Manager",
        (
            "<h1>KDE Theme Profile Manager</h1>"
            "<p><b>Version:</b> 0.2.0-dev</p>"
            "<p>A Qt/QML-based theme profile manager for KDE Plasma.</p>"
            "<p><b>Usage:</b></p>"
            "<pre>kde-theme-manager [options]</pre>"
            "<p><b>Options:</b></p>"
            "<ul>"
            "<li><code>--help, -h</code> — Show this help message</li>"
            "<li><code>--version</code> — Show version and exit</li>"
            "</ul>"
        ),
    )
    return 0


def main() -> int:
    # Handle --help / -h early (before QML engine setup)
    if "--help" in sys.argv or "-h" in sys.argv:
        return _show_help()

    # Handle --version
    if "--version" in sys.argv:
        print("KDE Theme Manager 0.2.0-dev")
        return 0

    # Настройка приложения
    QCoreApplication.setApplicationName("KDE Theme Manager")
    QCoreApplication.setApplicationVersion("0.2.0-dev")
    QCoreApplication.setOrganizationName("cbr")
    QCoreApplication.setOrganizationDomain("github.com/cbr18/kde-theme-manager")

    # Включаем High DPI scaling
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    # Стиль — Kirigami использует свой, но на всякий случай
    QQuickStyle.setStyle("org.kde.desktop")

    app = QGuiApplication(sys.argv)
    app.setWindowIcon(QIcon.fromTheme("preferences-desktop-theme"))

    # QML Engine
    engine = QQmlApplicationEngine()

    # Регистрация контроллеров
    main_controller = register_controllers(engine)

    # Регистрация ThemeController (dogfooding)
    theme_controller = register_theme_controller(engine)

    # Синхронизировать тему с активным профилем
    def sync_theme():
        active = main_controller.profile.activeProfile
        if active:
            theme_controller.sync_with_active_profile(active)

    main_controller.profile.activeProfileChanged.connect(sync_theme)

    # Инициализация контроллеров ДО загрузки QML
    main_controller.initialize()

    # Добавление путей для QML импортов
    qml_path = Path(__file__).parent.parent / "qml"
    engine.addImportPath(str(qml_path))

    # Загрузка главной QML
    main_qml = qml_path / "Main.qml"
    engine.load(QUrl.fromLocalFile(str(main_qml)))

    if not engine.rootObjects():
        print("Failed to load QML", file=sys.stderr)
        try:
            for error in engine.errors():
                print(f"  QML Error: {error}", file=sys.stderr)
        except AttributeError:
            pass
        return 1

    # Получить главное окно и зарегистрировать System Tray
    main_window = engine.rootObjects()[0]
    register_system_tray(engine, main_window)

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())