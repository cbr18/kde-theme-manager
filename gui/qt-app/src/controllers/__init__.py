"""
Controllers — слой между UI (QML) и Core.

Содержит бизнес-логику, валидацию, маппинг данных для QML.
Использует PySide6 Signals/Slots для реактивного UI.
"""

from typing import Optional
from dataclasses import dataclass
import sys

from PySide6.QtCore import QObject, Signal, Slot, Property, QTimer

from core.protocol import (
    ProfileCore, WallpaperCore, TrackedAppsCore, SettingsCore,
    ProfileInfo, Component, AppStatus, Result, AppSettings
)
from core.python_core import (
    PythonProfileCore, PythonWallpaperCore, PythonTrackedAppsCore, PythonSettingsCore
)
from core import CoreFactory


# ──────────────────────────────────────────────────────────────
# Контроллер профилей
# ──────────────────────────────────────────────────────────────

class ProfileController(QObject):
    """Контроллер для управления профилями."""

    # Signals для QML
    profilesChanged = Signal()
    activeProfileChanged = Signal()
    operationStarted = Signal(str)      # operation name
    operationFinished = Signal(bool, str)  # success, message
    componentsForProfileChanged = Signal(list)  # list of component IDs

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._core: ProfileCore = CoreFactory.profile_core()
        self._profiles: list[ProfileInfo] = []
        self._active_profile: str = ""
        self._components_for_active: list[str] = []
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.timeout.connect(self._delayed_refresh)

    @Property(list, notify=profilesChanged)
    def profiles(self) -> list:
        """Список профилей для QML (list of dicts)."""
        return [
            {
                "name": p.name,
                "isActive": p.is_active,
                "componentCount": len(p.components),
                "components": list(p.components),
                "createdAt": p.created_at,
                "description": p.description,
            }
            for p in self._profiles
        ]

    @Property(str, notify=activeProfileChanged)
    def activeProfile(self) -> str:
        return self._active_profile

    @Property(list, notify=componentsForProfileChanged)
    def componentsForActiveProfile(self) -> list:
        return self._components_for_active

    @Slot()
    def refresh(self) -> None:
        """Обновить список профилей."""
        self._profiles = self._core.list_profiles()
        self._active_profile = self._core.get_active_profile()
        self._update_active_components()
        self.profilesChanged.emit()
        self.activeProfileChanged.emit()

    def _update_active_components(self) -> None:
        if self._active_profile:
            self._components_for_active = self._core.get_profile_components(self._active_profile)
        else:
            self._components_for_active = []
        self.componentsForProfileChanged.emit(self._components_for_active)

    def _delayed_refresh(self) -> None:
        self.refresh()

    @Slot(str)
    def applyProfile(self, profile: str) -> None:
        """Применить профиль."""
        self.operationStarted.emit("apply")
        # Используем настройки для определения компонентов
        settings_core = CoreFactory.settings_core()
        settings = settings_core.load()
        components = None if settings.default_components_mode == "all" else list(settings.custom_components)
        
        result = self._core.apply(profile, components)
        self.operationFinished.emit(result.success, result.message)
        if result.success:
            self._refresh_timer.start(500)  # небольшая задержка для применения

    @Slot(str)
    def saveProfile(self, name: str) -> None:
        """Сохранить текущее состояние как профиль."""
        self.operationStarted.emit("save")
        settings_core = CoreFactory.settings_core()
        settings = settings_core.load()
        components = None if settings.default_components_mode == "all" else list(settings.custom_components)
        
        result = self._core.save(name, components)
        self.operationFinished.emit(result.success, result.message)
        if result.success:
            self._refresh_timer.start(500)

    @Slot(str)
    def deleteProfile(self, name: str) -> None:
        """Удалить профиль."""
        self.operationStarted.emit("delete")
        result = self._core.delete(name)
        self.operationFinished.emit(result.success, result.message)
        if result.success:
            self._refresh_timer.start(500)

    @Slot(str, result=str)
    def diffProfiles(self, profile_a: str, profile_b: str) -> str:
        """Сравнить два профиля."""
        return self._core.diff(profile_a, profile_b)

    @Slot(str, result=list)
    def getProfileComponents(self, profile: str) -> list:
        """Получить компоненты профиля для отображения в UI."""
        comps = self._core.get_profile_components(profile)
        return comps


# ──────────────────────────────────────────────────────────────
# Контроллер обоев
# ──────────────────────────────────────────────────────────────

class WallpaperController(QObject):
    """Контроллер для управления обоями."""

    currentWallpaperChanged = Signal()
    wallpapersChanged = Signal()
    operationStarted = Signal(str)
    operationFinished = Signal(bool, str)

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._core: WallpaperCore = CoreFactory.wallpaper_core()
        self._wallpapers: list[str] = []
        self._current_wallpaper: str = ""
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.timeout.connect(self._delayed_refresh)

    @Property(str, notify=currentWallpaperChanged)
    def currentWallpaper(self) -> str:
        return self._current_wallpaper

    @Property(list, notify=wallpapersChanged)
    def wallpapers(self) -> list:
        return self._wallpapers

    @Slot()
    def refresh(self) -> None:
        self._wallpapers = self._core.list_wallpapers()
        self._current_wallpaper = self._core.current() or ""
        self.wallpapersChanged.emit()
        self.currentWallpaperChanged.emit()

    def _delayed_refresh(self) -> None:
        self.refresh()

    @Slot(result=str)
    def pickWallpaper(self) -> str:
        """Открыть пикер и вернуть путь."""
        self.operationStarted.emit("pick")
        path = self._core.pick()
        self.operationFinished.emit(path is not None, path or "Cancelled")
        if path:
            self._refresh_timer.start(500)
        return path or ""

    @Slot()
    def nextWallpaper(self) -> None:
        self.operationStarted.emit("next")
        result = self._core.next()
        self.operationFinished.emit(result.success, result.message)
        if result.success:
            self._refresh_timer.start(500)

    @Slot()
    def prevWallpaper(self) -> None:
        self.operationStarted.emit("prev")
        result = self._core.prev()
        self.operationFinished.emit(result.success, result.message)
        if result.success:
            self._refresh_timer.start(500)

    @Slot(str)
    def setWallpaper(self, path: str) -> None:
        self.operationStarted.emit("set")
        result = self._core.set_wallpaper(path)
        self.operationFinished.emit(result.success, result.message)
        if result.success:
            self._refresh_timer.start(500)


# ──────────────────────────────────────────────────────────────
# Контроллер отслеживаемых приложений
# ──────────────────────────────────────────────────────────────

class TrackedAppsController(QObject):
    """Контроллер для реестра приложений."""

    componentsChanged = Signal()
    categoriesChanged = Signal()

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._core: TrackedAppsCore = CoreFactory.tracked_apps_core()
        self._components: list[Component] = []
        self._categories: list[str] = []

    @Property(list, notify=componentsChanged)
    def components(self) -> list:
        """Компоненты для QML (list of dicts)."""
        return [
            {
                "id": c.id,
                "name": c.name,
                "category": c.category,
                "status": c.status.value,
                "statusText": self._status_text(c.status),
                "supportsLiveReload": c.supports_live_reload,
                "description": c.description,
                "icon": c.icon,
                "docsUrl": c.docs_url,
                "configPaths": list(c.config_paths),
            }
            for c in self._components
        ]

    @Property(list, notify=categoriesChanged)
    def categories(self) -> list:
        return self._categories

    def _status_text(self, status: AppStatus) -> str:
        return {
            AppStatus.AVAILABLE: "Установлен",
            AppStatus.NOT_INSTALLED: "Не установлен",
            AppStatus.PARTIAL: "Частично",
        }[status]

    @Slot()
    def refresh(self) -> None:
        self._components = self._core.detect_all()
        self._categories = self._core.get_categories()
        self.componentsChanged.emit()
        self.categoriesChanged.emit()

    @Slot(str, result=list)
    def getComponentsByCategory(self, category: str) -> list:
        comps = self._core.get_components_by_category(category)
        return [
            {
                "id": c.id,
                "name": c.name,
                "status": c.status.value,
                "statusText": self._status_text(c.status),
                "supportsLiveReload": c.supports_live_reload,
                "description": c.description,
                "icon": c.icon,
                "docsUrl": c.docs_url,
            }
            for c in comps
        ]


# ──────────────────────────────────────────────────────────────
# Контроллер настроек
# ──────────────────────────────────────────────────────────────

class SettingsController(QObject):
    """Контроллер настроек приложения."""

    settingsChanged = Signal()
    availableComponentsChanged = Signal()

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._core: SettingsCore = CoreFactory.settings_core()
        self._settings: AppSettings = self._core.get_defaults()
        self._available_components: list[str] = []

    @Property(str, notify=settingsChanged)
    def defaultComponentsMode(self) -> str:
        return self._settings.default_components_mode

    @defaultComponentsMode.setter
    def defaultComponentsMode(self, value: str) -> None:
        if self._settings.default_components_mode != value:
            self._settings = AppSettings(
                **{**self._settings.to_dict(), "default_components_mode": value}
            )
            self.settingsChanged.emit()

    @Property(list, notify=settingsChanged)
    def customComponents(self) -> list:
        return list(self._settings.custom_components)

    @customComponents.setter
    def customComponents(self, value: list) -> None:
        if list(self._settings.custom_components) != value:
            self._settings = AppSettings(
                **{**self._settings.to_dict(), "custom_components": tuple(value)}
            )
            self.settingsChanged.emit()

    @Property(bool, notify=settingsChanged)
    def wallpaperLinkedToProfile(self) -> bool:
        return self._settings.wallpaper_linked_to_profile

    @wallpaperLinkedToProfile.setter
    def wallpaperLinkedToProfile(self, value: bool) -> None:
        if self._settings.wallpaper_linked_to_profile != value:
            self._settings = AppSettings(
                **{**self._settings.to_dict(), "wallpaper_linked_to_profile": value}
            )
            self.settingsChanged.emit()

    @Property(str, notify=settingsChanged)
    def wallpaperDirectory(self) -> str:
        return self._settings.wallpaper_directory

    @wallpaperDirectory.setter
    def wallpaperDirectory(self, value: str) -> None:
        if self._settings.wallpaper_directory != value:
            self._settings = AppSettings(
                **{**self._settings.to_dict(), "wallpaper_directory": value}
            )
            self.settingsChanged.emit()

    @Property(str, notify=settingsChanged)
    def theme(self) -> str:
        return self._settings.theme

    @theme.setter
    def theme(self, value: str) -> None:
        if self._settings.theme != value:
            self._settings = AppSettings(
                **{**self._settings.to_dict(), "theme": value}
            )
            self.settingsChanged.emit()
            self._apply_theme()

    @Property(bool, notify=settingsChanged)
    def showNotInstalledWarning(self) -> bool:
        return self._settings.show_not_installed_warning

    @showNotInstalledWarning.setter
    def showNotInstalledWarning(self, value: bool) -> None:
        if self._settings.show_not_installed_warning != value:
            self._settings = AppSettings(
                **{**self._settings.to_dict(), "show_not_installed_warning": value}
            )
            self.settingsChanged.emit()

    @Property(bool, notify=settingsChanged)
    def autoApplyOnStartup(self) -> bool:
        return self._settings.auto_apply_on_startup

    @autoApplyOnStartup.setter
    def autoApplyOnStartup(self, value: bool) -> None:
        if self._settings.auto_apply_on_startup != value:
            self._settings = AppSettings(
                **{**self._settings.to_dict(), "auto_apply_on_startup": value}
            )
            self.settingsChanged.emit()

    @Property(bool, notify=settingsChanged)
    def minimizeToTray(self) -> bool:
        return self._settings.minimize_to_tray

    @minimizeToTray.setter
    def minimizeToTray(self, value: bool) -> None:
        if self._settings.minimize_to_tray != value:
            self._settings = AppSettings(
                **{**self._settings.to_dict(), "minimize_to_tray": value}
            )
            self.settingsChanged.emit()

    @Property(str, notify=settingsChanged)
    def globalHotkey(self) -> str:
        return self._settings.global_hotkey

    @globalHotkey.setter
    def globalHotkey(self, value: str) -> None:
        if self._settings.global_hotkey != value:
            self._settings = AppSettings(
                **{**self._settings.to_dict(), "global_hotkey": value}
            )
            self.settingsChanged.emit()

    @Property(bool, notify=settingsChanged)
    def confirmBeforeApply(self) -> bool:
        return self._settings.confirm_before_apply

    @confirmBeforeApply.setter
    def confirmBeforeApply(self, value: bool) -> None:
        if self._settings.confirm_before_apply != value:
            self._settings = AppSettings(
                **{**self._settings.to_dict(), "confirm_before_apply": value}
            )
            self.settingsChanged.emit()

    @Property(bool, notify=settingsChanged)
    def createBackupBeforeApply(self) -> bool:
        return self._settings.create_backup_before_apply

    @createBackupBeforeApply.setter
    def createBackupBeforeApply(self, value: bool) -> None:
        if self._settings.create_backup_before_apply != value:
            self._settings = AppSettings(
                **{**self._settings.to_dict(), "create_backup_before_apply": value}
            )
            self.settingsChanged.emit()

    @Property(bool, notify=settingsChanged)
    def notifyOnSuccess(self) -> bool:
        return self._settings.notify_on_success

    @notifyOnSuccess.setter
    def notifyOnSuccess(self, value: bool) -> None:
        if self._settings.notify_on_success != value:
            self._settings = AppSettings(
                **{**self._settings.to_dict(), "notify_on_success": value}
            )
            self.settingsChanged.emit()

    @Property(list, notify=availableComponentsChanged)
    def availableComponents(self) -> list:
        """Список доступных компонентов для кастомного выбора."""
        apps_core = CoreFactory.tracked_apps_core()
        components = apps_core.get_all_components()
        return [c.id for c in components if c.status == AppStatus.AVAILABLE]

    def _apply_theme(self) -> None:
        """Применить тему к приложению (dogfooding)."""
        try:
            from theme_controller import ThemeController
            controller = ThemeController.instance()
            controller.currentTheme = self._settings.theme
        except Exception as e:
            print(f"ThemeController integration failed: {e}", file=sys.stderr)

    @Slot()
    def load(self) -> None:
        self._settings = self._core.load()
        self.settingsChanged.emit()
        self.availableComponentsChanged.emit()

    @Slot()
    def save(self) -> None:
        result = self._core.save(self._settings)
        if result.success:
            self.availableComponentsChanged.emit()

    @Slot()
    def resetToDefaults(self) -> None:
        self._settings = self._core.get_defaults()
        self.settingsChanged.emit()
        self.availableComponentsChanged.emit()


# ──────────────────────────────────────────────────────────────
# Главный контроллер (агрегатор)
# ──────────────────────────────────────────────────────────────

class MainController(QObject):
    """Главный контроллер — точка входа для QML."""

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._profile = ProfileController(self)
        self._wallpaper = WallpaperController(self)
        self._tracked_apps = TrackedAppsController(self)
        self._settings = SettingsController(self)

    @Property(QObject, constant=True)
    def profile(self):
        return self._profile

    @Property(QObject, constant=True)
    def wallpaper(self):
        return self._wallpaper

    @Property(QObject, constant=True)
    def tracked_apps(self):
        return self._tracked_apps

    @Property(QObject, constant=True)
    def settings(self):
        return self._settings

    @Slot()
    def initialize(self) -> None:
        """Инициализация всех контроллеров."""
        self._profile.refresh()
        self._wallpaper.refresh()
        self._tracked_apps.refresh()
        self._settings.load()


# ──────────────────────────────────────────────────────────────
# Регистрация типов для QML
# ──────────────────────────────────────────────────────────────

def register_controllers(engine) -> None:
    """Зарегистрировать контроллеры в QML engine."""
    main_ctrl = MainController()
    
    # Register main controller
    engine.rootContext().setContextProperty("mainController", main_ctrl)
    
    # Register sub-controllers as separate context properties for direct access
    engine.rootContext().setContextProperty("profileController", main_ctrl._profile)
    engine.rootContext().setContextProperty("wallpaperController", main_ctrl._wallpaper)
    engine.rootContext().setContextProperty("trackedAppsController", main_ctrl._tracked_apps)
    engine.rootContext().setContextProperty("settingsController", main_ctrl._settings)
    
    return main_ctrl