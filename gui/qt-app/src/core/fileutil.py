"""Small filesystem helpers with predictable permissions.

Config files frequently contain private application data and are often created
by tools with ``0600``.  A plain ``Path.write_text`` uses the process umask
(usually ``0644``), so re-saving such a file silently widens its permissions.
``atomic_write_bytes`` writes a temporary file in the same directory, copies the
mode of the destination when it exists, and uses ``0600`` for new files.
"""

from __future__ import annotations

import os
import stat
import tempfile
from pathlib import Path


def _current_mode(path: Path) -> int | None:
    try:
        return stat.S_IMODE(path.stat().st_mode)
    except OSError:
        return None


def atomic_write_bytes(path: Path, data: bytes, mode: int | None = None) -> None:
    """Atomically replace ``path`` with ``data``.

    ``mode`` overrides the destination mode; otherwise an existing file keeps
    its mode and a new file is created with ``0600``.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    target_mode = mode if mode is not None else _current_mode(path)
    if target_mode is None:
        target_mode = 0o600

    fd, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".ktm-tmp", dir=str(path.parent)
    )
    tmp = Path(temporary)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(tmp, target_mode)
        os.replace(tmp, path)
    except BaseException:
        try:
            tmp.unlink()
        except OSError:
            pass
        raise


def atomic_write_text(path: Path, text: str, mode: int | None = None) -> None:
    atomic_write_bytes(path, text.encode("utf-8"), mode=mode)


def copy_preserving_mode(source: Path, destination: Path) -> None:
    """Copy a file's bytes and mode without following the destination mode."""
    source = Path(source)
    mode = _current_mode(source)
    atomic_write_bytes(Path(destination), source.read_bytes(), mode=mode)
