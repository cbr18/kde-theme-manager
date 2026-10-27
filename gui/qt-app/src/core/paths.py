"""Path and profile-name helpers shared by the Bash core.

The application supports the XDG base directories, but existing installations
created before XDG support keep their data in ``~/.config/theme-profile``.  The
helpers therefore prefer an already existing XDG location and fall back to the
legacy path only when it really exists.  Profile names are validated here as a
single, reusable rule; the same rule is implemented in the bash and Rust cores.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

# A profile name is a single path component.  It must not start with a dot so
# that ``.``/``..`` can never be selected, and the allowed set excludes every
# path separator and shell metacharacter.
_PROFILE_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


def home_dir() -> Path:
    return Path.home()


def config_home() -> Path:
    value = os.environ.get("XDG_CONFIG_HOME", "").strip()
    return Path(value).expanduser() if value else home_dir() / ".config"


def cache_home() -> Path:
    value = os.environ.get("XDG_CACHE_HOME", "").strip()
    return Path(value).expanduser() if value else home_dir() / ".cache"


def data_home() -> Path:
    value = os.environ.get("XDG_DATA_HOME", "").strip()
    return Path(value).expanduser() if value else home_dir() / ".local/share"


def theme_root() -> Path:
    """Theme-profile data root, compatible with pre-XDG installations."""
    preferred = config_home() / "theme-profile"
    legacy = home_dir() / ".config" / "theme-profile"
    if preferred.exists():
        return preferred
    if legacy.exists():
        return legacy
    return preferred


def profiles_dir() -> Path:
    return theme_root() / "profiles"


def active_profile_file() -> Path:
    return theme_root() / "active-profile"


def settings_file() -> Path:
    return theme_root() / "app-preferences.json"


def live_path(relative: str) -> Path:
    """Resolve a profile-relative path against the live XDG environment.

    Profile snapshots keep the historical ``.config/...`` layout.  Live files
    must be resolved through the XDG variables instead.  Paths outside the
    known XDG prefixes (Zen profiles, ``obsidian/vault``) stay relative to the
    home directory, exactly like in the bash layer.
    """
    path = Path(relative)
    if path.is_absolute():
        return path
    parts = path.parts
    if parts[:1] == (".config",):
        return config_home() / Path(*parts[1:])
    if parts[:2] == (".local", "share"):
        return data_home() / Path(*parts[2:])
    if parts[:1] == (".cache",):
        return cache_home() / Path(*parts[1:])
    return home_dir() / path


def is_valid_profile_name(name: object) -> bool:
    if not isinstance(name, str):
        return False
    return bool(_PROFILE_NAME_RE.fullmatch(name))


def validate_profile_name(name: object) -> str:
    """Return a safe profile name or raise :class:`ValueError`."""
    if not isinstance(name, str) or not is_valid_profile_name(name):
        raise ValueError(
            "Invalid profile name: must match [A-Za-z0-9][A-Za-z0-9._-]{0,63}"
        )
    return name


def profile_dir(name: object) -> Path:
    """Absolute profile directory, guaranteed to stay under ``profiles/``."""
    safe = validate_profile_name(name)
    root = profiles_dir().resolve()
    candidate = (root / safe).resolve()
    if candidate.parent != root:
        raise ValueError("Invalid profile name: path escapes profiles directory")
    return candidate
