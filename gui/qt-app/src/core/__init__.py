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
    BashTrackedAppsCore
)

from .bash_core import (
    BashProfileCore,
    BashWallpaperCore,
    BashTrackedAppsCore,
    BashSettingsCore,
    BASH_FACTORIES,
)

__all__ = [
    # Protocol
    "ProfileCore", "WallpaperCore", "TrackedAppsCore", "SettingsCore",
    "ProfileInfo", "Component", "AppStatus", "Result", "AppSettings",
    "CoreFactory",
    # Tracked apps
    "TRACKED_APPS", "TrackedAppDef", "detect_all_apps",
    "detect_app_status", "build_component", "BashTrackedAppsCore",
    # Bash core
    "BashProfileCore", "BashWallpaperCore", "BashTrackedAppsCore", "BashSettingsCore",
    "BASH_FACTORIES",
]