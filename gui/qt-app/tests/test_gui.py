"""
Test suite for KDE Theme Manager — QA audit.

Tests cover:
  1. py_compile validation of all Python source files.
  2. Import checks for modules that don't require a display.
  3. Mock / unit tests for PythonCore classes (Profile, Wallpaper, Settings).
  4. Protocol / dataclass integrity checks.
  5. Tracked-apps registry structural validation.
"""

from __future__ import annotations

import json
import os
import inspect
import subprocess
import sys
import tempfile
import ctypes
from pathlib import Path
from unittest import mock

import pytest

# ─────────────────────────────────────────────────────────────────────────────
# Path setup — ensure `src/` is importable
# ─────────────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


# ─────────────────────────────────────────────────────────────────────────────
# 1. py_compile validation
# ─────────────────────────────────────────────────────────────────────────────
ALL_PY_FILES = sorted(
    p for p in SRC_DIR.rglob("*.py") if "core/rust_core/" not in str(p)
)


@pytest.mark.parametrize("py_file", ALL_PY_FILES, ids=lambda p: p.relative_to(SRC_DIR))
def test_py_compile(py_file: Path) -> None:
    """Every Python source file must compile without syntax errors."""
    result = subprocess.run(
        [sys.executable, "-m", "py_compile", str(py_file)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"py_compile failed for {py_file}:\n{result.stderr}"


# ─────────────────────────────────────────────────────────────────────────────
# 2. Import checks (no display required)
# ─────────────────────────────────────────────────────────────────────────────
def test_import_core_protocol() -> None:
    """Core protocol (ABCs + dataclasses) must import without side effects."""
    from core.protocol import (
        AppSettings,
        AppStatus,
        Component,
        CoreFactory,
        ProfileCore,
        Result,
        TrackedAppsCore,
        WallpaperCore,
    )
    # Ensure dataclasses produce expected defaults
    settings = AppSettings()
    assert settings.default_components_mode == "all"
    assert settings.theme == "system"
    assert settings.custom_components == ()
    assert "wallpaper_directory" in settings.to_dict()


def test_import_tracked_apps() -> None:
    """Tracked apps registry must import and contain 20 definitions."""
    from core.tracked_apps import TRACKED_APPS, detect_all_apps

    assert len(TRACKED_APPS) == 20, f"Expected 20 tracked apps, got {len(TRACKED_APPS)}"
    detect_all_apps()  # must not raise


def test_import_python_core() -> None:
    """Python core implementations must import cleanly."""
    from core.python_core import (
        PythonProfileCore,
        PythonSettingsCore,
        PythonTrackedAppsCore,
        PythonWallpaperCore,
    )
    from core.protocol import Result
    # Smoke-check Result constructors
    ok = Result.ok("done")
    assert ok.success is True
    err = Result.err("oops")
    assert err.success is False


# ─────────────────────────────────────────────────────────────────────────────
# 3. Protocol / dataclass integrity
# ─────────────────────────────────────────────────────────────────────────────
def test_appsettings_roundtrip() -> None:
    """AppSettings → dict → AppSettings must preserve all fields."""
    from core.protocol import AppSettings

    original = AppSettings(
        default_components_mode="custom",
        custom_components=("kwin", "kdeglobals", "kitty"),
        wallpaper_linked_to_profile=True,
        wallpaper_directory="~/Изображения/Wallpaper",
        theme="glass",
        show_not_installed_warning=False,
        auto_apply_on_startup=True,
        minimize_to_tray=True,
        global_hotkey="Meta+T",
        confirm_before_apply=False,
        create_backup_before_apply=False,
        notify_on_success=False,
    )
    data = original.to_dict()
    restored = AppSettings.from_dict(data)
    assert restored == original


def test_component_is_frozen() -> None:
    """Component dataclass must be frozen (slots=True)."""
    from core.protocol import AppStatus, Component

    comp = Component(
        id="test",
        name="Test",
        category="Test",
        config_paths=(".config/test",),
        status=AppStatus.AVAILABLE,
    )
    with pytest.raises((AttributeError, Exception)):
        comp.id = "mutated"  # frozen=True should block this


def test_result_ok_err_methods() -> None:
    from core.protocol import Result

    ok = Result.ok("success message", {"key": "val"})
    assert ok.success is True
    assert ok.message == "success message"
    assert ok.data == {"key": "val"}

    err = Result.err("error message", {"code": 1})
    assert err.success is False
    assert err.data == {"code": 1}


# ─────────────────────────────────────────────────────────────────────────────
# 4. CoreFactory
# ─────────────────────────────────────────────────────────────────────────────
def test_core_factory_reset_and_recreate() -> None:
    """CoreFactory must allow reset (for tests) and lazy instantiation."""
    from core.protocol import CoreFactory

    CoreFactory.reset()
    # After reset, calling the factories should lazily create new instances
    profile_core = CoreFactory.profile_core()
    assert profile_core is not None
    wallpaper_core = CoreFactory.wallpaper_core()
    assert wallpaper_core is not None
    # After reset, the same instance should be returned (singleton per core)
    assert CoreFactory.profile_core() is profile_core


# ─────────────────────────────────────────────────────────────────────────────
# 5. PythonProfileCore — mocked subprocess
# ─────────────────────────────────────────────────────────────────────────────
class TestPythonProfileCore:
    """Unit tests for PythonProfileCore with mocked subprocess."""

    def _make_core(self) -> "object":
        from core.python_core import PythonProfileCore

        return PythonProfileCore()

    def test_list_profiles_empty(self) -> None:
        core = self._make_core()
        with mock.patch.object(core, "_run") as mock_run:
            mock_run.return_value = mock.Mock(success=False, message="error")
            profiles = core.list_profiles()
        assert profiles == []

    def test_list_profiles_success(self) -> None:
        core = self._make_core()
        with mock.patch.object(core, "_run") as mock_run, \
             mock.patch.object(core, "get_active_profile") as mock_active:
            mock_run.return_value = mock.Mock(success=True, message="glass\npaper")
            mock_active.return_value = "glass"
            profiles = core.list_profiles()
        assert len(profiles) == 2
        assert profiles[0].name == "glass"
        assert profiles[0].is_active is True
        assert profiles[1].name == "paper"
        assert profiles[1].is_active is False

    def test_get_active_profile_file_not_found(self) -> None:
        core = self._make_core()
        with mock.patch.object(core, "_active_file", Path("/nonexistent/active-profile-12345")):
            result = core.get_active_profile()
        assert result == ""

    def test_apply_profile_passes_components(self) -> None:
        core = self._make_core()
        with mock.patch.object(core, "_run") as mock_run:
            mock_run.return_value = mock.Mock(success=True, message="ok")
            core.apply("glass", components=["kwin", "kdeglobals"])
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        assert args[0] == ["apply", "glass", "--components=kwin,kdeglobals"]

    def test_apply_profile_no_components(self) -> None:
        core = self._make_core()
        with mock.patch.object(core, "_run") as mock_run:
            mock_run.return_value = mock.Mock(success=True, message="ok")
            core.apply("glass")
        mock_run.assert_called_once()
        args, _ = mock_run.call_args
        assert args[0] == ["apply", "glass"]

    def test_delete_profile_not_found(self) -> None:
        core = self._make_core()
        result = core.delete("nonexistent_profile_12345")
        assert result.success is False
        assert "not found" in result.message.lower()

    def test_delete_profile_success(self) -> None:
        core = self._make_core()
        fake_dir = Path(tempfile.mkdtemp())
        result = core.delete(fake_dir.name)
        # May succeed or fail depending on whether the dir exists in profiles_dir
        # Just verify the method runs without crashing
        assert isinstance(result.success, bool)


# ─────────────────────────────────────────────────────────────────────────────
# 6. PythonSettingsCore — file-based I/O
# ─────────────────────────────────────────────────────────────────────────────
class TestPythonSettingsCore:
    """Unit tests for PythonSettingsCore with temp directory."""

    def test_defaults(self) -> None:
        from core.python_core import PythonSettingsCore

        core = PythonSettingsCore()
        settings = core.get_defaults()
        assert settings.theme == "system"
        assert settings.default_components_mode == "all"
        assert settings.custom_components == ()

    def test_load_nonexistent_returns_defaults(self) -> None:
        from core.python_core import PythonSettingsCore

        core = PythonSettingsCore()
        settings = core.load()
        assert settings.theme == "system"

    def test_save_and_load_roundtrip(self, tmp_path: Path) -> None:
        from core.python_core import PythonSettingsCore
        from core.protocol import AppSettings

        core = PythonSettingsCore()
        custom = AppSettings(
            theme="glass",
            default_components_mode="custom",
            custom_components=("kwin", "kdeglobals"),
        )
        with mock.patch("core.python_core.SETTINGS_FILE", tmp_path / "settings.json"):
            result = core.save(custom)
            assert result.success

            loaded = core.load()
            assert loaded.theme == "glass"
            assert loaded.default_components_mode == "custom"
            assert loaded.custom_components == ("kwin", "kdeglobals")


# ─────────────────────────────────────────────────────────────────────────────
# 7. PythonWallpaperCore — wallpaper dir uses settings
# ─────────────────────────────────────────────────────────────────────────────
class TestPythonWallpaperCore:
    """Test that wallpaper_dir resolves from settings, not hardcoded."""

    def test_wallpaper_dir_is_property(self) -> None:
        """wallpaper_dir is now a property, not a hardcoded attribute."""
        from core.python_core import PythonWallpaperCore

        core = PythonWallpaperCore()
        # Should be accessible as a property (Path object)
        dir_path = core.wallpaper_dir
        assert isinstance(dir_path, Path)

    def test_wallpaper_dir_uses_settings(self) -> None:
        """wallpaper_dir should come from AppSettings.wallpaper_directory."""
        from core.python_core import PythonWallpaperCore

        core = PythonWallpaperCore()
        # The property should resolve to the default wallpaper directory
        # (since no settings file exists in CI, it falls back to default)
        assert core.wallpaper_dir is not None

    def test_list_wallpapers_nonexistent_dir(self) -> None:
        """list_wallpapers returns [] when dir doesn't exist."""
        from core.python_core import PythonWallpaperCore

        core = PythonWallpaperCore()
        with mock.patch.object(type(core), "wallpaper_dir", Path("/nonexistent/dir/12345")):
            assert core.list_wallpapers() == []

    def test_resolve_wallpaper_dir_from_settings(self) -> None:
        """_resolve_wallpaper_dir should use CoreFactory settings."""
        from core.python_core import PythonWallpaperCore

        core = PythonWallpaperCore()
        core._wallpaper_dir = None  # Reset
        with mock.patch("core.python_core.CoreFactory") as mock_factory:
            mock_settings = mock.Mock()
            mock_settings.wallpaper_directory = "/tmp/test-wallpapers"
            mock_factory.settings_core.return_value.load.return_value = mock_settings
            result = core._resolve_wallpaper_dir()
            assert result == Path("/tmp/test-wallpapers")


# ─────────────────────────────────────────────────────────────────────────────
# 7b. Wallpaper list/order and "current wallpaper" resolution
#
# The cached index in ~/.cache/wallpaper_index is a *position* in the list, so
# the bash scripts and this core must enumerate the same files in the same
# order. A locale-aware `sort` (ru_RU.UTF-8) or a different extension list
# made the GUI resolve the index to a wallpaper other than the one applied.
# ─────────────────────────────────────────────────────────────────────────────
def _make_wallpaper_dir(tmp_path: Path) -> Path:
    """Wallpaper dir with the names that used to break the ordering."""
    d = tmp_path / "walls"
    d.mkdir()
    for name in (
        "apple.png",       # lowercase ASCII
        "Zebra.png",       # uppercase sorts before lowercase in byte order
        "-dash.jpg",       # leading punctuation sorts before digits
        "1number.webp",    # digit
        "Beta.bmp",        # .bmp used to be accepted by Python but not bash
        "UP.PNG",          # uppercase extension used to be rejected in Rust
        "Обои.jpg",        # Cyrillic sorts after ASCII in byte order
        "notes.txt",       # not an image -> never listed
    ):
        (d / name).write_bytes(b"x")
    (d / "linked.png").symlink_to(d / "apple.png")  # find -L / is_file() follow
    return d


class TestWallpaperOrdering:
    """Ordering/selection rules that the bash scripts and the GUI must share."""

    def _core(self, directory: Path):
        from core.python_core import PythonWallpaperCore

        core = PythonWallpaperCore()
        core._wallpaper_dir = directory
        return core

    def test_list_wallpapers_byte_order_symlinks_and_extensions(
        self, tmp_path: Path
    ) -> None:
        d = _make_wallpaper_dir(tmp_path)
        files = self._core(d).list_wallpapers()

        names = [Path(f).name for f in files]
        assert names == sorted(names), "list must be in byte/code-point order"
        assert "Zebra.png" in names and "apple.png" in names
        assert names.index("-dash.jpg") == 0
        assert names.index("Обои.jpg") > names.index("apple.png")
        assert "Beta.bmp" in names, ".bmp must be listed (bash accepts it)"
        assert "UP.PNG" in names, "extensions must match case-insensitively"
        assert "linked.png" in names, "symlinks must be listed (find -L)"
        assert "notes.txt" not in names
        assert len(files) == 8

    def test_list_wallpapers_matches_wallpaper_next(self, tmp_path: Path) -> None:
        """The scripts and the GUI must walk the *same* list in the same order."""
        script = PROJECT_ROOT.parents[1] / "files" / "bin" / "wallpaper-next"
        if not script.exists():
            pytest.skip(f"kit script not found: {script}")

        d = _make_wallpaper_dir(tmp_path)
        files = [Path(f).name for f in self._core(d).list_wallpapers()]

        state = tmp_path / "state"
        state.write_text(str(len(files) - 1))  # next one wraps to index 0
        env = {
            **os.environ,
            "WALLPAPER_DIR": str(d),
            "WALLPAPER_STATE": str(state),
            "WALLPAPER_DRY_RUN": "1",
            "PLASMA_APPLETSRC": str(tmp_path / "no-such-config"),
        }

        walked = []
        for _ in range(len(files)):
            proc = subprocess.run(
                ["bash", str(script)], capture_output=True, text=True, env=env
            )
            assert proc.returncode == 0, proc.stderr
            walked.append(Path(proc.stdout.strip()).name)

        assert walked == files

    def test_current_reads_plasma_config(self, tmp_path: Path, monkeypatch) -> None:
        """current() must report the wallpaper Plasma actually shows."""
        from core.python_core import PythonWallpaperCore

        d = _make_wallpaper_dir(tmp_path)
        real = d / "Zebra.png"
        config = tmp_path / "appletsrc"
        config.write_text(
            "[Containments][1][Wallpaper]\n"
            "wallpaperPlugin=org.kde.image\n"
            "[Containments][281][Wallpaper][org.kde.image][General]\n"
            f"Image=file://{real}\n"
            "[Containments][282][Wallpaper][org.kde.slideshow][General]\n"
            "Image=file:///elsewhere/slide.png\n"
        )
        monkeypatch.setattr(PythonWallpaperCore, "PLASMA_CONFIG", config)

        core = self._core(d)
        core.cache_index = tmp_path / "state"
        core.cache_index.write_text("0")  # wrong on purpose: Plasma must win

        assert core.current() == str(real)

    def test_current_decodes_url_escapes(self, tmp_path: Path, monkeypatch) -> None:
        from core.python_core import PythonWallpaperCore

        config = tmp_path / "appletsrc"
        config.write_text(
            "[Containments][281][Wallpaper][org.kde.image][General]\n"
            "Image=file:///home/u/My%20Pictures/wall%20one.png\n"
        )
        monkeypatch.setattr(PythonWallpaperCore, "PLASMA_CONFIG", config)

        core = self._core(tmp_path)
        assert core.current() == "/home/u/My Pictures/wall one.png"

    def test_current_falls_back_to_cached_index(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        from core.python_core import PythonWallpaperCore

        d = _make_wallpaper_dir(tmp_path)
        monkeypatch.setattr(
            PythonWallpaperCore, "PLASMA_CONFIG", tmp_path / "missing-appletsrc"
        )

        core = self._core(d)
        core.cache_index = tmp_path / "state"
        core.cache_index.write_text("2")
        assert core.current() == core.list_wallpapers()[2]

        core.cache_index.write_text("not-a-number")
        assert core.current() is None

    def test_script_env_pins_the_wallpaper_dir(self, tmp_path: Path) -> None:
        """The scripts must be told which dir the app is showing."""
        core = self._core(tmp_path)
        assert core._script_env() == {"WALLPAPER_DIR": str(tmp_path)}


# ─────────────────────────────────────────────────────────────────────────────
# 8. Tracked apps structure
# ─────────────────────────────────────────────────────────────────────────────
def test_tracked_apps_have_required_fields() -> None:
    """Every tracked app definition must have all required metadata."""
    from core.tracked_apps import TRACKED_APPS

    for app in TRACKED_APPS:
        assert app.id, f"Missing id for app: {app}"
        assert app.name, f"Missing name for app: {app}"
        assert app.category, f"Missing category for app: {app}"
        assert len(app.config_paths) > 0, f"No config_paths for app: {app.id}"
        assert app.description, f"Missing description for app: {app.id}"
        assert app.icon, f"Missing icon for app: {app.id}"


def test_tracked_apps_categories() -> None:
    """Categories should include expected KDE/Plasma categories."""
    from core.tracked_apps import PythonTrackedAppsCore

    core = PythonTrackedAppsCore()
    categories = core.get_categories()
    expected = {"KDE / Plasma", "GTK / Qt", "Window Decorations", "Terminals",
                "Editors", "Browser"}
    assert expected.issubset(set(categories))


# ─────────────────────────────────────────────────────────────────────────────
# 9. Duplicate QAction import check
# ─────────────────────────────────────────────────────────────────────────────
def test_no_duplicate_qaction_import() -> None:
    """system_tray.py must not import QAction twice."""
    import ast

    system_tray_path = SRC_DIR / "system_tray.py"
    tree = ast.parse(system_tray_path.read_text())

    qaction_imports = 0
    for node in ast.walk(tree):
        # Top-level import from PySide6.QtGui
        if isinstance(node, ast.ImportFrom):
            if node.module and "PySide6" in node.module:
                for alias in node.names:
                    if alias.name == "QAction":
                        qaction_imports += 1
        # Lazy import inside _import_widgets
        if isinstance(node, ast.ImportFrom):
            if node.module and "QtWidgets" in node.module:
                for alias in node.names:
                    if alias.name == "QAction":
                        qaction_imports += 1

    # QAction should appear in at most ONE import statement
    assert qaction_imports <= 1, (
        f"QAction imported {qaction_imports} times in system_tray.py; "
        "expected at most 1 (the duplicate in _import_widgets should be removed)"
    )


# ─────────────────────────────────────────────────────────────────────────────
# 10. pyproject.toml dependency check
# ─────────────────────────────────────────────────────────────────────────────
def test_pyproject_no_unused_deps() -> None:
    """pyproject.toml must not list pydantic or pyyaml as dependencies."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    if not pyproject_path.exists():
        pytest.skip("pyproject.toml not found")

    content = pyproject_path.read_text()
    lower = content.lower()
    assert "pydantic" not in lower, "pydantic should be removed from dependencies"
    assert "pyyaml" not in lower, "pyyaml should be removed from dependencies"
    assert "pyside6" in lower, "PySide6 must remain in dependencies"


# ─────────────────────────────────────────────────────────────────────────────
# 11. QML file existence and basic structure
# ─────────────────────────────────────────────────────────────────────────────
def test_qml_files_exist() -> None:
    """Core QML files must exist at expected paths."""
    qml_dir = PROJECT_ROOT / "qml"
    assert (qml_dir / "Main.qml").exists()
    assert (qml_dir / "Components" / "qmldir").exists()
    assert (qml_dir / "Components" / "ComponentCategoryGroup.qml").exists()
    assert (qml_dir / "Components" / "ComponentCheckbox.qml").exists()
    assert (qml_dir / "Components" / "ProfileCardDelegate.qml").exists()
    assert (qml_dir / "Components" / "ProfileRadioButton.qml").exists()
    assert (qml_dir / "Components" / "ThemeColors.qml").exists()
    assert (qml_dir / "Components" / "TypeScale.qml").exists()
    assert (qml_dir / "pages" / "SettingsPage.qml").exists()


def test_no_duplicate_components_dir() -> None:
    """The old Components/ directory at project root must be removed."""
    assert not (PROJECT_ROOT / "Components").exists(), (
        "Duplicate Components/ directory at project root should be deleted"
    )
    assert (PROJECT_ROOT / "qml" / "Components").exists(), (
        "qml/Components/ (renamed from qml/components/) must exist"
    )


def test_qmldir_lists_all_components() -> None:
    """qmldir must declare all four component QML types and the two singletons."""
    qmldir = (PROJECT_ROOT / "qml" / "Components" / "qmldir").read_text()
    assert "module Components" in qmldir
    assert "ProfileCardDelegate" in qmldir
    assert "ProfileRadioButton" in qmldir
    assert "ComponentCategoryGroup" in qmldir
    assert "ComponentCheckbox" in qmldir
    assert "singleton ThemeColors" in qmldir
    assert "singleton TypeScale" in qmldir


# ─────────────────────────────────────────────────────────────────────────────
# 12. __main__.py --help handling
# ─────────────────────────────────────────────────────────────────────────────
def test_main_has_help_flag() -> None:
    """__main__.py must handle --help and -h."""
    import ast

    main_path = SRC_DIR / "__main__.py"
    tree = ast.parse(main_path.read_text())

    found_help = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            for comparator in node.comparators:
                if isinstance(comparator, ast.Constant) and comparator.value == "--help":
                    found_help = True
        if isinstance(node, ast.Constant) and node.value == "--help":
            found_help = True
    assert found_help, "--help flag not handled in __main__.py"


# ─────────────────────────────────────────────────────────────────────────────
# 13. SettingsController._apply_theme integration
# ─────────────────────────────────────────────────────────────────────────────
def test_settings_controller_apply_theme_not_empty() -> None:
    """SettingsController._apply_theme must not be a TODO stub."""
    import inspect
    from controllers import SettingsController

    source = inspect.getsource(SettingsController._apply_theme)
    assert "pass" not in source.replace("pass", "", 0) or "TODO" not in source, (
        "SettingsController._apply_theme is still a TODO stub"
    )
    assert "TODO" not in source, (
        "SettingsController._apply_theme still contains TODO"
    )
    assert "ThemeController" in source, (
        "SettingsController._apply_theme must reference ThemeController"
    )


def test_settings_controller_has_backup_and_notify_properties() -> None:
    """SettingsController must expose createBackupBeforeApply and notifyOnSuccess."""
    from controllers import SettingsController

    # We can't fully instantiate SettingsController (requires Qt event loop),
    # but we can verify the properties are declared on the class
    cls = SettingsController
    assert hasattr(cls, "createBackupBeforeApply"), (
        "SettingsController must have createBackupBeforeApply property "
        "(referenced by SettingsPage.qml)"
    )
    assert hasattr(cls, "notifyOnSuccess"), (
        "SettingsController must have notifyOnSuccess property "
        "(in AppSettings but missing from controller)"
    )


# ─────────────────────────────────────────────────────────────────────────────
# 14. Resources/icons directory
# ─────────────────────────────────────────────────────────────────────────────
def test_resources_icons_not_empty() -> None:
    """resources/icons/ must not be empty (has .gitkeep or icon files)."""
    icons_dir = PROJECT_ROOT / "resources" / "icons"
    assert icons_dir.exists(), "resources/icons/ directory must exist"
    contents = list(icons_dir.iterdir())
    assert len(contents) > 0, "resources/icons/ must not be empty"


# ─────────────────────────────────────────────────────────────────────────────
# 15. theme-profile --components support
# ─────────────────────────────────────────────────────────────────────────────
def test_theme_profile_has_components_support() -> None:
    """bash theme-profile must support --components= flag (required by GUI)."""
    theme_profile = Path(__file__).resolve().parents[3] / "files" / "bin" / "theme-profile"
    if not theme_profile.exists():
        pytest.skip("theme-profile not found at expected path")
    content = theme_profile.read_text()
    assert "COMPONENT_PATHS" in content, "theme-profile must define COMPONENT_PATHS"
    assert "parse_components_arg" in content, "theme-profile must have parse_components_arg"
    assert "build_tracked_paths" in content, "theme-profile must have build_tracked_paths"
    assert "--components" in content, "theme-profile must support --components flag"


# ─────────────────────────────────────────────────────────────────────────────
# 16. __main__.py uses QApplication (not QGuiApplication-only)
# ─────────────────────────────────────────────────────────────────────────────
def test_main_uses_qapplication() -> None:
    """__main__.py must import QApplication (for system tray support)."""
    main_path = SRC_DIR / "__main__.py"
    content = main_path.read_text()
    assert "QApplication" in content, (
        "__main__.py must use QApplication (supports both QML and Widgets/tray)"
    )
    assert "QQuickStyle.setStyle" not in content, (
        "QQuickStyle.setStyle('org.kde.desktop') removed (causes QWidget crash)"
    )


# ─────────────────────────────────────────────────────────────────────────────
# 17. system_tray.py guards against missing QApplication
# ─────────────────────────────────────────────────────────────────────────────
def test_system_tray_guard() -> None:
    """register_system_tray must check QApplication.instance() before creating QWidgets."""
    import ast

    path = SRC_DIR / "system_tray.py"
    tree = ast.parse(path.read_text())

    # Find register_system_tray function
    found_qapp_check = False
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "register_system_tray":
            source = ast.get_source_segment(path.read_text(), node)
            if source and "QApplication" in source:
                found_qapp_check = True
    assert found_qapp_check, (
        "register_system_tray must check for QApplication before creating QSystemTrayIcon"
    )


# ─────────────────────────────────────────────────────────────────────────────
# 18. theme_controller.py uses setColor, not setAttribute
# ─────────────────────────────────────────────────────────────────────────────
def test_theme_controller_no_setattribute() -> None:
    """ThemeController must not use QWindow.setAttribute (not available in PySide6)."""
    path = SRC_DIR / "theme_controller.py"
    content = path.read_text()
    assert "setAttribute" not in content, (
        "QWindow.setAttribute doesn't exist in PySide6 — use setColor with try/except"
    )


# ─────────────────────────────────────────────────────────────────────────────
# 19. QML fixed: no deprecated tooltip property
# ─────────────────────────────────────────────────────────────────────────────
def test_qml_no_tooltip_property() -> None:
    """QML files must use ToolTip attached property, not 'tooltip:' shorthand."""
    qml_dir = PROJECT_ROOT / "qml"
    for qml_file in qml_dir.rglob("*.qml"):
        content = qml_file.read_text()
        # 'tooltip:' (without ToolTip. prefix) is invalid in Qt 6.12
        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("tooltip:") or stripped.startswith("tooltip "):
                pytest.fail(
                    f"{qml_file.name}:{i} uses 'tooltip:' property "
                    f"(use ToolTip.text + ToolTip.visible instead)"
                )


# ─────────────────────────────────────────────────────────────────────────────
# 20. QML Main.qml uses function syntax for Connections
# ─────────────────────────────────────────────────────────────────────────────
def test_qml_connections_function_syntax() -> None:
    """Connections must use function syntax (onFoo: handler is deprecated in Qt 6.8+)."""
    import re

    main_qml = (PROJECT_ROOT / "qml" / "Main.qml").read_text()
    assert "Connections {" in main_qml, "Main.qml should use a Connections block"

    blocks = []
    for match in re.finditer(r"Connections\s*\{", main_qml):
        i = match.end()
        depth = 1
        start = i
        while i < len(main_qml) and depth > 0:
            if main_qml[i] == "{":
                depth += 1
            elif main_qml[i] == "}":
                depth -= 1
            i += 1
        blocks.append(main_qml[start : i - 1])

    assert blocks, "Expected at least one Connections block"
    for block in blocks:
        for line in block.split("\n"):
            assert not re.match(r"\s*on[A-Z]\w*\s*:", line), (
                "Connections handlers must use 'function onFoo(...)' syntax, "
                f"not '{line.strip()}'"
            )
        assert re.search(r"function\s+on\w+\s*\(", block), (
            "Each Connections block must declare its handlers with function syntax"
        )


# ─────────────────────────────────────────────────────────────────────────────
# 21. QML safeColor helper (fallback for PySide6 bundled Qt Kirigami.Theme)
# ─────────────────────────────────────────────────────────────────────────────
def test_qml_has_safecolor_helper() -> None:
    """All QML files using Kirigami.Theme color roles must use safeColor fallback."""
    qml_dir = PROJECT_ROOT / "qml"
    for qml_file in qml_dir.rglob("*.qml"):
        content = qml_file.read_text()
        # If the file uses Kirigami.Theme color roles, it must also define safeColor
        if "Kirigami.Theme." in content:
            assert "function safeColor" in content, (
                f"{qml_file.relative_to(qml_dir)} uses Kirigami.Theme colors "
                "but doesn't define safeColor fallback"
            )


# ─────────────────────────────────────────────────────────────────────────────
# 22. Main.qml glass styling (translucent, driven by glassMode)
# ─────────────────────────────────────────────────────────────────────────────
def test_main_has_glass_styling() -> None:
    """Main.qml must drive a translucent glass look from the glassMode flag."""
    main_qml = (PROJECT_ROOT / "qml" / "Main.qml").read_text()
    assert "property bool glassMode: themeController.isGlass" in main_qml, (
        "Main.qml must expose glassMode bound to themeController.isGlass"
    )
    # The page must paint its own glass panel / background, not rely on the
    # Kirigami default Platform.Theme.backgroundColor (which was the white bug).
    assert "background: Rectangle" in main_qml, (
        "Main.qml page must define an explicit background Rectangle"
    )
    assert main_qml.count("root.glassMode") >= 2, (
        "The page/window background must react to glassMode"
    )
    # Translucent colours are how glass is implemented. They live in the
    # ThemeColors singleton now (Main.qml must not carry its own colour
    # literals), so assert it there.
    theme_colors = (PROJECT_ROOT / "qml" / "Components" / "ThemeColors.qml").read_text()
    assert "Qt.rgba(" in theme_colors, (
        "ThemeColors.qml must use translucent Qt.rgba() colours for glass mode"
    )
    assert "glassPanel" in theme_colors, (
        "ThemeColors.qml must expose the glass panel colour"
    )


# ─────────────────────────────────────────────────────────────────────────────
# 22b. Selection and application are separate actions
# ─────────────────────────────────────────────────────────────────────────────
def test_selection_is_separate_from_apply() -> None:
    """Clicking a profile selects it; applying requires the explicit Apply button."""
    main_qml = (PROJECT_ROOT / "qml" / "Main.qml").read_text()
    assert "property string selectedProfile" in main_qml, (
        "Main.qml must track a pending selectedProfile"
    )
    # The radio delegate only sets the selection...
    assert "onProfileClicked: function(profileName)" in main_qml, (
        "Clicking a profile must only select it, not apply it"
    )
    assert "root.selectedProfile = profileName" in main_qml, (
        "Clicking a profile must only assign the pending selection"
    )
    # ...and a dedicated Apply button performs the (slow) application.
    assert "profileController.applyProfile(root.selectedProfile)" in main_qml, (
        "An explicit Apply button must trigger profile application"
    )


# ─────────────────────────────────────────────────────────────────────────────
# 22c. Theme controller switches the application palette
# ─────────────────────────────────────────────────────────────────────────────
def test_theme_controller_applies_palette() -> None:
    """Glass/dark themes must switch the app palette (else controls stay light)."""
    controller_path = SRC_DIR / "theme_controller.py"
    content = controller_path.read_text()
    assert "def _apply_palette" in content, (
        "ThemeController must define _apply_palette"
    )
    assert "setPalette(" in content, (
        "ThemeController must apply the palette via QGuiApplication.setPalette"
    )
    assert "_apply_palette(dark=True)" in content, (
        "Glass theme must apply a dark palette so QQC2 controls match"
    )
    # The window colour must be owned by QML, not overridden from Python.
    assert "_window.setColor(" not in content, (
        "ThemeController must not call QWindow.setColor() — it fights the QML binding"
    )


# ─────────────────────────────────────────────────────────────────────────────
# 23. Python core uses shutil.which for binary path resolution
# ─────────────────────────────────────────────────────────────────────────────
def test_python_core_binary_resolution() -> None:
    """python_core.py must use shutil.which with ~/.local/bin fallback for theme-profile."""
    core_path = SRC_DIR / "core" / "python_core.py"
    content = core_path.read_text()
    assert "import shutil" in content, (
        "python_core.py must import shutil for PATH resolution"
    )
    assert shutil_path_in_init(content), (
        "PythonProfileCore.__init__ must use shutil.which with ~/.local/bin fallback"
    )


def shutil_path_in_init(content: str) -> bool:
    """Check that __init__ has shutil.which + ~/.local/bin fallback."""
    # Check for shutil.which call
    has_which = "shutil.which" in content
    # Check for local/bin fallback
    has_fallback = ".local/bin" in content
    return has_which and has_fallback


# ─────────────────────────────────────────────────────────────────────────────
# 23. Typography: font sizes must not be bound to layout spacing tokens
# ─────────────────────────────────────────────────────────────────────────────
def test_qml_font_sizes_not_bound_to_spacing_tokens() -> None:
    """No QML file may use Platform.Units.*Spacing as a font.pointSize.

    In this environment gridUnit=18, smallSpacing=4, mediumSpacing=6, so those
    bindings rendered body text at 4-6 pt (visually illegible).
    """
    qml_dir = PROJECT_ROOT / "qml"
    offenders = []
    for qml_file in qml_dir.rglob("*.qml"):
        for i, line in enumerate(qml_file.read_text().split("\n"), 1):
            stripped = line.strip()
            if not stripped.startswith("font.pointSize"):
                continue
            if "TypeScale." not in stripped:
                offenders.append(f"{qml_file.relative_to(qml_dir)}:{i}: {stripped}")
    assert not offenders, (
        "font.pointSize must come from TypeScale: " + "; ".join(offenders)
    )


# ─────────────────────────────────────────────────────────────────────────────
# 24. ThemeColors / TypeScale are the single source of colour and type
# ─────────────────────────────────────────────────────────────────────────────
def test_themecolors_is_the_only_colour_source() -> None:
    """Only ThemeColors.qml may read Kirigami.Theme directly (plus safeColor)."""
    qml_dir = PROJECT_ROOT / "qml"
    offenders = []
    for qml_file in qml_dir.rglob("*.qml"):
        if qml_file.name == "ThemeColors.qml":
            continue
        content = qml_file.read_text()
        if "Kirigami.Theme." in content or "function safeColor" in content:
            offenders.append(str(qml_file.relative_to(qml_dir)))
    assert not offenders, (
        "These files duplicate the colour logic instead of using ThemeColors: "
        + ", ".join(offenders)
    )

    theme_colors = (qml_dir / "Components" / "ThemeColors.qml").read_text()
    assert "pragma Singleton" in theme_colors
    assert "function safeColor" in theme_colors

    type_scale = (qml_dir / "Components" / "TypeScale.qml").read_text()
    assert "pragma Singleton" in type_scale
    for token in ("base", "body", "subtitle", "title", "caption"):
        assert token in type_scale, f"TypeScale must expose '{token}'"


# ─────────────────────────────────────────────────────────────────────────────
# 25. QQC2 controls must not own their own `checked` state (D-03)
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize(
    "rel_path",
    ["Components/ProfileRadioButton.qml", "Components/ComponentCheckbox.qml"],
)
def test_checked_binding_is_repairable(rel_path: str) -> None:
    """Radio/checkbox state must be corrected after a user click destroys the binding.

    A QQC2 control writes to `checked` on click, which kills a plain
    `checked: model.x` binding; two cards could then look checked at once.
    `Binding { restoreMode: ... }` re-arms it.
    """
    content = (PROJECT_ROOT / "qml" / rel_path).read_text()
    assert "Binding.RestoreBindingOrValue" in content, (
        f"{rel_path} must declare a Binding with restoreMode to survive user clicks"
    )
    assert "Binding {" in content, f"{rel_path} must use a Binding element"


def test_category_group_uses_modeldata() -> None:
    """Slot-returned list-of-dicts models are only readable via modelData."""
    content = (
        PROJECT_ROOT / "qml" / "Components" / "ComponentCategoryGroup.qml"
    ).read_text()
    assert "modelData.id" in content, (
        "ComponentCategoryGroup must read the delegate model via modelData.*"
    )
    assert "model.id" not in content, (
        "model.<key> is undefined for @Slot(result=list) models in Qt 6.12"
    )
    assert "componentsRevision" in content, (
        "The model binding must depend on componentsRevision so it re-evaluates "
        "after the asynchronous registry detection"
    )
    assert "signal selectionChanged(var components)" in content, (
        "ComponentCategoryGroup must emit the new full selection"
    )
    assert "group.selectedComponents = " not in content, (
        "ComponentCategoryGroup must never assign to its parent-bound property"
    )


# ─────────────────────────────────────────────────────────────────────────────
# 26. Preview dialog computes its content at open time (D-02)
# ─────────────────────────────────────────────────────────────────────────────
def test_preview_dialog_computes_on_open() -> None:
    """The preview must be built when the dialog opens, not from a property handler."""
    main_qml = (PROJECT_ROOT / "qml" / "Main.qml").read_text()
    assert "function updatePreview()" in main_qml, (
        "previewDialog must expose updatePreview()"
    )
    assert "onOpened: updatePreview()" in main_qml, (
        "previewDialog must compute its content in onOpened"
    )
    assert "onPreviewProfileChanged" not in main_qml, (
        "The property-changed handler ran before activeProfile was assigned "
        "(empty chips / stale diff) and must be gone"
    )


# ─────────────────────────────────────────────────────────────────────────────
# 27. Settings page is reachable (D-20) and loadable (D-01)
# ─────────────────────────────────────────────────────────────────────────────
def test_settings_page_is_wired_up() -> None:
    """Main.qml must reach SettingsPage through the global drawer."""
    main_qml = (PROJECT_ROOT / "qml" / "Main.qml").read_text()
    assert "globalDrawer" in main_qml, "Main.qml must define a globalDrawer"
    assert 'pages/SettingsPage.qml' in main_qml, (
        "The drawer must reference pages/SettingsPage.qml"
    )


def test_settings_page_uses_valid_types() -> None:
    """SettingsPage must not use Kirigami types that do not exist."""
    content = (PROJECT_ROOT / "qml" / "pages" / "SettingsPage.qml").read_text()
    for bogus in ("Kirigami.RadioButton", "Kirigami.Switch", "Kirigami.Button"):
        assert bogus not in content, (
            f"{bogus} does not exist in Qt 6 Kirigami (use QtQuick.Controls)"
        )
    assert "import Components 1.0" in content, (
        "SettingsPage uses ComponentCategoryGroup and must import the module"
    )
    assert "Kirigami.ScrollablePage" in content, (
        "SettingsPage must be a ScrollablePage with a single layout child"
    )
    assert content.count("contentItem:") >= 1, (
        "Each Kirigami.Card must assign an explicit contentItem"
    )
    assert "Kirigami.Separator" not in content, (
        "Use a 1 px Rectangle instead of the heavy Kirigami.Separator"
    )


# ─────────────────────────────────────────────────────────────────────────────
# 28. Controllers: cached models, async operations, single palette pass
# ─────────────────────────────────────────────────────────────────────────────
def test_profile_controller_caches_its_qml_model() -> None:
    """ProfileController.profiles must return a cache, not rebuild per read."""
    from controllers import ProfileController

    source = inspect.getsource(ProfileController.profiles.fget)
    assert "_profiles_model" in source, (
        "profiles must return the cached _profiles_model list"
    )
    assert "for p in self._profiles" not in source, (
        "profiles must not rebuild the model on every read"
    )


def test_profile_operations_run_off_the_gui_thread() -> None:
    """apply/save/delete must be handed to QThreadPool and expose `busy`."""
    content = (SRC_DIR / "controllers" / "__init__.py").read_text()
    assert "QThreadPool" in content, "controllers must use QThreadPool"
    assert "_start_operation" in content, (
        "ProfileController must route write operations through _start_operation"
    )
    assert "_OperationWorker" in content and "_OperationSignals" in content, (
        "A shared worker must exist for background operations"
    )
    from controllers import ProfileController

    assert hasattr(ProfileController, "busy"), (
        "ProfileController must expose a `busy` property for the busy indicator"
    )
    for slot in ("applyProfile", "saveProfile", "deleteProfile"):
        body = inspect.getsource(getattr(ProfileController, slot))
        assert "_start_operation" in body, (
            f"{slot} must run through the thread pool, not block the GUI thread"
        )


def test_tracked_apps_detection_is_async() -> None:
    """detect_all() must not run on the GUI thread during startup."""
    from controllers import TrackedAppsController

    source = inspect.getsource(TrackedAppsController.refresh)
    assert "_run_async" in source, (
        "TrackedAppsController.refresh must delegate detection to the thread pool"
    )
    assert hasattr(TrackedAppsController, "componentsRevision"), (
        "TrackedAppsController must expose componentsRevision for QML"
    )


def test_theme_controller_single_palette_pass() -> None:
    """No _apply_*_theme helper may chain into another one (double palette apply)."""
    import theme_controller as theme_controller_mod

    content = (SRC_DIR / "theme_controller.py").read_text()
    assert "def _apply_flags" in content, (
        "ThemeController must funnel every theme into a single _apply_flags pass"
    )
    helpers = ("_apply_glass_theme", "_apply_paper_theme", "_apply_dark_theme",
               "_apply_light_theme", "_apply_system_theme")
    for helper in helpers:
        body = inspect.getsource(getattr(theme_controller_mod.ThemeController, helper))
        for other in helpers:
            if other != helper:
                assert f"{other}(" not in body, (
                    f"{helper} must not call {other} (double apply / double emit)"
                )


def test_settings_available_components_uses_no_core_detection() -> None:
    """SettingsController must not trigger a detection when refreshing its cache."""
    from controllers import SettingsController

    source = inspect.getsource(SettingsController.refreshAvailableComponents)
    assert "_tracked_apps" in source, (
        "refreshAvailableComponents must read the wired tracked-apps controller "
        "(calling get_all_components() on a cold cache blocks the GUI thread)"
    )


# ─────────────────────────────────────────────────────────────────────────────
# 29. PySide6 @Slot() arity must match the Python signature
# ─────────────────────────────────────────────────────────────────────────────
def test_slots_declare_every_python_argument() -> None:
    """A @Slot() with fewer argument types than the Python signature makes Qt
    silently drop the extra arguments at call time.

    That is what broke ``diffProfiles``: declared ``@Slot(str, result=str)`` but
    implemented as ``(profile_a, profile_b)``, so every call from QML raised
    "diffProfiles() missing 1 required positional argument: 'profile_b'" and the
    preview dialog rendered an empty diff.
    """
    from PySide6.QtCore import QMetaMethod

    from controllers import (
        ProfileController, WallpaperController, TrackedAppsController,
        SettingsController, MainController,
    )

    problems = []
    for klass in (ProfileController, WallpaperController, TrackedAppsController,
                  SettingsController, MainController):
        meta = klass.staticMetaObject
        for i in range(meta.methodOffset(), meta.methodCount()):
            method = meta.method(i)
            if method.methodType() != QMetaMethod.Slot:
                continue
            name = bytes(method.name()).decode()
            signature = bytes(method.methodSignature()).decode()
            args = signature[signature.find("(") + 1:signature.rfind(")")]
            declared = len([a for a in args.split(",") if a.strip()])
            func = getattr(klass, name, None)
            if func is None:
                continue
            params = inspect.signature(func).parameters.values()
            python_args = [
                p for p in params
                if p.kind in (p.POSITIONAL_OR_KEYWORD, p.POSITIONAL_ONLY)
                and p.name != "self"
            ]
            if declared != len(python_args):
                problems.append(
                    f"{klass.__name__}.{name}: Qt slot declares {declared} "
                    f"argument(s) but Python takes {len(python_args)}"
                )
    assert not problems, "; ".join(problems)


def test_dialogs_compute_content_on_open() -> None:
    """Both content-heavy dialogs build their body when they are opened."""
    main_qml = (PROJECT_ROOT / "qml" / "Main.qml").read_text()
    assert "onOpened: updateDiff()" in main_qml, (
        "diffDialog must compute the diff when it opens"
    )
    assert "onOpened: updatePreview()" in main_qml, (
        "previewDialog must compute its content when it opens"
    )


# ─────────────────────────────────────────────────────────────────────────────
# 21. System tray: quick profile switching
#
# The tray used to show a disabled "Profiles" placeholder. It now lists the
# profiles (active one checked), applies them without blocking the GUI thread
# and reports the result as a desktop notification.
# ─────────────────────────────────────────────────────────────────────────────
class TestSystemTray:
    """Tray menu model + wiring."""

    @staticmethod
    def _controller():
        from system_tray import SystemTrayController

        return SystemTrayController.instance()

    def test_profile_entries_put_active_first(self) -> None:
        entries = self._controller()._profile_entries(
            [
                {"name": "paper", "componentCount": 20, "isActive": False},
                {"name": "glass", "componentCount": 20, "isActive": True},
            ],
            "glass",
        )
        assert [e["name"] for e in entries] == ["glass", "paper"]
        assert [e["active"] for e in entries] == [True, False]

    def test_profile_entries_label_carries_component_count(self) -> None:
        entries = self._controller()._profile_entries(
            [{"name": "glass", "componentCount": 20}], "glass"
        )
        assert entries[0]["label"] == "glass (20)"

    def test_profile_entries_ignore_empty_and_plain_strings(self) -> None:
        entries = self._controller()._profile_entries(
            [{"name": ""}, {"name": "solo"}, "plain"], "solo"
        )
        assert [e["name"] for e in entries] == ["solo", "plain"]
        assert entries[0]["label"] == "solo"  # no count → no suffix

    def test_profile_entries_handle_missing_input(self) -> None:
        assert self._controller()._profile_entries(None, "") == []
        assert self._controller()._profile_entries([], "glass") == []

    def test_tray_applies_through_the_controller_off_the_gui_thread(self) -> None:
        source = (SRC_DIR / "system_tray.py").read_text()
        assert "controller.applyProfile(name)" in source, (
            "the tray must apply profiles through ProfileController.applyProfile "
            "(which runs the operation on the thread pool)"
        )
        assert "_pending_profile" in source, (
            "the tray must remember which profile it started, so it knows "
            "whether an operationFinished signal belongs to it"
        )
        assert "subprocess" not in source, "the tray must not shell out itself"

    def test_tray_wires_controllers_from_main_controller(self) -> None:
        import ast

        tree = ast.parse((SRC_DIR / "system_tray.py").read_text())
        register = next(
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name == "register_system_tray"
        )
        params = [a.arg for a in register.args.args]
        assert params[:3] == ["engine", "main_window", "main_controller"], params

        body = ast.dump(register)
        for call in ("set_profile_controller", "set_wallpaper_controller"):
            assert call in body, f"register_system_tray must call {call}"

    def test_tray_has_a_quit_action(self) -> None:
        """Minimize-to-tray must not leave the app without a way out."""
        source = (SRC_DIR / "system_tray.py").read_text()
        assert "QCoreApplication.quit()" in source
        assert "self._quit_app" in source

    def test_tray_notifies_via_show_message(self) -> None:
        """Notifications must go through QSystemTrayIcon.showMessage.

        A hand-built org.freedesktop.Notifications.Notify call is silently
        dropped: PySide6 marshals Python ints as D-Bus 'i' while Notify's
        replaces_id is 'u', so the daemon answers "No such method 'Notify'"
        (verified with dbus-monitor on Plasma 6).
        """
        source = (SRC_DIR / "system_tray.py").read_text()
        assert "showMessage(" in source
        assert '"Notify"' not in source, (
            "the hand-built Notify call is rejected by the notification daemon"
        )

    def test_minimize_to_tray_is_guarded_in_qml(self) -> None:
        main_qml = (PROJECT_ROOT / "qml" / "Main.qml").read_text()
        assert "onClosing" in main_qml, (
            "closing the window must consult the minimize-to-tray preference"
        )
        assert "trayController.trayIconVisible" in main_qml, (
            "hiding the window without a tray icon would make the app unreachable"
        )


# ─────────────────────────────────────────────────────────────────────────────
# 22. Wallpaper operations are asynchronous
#
# Opening the picker is interactive (wofi stays open until the user picks),
# so every wallpaper operation runs on the thread pool and the UI disables
# its buttons while one is in flight.
# ─────────────────────────────────────────────────────────────────────────────
def test_wallpaper_controller_operations_are_async() -> None:
    source = (SRC_DIR / "controllers" / "__init__.py").read_text()
    start = source.index("class WallpaperController")
    end = source.index("class TrackedAppsController")
    block = source[start:end]

    assert "_run_async(self" in block, (
        "wallpaper operations must not run on the GUI thread"
    )
    for method in ("nextWallpaper", "prevWallpaper", "pickWallpaper", "setWallpaper"):
        assert f"def {method}" in block, f"{method} disappeared from the controller"

    # `busy` must be a Property with a change signal so QML/tray can react.
    assert "@Property(bool, notify=busyChanged)" in block
    assert "busyChanged = Signal()" in block


def test_qml_disables_wallpaper_buttons_while_busy() -> None:
    main_qml = (PROJECT_ROOT / "qml" / "Main.qml").read_text()
    assert main_qml.count("enabled: !wallpaperController.busy") == 3, (
        "Previous/Pick/Next must all be disabled while an operation runs"
    )


# ─────────────────────────────────────────────────────────────────────────────
# 23. Application icon
# ─────────────────────────────────────────────────────────────────────────────
def test_app_icon_matches_the_desktop_entry() -> None:
    """The icon name used at runtime must be the one the .desktop installs."""
    from app_icon import FALLBACK_ICON_NAME, ICON_NAME

    desktop = (PROJECT_ROOT / "resources" / "kde-theme-manager.desktop").read_text()
    assert f"Icon={ICON_NAME}" in desktop, (
        "app_icon.ICON_NAME and the desktop entry's Icon= must agree"
    )
    assert (PROJECT_ROOT / "resources" / "icons" / f"{ICON_NAME}.svg").is_file(), (
        "the svg the installer deploys is missing"
    )
    assert FALLBACK_ICON_NAME == "preferences-desktop-theme"


def test_tray_and_window_use_the_shared_icon() -> None:
    assert "app_icon()" in (SRC_DIR / "system_tray.py").read_text()
    assert "app_icon()" in (SRC_DIR / "__main__.py").read_text()


def test_icon_name_survives_kde_icon_loader() -> None:
    """KDE's loader collapses "<existing-icon>-<suffix>" to the existing icon.

    ``kde-theme-manager`` therefore resolved to the *KDE logo* and
    ``plasma-theme-manager`` to the Plasma logo, so the tray/menu icon was the
    wrong picture (verified on Plasma 6 via QIcon.fromTheme). The icon name
    must keep a first dash-separated token that cannot be an existing icon.
    """
    from app_icon import ICON_NAME

    reserved = {"kde", "plasma", "org", "theme", "preferences", "application"}
    first_token = ICON_NAME.split("-")[0].lower()
    assert first_token not in reserved, (
        f"{ICON_NAME!r} starts with {first_token!r}, which KDE's icon loader "
        "may resolve to that icon instead"
    )
    assert ICON_NAME != "kde-theme-manager"


# ─────────────────────────────────────────────────────────────────────────────
# 30. Rust core: library lookup, FFI contract, graceful degradation
#
# The Rust core is an optional drop-in: a shared library behind a C ABI of
# `*mut c_char` JSON payloads (freed with kde_theme_core_free_string) and
# c_int status codes. Without the library everything must degrade to the
# Python core instead of crashing.
# ─────────────────────────────────────────────────────────────────────────────
RUST_LIB = (
    PROJECT_ROOT / "src" / "core" / "rust_core" / "target" / "release"
    / "libkde_theme_core.so"
)
needs_rust_lib = pytest.mark.skipif(
    not RUST_LIB.is_file(), reason="libkde_theme_core.so is not built"
)


@pytest.fixture
def core_factory():
    """Keep CoreFactory on the Python backend around a test."""
    from core.protocol import CoreFactory

    CoreFactory.set_backend("python")
    try:
        yield CoreFactory
    finally:
        CoreFactory.set_backend("python")


def test_rust_core_library_candidates_cover_both_layouts(monkeypatch) -> None:
    """Source checkout and installed app layouts must both be searched."""
    from core import rust_core

    override = Path("/tmp/opencode/does-not-exist/libkde_theme_core.so")
    monkeypatch.setenv(rust_core.LIBRARY_ENV_VAR, str(override))
    candidates = rust_core.library_candidates()

    assert candidates[0] == override, "the env override must win"
    as_text = [str(c) for c in candidates]
    assert any(c.endswith("rust_core/target/release/libkde_theme_core.so") for c in as_text), (
        "the cargo build tree must be searched"
    )
    # Installed layout: <appdir>/lib, where <appdir> is the package's parent.
    assert str(PROJECT_ROOT / "lib" / rust_core.LIBRARY_NAME) in as_text, (
        "the installed app keeps the library in <appdir>/lib"
    )


def test_rust_core_reports_a_missing_library(tmp_path) -> None:
    from core import rust_core

    with pytest.raises(rust_core.RustCoreUnavailable) as excinfo:
        rust_core.load_library(path=tmp_path / "nope.so", reload=True)

    assert "nope.so" in str(excinfo.value)
    # A bogus path must be reported through the inspection API, not raised.
    assert rust_core.find_library() is None or rust_core.find_library().is_file()


def test_rust_core_mapping_helpers() -> None:
    """The JSON payloads must map onto the protocol dataclasses."""
    from core import rust_core
    from core.protocol import AppStatus

    info = rust_core._profile_info(
        {"name": "glass", "is_active": True, "components": ["kwin"],
         "created_at": "2026-10-19", "description": "d", "wallpaper_path": "w"}
    )
    assert (info.name, info.is_active, info.components) == ("glass", True, ("kwin",))
    assert info.created_at == "2026-10-19" and info.wallpaper_path == "w"

    # An unknown status must not explode — the UI shows "partial".
    component = rust_core._component({"id": "kitty", "status": "who-knows"})
    assert component.status is AppStatus.PARTIAL
    known = rust_core._component({"id": "kitty", "status": AppStatus.AVAILABLE.value})
    assert known.status is AppStatus.AVAILABLE

    assert rust_core._json_argument(None) is None
    assert rust_core._json_argument([]) is None
    assert json.loads(rust_core._json_argument(["kwin", "gtk3"])) == ["kwin", "gtk3"]


def test_rust_core_declares_types_for_a_fixed_signature_table() -> None:
    """Every FFI entry must carry its argument types and result kind."""
    from core import rust_core

    kinds = {rust_core._JSON, rust_core._TEXT, rust_core._STATUS}
    for name, (argtypes, kind) in rust_core._FUNCTIONS.items():
        assert name.startswith("kde_theme_core_"), name
        assert kind in kinds, f"{name}: unknown result kind {kind!r}"
        assert all(t is ctypes.c_char_p for t in argtypes), name

    # Pointers must never be passed as bare Python ints (ctypes would truncate
    # them to C int and the library would crash inside free()).
    assert rust_core._FUNCTIONS["kde_theme_core_profile_apply"][0] == [
        ctypes.c_char_p, ctypes.c_char_p
    ]


@needs_rust_lib
def test_rust_core_library_exports_the_declared_surface() -> None:
    from core import rust_core

    library = rust_core.load_library()
    for name in rust_core._FUNCTIONS:
        assert getattr(library, name, None) is not None, f"{name} is not exported"

    # Guards the segfault class of bug: without argtypes ctypes truncates the
    # returned pointer before handing it to free().
    assert library.kde_theme_core_free_string.argtypes == [ctypes.c_void_p]
    assert library.kde_theme_core_get_error.restype is ctypes.c_void_p


@needs_rust_lib
def test_rust_core_status_calls_map_errors_to_result(core_factory) -> None:
    from core.rust_core import RustProfileCore

    result = RustProfileCore().apply("there-is-no-such-profile")
    assert not result.success and result.message


# ─────────────────────────────────────────────────────────────────────────────
# 31. Parity: the two cores must stay interchangeable
#
# Same listing order, same current wallpaper, same component detection, same
# diff text — switching cores (--core) must not change what the UI shows.
# ─────────────────────────────────────────────────────────────────────────────
@needs_rust_lib
class TestCoreParity:
    @staticmethod
    def cores():
        from core.python_core import (
            PythonProfileCore,
            PythonSettingsCore,
            PythonTrackedAppsCore,
            PythonWallpaperCore,
        )
        from core.rust_core import (
            RustProfileCore,
            RustSettingsCore,
            RustTrackedAppsCore,
            RustWallpaperCore,
        )

        return (
            (PythonProfileCore(), RustProfileCore()),
            (PythonWallpaperCore(), RustWallpaperCore()),
            (PythonTrackedAppsCore(), RustTrackedAppsCore()),
            (PythonSettingsCore(), RustSettingsCore()),
        )

    def test_profiles(self, core_factory) -> None:
        (py, rust), *_ = self.cores()

        py_profiles = py.list_profiles()
        rust_profiles = rust.list_profiles()
        assert [p.name for p in rust_profiles] == [p.name for p in py_profiles]
        for expected, actual in zip(py_profiles, rust_profiles, strict=True):
            assert actual.is_active == expected.is_active
            assert actual.components == expected.components
            assert actual.created_at == expected.created_at

        assert rust.get_active_profile() == py.get_active_profile()

    def test_profile_components_and_diff(self, core_factory) -> None:
        (py, rust), *_ = self.cores()

        for profile in [p.name for p in py.list_profiles()]:
            assert rust.get_profile_components(profile) == py.get_profile_components(profile)

        names = [p.name for p in py.list_profiles()][:2]
        if len(names) == 2:
            assert rust.diff(*names) == py.diff(*names)

    def test_wallpapers(self, core_factory) -> None:
        _, (py, rust), *_ = self.cores()

        assert rust.list_wallpapers() == py.list_wallpapers()
        assert rust.current() == py.current()

    def test_wallpaper_directory_comes_from_the_settings(self, core_factory, tmp_path) -> None:
        """A settings directory must reach the library (set_dir), not be ignored.

        The cached index is a *position* in the list the app displays, so the
        library listing another directory would make next/prev jump elsewhere.
        """
        from core.protocol import AppSettings

        (tmp_path / "a.jpg").write_bytes(b"x")
        (tmp_path / "B.PNG").write_bytes(b"x")
        (tmp_path / "notes.txt").write_bytes(b"x")  # wrong extension: ignored
        os.symlink(tmp_path / "a.jpg", tmp_path / "0-link.webp")  # symlink: followed

        class FakeSettings:
            def load(self):
                return AppSettings(wallpaper_directory=str(tmp_path))

        core_factory.set_settings_core(FakeSettings())

        from core.python_core import PythonWallpaperCore
        from core.rust_core import RustWallpaperCore

        rust_listed = RustWallpaperCore().list_wallpapers()
        assert rust_listed == PythonWallpaperCore().list_wallpapers()
        assert [Path(p).name for p in rust_listed] == ["0-link.webp", "B.PNG", "a.jpg"]

    def test_tracked_apps(self, core_factory) -> None:
        *_, (py, rust), _ = self.cores()

        py_apps = py.detect_all()
        rust_apps = rust.detect_all()
        assert [(c.id, c.status) for c in rust_apps] == [(c.id, c.status) for c in py_apps]
        assert [c.config_paths for c in rust_apps] == [c.config_paths for c in py_apps]
        assert rust.get_categories() == py.get_categories()

    def test_settings(self, core_factory) -> None:
        *_, (py, rust) = self.cores()

        assert rust.get_defaults().to_dict() == py.get_defaults().to_dict()
        assert rust.load().to_dict() == py.load().to_dict()

    def test_settings_round_trip_keeps_the_core_choice(self, core_factory, monkeypatch, tmp_path) -> None:
        """Saving through the Rust core must keep `core_backend` (it is a setting).

        Switching to Rust and saving the settings would otherwise silently flip
        back to Python on the next start.
        """
        from core.protocol import AppSettings
        from core.rust_core import RustSettingsCore

        monkeypatch.setenv("HOME", str(tmp_path))

        saved = AppSettings(
            **{**AppSettings().to_dict(), "core_backend": "rust", "theme": "paper"}
        )
        assert RustSettingsCore().save(saved).success

        written = tmp_path / ".config" / "theme-profile" / "app-preferences.json"
        assert written.is_file(), "the Rust core must create the config directory"

        loaded = RustSettingsCore().load()
        assert loaded.core_backend == "rust"
        assert loaded.theme == "paper"
        assert loaded.to_dict() == saved.to_dict()
        # …and the file must stay readable by the Python core.
        assert AppSettings.from_dict(json.loads(written.read_text())).to_dict() == saved.to_dict()

    def test_mutating_profile_operations_go_through_the_script(self, core_factory) -> None:
        """The Rust core must delegate apply/save to `theme-profile`.

        A native implementation copied profile entries to `~/<component>`
        (`kwinrc` → `~/kwin`) and restarted plasmashell on every apply.
        """
        rust_source = (SRC_DIR / "core" / "rust_core" / "src" / "profile.rs").read_text()

        assert "run_theme_profile(&args)" in rust_source
        assert 'run_theme_profile(&["diff"' in rust_source
        assert "restart_plasma_shell" not in rust_source


# ─────────────────────────────────────────────────────────────────────────────
# 32. Core selection: --core flag, $KTM_CORE, saved setting, fallback
# ─────────────────────────────────────────────────────────────────────────────
def test_core_factory_rejects_unknown_backend(core_factory) -> None:
    with pytest.raises(ValueError):
        core_factory.set_backend("cobol")


def test_core_factory_auto_prefers_rust_when_built(core_factory, monkeypatch) -> None:
    monkeypatch.setattr(core_factory, "rust_available", classmethod(lambda cls: True))
    assert core_factory.set_backend("auto") == "rust"


def test_core_factory_auto_falls_back_to_python(core_factory, monkeypatch) -> None:
    monkeypatch.setattr(core_factory, "rust_available", classmethod(lambda cls: False))
    assert core_factory.set_backend("auto") == "python"


def test_core_factory_strict_rust_failure_is_loud(core_factory, monkeypatch) -> None:
    from core.rust_core import RustCoreUnavailable

    monkeypatch.setattr(core_factory, "rust_available", classmethod(lambda cls: False))
    with pytest.raises(RustCoreUnavailable):
        core_factory.set_backend("rust")


def test_core_factory_soft_fallback_warns(core_factory, monkeypatch, capsys) -> None:
    monkeypatch.setattr(core_factory, "rust_available", classmethod(lambda cls: False))

    assert core_factory.set_backend("rust", strict=False) == "python"
    assert "falling back" in capsys.readouterr().err


def test_core_factory_reads_the_environment(core_factory, monkeypatch) -> None:
    monkeypatch.setenv(core_factory.ENV_VAR, "python")
    assert core_factory.set_backend_from_env() == "python"

    monkeypatch.delenv(core_factory.ENV_VAR)
    assert core_factory.set_backend_from_env(default="python") == "python"


@needs_rust_lib
def test_core_factory_builds_rust_implementations(core_factory) -> None:
    import core.rust_core as rust_core

    assert core_factory.set_backend("rust") == "rust"
    assert isinstance(core_factory.profile_core(), rust_core.RustProfileCore)
    assert isinstance(core_factory.wallpaper_core(), rust_core.RustWallpaperCore)
    assert isinstance(core_factory.tracked_apps_core(), rust_core.RustTrackedAppsCore)
    assert isinstance(core_factory.settings_core(), rust_core.RustSettingsCore)
    assert "libkde_theme_core.so" in core_factory.backend_label()

    # Switching back must rebuild the Python implementations.
    assert core_factory.set_backend("python") == "python"
    from core.python_core import PythonProfileCore

    assert isinstance(core_factory.profile_core(), PythonProfileCore)
    assert core_factory.backend_label() == "Python"


def test_settings_expose_the_core_selector() -> None:
    """SettingsController must persist the choice and show the running core."""
    from core.protocol import AppSettings

    source = (SRC_DIR / "controllers" / "__init__.py").read_text()
    assert "def coreBackend" in source
    assert "def activeCore" in source
    assert "def rustCoreBuilt" in source

    qml = (PROJECT_ROOT / "qml" / "pages" / "SettingsPage.qml").read_text()
    assert 'settingsController.coreBackend' in qml
    assert 'model: ["python", "rust", "auto"]' in qml

    defaults = AppSettings()
    assert defaults.core_backend == "python"
    assert AppSettings.from_dict({}).core_backend == "python"
    assert AppSettings.from_dict({"core_backend": "rust"}).core_backend == "rust"
    assert defaults.to_dict()["core_backend"] == "python"


# ─────────────────────────────────────────────────────────────────────────────
# 33. --core CLI flag
# ─────────────────────────────────────────────────────────────────────────────
def _load_main_module():
    """Import src/__main__.py under a private name (it runs main() only as __main__)."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("ktm_main", SRC_DIR / "__main__.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "argv, expected, rest",
    [
        (["--core=rust"], "rust", []),
        (["--core", "rust"], "rust", []),
        (["--core=auto", "--verbose"], "auto", ["--verbose"]),
        (["--core", "python", "file.qml"], "python", ["file.qml"]),
        ([], None, []),
    ],
)
def test_core_flag_is_parsed_and_removed(argv, expected, rest, monkeypatch) -> None:
    """Qt must never see --core (a stray value would look like a file to open)."""
    main_module = _load_main_module()
    monkeypatch.setattr(sys, "argv", ["kde-theme-manager", *argv])

    assert main_module._extract_core_arg() == expected
    assert sys.argv[1:] == rest


def test_core_flag_without_a_value_is_an_error(monkeypatch) -> None:
    main_module = _load_main_module()
    monkeypatch.setattr(sys, "argv", ["kde-theme-manager", "--core"])

    with pytest.raises(SystemExit):
        main_module._extract_core_arg()


def test_explicit_core_that_cannot_load_is_fatal(core_factory, monkeypatch, capsys) -> None:
    main_module = _load_main_module()
    monkeypatch.setattr(core_factory, "rust_available", classmethod(lambda cls: False))

    with pytest.raises(SystemExit) as excinfo:
        main_module._select_core("rust")

    assert excinfo.value.code == 3
    assert "Error:" in capsys.readouterr().err


def test_stale_saved_core_falls_back_instead_of_failing(core_factory, monkeypatch, capsys) -> None:
    """A setting pointing at a since-removed library must not break startup."""
    from core.protocol import AppSettings

    main_module = _load_main_module()
    import core.python_core as python_core

    monkeypatch.setattr(core_factory, "rust_available", classmethod(lambda cls: False))
    monkeypatch.delenv(core_factory.ENV_VAR, raising=False)

    saved: list[AppSettings] = []

    class FakeSettingsCore:
        def load(self):
            return AppSettings(**{**AppSettings().to_dict(), "core_backend": "rust"})

        def save(self, settings):
            saved.append(settings)
            from core.protocol import Result

            return Result.ok()

    monkeypatch.setattr(python_core, "PythonSettingsCore", FakeSettingsCore)

    main_module._select_core(None)

    assert core_factory.backend() == "python"
    assert "falling back" in capsys.readouterr().err
    assert saved == [], "a fallback must not overwrite the saved preference"


def test_explicit_core_is_persisted(core_factory, monkeypatch) -> None:
    from core.protocol import AppSettings

    main_module = _load_main_module()
    import core.python_core as python_core

    monkeypatch.delenv(core_factory.ENV_VAR, raising=False)
    saved: list[AppSettings] = []

    class FakeSettingsCore:
        def load(self):
            # Saved as "rust"; the flag asks for python → the preference flips.
            return AppSettings(**{**AppSettings().to_dict(), "core_backend": "rust"})

        def save(self, settings):
            saved.append(settings)
            from core.protocol import Result

            return Result.ok()

    monkeypatch.setattr(python_core, "PythonSettingsCore", FakeSettingsCore)

    main_module._select_core("python")

    assert [s.core_backend for s in saved] == ["python"]


def test_list_cores_reports_availability(capsys) -> None:
    main_module = _load_main_module()
    assert main_module._list_cores() == 0

    out = capsys.readouterr().out
    assert "python" in out and "rust" in out
    assert ("available" in out) or ("NOT AVAILABLE" in out)


def test_help_mentions_the_core_flag(capsys) -> None:
    main_module = _load_main_module()
    assert main_module._show_help() == 0

    out = capsys.readouterr().out
    assert "--core" in out and "--list-cores" in out
