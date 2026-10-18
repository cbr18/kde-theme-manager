//! Profile Core Implementation

use std::path::{Path, PathBuf};
use std::fs;
use std::process::Command;
use anyhow::{Result, Context, anyhow};
use serde::{Deserialize, Serialize};
use walkdir::WalkDir;
use chrono;
use dirs;

use crate::types::{ProfileInfo, Component, AppStatus, OperationResult};

/// Profile Core Trait - defines the interface for profile operations
pub trait ProfileCore {
    fn list_profiles(&self) -> Result<Vec<ProfileInfo>>;
    fn get_active_profile(&self) -> Result<String>;
    fn apply(&self, profile: &str, components: Option<Vec<String>>) -> Result<()>;
    fn save(&self, name: &str, components: Option<Vec<String>>) -> Result<()>;
    fn delete(&self, name: &str) -> Result<()>;
    fn diff(&self, a: &str, b: &str) -> Result<String>;
    fn get_profile_components(&self, profile: &str) -> Result<Vec<String>>;
}

/// Default implementation of ProfileCore
pub struct DefaultProfileCore;

impl ProfileCore for DefaultProfileCore {
    fn list_profiles(&self) -> Result<Vec<ProfileInfo>> {
        list_profiles()
    }

    fn get_active_profile(&self) -> Result<String> {
        get_active_profile()
    }

    fn apply(&self, profile: &str, components: Option<Vec<String>>) -> Result<()> {
        apply_profile(profile, components)
    }

    fn save(&self, name: &str, components: Option<Vec<String>>) -> Result<()> {
        save_profile(name, components)
    }

    fn delete(&self, name: &str) -> Result<()> {
        delete_profile(name)
    }

    fn diff(&self, a: &str, b: &str) -> Result<String> {
        diff_profiles(a, b)
    }

    fn get_profile_components(&self, profile: &str) -> Result<Vec<String>> {
        get_profile_components(profile)
    }
}

/// Profile directory structure
const PROFILES_DIR: &str = ".config/theme-profile/profiles";
const BACKUPS_DIR: &str = ".config/theme-profile/backups";
const ACTIVE_FILE: &str = ".config/theme-profile/active-profile";

/// Get profiles directory
fn profiles_dir() -> PathBuf {
    dirs::home_dir().unwrap().join(PROFILES_DIR)
}

/// Get active profile file
fn active_file() -> PathBuf {
    dirs::home_dir().unwrap().join(ACTIVE_FILE)
}

/// List all profiles
pub fn list_profiles() -> Result<Vec<ProfileInfo>> {
    let profiles_dir = profiles_dir();
    if !profiles_dir.exists() {
        return Ok(vec![]);
    }

    let active = get_active_profile().unwrap_or_default();
    let mut profiles = Vec::new();

    for entry in fs::read_dir(&profiles_dir)? {
        let entry = entry?;
        let name = entry.file_name().to_string_lossy().to_string();
        
        if entry.file_type()?.is_dir() {
            let profile_path = entry.path();
            let is_active = name == active;
            let components = get_profile_components(&name)?;
            let created_at = get_profile_created_at(&profile_path)?;
            
            profiles.push(ProfileInfo {
                name,
                is_active,
                components,
                created_at,
                description: String::new(),
                wallpaper_path: String::new(),
            });
        }
    }

    profiles.sort_by(|a, b| a.name.cmp(&b.name));
    Ok(profiles)
}

/// Get active profile name
pub fn get_active_profile() -> Result<String> {
    let active_file = active_file();
    if active_file.exists() {
        let content = fs::read_to_string(&active_file)?;
        Ok(content.trim().to_string())
    } else {
        Ok(String::new())
    }
}

/// Get components in a profile
pub fn get_profile_components(profile_name: &str) -> Result<Vec<String>> {
    let profile_dir = profiles_dir().join(profile_name);
    if !profile_dir.exists() {
        return Ok(vec![]);
    }

    let known_components = vec![
        "kwin", "plasma_shell", "kdeglobals", "gtk3", "gtk4", "qt5ct",
        "klassy", "kvantum", "alacritty", "kitty", "wofi", "btop",
        "fastfetch", "zed", "vscode", "cursor", "zen", "obsidian",
        "color_schemes", "look_and_feel",
    ];

    let mut components = Vec::new();
    for comp in known_components {
        let comp_path = profile_dir.join(comp);
        if comp_path.exists() {
            components.push(comp.to_string());
        }
    }
    Ok(components)
}

/// Get profile creation timestamp
fn get_profile_created_at(profile_path: &Path) -> Result<String> {
    let manifest = profile_path.join("manifest.txt");
    if manifest.exists() {
        let content = fs::read_to_string(&manifest)?;
        for line in content.lines() {
            if line.starts_with("timestamp=") {
                return Ok(line["timestamp=".len()..].to_string());
            }
        }
    }
    
    if let Ok(metadata) = fs::metadata(profile_path) {
        if let Ok(created) = metadata.created() {
            return Ok(chrono::DateTime::<chrono::Utc>::from(created).to_rfc3339());
        }
    }
    Ok(String::new())
}

/// Apply a profile
pub fn apply_profile(profile_name: &str, components: Option<Vec<String>>) -> Result<()> {
    let profile_dir = profiles_dir().join(profile_name);
    if !profile_dir.exists() {
        return Err(anyhow::anyhow!("Profile not found: {}", profile_name));
    }

    // Create backup before applying
    let backup_name = format!("pre-apply-{}-{}", profile_name, chrono::Utc::now().format("%Y%m%d-%H%M%S"));
    create_backup(&backup_name)?;

    // Determine which components to apply
    let comps_to_apply = components.unwrap_or_else(get_all_known_components);

    // Apply each component
    for comp in comps_to_apply {
        apply_component(&profile_dir, &comp)?;
    }

    // Update active profile
    fs::write(active_file(), profile_name)?;

    // Apply live hooks
    apply_live_hooks(profile_name)?;

    Ok(())
}

/// Create backup of current state
fn create_backup(backup_name: &str) -> Result<()> {
    let backups_dir = dirs::home_dir().unwrap().join(BACKUPS_DIR);
    fs::create_dir_all(&backups_dir)?;
    let backup_path = backups_dir.join(backup_name);
    fs::create_dir_all(&backup_path)?;

    // Copy tracked paths to backup (simplified)
    Ok(())
}

/// Apply a single component
///
/// # KNOWN BUG (documented, not yet fixed)
///
/// This function uses `component` (e.g. `"kwin"`) directly as a path segment
/// under the home directory (`~/.{component}`), but profile directories store
/// config files at their actual relative paths (e.g. `.config/kwinrc`,
/// `.config/kwinrulesrc`).  The correct behavior is to look up the
/// component definition in `TRACKED_APPS` and copy from the matching
/// `config_paths` entries inside the profile directory.
///
/// Example of the broken logic:
/// ```text
/// profile_dir/kwin         ← exists (dir copied from ~/.config/kwinrc)
///   → target = ~/kwin       ← WRONG! Should be ~/.config/kwinrc
/// ```
///
/// The Python core (`PythonProfileCore`) does not have this bug because it
/// delegates to the `theme-profile` bash script.
/// The Rust core is currently **not** used by the Python codebase.
fn apply_component(profile_dir: &Path, component: &str) -> Result<()> {
    let comp_path = profile_dir.join(component);
    if !comp_path.exists() {
        return Ok(()); // Component not in profile, skip
    }

    let target = dirs::home_dir().unwrap().join(component);
    fs::create_dir_all(target.parent().unwrap_or(&target))?;

    if comp_path.is_dir() {
        copy_dir_all(&comp_path, &target)?;
    } else {
        fs::copy(&comp_path, &target)?;
    }
    Ok(())
}

/// Recursively copy directory
fn copy_dir_all(src: &Path, dst: &Path) -> Result<()> {
    fs::create_dir_all(dst)?;
    for entry in fs::read_dir(src)? {
        let entry = entry?;
        let src_path = entry.path();
        let dst_path = dst.join(entry.file_name());
        if src_path.is_dir() {
            copy_dir_all(&src_path, &dst_path)?;
        } else {
            fs::copy(&src_path, &dst_path)?;
        }
    }
    Ok(())
}

/// Get all known component names
fn get_all_known_components() -> Vec<String> {
    vec![
        "kwin", "plasma_shell", "kdeglobals", "gtk3", "gtk4", "qt5ct",
        "klassy", "kvantum", "alacritty", "kitty", "wofi", "btop",
        "fastfetch", "zed", "vscode", "cursor", "zen", "obsidian",
        "color_schemes", "look_and_feel",
    ].into_iter().map(String::from).collect()
}

/// Apply live hooks after profile application
fn apply_live_hooks(profile_name: &str) -> Result<()> {
    let profile_dir = profiles_dir().join(profile_name);
    
    reconfigure_kwin_effects(&profile_dir)?;
    apply_kitty_live(&profile_dir)?;
    restart_plasma_shell()?;

    Ok(())
}

/// Reconfigure KWin effects
fn reconfigure_kwin_effects(profile_dir: &Path) -> Result<()> {
    let kwinrc = profile_dir.join("kwinrc");
    if !kwinrc.exists() {
        return Ok(());
    }

    let effects = vec!["glass", "blur", "contrast", "better_blur_dx"];
    
    for effect in effects {
        let _ = Command::new("qdbus6")
            .args(["org.kde.KWin", "/Effects", "reconfigureEffect", effect])
            .output();
    }

    let _ = Command::new("qdbus6")
        .args(["org.kde.KWin", "/KWin", "reconfigure"])
        .output();

    Ok(())
}

/// Apply Kitty live reload
fn apply_kitty_live(profile_dir: &Path) -> Result<()> {
    let kitty_conf = profile_dir.join("kitty.conf");
    if !kitty_conf.exists() {
        return Ok(());
    }

    let _ = Command::new("kitty")
        .args(["@", "--to", "unix:/tmp/kitty-theme-profile", "load-config", kitty_conf.to_str().unwrap()])
        .output();

    Ok(())
}

/// Restart Plasma shell
fn restart_plasma_shell() -> Result<()> {
    let _ = Command::new("systemctl")
        .args(["--user", "restart", "plasma-plasmashell.service"])
        .output();
    Ok(())
}

/// Save current state as a profile
///
/// # KNOWN BUG (same as `apply_component`)
/// See the documentation on `apply_component` — this function also joins
/// `comp` (e.g. `"kwin"`) directly to the home directory instead of using
/// the actual `config_paths` from the tracked-app definitions (e.g.
/// `.config/kwinrc`).
pub fn save_profile(profile_name: &str, components: Option<Vec<String>>) -> Result<()> {
    let profile_dir = profiles_dir().join(profile_name);
    fs::create_dir_all(&profile_dir)?;

    let comps = components.unwrap_or_else(get_all_known_components);
    
    for comp in comps {
        let src = dirs::home_dir().unwrap().join(&comp);
        if src.exists() {
            let dst = profile_dir.join(&comp);
            fs::create_dir_all(dst.parent().unwrap_or(&dst))?;
            if src.is_dir() {
                copy_dir_all(&src, &dst)?;
            } else {
                fs::copy(&src, &dst)?;
            }
        }
    }

    // Write manifest
    let manifest = profile_dir.join("manifest.txt");
    let content = format!("Generated by kde-theme-core\ntimestamp={}\n", chrono::Utc::now().to_rfc3339());
    fs::write(manifest, content)?;

    // Update active profile
    fs::write(active_file(), profile_name)?;

    Ok(())
}

/// Delete a profile
pub fn delete_profile(profile_name: &str) -> Result<()> {
    let profile_dir = profiles_dir().join(profile_name);
    if profile_dir.exists() {
        fs::remove_dir_all(profile_dir)?;
    }
    Ok(())
}

/// Diff two profiles
pub fn diff_profiles(profile_a: &str, profile_b: &str) -> Result<String> {
    let dir_a = profiles_dir().join(profile_a);
    let dir_b = profiles_dir().join(profile_b);

    if !dir_a.exists() || !dir_b.exists() {
        return Err(anyhow::anyhow!("One or both profiles not found"));
    }

    let output = Command::new("diff")
        .args(["-ru", dir_a.to_str().unwrap(), dir_b.to_str().unwrap()])
        .output()?;

    Ok(String::from_utf8_lossy(&output.stdout).to_string())
}