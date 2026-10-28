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

/// Cache thumbnails and the wofi CSS live under the XDG cache/config dirs.
const PICKER_THUMB_DIR: &str = "wallpaper-picker";
const PICKER_STYLE: &str = "wofi/wallpaper.css";

const THUMB_WIDTH: &str = "420";
const THUMB_HEIGHT: &str = "260";
const THUMB_RADIUS: u32 = 18;
const THUMB_VERSION: &str = "rounded-v1";

/// Deterministic 64-bit FNV-1a (cache keys don't leave the machine).
fn fnv1a64(input: &[u8]) -> u64 {
    let mut hash: u64 = 0xcbf2_9ce4_8422_2325;
    for &b in input {
        hash ^= u64::from(b);
        hash = hash.wrapping_mul(0x1000_0000_01b3);
    }
    hash
}

fn thumb_path(thumb_dir: &Path, file: &str) -> PathBuf {
    let mut key = file.as_bytes().to_vec();
    key.push(0);
    key.extend_from_slice(THUMB_VERSION.as_bytes());
    let hash = fnv1a64(&key);
    thumb_dir.join(format!("{hash:016x}.png"))
}

fn file_newer_than(file: &str, thumb: &Path) -> bool {
    let file_mtime = fs::metadata(file).and_then(|m| m.modified()).ok();
    let thumb_mtime = fs::metadata(thumb).and_then(|m| m.modified()).ok();
    match (file_mtime, thumb_mtime) {
        (Some(f), Some(t)) => f > t,
        _ => true,
    }
}

/// Generate a rounded-corner thumbnail with ImageMagick (best effort).
fn make_thumb(file: &str, thumb: &Path) -> bool {
    let width: u32 = THUMB_WIDTH.parse().unwrap_or(0);
    let height: u32 = THUMB_HEIGHT.parse().unwrap_or(0);
    let status = Command::new("magick")
        .arg(file)
        .args(["-thumbnail", &format!("{THUMB_WIDTH}x{THUMB_HEIGHT}^")])
        .args(["-gravity", "center"])
        .args(["-extent", &format!("{THUMB_WIDTH}x{THUMB_HEIGHT}")])
        .arg("(")
        .args(["-size", &format!("{THUMB_WIDTH}x{THUMB_HEIGHT}"), "xc:none"])
        .args(["-fill", "white"])
        .arg("-draw")
        .arg(format!(
            "roundrectangle 0,0,{},{},{},{}",
            width.saturating_sub(1),
            height.saturating_sub(1),
            THUMB_RADIUS,
            THUMB_RADIUS
        ))
        .arg(")")
        .args(["-alpha", "set", "-compose", "DstIn", "-composite", thumb.to_string_lossy().as_ref()])
        .stdout(std::process::Stdio::null())
        .stderr(std::process::Stdio::null())
        .status();
    status.map(|s| s.success()).unwrap_or(false)
}

/// Outcome of the interactive picker.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum PickOutcome {
    /// wofi was cancelled (empty selection) — nothing to do.
    Cancelled,
    /// A wallpaper was chosen (its full-list index is already cached).
    Selected(String),
}

/// Full picker flow: thumbnails -> wofi grid -> cache the selection.
///
/// Shared by the library (FFI `kde_theme_core_wallpaper_pick`) and the CLI
/// binary (`theme-profile`/`wallpaper-picker`), so there is exactly one
/// implementation of the picker logic.
pub fn pick_wallpaper_flow(
    dir: &Path,
    state: &Path,
    thumb_dir: &Path,
    style: &Path,
) -> Result<PickOutcome> {
    let files = list_wallpapers_in(dir)?;
    if files.is_empty() {
        return Err(anyhow::anyhow!("No wallpapers found"));
    }

    fs::create_dir_all(thumb_dir)?;

    let mut entries = String::new();
    let mut displayed: Vec<String> = Vec::new();

    for file in &files {
        let name = Path::new(file)
            .file_name()
            .map(|n| n.to_string_lossy().to_string())
            .unwrap_or_else(|| file.clone());
        let thumb = thumb_path(thumb_dir, file);
        if (!thumb.is_file() || file_newer_than(file, &thumb)) && !make_thumb(file, &thumb) {
            let _ = fs::remove_file(&thumb);
            continue;
        }
        displayed.push(file.clone());
        entries.push_str(&format!("img:{}:text:{}\n", thumb.display(), name));
    }

    if displayed.is_empty() {
        return Err(anyhow::anyhow!("No displayable wallpapers"));
    }

    let mut wofi = Command::new("wofi")
        .args([
            "--dmenu",
            "--allow-images",
            "--insensitive",
            "--width",
            "40%",
            "--height",
            "60%",
            "--columns",
            "4",
            "--define",
            "image_size=210",
            "--define",
            "content_halign=center",
            "--define",
            "dmenu-print_line_num=true",
            "--style",
            style.to_string_lossy().as_ref(),
        ])
        .stdin(std::process::Stdio::piped())
        .stdout(std::process::Stdio::piped())
        .spawn()
        .context("could not start wofi")?;

    if let Some(mut stdin) = wofi.stdin.take() {
        use std::io::Write;
        let _ = stdin.write_all(entries.as_bytes());
    }

    let output = wofi.wait_with_output()?;
    let selection = String::from_utf8_lossy(&output.stdout).trim().to_string();
    if selection.is_empty() {
        return Ok(PickOutcome::Cancelled);
    }
    if !selection.bytes().all(|b| b.is_ascii_digit()) {
        // A typed custom entry is not a position.
        return Err(anyhow::anyhow!("Invalid selection: not a position"));
    }
    let index: usize = selection.parse().map_err(|_| anyhow::anyhow!("Invalid selection"))?;
    let Some(selected) = displayed.get(index) else {
        return Err(anyhow::anyhow!("Selection out of range"));
    };

    // Cache the position in the FULL enumeration (the displayed list can be a
    // subset when a thumbnail failed to render).
    if let Some(full_index) = files.iter().position(|f| f == selected) {
        write_cache_index(state, full_index)?;
    }

    Ok(PickOutcome::Selected(selected.clone()))
}

/// Pick wallpaper using wofi (native — thumbnails + grid are implemented here
/// and shared with the CLI binary; no subprocess to `wallpaper-picker`).
pub fn pick_wallpaper() -> Result<String> {
    let dir = wallpaper_dir();
    let state = cache_index();
    let thumb_dir = crate::paths::cache_home().join(PICKER_THUMB_DIR);
    let style = crate::paths::config_home().join(PICKER_STYLE);

    match pick_wallpaper_flow(&dir, &state, &thumb_dir, &style)? {
        PickOutcome::Selected(path) => {
            set_wallpaper(&path)?;
            Ok(path)
        }
        PickOutcome::Cancelled => Err(anyhow::anyhow!("wallpaper picker cancelled")),
    }
}

/// Step the wallpaper index relative to the anchor (Plasma's current file,
/// else the cached index, else 0) and persist the new position.
pub fn step_index(
    files: &[String],
    state: &Path,
    plasma: Option<&Path>,
    delta: i64,
) -> Result<usize> {
    let len = files.len();
    if len == 0 {
        return Err(anyhow::anyhow!("No wallpapers found"));
    }
    let anchor = anchor_index(files, state, plasma);
    let index = ((anchor as i64 + delta).rem_euclid(len as i64)) as usize;
    write_cache_index(state, index)?;
    Ok(index)
}

fn plasma_default_config() -> PathBuf {
    dirs::config_dir()
        .unwrap_or_else(|| PathBuf::from(".config"))
        .join("plasma-org.kde.plasma.desktop-appletsrc")
}

/// Next wallpaper (native — no subprocess to `wallpaper-next`).
pub fn next_wallpaper() -> Result<()> {
    let files = list_wallpapers_in(&wallpaper_dir())?;
    let index = step_index(&files, &cache_index(), Some(&plasma_default_config()), 1)?;
    set_wallpaper(&files[index])
}

/// Previous wallpaper (native — no subprocess to `wallpaper-prev`).
pub fn prev_wallpaper() -> Result<()> {
    let files = list_wallpapers_in(&wallpaper_dir())?;
    let index = step_index(&files, &cache_index(), Some(&plasma_default_config()), -1)?;
    set_wallpaper(&files[index])
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