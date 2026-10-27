//! Wallpaper Core Implementation

use std::path::{Path, PathBuf};
use std::fs;
use std::process::Command;
use std::sync::Mutex;
use anyhow::{Result, Context};
use dirs;
use once_cell::sync::Lazy;

/// Wallpaper directory override, set from Python via
/// `kde_theme_core_wallpaper_set_dir` so the Rust core lists the same
/// directory the application is configured for (AppSettings.wallpaper_directory).
/// Without it the core would always use the built-in default and the cached
/// index would point into a different list.
static WALLPAPER_DIR: Lazy<Mutex<Option<String>>> = Lazy::new(|| Mutex::new(None));

/// Wallpaper Core Trait
pub trait WallpaperCore {
    fn pick(&self) -> Result<String>;
    fn next(&self) -> Result<()>;
    fn prev(&self) -> Result<()>;
    fn current(&self) -> Result<String>;
    fn list(&self) -> Result<Vec<String>>;
    fn set(&self, path: &str) -> Result<()>;
}

/// Default implementation
pub struct DefaultWallpaperCore;

impl WallpaperCore for DefaultWallpaperCore {
    fn pick(&self) -> Result<String> {
        pick_wallpaper()
    }

    fn next(&self) -> Result<()> {
        next_wallpaper()
    }

    fn prev(&self) -> Result<()> {
        prev_wallpaper()
    }

    fn current(&self) -> Result<String> {
        current_wallpaper()
    }

    fn list(&self) -> Result<Vec<String>> {
        list_wallpapers()
    }

    fn set(&self, path: &str) -> Result<()> {
        set_wallpaper(path)
    }
}

/// Get wallpaper directory (override from Python, otherwise the default)
pub fn wallpaper_dir() -> PathBuf {
    if let Ok(guard) = WALLPAPER_DIR.lock() {
        if let Some(dir) = guard.as_ref() {
            let expanded = expand_tilde(dir);
            if !expanded.as_os_str().is_empty() {
                return expanded;
            }
        }
    }
    dirs::home_dir()
        .map(|home| home.join("Изображения/Wallpaper"))
        .unwrap_or_else(|| PathBuf::from("Изображения/Wallpaper"))
}

/// Override the wallpaper directory (empty or missing path resets to default)
pub fn set_wallpaper_dir(dir: &str) {
    if let Ok(mut guard) = WALLPAPER_DIR.lock() {
        let trimmed = dir.trim();
        *guard = if trimmed.is_empty() {
            None
        } else {
            Some(trimmed.to_string())
        };
    }
}

/// Expand a leading `~` (the settings store paths as `~/Pictures/...`)
fn expand_tilde(path: &str) -> PathBuf {
    if let Some(rest) = path.strip_prefix("~/") {
        if let Some(home) = dirs::home_dir() {
            return home.join(rest);
        }
    } else if path == "~" {
        if let Some(home) = dirs::home_dir() {
            return home;
        }
    }
    PathBuf::from(path)
}

/// Get cache index file
pub fn cache_index() -> PathBuf {
    dirs::cache_dir()
        .unwrap_or_else(|| PathBuf::from("/tmp"))
        .join("wallpaper_index")
}

/// Environment forcing the CLI binaries onto our directory
fn script_env() -> Vec<(&'static str, String)> {
    vec![("WALLPAPER_DIR", wallpaper_dir().to_string_lossy().to_string())]
}

/// Pick wallpaper using wofi
pub fn pick_wallpaper() -> Result<String> {
    let wallpapers = list_wallpapers()?;
    if wallpapers.is_empty() {
        return Err(anyhow::anyhow!("No wallpapers found"));
    }

    let mut command = Command::new("wallpaper-picker");
    for (key, value) in script_env() {
        command.env(key, value);
    }
    let output = command
        .output()
        .context("Failed to run wallpaper-picker")?;

    if !output.status.success() {
        return Err(anyhow::anyhow!("wallpaper-picker cancelled or failed"));
    }

    current_wallpaper()
}

/// Next wallpaper
pub fn next_wallpaper() -> Result<()> {
    let mut command = Command::new("wallpaper-next");
    for (key, value) in script_env() {
        command.env(key, value);
    }
    let output = command.output().context("Failed to run wallpaper-next")?;

    if !output.status.success() {
        return Err(anyhow::anyhow!("wallpaper-next failed"));
    }
    Ok(())
}

/// Previous wallpaper
pub fn prev_wallpaper() -> Result<()> {
    let mut command = Command::new("wallpaper-prev");
    for (key, value) in script_env() {
        command.env(key, value);
    }
    let output = command.output().context("Failed to run wallpaper-prev")?;

    if !output.status.success() {
        return Err(anyhow::anyhow!("wallpaper-prev failed"));
    }
    Ok(())
}

/// Path of the wallpaper Plasma is showing right now (None — unreadable)
///
/// Plasma keeps the desktop wallpaper per containment in the appletsrc; it is
/// the authoritative answer to "what is on the desktop". Mirrors
/// CLI core's `_plasma_wallpaper()`: the *last* `Image=` inside a
/// `[Containments][N][Wallpaper][org.kde.image][General]` group wins.
fn plasma_wallpaper() -> Option<String> {
    let config = dirs::config_dir()?.join("plasma-org.kde.plasma.desktop-appletsrc");
    plasma_wallpaper_from(&config)
}

/// Same as [`plasma_wallpaper`] but against an explicit appletsrc path
/// (used by the CLI, which honours `PLASMA_APPLETSRC`).
pub fn plasma_wallpaper_from(config: &Path) -> Option<String> {
    let text = fs::read_to_string(config).ok()?;

    let mut url: Option<String> = None;
    let mut in_image_group = false;
    for line in text.lines() {
        if line.starts_with('[') {
            let trimmed = line.trim();
            in_image_group = trimmed.starts_with("[Containments]")
                && trimmed.ends_with("[Wallpaper][org.kde.image][General]");
            continue;
        }
        if in_image_group {
            if let Some(value) = line.strip_prefix("Image=") {
                url = Some(value.trim().to_string());
            }
        }
    }

    let url = url?;
    let path = if let Some(rest) = url.strip_prefix("file://") {
        percent_decode(rest)
    } else {
        percent_decode(&url)
    };
    if path.is_empty() {
        None
    } else {
        Some(path)
    }
}

/// Decode %XX escapes (Plasma stores file URLs percent-encoded)
fn percent_decode(input: &str) -> String {
    let bytes = input.as_bytes();
    let mut out: Vec<u8> = Vec::with_capacity(bytes.len());
    let mut i = 0;
    while i < bytes.len() {
        if bytes[i] == b'%' && i + 2 < bytes.len() {
            let hex = std::str::from_utf8(&bytes[i + 1..i + 3]).ok();
            if let Some(value) = hex.and_then(|h| u8::from_str_radix(h, 16).ok()) {
                out.push(value);
                i += 3;
                continue;
            }
        }
        out.push(bytes[i]);
        i += 1;
    }
    String::from_utf8_lossy(&out).to_string()
}

/// Get current wallpaper
///
/// Plasma first (self-healing, like the CLI core), cached index only as a
/// fallback: the index is a position in the list and silently points at a
/// different file once the enumeration order changes.
pub fn current_wallpaper() -> Result<String> {
    if let Some(real) = plasma_wallpaper() {
        return Ok(real);
    }

    let cache_index = cache_index();
    if !cache_index.exists() {
        return Err(anyhow::anyhow!("No wallpaper index found"));
    }

    let index_str = fs::read_to_string(&cache_index)?.trim().to_string();
    let index: usize = index_str.parse().context("Invalid wallpaper index")?;

    let wallpapers = list_wallpapers()?;
    if index < wallpapers.len() {
        Ok(wallpapers[index].clone())
    } else {
        Err(anyhow::anyhow!("Wallpaper index out of bounds"))
    }
}

/// List all wallpapers
///
/// The order and the accepted extensions must match the CLI binaries
/// (theme-profile/wallpaper-*) and the CLI core: the cached
/// index is a position in this list. `is_file()` follows symlinks (like
/// `find -L`), extensions are compared case-insensitively (like
/// `find -iname`), and `sort()` on String is byte order (like `LC_ALL=C sort`).
pub fn list_wallpapers() -> Result<Vec<String>> {
    list_wallpapers_in(&wallpaper_dir())
}

/// List wallpapers in an explicit directory (CLI: honours `WALLPAPER_DIR`).
pub fn list_wallpapers_in(dir: &Path) -> Result<Vec<String>> {
    if !dir.exists() {
        return Ok(vec![]);
    }

    let mut wallpapers = Vec::new();
    let extensions = ["jpg", "jpeg", "png", "webp", "bmp"];

    for entry in fs::read_dir(dir)? {
        let entry = entry?;
        let path = entry.path();
        if path.is_file() {
            if let Some(ext) = path.extension() {
                let ext = ext.to_string_lossy().to_lowercase();
                if extensions.contains(&ext.as_str()) {
                    wallpapers.push(path.to_string_lossy().to_string());
                }
            }
        }
    }

    wallpapers.sort();
    Ok(wallpapers)
}

/// Starting index for next/prev: the wallpaper Plasma actually shows, else the
/// cached index, else 0. Mirrors the historical bash scripts exactly.
pub fn anchor_index(files: &[String], state: &Path, plasma: Option<&Path>) -> usize {
    let mut index: Option<usize> = None;
    if let Some(config) = plasma {
        if let Some(current) = plasma_wallpaper_from(config) {
            index = files.iter().position(|f| f == &current);
        }
    }
    if index.is_none() {
        index = fs::read_to_string(state)
            .ok()
            .and_then(|s| s.trim().parse::<usize>().ok());
    }
    index.unwrap_or(0)
}

/// Write the cached index (`mkdir -p` + `echo > state`).
pub fn write_cache_index(state: &Path, index: usize) -> Result<()> {
    if let Some(parent) = state.parent() {
        fs::create_dir_all(parent)?;
    }
    fs::write(state, format!("{index}\n"))?;
    Ok(())
}

/// Set wallpaper
pub fn set_wallpaper(path: &str) -> Result<()> {
    let path = Path::new(path);
    if !path.exists() {
        return Err(anyhow::anyhow!("Wallpaper file not found: {}", path.display()));
    }

    let output = Command::new("plasma-apply-wallpaperimage")
        .arg(path)
        .output()
        .context("Failed to run plasma-apply-wallpaperimage")?;

    if !output.status.success() {
        return Err(anyhow::anyhow!("plasma-apply-wallpaperimage failed: {}", 
            String::from_utf8_lossy(&output.stderr)));
    }

    Ok(())
}