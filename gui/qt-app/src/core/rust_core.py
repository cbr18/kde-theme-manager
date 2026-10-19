"""
Rust core bindings — ctypes FFI over ``libkde_theme_core.so``.

The Rust crate (``core/rust_core``) exposes a C ABI: functions returning
JSON strings (``*mut c_char``, freed with ``kde_theme_core_free_string``) and
``c_int`` status codes, with the message of the last failure available through
``kde_theme_core_get_error``.

The four classes at the bottom implement the same protocol ABCs as
``python_core``, so controllers/QML cannot tell which core they are talking to
(``CoreFactory`` picks one).

Contract notes (both cores have to agree, otherwise switching backends changes
behaviour):

* Mutating profile operations delegate to the ``theme-profile`` bash script —
  it owns the component→config-path mapping and the backups. The Rust side
  reads profiles natively.
* Wallpaper enumeration uses the directory from the app settings; it is pushed
  into the library with ``kde_theme_core_wallpaper_set_dir`` before every call,
  mirroring ``PythonWallpaperCore._script_env``.
"""

from __future__ import annotations

import ctypes
import json
import os
from pathlib import Path
from typing import Callable, Optional

from .protocol import (
    AppSettings,
    AppStatus,
    Component,
    CoreFactory,
    ProfileCore,
    ProfileInfo,
    Result,
    SettingsCore,
    TrackedAppsCore,
    WallpaperCore,
)

LIBRARY_NAME = "libkde_theme_core.so"

#: Environment override for the library location (handy for testing).
LIBRARY_ENV_VAR = "KTM_RUST_CORE_LIB"

_c_string = ctypes.c_char_p


class RustCoreError(RuntimeError):
    """A call into the Rust library failed."""


class RustCoreUnavailable(RustCoreError):
    """The Rust library could not be found or loaded."""


# ──────────────────────────────────────────────────────────────
# Library lookup
# ──────────────────────────────────────────────────────────────

def library_candidates() -> list[Path]:
    """Where to look for the shared library, most specific first."""
    here = Path(__file__).resolve().parent          # …/src/core
    app_dir = here.parents[1]                       # …/kde-theme-manager

    candidates: list[Path] = []
    override = os.environ.get(LIBRARY_ENV_VAR)
    if override:
        candidates.append(Path(override).expanduser())

    candidates += [
        # Built from the source tree (cargo build --release).
        here / "rust_core" / "target" / "release" / LIBRARY_NAME,
        # Shipped next to the installed application.
        app_dir / "lib" / LIBRARY_NAME,
        app_dir / LIBRARY_NAME,
        # Dropped straight into the package (packaging/tests).
        here / LIBRARY_NAME,
        # System-wide installs.
        Path("/usr/local/lib") / LIBRARY_NAME,
        Path("/usr/lib") / LIBRARY_NAME,
    ]
    return candidates


def find_library() -> Optional[Path]:
    """First existing candidate, or None."""
    for candidate in library_candidates():
        if candidate.is_file():
            return candidate
    return None


# ──────────────────────────────────────────────────────────────
# FFI surface
# ──────────────────────────────────────────────────────────────

# name → (argument types, kind). `kind` is what the function returns:
#   "json"   — a JSON-encoded payload (null pointer means failure)
#   "text"   — a plain UTF-8 string (null pointer means failure)
#   "status" — c_int, 0 = success
_JSON = "json"
_TEXT = "text"
_STATUS = "status"

_FUNCTIONS: dict[str, tuple[list, str]] = {
    "kde_theme_core_profile_list": ([], _JSON),
    "kde_theme_core_profile_get_active": ([], _TEXT),
    "kde_theme_core_profile_diff": ([_c_string, _c_string], _TEXT),
    "kde_theme_core_profile_get_components": ([_c_string], _JSON),
    "kde_theme_core_profile_apply": ([_c_string, _c_string], _STATUS),
    "kde_theme_core_profile_save": ([_c_string, _c_string], _STATUS),
    "kde_theme_core_profile_delete": ([_c_string], _STATUS),
    "kde_theme_core_wallpaper_pick": ([], _TEXT),
    "kde_theme_core_wallpaper_next": ([], _STATUS),
    "kde_theme_core_wallpaper_prev": ([], _STATUS),
    "kde_theme_core_wallpaper_current": ([], _TEXT),
    "kde_theme_core_wallpaper_list": ([], _JSON),
    "kde_theme_core_wallpaper_set": ([_c_string], _STATUS),
    "kde_theme_core_wallpaper_set_dir": ([_c_string], _STATUS),
    "kde_theme_core_apps_detect_all": ([], _JSON),
    "kde_theme_core_apps_get_all": ([], _JSON),
    "kde_theme_core_apps_get_categories": ([], _JSON),
    "kde_theme_core_apps_get_by_category": ([_c_string], _JSON),
    "kde_theme_core_apps_refresh": ([], _JSON),
    "kde_theme_core_settings_load": ([], _JSON),
    "kde_theme_core_settings_get_defaults": ([], _JSON),
    "kde_theme_core_settings_save": ([_c_string], _STATUS),
}

_library: Optional[ctypes.CDLL] = None
_library_path: Optional[Path] = None


def load_library(path: Optional[Path] = None, reload: bool = False) -> ctypes.CDLL:
    """Load (and cache) the Rust library, declaring every signature.

    Signatures matter: without ``argtypes`` ctypes truncates pointers to C int
    and the library crashes the interpreter on the first free().
    """
    global _library, _library_path
    if _library is not None and not reload and path is None:
        return _library

    target = Path(path) if path is not None else find_library()
    if target is None:
        raise RustCoreUnavailable(
            f"{LIBRARY_NAME} not found (build it with "
            f"`cargo build --release` in src/core/rust_core, or set {LIBRARY_ENV_VAR}); "
            f"looked in: {', '.join(str(c) for c in library_candidates())}"
        )

    try:
        library = ctypes.CDLL(str(target))
    except OSError as exc:
        raise RustCoreUnavailable(f"Cannot load {target}: {exc}") from exc

    library.kde_theme_core_init.restype = ctypes.c_int
    library.kde_theme_core_init.argtypes = []
    library.kde_theme_core_get_error.restype = ctypes.c_void_p
    library.kde_theme_core_get_error.argtypes = []
    library.kde_theme_core_free_string.restype = None
    library.kde_theme_core_free_string.argtypes = [ctypes.c_void_p]

    for name, (argtypes, kind) in _FUNCTIONS.items():
        function = getattr(library, name, None)
        if function is None:
            raise RustCoreUnavailable(f"{target} does not export {name}")
        function.argtypes = argtypes
        function.restype = ctypes.c_int if kind == _STATUS else ctypes.c_void_p

    library.kde_theme_core_init()
    _library = library
    _library_path = target
    return library


def library_path() -> Optional[Path]:
    """Path of the loaded library (loads it if necessary)."""
    if _library is None:
        try:
            load_library()
        except RustCoreUnavailable:
            return None
    return _library_path


def is_available() -> bool:
    """True when the Rust core can be used."""
    try:
        load_library()
        return True
    except RustCoreUnavailable:
        return False


def _decode(pointer: int) -> Optional[str]:
    """Decode a returned C string and free it (None stays None)."""
    if not pointer:
        return None
    try:
        return ctypes.string_at(pointer).decode("utf-8")
    finally:
        _lib().kde_theme_core_free_string(pointer)


def _lib() -> ctypes.CDLL:
    """The loaded library, loading it on first use.

    A core may be constructed without anyone having probed for the library
    (tests, or a caller that did not go through CoreFactory.rust_available()),
    so every call goes through here instead of assuming warm module state.
    """
    if _library is None:
        return load_library()
    return _library


def _last_error() -> str:
    error = _decode(_lib().kde_theme_core_get_error())
    return error or "unknown error"


def _call_json(name: str, *args: str) -> object:
    """Call a JSON-returning function; raise RustCoreError on NULL."""
    library = _lib()
    encoded = [a.encode("utf-8") if isinstance(a, str) else a for a in args]
    pointer = getattr(library, name)(*encoded)
    if not pointer:
        raise RustCoreError(f"{name}: {_last_error()}")

    raw = _decode(pointer)
    if raw is None:
        raise RustCoreError(f"{name}: {_last_error()}")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RustCoreError(f"{name}: invalid JSON from the core: {exc}") from exc


def _call_text(name: str, *args: str) -> str:
    """Call a string-returning function; raise RustCoreError on NULL."""
    library = _lib()
    encoded = [a.encode("utf-8") if isinstance(a, str) else a for a in args]
    pointer = getattr(library, name)(*encoded)
    if not pointer:
        raise RustCoreError(_last_error())
    return _decode(pointer) or ""


def _call_status(name: str, *args: str) -> Result:
    """Call a status-returning function; c_int 0 means success."""
    library = _lib()
    encoded = [a.encode("utf-8") if isinstance(a, str) else a for a in args]
    status = getattr(library, name)(*encoded)
    if status == 0:
        return Result.ok()
    return Result.err(_last_error())


def _json_argument(components: Optional[list[str]]) -> Optional[str]:
    """`--components` list → JSON string (None when unset)."""
    if not components:
        return None
    return json.dumps(list(components))


# ──────────────────────────────────────────────────────────────
# Mapping helpers
# ──────────────────────────────────────────────────────────────

def _profile_info(data: dict) -> ProfileInfo:
    return ProfileInfo(
        name=data.get("name", ""),
        is_active=bool(data.get("is_active", False)),
        components=tuple(data.get("components", ())),
        created_at=data.get("created_at", ""),
        description=data.get("description", ""),
        wallpaper_path=data.get("wallpaper_path", ""),
    )


def _component(data: dict) -> Component:
    try:
        status = AppStatus(data.get("status", "partial"))
    except ValueError:
        status = AppStatus.PARTIAL
    return Component(
        id=data.get("id", ""),
        name=data.get("name", ""),
        category=data.get("category", ""),
        config_paths=tuple(data.get("config_paths", ())),
        status=status,
        supports_live_reload=bool(data.get("supports_live_reload", False)),
        description=data.get("description", ""),
        icon=data.get("icon", ""),
        docs_url=data.get("docs_url", ""),
    )


# ──────────────────────────────────────────────────────────────
# Core implementations
# ──────────────────────────────────────────────────────────────

class RustProfileCore(ProfileCore):
    """ProfileCore backed by the Rust library."""

    def list_profiles(self) -> list[ProfileInfo]:
        try:
            data = _call_json("kde_theme_core_profile_list") or []
        except RustCoreError:
            return []
        return [_profile_info(item) for item in data]

    def get_active_profile(self) -> str:
        try:
            return _call_text("kde_theme_core_profile_get_active")
        except RustCoreError:
            return ""

    def apply(self, profile: str, components: Optional[list[str]] = None) -> Result:
        return _call_status(
            "kde_theme_core_profile_apply", profile, _json_argument(components)
        )

    def save(self, name: str, components: Optional[list[str]] = None) -> Result:
        return _call_status(
            "kde_theme_core_profile_save", name, _json_argument(components)
        )

    def delete(self, name: str) -> Result:
        return _call_status("kde_theme_core_profile_delete", name)

    def diff(self, a: str, b: str) -> str:
        """Различия профилей. Как в Python-ядре, текст ошибки идёт с префиксом."""
        try:
            return _call_text("kde_theme_core_profile_diff", a, b)
        except RustCoreError as exc:
            return f"Error: {exc}"

    def get_profile_components(self, profile: str) -> list[str]:
        try:
            return list(_call_json("kde_theme_core_profile_get_components", profile) or [])
        except RustCoreError:
            return []


class RustWallpaperCore(WallpaperCore):
    """WallpaperCore backed by the Rust library."""

    def __init__(self) -> None:
        self._synced_dir: Optional[str] = None

    def _sync_dir(self) -> None:
        """Push the configured wallpaper directory into the library.

        The library defaults to ~/Изображения/Wallpaper; the app may point
        somewhere else, and the cached index is a position in the list the app
        displays — a mismatch would make next/prev jump to a different file.
        """
        try:
            directory = CoreFactory.settings_core().load().wallpaper_directory
        except Exception:
            directory = "~/Изображения/Wallpaper"
        if directory != self._synced_dir:
            _call_status("kde_theme_core_wallpaper_set_dir", directory)
            self._synced_dir = directory

    def pick(self) -> Optional[str]:
        self._sync_dir()
        try:
            return _call_text("kde_theme_core_wallpaper_pick")
        except RustCoreError:
            return None

    def next(self) -> Result:
        self._sync_dir()
        return _call_status("kde_theme_core_wallpaper_next")

    def prev(self) -> Result:
        self._sync_dir()
        return _call_status("kde_theme_core_wallpaper_prev")

    def current(self) -> Optional[str]:
        self._sync_dir()
        try:
            return _call_text("kde_theme_core_wallpaper_current")
        except RustCoreError:
            return None

    def list_wallpapers(self) -> list[str]:
        self._sync_dir()
        try:
            return list(_call_json("kde_theme_core_wallpaper_list") or [])
        except RustCoreError:
            return []

    def set_wallpaper(self, path: str) -> Result:
        self._sync_dir()
        return _call_status("kde_theme_core_wallpaper_set", path)


class RustTrackedAppsCore(TrackedAppsCore):
    """TrackedAppsCore backed by the Rust library."""

    def _components(self, function: str, *args: str) -> list[Component]:
        try:
            data = _call_json(function, *args) or []
        except RustCoreError:
            return []
        return [_component(item) for item in data]

    def detect_all(self) -> list[Component]:
        return self._components("kde_theme_core_apps_detect_all")

    def get_categories(self) -> list[str]:
        try:
            return list(_call_json("kde_theme_core_apps_get_categories") or [])
        except RustCoreError:
            return []

    def get_components_by_category(self, category: str) -> list[Component]:
        return self._components("kde_theme_core_apps_get_by_category", category)

    def get_all_components(self) -> list[Component]:
        return self._components("kde_theme_core_apps_get_all")

    def refresh(self) -> list[Component]:
        return self._components("kde_theme_core_apps_refresh")


class RustSettingsCore(SettingsCore):
    """SettingsCore backed by the Rust library."""

    def load(self) -> AppSettings:
        try:
            data = _call_json("kde_theme_core_settings_load")
        except RustCoreError:
            data = None
        if not data:
            return self.get_defaults()
        return AppSettings.from_dict(data)

    def save(self, settings: AppSettings) -> Result:
        return _call_status(
            "kde_theme_core_settings_save", json.dumps(settings.to_dict())
        )

    def get_defaults(self) -> AppSettings:
        try:
            data = _call_json("kde_theme_core_settings_get_defaults")
        except RustCoreError:
            data = None
        return AppSettings.from_dict(data) if data else AppSettings()


# ──────────────────────────────────────────────────────────────
# Factory registration
# ──────────────────────────────────────────────────────────────

#: python backend name → rust backend equivalent
RUST_FACTORIES: dict[str, Callable[[], object]] = {
    "profile": RustProfileCore,
    "wallpaper": RustWallpaperCore,
    "tracked_apps": RustTrackedAppsCore,
    "settings": RustSettingsCore,
}
