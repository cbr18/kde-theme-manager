//! Wallpaper Core Implementation

use std::path::{Path, PathBuf};
use std::fs;
use std::process::Command;
use anyhow::{Result, Context};
use dirs;

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

/// Get wallpaper directory
fn wallpaper_dir() -> PathBuf {
    dirs::home_dir().unwrap().join("Изображения/Wallpaper")
}

/// Get cache index file
fn cache_index() -> PathBuf {
    dirs::cache_dir().unwrap().join("wallpaper_index")
}

/// Pick wallpaper using wofi
pub fn pick_wallpaper() -> Result<String> {
    let wallpapers = list_wallpapers()?;
    if wallpapers.is_empty() {
        return Err(anyhow::anyhow!("No wallpapers found"));
    }

    let output = Command::new("wallpaper-picker")
        .output()
        .context("Failed to run wallpaper-picker")?;

    if !output.status.success() {
        return Err(anyhow::anyhow!("wallpaper-picker cancelled or failed"));
    }

    current_wallpaper()
}

/// Next wallpaper
pub fn next_wallpaper() -> Result<()> {
    let output = Command::new("wallpaper-next")
        .output()
        .context("Failed to run wallpaper-next")?;

    if !output.status.success() {
        return Err(anyhow::anyhow!("wallpaper-next failed"));
    }
    Ok(())
}

/// Previous wallpaper
pub fn prev_wallpaper() -> Result<()> {
    let output = Command::new("wallpaper-prev")
        .output()
        .context("Failed to run wallpaper-prev")?;

    if !output.status.success() {
        return Err(anyhow::anyhow!("wallpaper-prev failed"));
    }
    Ok(())
}

/// Get current wallpaper
pub fn current_wallpaper() -> Result<String> {
    let cache_index = dirs::cache_dir().unwrap().join("wallpaper_index");
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
/// The order and the accepted extensions must match the bash scripts
/// (files/bin/wallpaper-{picker,next,prev}) and the Python core: the cached
/// index is a position in this list. `is_file()` follows symlinks (like
/// `find -L`), extensions are compared case-insensitively (like
/// `find -iname`), and `sort()` on String is byte order (like `LC_ALL=C sort`).
pub fn list_wallpapers() -> Result<Vec<String>> {
    let dir = dirs::home_dir().unwrap().join("Изображения/Wallpaper");
    if !dir.exists() {
        return Ok(vec![]);
    }

    let mut wallpapers = Vec::new();
    let extensions = ["jpg", "jpeg", "png", "webp", "bmp"];

    for entry in fs::read_dir(&dir)? {
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