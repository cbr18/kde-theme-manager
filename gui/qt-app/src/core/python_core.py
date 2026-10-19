"""
Python Core Implementation — обёртки над существующими bash-скриптами.

Использует subprocess для вызова theme-profile, wallpaper-picker/next/prev.
Парсит выход, конфиги, кэш.
"""

import json
import os
import re
import subprocess
import time
import shutil
from pathlib import Path
from typing import Optional
from urllib.parse import unquote, urlsplit

from .protocol import (
    ProfileCore, WallpaperCore, TrackedAppsCore, SettingsCore,
    ProfileInfo, Result, AppSettings, Component, AppStatus, CoreFactory
)
from .tracked_apps import PythonTrackedAppsCore, detect_all_apps, TRACKED_APPS


# ──────────────────────────────────────────────────────────────
# Profile Core
# ──────────────────────────────────────────────────────────────

class PythonProfileCore(ProfileCore):
    """Обёртка над theme-profile bash скриптом."""

    def __init__(self, theme_profile_bin: str = "theme-profile"):
        # Resolve binary path: check PATH, then fallback to ~/.local/bin/
        resolved = shutil.which(theme_profile_bin)
        if resolved:
            self.bin = resolved
        else:
            fallback = Path.home() / ".local/bin" / theme_profile_bin
            self.bin = str(fallback) if fallback.exists() else theme_profile_bin
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

# Extensions and ordering *must* match files/bin/wallpaper-{picker,next,prev}:
# the cached index is a position in that list, not a file name.
WALLPAPER_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp", ".bmp")


class PythonWallpaperCore(WallpaperCore):
    """Обёртка над wallpaper-* bash скриптами."""

    def __init__(self):
        self._wallpaper_dir: Optional[Path] = None
        self.cache_index = Path.home() / ".cache/wallpaper_index"

    def _resolve_wallpaper_dir(self) -> Path:
        """Resolve wallpaper directory from AppSettings (falls back to default)."""
        if self._wallpaper_dir is None:
            try:
                settings_core = CoreFactory.settings_core()
                settings = settings_core.load()
                self._wallpaper_dir = Path(settings.wallpaper_directory).expanduser()
            except Exception:
                self._wallpaper_dir = Path.home() / "Изображения/Wallpaper"
        return self._wallpaper_dir

    @property
    def wallpaper_dir(self) -> Path:
        return self._resolve_wallpaper_dir()

    # Plasma stores the desktop wallpaper per screen in the appletsrc; it is the
    # authoritative answer to "what is on the desktop right now".
    PLASMA_CONFIG = Path.home() / ".config/plasma-org.kde.plasma.desktop-appletsrc"

    _IMAGE_GROUP_RE = re.compile(
        r"^\[Containments\]\[\d+\]\[Wallpaper\]\[org\.kde\.image\]\[General\]$"
    )

    def _plasma_wallpaper(self) -> Optional[str]:
        """Путь обоев, которые Plasma показывает сейчас (None — не прочитать)."""
        try:
            text = self.PLASMA_CONFIG.read_text(errors="replace")
        except OSError:
            return None

        url: Optional[str] = None
        in_image_group = False
        for line in text.splitlines():
            if line.startswith("["):
                in_image_group = self._IMAGE_GROUP_RE.match(line) is not None
                continue
            if in_image_group and line.startswith("Image="):
                url = line[len("Image="):].strip()

        if not url:
            return None
        if url.startswith("file://"):
            path = unquote(urlsplit(url).path)
        else:
            path = unquote(url)
        return path or None

    def _run(
        self, args: list[str], timeout: int = 15, env: Optional[dict[str, str]] = None
    ) -> Result:
        environ = None
        if env:
            environ = {**os.environ, **env}
        try:
            proc = subprocess.run(
                args, capture_output=True, text=True, timeout=timeout, env=environ
            )
            return Result(
                proc.returncode == 0,
                proc.stdout.strip() or proc.stderr.strip()
            )
        except subprocess.TimeoutExpired:
            return Result.err(f"Timeout after {timeout}s")
        except Exception as e:
            return Result.err(str(e))

    def _script_env(self) -> dict[str, str]:
        """Force the scripts to use the directory the app is showing.

        The scripts default to ~/Изображения/Wallpaper, while the app reads
        `wallpaper_directory` from the settings file; if the two ever differ
        the index written by a script would point into another list.
        """
        return {"WALLPAPER_DIR": str(self.wallpaper_dir)}

    def pick(self) -> Optional[str]:
        """Открыть wofi пикер — ждём завершения, возвращаем выбранный файл."""
        # wallpaper-picker записывает индекс в cache, затем применяет
        res = self._run(["wallpaper-picker"], timeout=60, env=self._script_env())
        if res.success:
            return self.current()
        return None

    def next(self) -> Result:
        return self._run(["wallpaper-next"], env=self._script_env())

    def prev(self) -> Result:
        return self._run(["wallpaper-prev"], env=self._script_env())

    def current(self) -> Optional[str]:
        """Текущие обои: реальное значение Plasma, иначе кэшированный индекс.

        The cached index only resolves correctly while the file list is
        unchanged, and it silently pointed at another wallpaper whenever the
        enumeration order changed. Plasma knows the actual answer.
        """
        real = self._plasma_wallpaper()
        if real:
            return real

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
        """Файлы обоев в том же порядке, что и в bash-скриптах.

        The cached index is a *position* in this list, so the ordering rules
        have to match files/bin/wallpaper-{picker,next,prev} exactly:
        symlinks are followed (Path.is_file(), like find -L), the same
        extensions are accepted, and the sort is by the path string, i.e.
        code-point order — identical to `LC_ALL=C sort` over the UTF-8 bytes,
        but *not* to a locale-aware sort.
        """
        try:
            entries = list(self.wallpaper_dir.iterdir())
        except OSError:
            return []

        files = [
            f for f in entries
            if f.is_file() and f.suffix.lower() in WALLPAPER_EXTENSIONS
        ]
        files.sort(key=str)
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
    "PYTHON_FACTORIES",
]

#: Ядро, выбираемое CoreFactory._build() — см. CoreFactory.set_backend()
PYTHON_FACTORIES = {
    "profile": PythonProfileCore,
    "wallpaper": PythonWallpaperCore,
    "tracked_apps": PythonTrackedAppsCore,
    "settings": PythonSettingsCore,
}
