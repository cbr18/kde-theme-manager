"""
Python Core Implementation — обёртки над существующими bash-скриптами.

Использует subprocess для вызова theme-profile, wallpaper-picker/next/prev.
Парсит выход, конфиги, кэш.
"""

import json
import subprocess
import time
from pathlib import Path
from typing import Optional

from .protocol import (
    ProfileCore, WallpaperCore, TrackedAppsCore, SettingsCore,
    ProfileInfo, Result, AppSettings, Component, AppStatus
)
from .tracked_apps import PythonTrackedAppsCore, detect_all_apps, TRACKED_APPS


# ──────────────────────────────────────────────────────────────
# Profile Core
# ──────────────────────────────────────────────────────────────

class PythonProfileCore(ProfileCore):
    """Обёртка над theme-profile bash скриптом."""

    def __init__(self, theme_profile_bin: str = "theme-profile"):
        self.bin = theme_profile_bin
        self._profiles_dir = Path.home() / ".config/theme-profile/profiles"
        self._active_file = Path.home() / ".config/theme-profile/active-profile"

    def _run(self, args: list[str], timeout: int = 30) -> Result:
        try:
            proc = subprocess.run(
                [self.bin, *args],
                capture_output=True, text=True, timeout=timeout
            )
            return Result(
                proc.returncode == 0,
                proc.stdout.strip() or proc.stderr.strip()
            )
        except subprocess.TimeoutExpired:
            return Result.err(f"Timeout after {timeout}s")
        except Exception as e:
            return Result.err(str(e))

    def list_profiles(self) -> list[ProfileInfo]:
        res = self._run(["list"])
        if not res.success:
            return []
        names = [n.strip() for n in res.message.split("\n") if n.strip()]
        active = self.get_active_profile()
        profiles = []
        for name in names:
            info = self._get_profile_info(name, name == active)
            profiles.append(info)
        return profiles

    def get_active_profile(self) -> str:
        try:
            return self._active_file.read_text().strip()
        except Exception:
            return ""

    def _get_profile_info(self, name: str, is_active: bool) -> ProfileInfo:
        """Получить метаданные профиля."""
        profile_dir = self._profiles_dir / name
        created_at = ""
        description = ""
        components = ()
        wallpaper_path = ""

        # Читаем манифест если есть
        manifest = profile_dir / "manifest.txt"
        if manifest.exists():
            try:
                content = manifest.read_text()
                for line in content.split("\n"):
                    if line.startswith("timestamp="):
                        created_at = line.split("=", 1)[1]
                    elif line.startswith("["):
                        break
            except Exception:
                pass

        # Определяем компоненты по наличию директорий в профиле
        comps = []
        for app_def in TRACKED_APPS:
            for rel_path in app_def.config_paths:
                if (profile_dir / rel_path).exists():
                    comps.append(app_def.id)
                    break

        return ProfileInfo(
            name=name,
            is_active=is_active,
            components=tuple(comps),
            created_at=created_at,
            description=description,
            wallpaper_path=wallpaper_path,
        )

    def apply(self, profile: str, components: Optional[list[str]] = None) -> Result:
        args = ["apply", profile]
        if components:
            args.append(f"--components={','.join(components)}")
        return self._run(args, timeout=60)

    def save(self, name: str, components: Optional[list[str]] = None) -> Result:
        args = ["save", name]
        if components:
            args.append(f"--components={','.join(components)}")
        return self._run(args, timeout=60)

    def delete(self, name: str) -> Result:
        # Нет в bash — делаем вручную
        profile_dir = self._profiles_dir / name
        if not profile_dir.exists():
            return Result.err(f"Profile not found: {name}")
        try:
            import shutil
            shutil.rmtree(profile_dir)
            return Result.ok(f"Deleted profile: {name}")
        except Exception as e:
            return Result.err(str(e))

    def diff(self, a: str, b: str) -> str:
        res = self._run(["diff", a, b], timeout=30)
        return res.message if res.success else f"Error: {res.message}"

    def get_profile_components(self, profile: str) -> list[str]:
        info = self._get_profile_info(profile, False)
        return list(info.components)


# ──────────────────────────────────────────────────────────────
# Wallpaper Core
# ──────────────────────────────────────────────────────────────

class PythonWallpaperCore(WallpaperCore):
    """Обёртка над wallpaper-* bash скриптами."""

    def __init__(self):
        self.wallpaper_dir = Path.home() / "Изображения/Wallpaper"
        self.cache_index = Path.home() / ".cache/wallpaper_index"

    def _run(self, args: list[str], timeout: int = 15) -> Result:
        try:
            proc = subprocess.run(
                args, capture_output=True, text=True, timeout=timeout
            )
            return Result(
                proc.returncode == 0,
                proc.stdout.strip() or proc.stderr.strip()
            )
        except subprocess.TimeoutExpired:
            return Result.err(f"Timeout after {timeout}s")
        except Exception as e:
            return Result.err(str(e))

    def pick(self) -> Optional[str]:
        """Открыть wofi пикер — ждём завершения, возвращаем выбранный файл."""
        # wallpaper-picker записывает индекс в cache, затем применяет
        res = self._run(["wallpaper-picker"], timeout=60)
        if res.success:
            return self.current()
        return None

    def next(self) -> Result:
        return self._run(["wallpaper-next"])

    def prev(self) -> Result:
        return self._run(["wallpaper-prev"])

    def current(self) -> Optional[str]:
        try:
            idx_text = self.cache_index.read_text().strip()
            if not idx_text.isdigit():
                return None
            idx = int(idx_text)
            files = self.list_wallpapers()
            if 0 <= idx < len(files):
                return files[idx]
        except Exception:
            pass
        return None

    def list_wallpapers(self) -> list[str]:
        if not self.wallpaper_dir.exists():
            return []
        exts = (".jpg", ".jpeg", ".png", ".webp", ".bmp")
        files = sorted(
            f for f in self.wallpaper_dir.iterdir()
            if f.is_file() and f.suffix.lower() in exts
        )
        return [str(f) for f in files]

    def set_wallpaper(self, path: str) -> Result:
        return self._run(["plasma-apply-wallpaperimage", path])


# ──────────────────────────────────────────────────────────────
# Settings Core
# ──────────────────────────────────────────────────────────────

SETTINGS_FILE = Path.home() / ".config/theme-profile/app-preferences.json"


class PythonSettingsCore(SettingsCore):
    """Настройки приложения в JSON."""

    def load(self) -> AppSettings:
        if SETTINGS_FILE.exists():
            try:
                data = json.loads(SETTINGS_FILE.read_text())
                return AppSettings.from_dict(data)
            except Exception:
                pass
        return self.get_defaults()

    def save(self, settings: AppSettings) -> Result:
        try:
            SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
            SETTINGS_FILE.write_text(json.dumps(settings.to_dict(), indent=2))
            return Result.ok("Settings saved")
        except Exception as e:
            return Result.err(str(e))

    def get_defaults(self) -> AppSettings:
        return AppSettings()


# ──────────────────────────────────────────────────────────────
# Экспорт
# ──────────────────────────────────────────────────────────────

__all__ = [
    "PythonProfileCore",
    "PythonWallpaperCore",
    "PythonTrackedAppsCore",
    "PythonSettingsCore",
]