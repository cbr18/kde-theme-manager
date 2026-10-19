/// Settings Core Implementation

use std::path::PathBuf;
use std::fs;
use anyhow::Result;
use dirs;

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
    dirs::home_dir().unwrap().join(".config/theme-profile/app-preferences.json")
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

/// Save settings
pub fn save_settings(settings: AppSettings) -> Result<()> {
    let file = settings_file();
    if let Some(parent) = file.parent() {
        fs::create_dir_all(parent)?;
    }
    let content = serde_json::to_string_pretty(&settings)?;
    fs::write(&file, content)?;
    Ok(())
}

/// Get default settings
pub fn get_defaults() -> AppSettings {
    AppSettings::default()
}