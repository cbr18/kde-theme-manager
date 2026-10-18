"""
KDE Theme Profile Manager — Qt/QML Application Entry Point.

v0.2.0 — Native KDE UI with Kirigami, Clean Architecture.
"""

import sys
from pathlib import Path

# Добавляем src в путь для импортов
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtWidgets import QApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtCore import QUrl, QCoreApplication, Qt
from PySide6.QtGui import QPalette, QColor

# Импорт контроллеров
from controllers import MainController, register_controllers
from theme_controller import register_theme_controller
from system_tray import register_system_tray

# Регистрация мета-типов для QML (not needed in PySide6, Python types auto-registered)
from core.protocol import Result, ProfileInfo, Component, AppStatus, AppSettings


def _show_help() -> int:
    """Print help to stdout (avoids QWidget/QApplication dependency)."""
    print(
        """KDE Theme Profile Manager v0.2.0-dev
A Qt/QML-based theme profile manager for KDE Plasma.

Usage: kde-theme-manager [options]

Options:
  --help, -h     Show this help message
  --version      Show version and exit

Requires KDE Plasma 6 + Kirigami (org.kde.kirigami, org.kde.desktop QML modules).
For PySide6 bundled Qt, ensure system QML import paths are available.
"""
    )
    return 0


def _find_system_qml_paths() -> list[str]:
    """Find system QML import directories (Qt6, Qt5) for KDE modules."""
    candidates = [
        "/usr/lib/qt6/qml",
        "/usr/lib64/qt6/qml",
        "/usr/lib/qt5/qml",
        "/usr/lib64/qt5/qml",
        "/usr/share/qt6/qml",
        "/usr/share/qt5/qml",
    ]
    return [p for p in candidates if Path(p).is_dir()]


def _setup_palette(app: QApplication) -> None:
    """Ensure valid palette colors for Kirigami.Theme.

    PySide6 bundles its own Qt; the Kirigami QML singleton reads colors
    from the QApplication palette. Without this, Kirigami.Theme may return
    invalid QColor (QVariant(Invalid)), producing QQuickColorValueType warnings.
    """
    palette = app.palette()
    palette.setColor(QPalette.ColorRole.Window, QColor(239, 240, 243))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(31, 31, 31))
    palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(245, 245, 245))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.Text, QColor(31, 31, 31))
    palette.setColor(QPalette.ColorRole.Button, QColor(239, 240, 243))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(31, 31, 31))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(41, 128, 185))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.Link, QColor(41, 128, 185))
    app.setPalette(palette)


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
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon.fromTheme("preferences-desktop-theme"))

    # Ensure valid palette for Kirigami (PySide6 bundled Qt may lack KDE palette)
    _setup_palette(app)

    # QML Engine
    engine = QQmlApplicationEngine()

    # Добавляем системные пути для QML импортов (Kirigami, org.kde.desktop)
    # PySide6 bundles its own Qt — system KDE QML modules need explicit paths
    for sys_qml_path in _find_system_qml_paths():
        engine.addImportPath(sys_qml_path)

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
