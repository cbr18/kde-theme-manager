//! Settings Core Implementation

use std::fs::{self, DirBuilder, OpenOptions};
use std::io::Write;
use std::os::unix::fs::{DirBuilderExt, OpenOptionsExt, PermissionsExt};
use std::path::PathBuf;

use anyhow::Result;

use crate::paths::settings_file as theme_settings_file;

pub use crate::types::{AppSettings, OperationResult};

/// Settings Core Trait
pub trait SettingsCore {
    fn load(&self) -> Result<AppSettings>;
    fn save(&self, settings: AppSettings) -> Result<()>;
    fn get_defaults(&self) -> AppSettings;
}

/// Default implementation
pub struct DefaultSettingsCore;

impl SettingsCore for DefaultSettingsCore {
    fn load(&self) -> Result<AppSettings> {
        load_settings()
    }

    fn save(&self, settings: AppSettings) -> Result<()> {
        save_settings(settings)
    }

    fn get_defaults(&self) -> AppSettings {
        get_defaults()
    }
}

/// Settings file path
fn settings_file() -> PathBuf {
    theme_settings_file()
}

/// Load settings
pub fn load_settings() -> Result<AppSettings> {
    let file = settings_file();
    if file.exists() {
        let content = fs::read_to_string(&file)?;
        let settings: AppSettings = serde_json::from_str(&content)?;
        Ok(settings)
    } else {
        Ok(get_defaults())
    }
}

/// Save settings atomically without widening permissions.
pub fn save_settings(settings: AppSettings) -> Result<()> {
    let file = settings_file();
    if let Some(parent) = file.parent() {
        let mut builder = DirBuilder::new();
        builder.recursive(true).mode(0o700);
        builder.create(parent)?;
    }

    let mode = fs::metadata(&file)
        .map(|m| m.permissions().mode() & 0o777)
        .unwrap_or(0o600);
    let content = serde_json::to_string_pretty(&settings)? + "\n";
    let tmp = file.with_extension("json.ktm-tmp");

    let mut handle = OpenOptions::new()
        .write(true)
        .create(true)
        .truncate(true)
        .mode(mode)
        .open(&tmp)?;
    handle.write_all(content.as_bytes())?;
    handle.sync_all()?;
    fs::set_permissions(&tmp, fs::Permissions::from_mode(mode))?;
    fs::rename(&tmp, &file)?;
    Ok(())
}

/// Get default settings
pub fn get_defaults() -> AppSettings {
    AppSettings::default()
}
