"""
Core Protocol (Abstract Base Classes) — КОНТРАКТ между UI и Core.

Этот модуль НЕ МЕНЯЕТСЯ при замене PythonCore на RustCore.
UI и Controllers зависят только от этих абстракций.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from pathlib import Path
import os
import sys


class AppStatus(Enum):
    """Статус доступности приложения/компонента."""
    AVAILABLE = "available"          # Установлен, конфиги найдены
    NOT_INSTALLED = "not_installed"  # Не установлен
    PARTIAL = "partial"              # Установлен, но часть конфигов отсутствует


@dataclass(frozen=True, slots=True)
class Component:
    """Один отслеживаемый компонент (приложение или группа настроек)."""
    id: str
    name: str
    category: str
    config_paths: tuple[str, ...]
    status: AppStatus
    supports_live_reload: bool = False
    description: str = ""
    # Доп. метаданные для UI
    icon: str = ""           # имя иконки (Kirigami/Theme)
    docs_url: str = ""       # ссылка на документацию


@dataclass(frozen=True, slots=True)
class ProfileInfo:
    """Информация о профиле."""
    name: str
    is_active: bool
    components: tuple[str, ...] = field(default_factory=tuple)  # какие компоненты в профиле
    created_at: str = ""
    description: str = ""
    # Метаданные
    wallpaper_path: str = ""


@dataclass(frozen=True, slots=True)
class Result:
    """Результат операции."""
    success: bool
    message: str
    data: Optional[dict] = None

    @classmethod
    def ok(cls, message: str = "", data: Optional[dict] = None) -> "Result":
        return cls(True, message, data)

    @classmethod
    def err(cls, message: str, data: Optional[dict] = None) -> "Result":
        return cls(False, message, data)


# ──────────────────────────────────────────────────────────────
# Протоколы (Abstract Base Classes)
# ──────────────────────────────────────────────────────────────

class ProfileCore(ABC):
    """Управление профилями тем."""

    @abstractmethod
    def list_profiles(self) -> list[ProfileInfo]:
        """Список всех профилей."""

    @abstractmethod
    def get_active_profile(self) -> str:
        """Имя активного профиля."""

    @abstractmethod
    def apply(self, profile: str, components: Optional[list[str]] = None) -> Result:
        """
        Применить профиль.
        components=None → всё (по умолчанию).
        components=['kwin', 'gtk3'] → только указанные.
        """

    @abstractmethod
    def save(self, name: str, components: Optional[list[str]] = None) -> Result:
        """Сохранить текущее состояние как профиль."""

    @abstractmethod
    def delete(self, name: str) -> Result:
        """Удалить профиль."""

    @abstractmethod
    def diff(self, a: str, b: str) -> str:
        """Сравнить два профиля (raw diff)."""

    @abstractmethod
    def get_profile_components(self, profile: str) -> list[str]:
        """Какие компоненты сохранены в профиле."""


class WallpaperCore(ABC):
    """Управление обоями."""

    @abstractmethod
    def pick(self) -> Optional[str]:
        """Открыть пикер, вернуть путь к выбранным обоям."""

    @abstractmethod
    def next(self) -> Result:
        """Следующие обои."""

    @abstractmethod
    def prev(self) -> Result:
        """Предыдущие обои."""

    @abstractmethod
    def current(self) -> Optional[str]:
        """Текущие обои (путь)."""

    @abstractmethod
    def list_wallpapers(self) -> list[str]:
        """Список всех обоев в директории."""

    @abstractmethod
    def set_wallpaper(self, path: str) -> Result:
        """Установить конкретные обои."""


class TrackedAppsCore(ABC):
    """Реестр отслеживаемых приложений."""

    @abstractmethod
    def detect_all(self) -> list[Component]:
        """Детект всех приложений, возврат списка Component с актуальным статусом."""

    @abstractmethod
    def get_categories(self) -> list[str]:
        """Список уникальных категорий."""

    @abstractmethod
    def get_components_by_category(self, category: str) -> list[Component]:
        """Компоненты по категории."""

    @abstractmethod
    def get_all_components(self) -> list[Component]:
        """Все компоненты (кэшированный или свежий)."""

    @abstractmethod
    def refresh(self) -> list[Component]:
        """Принудительный рефреш детекта."""


class SettingsCore(ABC):
    """Настройки самого приложения (user preferences)."""

    @abstractmethod
    def load(self) -> "AppSettings":
        """Загрузить настройки."""

    @abstractmethod
    def save(self, settings: "AppSettings") -> Result:
        """Сохранить настройки."""

    @abstractmethod
    def get_defaults(self) -> "AppSettings":
        """Дефолтные настройки."""


@dataclass(frozen=True, slots=True)
class AppSettings:
    """Настройки приложения (user preferences)."""
    # Режим применения профиля
    default_components_mode: str = "all"        # "all" | "custom"
    custom_components: tuple[str, ...] = field(default_factory=tuple)

    # Обои
    wallpaper_linked_to_profile: bool = False
    wallpaper_directory: str = "~/Изображения/Wallpaper"

    # UI
    theme: str = "system"                       # "system" | "glass" | "paper" | "dark" | "light"
    show_not_installed_warning: bool = True
    auto_apply_on_startup: bool = False
    minimize_to_tray: bool = False
    global_hotkey: str = ""                     # e.g. "Meta+T"

    # Поведение
    confirm_before_apply: bool = True
    create_backup_before_apply: bool = True
    notify_on_success: bool = True

    # Какое ядро использовать при старте: "python" | "rust"
    # (переопределяется флагом --core и переменной окружения KTM_CORE)
    core_backend: str = "python"

    def to_dict(self) -> dict:
        return {
            "default_components_mode": self.default_components_mode,
            "custom_components": list(self.custom_components),
            "wallpaper_linked_to_profile": self.wallpaper_linked_to_profile,
            "wallpaper_directory": self.wallpaper_directory,
            "theme": self.theme,
            "show_not_installed_warning": self.show_not_installed_warning,
            "auto_apply_on_startup": self.auto_apply_on_startup,
            "minimize_to_tray": self.minimize_to_tray,
            "global_hotkey": self.global_hotkey,
            "confirm_before_apply": self.confirm_before_apply,
            "create_backup_before_apply": self.create_backup_before_apply,
            "notify_on_success": self.notify_on_success,
            "core_backend": self.core_backend,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AppSettings":
        return cls(
            default_components_mode=data.get("default_components_mode", "all"),
            custom_components=tuple(data.get("custom_components", [])),
            wallpaper_linked_to_profile=data.get("wallpaper_linked_to_profile", False),
            wallpaper_directory=data.get("wallpaper_directory", "~/Изображения/Wallpaper"),
            theme=data.get("theme", "system"),
            show_not_installed_warning=data.get("show_not_installed_warning", True),
            auto_apply_on_startup=data.get("auto_apply_on_startup", False),
            minimize_to_tray=data.get("minimize_to_tray", False),
            global_hotkey=data.get("global_hotkey", ""),
            confirm_before_apply=data.get("confirm_before_apply", True),
            create_backup_before_apply=data.get("create_backup_before_apply", True),
            notify_on_success=data.get("notify_on_success", True),
            core_backend=data.get("core_backend", "python"),
        )


# ──────────────────────────────────────────────────────────────
# Фабрика для получения реализации Core
# ──────────────────────────────────────────────────────────────

class CoreFactory:
    """
    Фабрика для получения реализаций Core протоколов.
    Позволяет подменять реализацию (PythonCore → RustCore) в одной точке.

    Ядро выбирается флагом ``--core`` / переменной ``KTM_CORE`` / настройкой
    ``core_backend``; см. :meth:`set_backend`.
    """

    #: Доступные бэкенды. "auto" — rust, если библиотека есть, иначе python.
    BACKENDS = ("python", "rust", "auto")
    #: Переменная окружения, переопределяющая настройку (но не флаг --core).
    ENV_VAR = "KTM_CORE"

    _profile_core: Optional[ProfileCore] = None
    _wallpaper_core: Optional[WallpaperCore] = None
    _tracked_apps_core: Optional[TrackedAppsCore] = None
    _settings_core: Optional[SettingsCore] = None

    _backend: str = "python"          # фактически используемый

    # ── Выбор ядра ─────────────────────────────────────────────

    @classmethod
    def normalize_backend(cls, backend: str) -> str:
        """Проверить и нормализовать имя бэкенда."""
        name = (backend or "").strip().lower()
        if name not in cls.BACKENDS:
            raise ValueError(
                f"Unknown core backend {backend!r}; expected one of "
                f"{', '.join(cls.BACKENDS)}"
            )
        return name

    @classmethod
    def set_backend(cls, backend: str, strict: bool = True) -> str:
        """Выбрать ядро и сбросить кэш реализаций.

        ``strict=False`` — «мягкий» режим: если Rust-библиотека недоступна,
        используется Python-ядро (с предупреждением в stderr). Возвращает
        фактически используемый бэкенд.
        """
        name = cls.normalize_backend(backend)

        if name == "auto":
            name = "rust" if cls.rust_available() else "python"

        if name == "rust" and not cls.rust_available():
            if strict:
                from .rust_core import RustCoreUnavailable, library_candidates

                searched = ", ".join(str(p) for p in library_candidates())
                raise RustCoreUnavailable(
                    "Rust core requested but libkde_theme_core.so is not usable. "
                    f"Build it with `cargo build --release` in src/core/rust_core. "
                    f"Searched: {searched}"
                )
            print(
                "Warning: Rust core unavailable, falling back to the Python core",
                file=sys.stderr,
            )
            name = "python"

        cls._backend = name
        cls.reset()
        return cls._backend

    @classmethod
    def set_backend_from_env(cls, strict: bool = True, default: str = "python") -> str:
        """Выбрать ядро из ``KTM_CORE`` (если задана), иначе ``default``."""
        requested = os.environ.get(cls.ENV_VAR, "").strip() or default
        return cls.set_backend(requested, strict=strict)

    @classmethod
    def backend(cls) -> str:
        """Фактически используемое ядро."""
        return cls._backend

    @classmethod
    def backend_label(cls) -> str:
        """Человекочитаемое имя ядра для UI."""
        if cls._backend != "rust":
            return "Python"
        from .rust_core import library_path

        path = library_path()
        return f"Rust ({path.name})" if path else "Rust"

    @classmethod
    def rust_available(cls) -> bool:
        """Есть ли собранная Rust-библиотека."""
        try:
            from .rust_core import is_available
        except Exception:
            return False
        return is_available()

    @classmethod
    def _build(cls, kind: str):
        """Создать реализацию нужного ядра."""
        if cls._backend == "rust":
            from .rust_core import RUST_FACTORIES

            return RUST_FACTORIES[kind]()
        from .python_core import PYTHON_FACTORIES

        return PYTHON_FACTORIES[kind]()

    # ── Ручная подмена (тесты) ─────────────────────────────────

    @classmethod
    def set_profile_core(cls, core: ProfileCore) -> None:
        cls._profile_core = core

    @classmethod
    def set_wallpaper_core(cls, core: WallpaperCore) -> None:
        cls._wallpaper_core = core

    @classmethod
    def set_tracked_apps_core(cls, core: TrackedAppsCore) -> None:
        cls._tracked_apps_core = core

    @classmethod
    def set_settings_core(cls, core: SettingsCore) -> None:
        cls._settings_core = core

    @classmethod
    def profile_core(cls) -> ProfileCore:
        if cls._profile_core is None:
            cls._profile_core = cls._build("profile")
        return cls._profile_core

    @classmethod
    def wallpaper_core(cls) -> WallpaperCore:
        if cls._wallpaper_core is None:
            cls._wallpaper_core = cls._build("wallpaper")
        return cls._wallpaper_core

    @classmethod
    def tracked_apps_core(cls) -> TrackedAppsCore:
        if cls._tracked_apps_core is None:
            cls._tracked_apps_core = cls._build("tracked_apps")
        return cls._tracked_apps_core

    @classmethod
    def settings_core(cls) -> SettingsCore:
        if cls._settings_core is None:
            cls._settings_core = cls._build("settings")
        return cls._settings_core

    @classmethod
    def reset(cls) -> None:
        """Сброс для тестов или переинициализации."""
        cls._profile_core = None
        cls._wallpaper_core = None
        cls._tracked_apps_core = None
        cls._settings_core = None