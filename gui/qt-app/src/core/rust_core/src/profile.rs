//! Profile Core Implementation

use std::path::{Path, PathBuf};
use std::fs;
use std::process::Command;
use anyhow::{Result, anyhow};
use dirs;

use crate::paths::{
    active_file, profile_dir as safe_profile_dir, profiles_dir as theme_profiles_dir,
    validate_profile_name,
};
use crate::tracked_apps::component_config_paths;
use crate::types::ProfileInfo;

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

/// List all profiles
pub fn list_profiles() -> Result<Vec<ProfileInfo>> {
    let profiles_dir = theme_profiles_dir();
    if !profiles_dir.exists() {
        return Ok(vec![]);
    }

    let active = get_active_profile().unwrap_or_default();
    let mut profiles = Vec::new();

    for entry in fs::read_dir(&profiles_dir)? {
        let entry = entry?;
        let name = entry.file_name().to_string_lossy().to_string();
        
        if entry.file_type()?.is_dir() {
            if validate_profile_name(&name).is_err() {
                continue;
            }
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
        let name = content.trim();
        if validate_profile_name(name).is_ok() {
            Ok(name.to_string())
        } else {
            Ok(String::new())
        }
    } else {
        Ok(String::new())
    }
}

/// Get components in a profile
///
/// A profile directory mirrors the real layout (`<profile>/.config/kwinrc`, …),
/// so components are detected through the same tracked-app registry the Python
/// core uses — joining the bare component id to the profile root would look for
/// `<profile>/kwin` and find nothing.
pub fn get_profile_components(profile_name: &str) -> Result<Vec<String>> {
    let profile_dir = safe_profile_dir(profile_name)?;
    if !profile_dir.exists() {
        return Ok(vec![]);
    }

    let mut components = Vec::new();
    for (id, config_paths) in component_config_paths() {
        if config_paths
            .iter()
            .any(|rel_path| profile_dir.join(rel_path).exists())
        {
            components.push(id);
        }
    }
    Ok(components)
}

/// Get profile creation timestamp (manifest only, like the Bash core)
fn get_profile_created_at(profile_path: &Path) -> Result<String> {
    let manifest = profile_path.join("manifest.txt");
    if manifest.exists() {
        let content = fs::read_to_string(&manifest)?;
        for line in content.lines() {
            if let Some(stamp) = line.strip_prefix("timestamp=") {
                return Ok(stamp.to_string());
            }
            if line.starts_with('[') {
                break;
            }
        }
    }
    Ok(String::new())
}

/// Path of the `theme-profile` bash script
///
/// The script owns every mutation: it knows the component→config-path mapping,
/// writes backups and reloads KWin/kitty. Re-implementing that in Rust (as this
/// crate used to) copied profile entries to `~/<component>` — i.e. `kwinrc`
/// into `~/kwin` — and restarted plasmashell on every apply.
fn theme_profile_bin() -> PathBuf {
    if let Ok(found) = which::which("theme-profile") {
        return found;
    }
    let fallback = dirs::home_dir()
        .unwrap_or_else(|| PathBuf::from("."))
        .join(".local/bin/theme-profile");
    if fallback.exists() {
        return fallback;
    }
    PathBuf::from("theme-profile")
}

/// Run the `theme-profile` script and return its stdout
fn run_theme_profile(args: &[&str]) -> Result<String> {
    let output = Command::new(theme_profile_bin())
        .args(args)
        .output()
        .map_err(|e| anyhow!("Failed to run theme-profile: {}", e))?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr).trim().to_string();
        let stdout = String::from_utf8_lossy(&output.stdout).trim().to_string();
        return Err(anyhow!(
            "{}",
            if stderr.is_empty() { stdout } else { stderr }
        ));
    }
    Ok(String::from_utf8_lossy(&output.stdout).trim().to_string())
}

/// Apply a profile (delegates to the `theme-profile` script)
fn component_arg(components: Option<Vec<String>>) -> Result<Option<String>> {
    match components {
        None => Ok(None),
        Some(comps) => {
            if comps.is_empty() {
                return Err(anyhow!("Select at least one component"));
            }
            let known = component_config_paths();
            let mut cleaned: Vec<String> = Vec::new();
            for component in comps {
                if component.is_empty()
                    || component.contains(',')
                    || component.contains('=')
                    || component.contains('\n')
                {
                    return Err(anyhow!("Invalid component id: {component:?}"));
                }
                if !known.iter().any(|(id, _)| id == &component) {
                    return Err(anyhow!("Unknown component: {component}"));
                }
                if !cleaned.contains(&component) {
                    cleaned.push(component);
                }
            }
            if cleaned.is_empty() {
                return Err(anyhow!("Select at least one component"));
            }
            Ok(Some(format!("--components={}", cleaned.join(","))))
        }
    }
}

pub fn apply_profile(profile_name: &str, components: Option<Vec<String>>) -> Result<()> {
    validate_profile_name(profile_name)?;
    let profile_dir = safe_profile_dir(profile_name)?;
    if !profile_dir.exists() {
        return Err(anyhow!("Profile not found: {}", profile_name));
    }

    let component_arg = component_arg(components)?;
    let mut args = vec!["apply", profile_name];
    if let Some(component_arg) = component_arg.as_deref() {
        args.push(component_arg);
    }

    run_theme_profile(&args).map(|_| ())
}

/// Save current state as a profile (delegates to the `theme-profile` script)
pub fn save_profile(profile_name: &str, components: Option<Vec<String>>) -> Result<()> {
    validate_profile_name(profile_name)?;
    let component_arg = component_arg(components)?;
    let mut args = vec!["save", profile_name];
    if let Some(component_arg) = component_arg.as_deref() {
        args.push(component_arg);
    }

    run_theme_profile(&args).map(|_| ())
}

/// Delete a profile and clear the active marker when it pointed at it.
pub fn delete_profile(profile_name: &str) -> Result<()> {
    let profile_dir = safe_profile_dir(profile_name)?;
    if !profile_dir.exists() && !profile_dir.is_symlink() {
        return Err(anyhow!("Profile not found: {}", profile_name));
    }
    if profile_dir.is_symlink() || !profile_dir.is_dir() {
        fs::remove_file(&profile_dir)?;
    } else {
        fs::remove_dir_all(&profile_dir)?;
    }
    let marker = active_file();
    if let Ok(active) = fs::read_to_string(&marker) {
        if active.trim() == profile_name {
            let _ = fs::remove_file(&marker);
        }
    }
    Ok(())
}

/// Diff two profiles (delegates to the `theme-profile` script)
pub fn diff_profiles(profile_a: &str, profile_b: &str) -> Result<String> {
    validate_profile_name(profile_a)?;
    validate_profile_name(profile_b)?;
    run_theme_profile(&["diff", profile_a, profile_b])
}
