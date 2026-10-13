"""
KDE Theme Profile Manager — Qt/QML Application Entry Point.

v0.2.0 — Native KDE UI with Kirigami, Clean Architecture.
"""

import sys
import os
from pathlib import Path

# Добавляем src в путь для импортов
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine, qmlRegisterSingletonInstance
from PySide6.QtCore import QUrl, QCoreApplication, Qt, QTimer
from PySide6.QtQuickControls2 import QQuickStyle

# Импорт контроллеров
from controllers import MainController, register_controllers
from theme_controller import register_theme_controller

# Регистрация мета-типов для QML
from PySide6.QtCore import qRegisterMetaType
from core.protocol import Result, ProfileInfo, Component, AppStatus, AppSettings

qRegisterMetaType(Result)
qRegisterMetaType(ProfileInfo)
qRegisterMetaType(Component)
qRegisterMetaType(AppStatus)
qRegisterMetaType(AppSettings)


def main() -> int:
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

    # Добавление путей для QML импортов
    qml_path = Path(__file__).parent.parent / "qml"
    engine.addImportPath(str(qml_path))

    # Загрузка главной QML
    main_qml = qml_path / "Main.qml"
    engine.load(QUrl.fromLocalFile(str(main_qml)))

    if not engine.rootObjects():
        print("Failed to load QML", file=sys.stderr)
        return 1

    # Инициализация контроллеров после загрузки QML
    def init_controllers():
        main_controller.initialize()

    QTimer.singleShot(0, init_controllers)

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())