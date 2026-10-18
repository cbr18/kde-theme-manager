//! Common Types - Shared data structures across the crate

use std::collections::HashMap;
use serde::{Deserialize, Serialize};
use std::path::PathBuf;

/// Application status
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum AppStatus {
    Available,
    NotInstalled,
    Partial,
}

/// Component/Application definition
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Component {
    pub id: String,
    pub name: String,
    pub category: String,
    pub config_paths: Vec<PathBuf>,
    pub status: AppStatus,
    pub supports_live_reload: bool,
    pub description: String,
    pub icon: String,
    pub docs_url: String,
}

/// Profile information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProfileInfo {
    pub name: String,
    pub is_active: bool,
    pub components: Vec<String>,
    pub created_at: String,
    pub description: String,
    pub wallpaper_path: String,
}

/// Application settings
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppSettings {
    pub default_components_mode: String,
    pub custom_components: Vec<String>,
    pub wallpaper_linked_to_profile: bool,
    pub wallpaper_directory: String,
    pub theme: String,
    pub show_not_installed_warning: bool,
    pub auto_apply_on_startup: bool,
    pub minimize_to_tray: bool,
    pub global_hotkey: String,
    pub confirm_before_apply: bool,
    pub create_backup_before_apply: bool,
    pub notify_on_success: bool,
}

impl Default for AppSettings {
    fn default() -> Self {
        Self {
            default_components_mode: "all".to_string(),
            custom_components: vec![],
            wallpaper_linked_to_profile: false,
            wallpaper_directory: "~/Изображения/Wallpaper".to_string(),
            theme: "system".to_string(),
            show_not_installed_warning: true,
            auto_apply_on_startup: false,
            minimize_to_tray: false,
            global_hotkey: "".to_string(),
            confirm_before_apply: true,
            create_backup_before_apply: true,
            notify_on_success: true,
        }
    }
}

/// Result of an operation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OperationResult {
    pub success: bool,
    pub message: String,
    pub data: Option<serde_json::Value>,
}

impl OperationResult {
    pub fn ok(message: String) -> Self {
        Self { success: true, message, data: None }
    }

    pub fn err(message: String) -> Self {
        Self { success: false, message, data: None }
    }
}