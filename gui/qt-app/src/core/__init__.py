"""
Core package exports.
"""

from .protocol import (
    ProfileCore, WallpaperCore, TrackedAppsCore, SettingsCore,
    ProfileInfo, Component, AppStatus, Result, AppSettings,
    CoreFactory
)

from .tracked_apps import (
    TRACKED_APPS,
    TrackedAppDef,
    detect_all_apps,
    detect_app_status,
    build_component,
    PythonTrackedAppsCore
)

from .python_core import (
    PythonProfileCore,
    PythonWallpaperCore,
    PythonTrackedAppsCore,
    PythonSettingsCore,
    PYTHON_FACTORIES,
)

__all__ = [
    # Protocol
    "ProfileCore", "WallpaperCore", "TrackedAppsCore", "SettingsCore",
    "ProfileInfo", "Component", "AppStatus", "Result", "AppSettings",
    "CoreFactory",
    # Tracked apps
    "TRACKED_APPS", "TrackedAppDef", "detect_all_apps",
    "detect_app_status", "build_component", "PythonTrackedAppsCore",
    # Python core
    "PythonProfileCore", "PythonWallpaperCore", "PythonTrackedAppsCore", "PythonSettingsCore",
    "PYTHON_FACTORIES",
]