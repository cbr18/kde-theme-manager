//! KDE Theme Profile Manager - Rust Core Library
//!
//! Provides native Rust implementation of the theme management protocol
//! with FFI interface for Python integration.

#![allow(non_snake_case)]

pub mod types;
pub mod ffi;
pub mod profile;
pub mod wallpaper;
pub mod tracked_apps;
pub mod settings;
pub mod config_parser;

use std::ffi::{CStr, CString};
use std::os::raw::{c_char, c_int};
use std::ptr;
use std::sync::Mutex;

use tracing::info;

#[cfg(test)]
mod tests;

// Re-export main types
pub use types::{
    AppStatus, Component, ProfileInfo, AppSettings, OperationResult,
};
pub use profile::ProfileCore;
pub use wallpaper::WallpaperCore;
pub use tracked_apps::TrackedAppsCore;
pub use settings::SettingsCore;

// Global error message storage for FFI
static LAST_ERROR: Mutex<Option<String>> = Mutex::new(None);

fn set_last_error(err: String) {
    if let Ok(mut guard) = LAST_ERROR.lock() {
        *guard = Some(err);
    }
}

fn take_last_error() -> Option<String> {
    if let Ok(mut guard) = LAST_ERROR.lock() {
        guard.take()
    } else {
        None
    }
}

/// Initialize the Rust core library
#[no_mangle]
pub extern "C" fn kde_theme_core_init() -> c_int {
    // Initialize tracing subscriber for logging
    let _ = tracing_subscriber::fmt()
        .with_env_filter(tracing_subscriber::EnvFilter::from_default_env())
        .try_init();
    
    info!("KDE Theme Core initialized");
    0 // Success
}

/// Get the last error message
#[no_mangle]
pub extern "C" fn kde_theme_core_get_error() -> *const c_char {
    if let Some(err) = take_last_error() {
        match CString::new(err) {
            Ok(c_str) => c_str.into_raw(),
            Err(_) => ptr::null(),
        }
    } else {
        ptr::null()
    }
}

/// Free a string returned by FFI functions
#[no_mangle]
pub extern "C" fn kde_theme_core_free_string(ptr: *mut c_char) {
    if !ptr.is_null() {
        unsafe {
            drop(CString::from_raw(ptr));
        }
    }
}

/// FFI wrapper for ProfileCore
#[no_mangle]
pub extern "C" fn kde_theme_core_profile_list() -> *mut c_char {
    match profile::list_profiles() {
        Ok(profiles) => {
            match serde_json::to_string(&profiles) {
                Ok(json) => match CString::new(json) {
                    Ok(c_str) => c_str.into_raw(),
                    Err(e) => {
                        set_last_error(e.to_string());
                        ptr::null_mut()
                    }
                }
                Err(e) => {
                    set_last_error(e.to_string());
                    ptr::null_mut()
                }
            }
        }
        Err(e) => {
            set_last_error(e.to_string());
            ptr::null_mut()
        }
    }
}

/// FFI wrapper for getting active profile
#[no_mangle]
pub extern "C" fn kde_theme_core_profile_get_active() -> *mut c_char {
    match profile::get_active_profile() {
        Ok(active) => match CString::new(active) {
            Ok(c_str) => c_str.into_raw(),
            Err(e) => {
                set_last_error(e.to_string());
                ptr::null_mut()
            }
        }
        Err(e) => {
            set_last_error(e.to_string());
            ptr::null_mut()
        }
    }
}

/// FFI wrapper for applying a profile
#[no_mangle]
pub extern "C" fn kde_theme_core_profile_apply(
    profile_name: *const c_char,
    components_json: *const c_char,
) -> c_int {
    let name = match unsafe { CStr::from_ptr(profile_name) }.to_str() {
        Ok(s) => s,
        Err(e) => {
            set_last_error(e.to_string());
            return -1;
        }
    };

    let components = if components_json.is_null() {
        None
    } else {
        match unsafe { CStr::from_ptr(components_json) }.to_str() {
            Ok(s) => match serde_json::from_str(s) {
                Ok(c) => Some(c),
                Err(e) => {
                    set_last_error(e.to_string());
                    return -1;
                }
            }
            Err(e) => {
                set_last_error(e.to_string());
                return -1;
            }
        }
    };

    match profile::apply_profile(name, components) {
        Ok(_) => 0,
        Err(e) => {
            set_last_error(e.to_string());
            -1
        }
    }
}

/// FFI wrapper for saving a profile
#[no_mangle]
pub extern "C" fn kde_theme_core_profile_save(
    profile_name: *const c_char,
    components_json: *const c_char,
) -> c_int {
    let name = match unsafe { CStr::from_ptr(profile_name) }.to_str() {
        Ok(s) => s,
        Err(e) => {
            set_last_error(e.to_string());
            return -1;
        }
    };

    let components = if components_json.is_null() {
        None
    } else {
        match unsafe { CStr::from_ptr(components_json) }.to_str() {
            Ok(s) => match serde_json::from_str(s) {
                Ok(c) => Some(c),
                Err(e) => {
                    set_last_error(e.to_string());
                    return -1;
                }
            }
            Err(e) => {
                set_last_error(e.to_string());
                return -1;
            }
        }
    };

    match profile::save_profile(name, components) {
        Ok(_) => 0,
        Err(e) => {
            set_last_error(e.to_string());
            -1
        }
    }
}

/// FFI wrapper for deleting a profile
#[no_mangle]
pub extern "C" fn kde_theme_core_profile_delete(profile_name: *const c_char) -> c_int {
    let name = match unsafe { CStr::from_ptr(profile_name) }.to_str() {
        Ok(s) => s,
        Err(e) => {
            set_last_error(e.to_string());
            return -1;
        }
    };

    match profile::delete_profile(name) {
        Ok(_) => 0,
        Err(e) => {
            set_last_error(e.to_string());
            -1
        }
    }
}

/// FFI wrapper for profile diff
#[no_mangle]
pub extern "C" fn kde_theme_core_profile_diff(
    profile_a: *const c_char,
    profile_b: *const c_char,
) -> *mut c_char {
    let a = match unsafe { CStr::from_ptr(profile_a) }.to_str() {
        Ok(s) => s,
        Err(e) => {
            set_last_error(e.to_string());
            return ptr::null_mut();
        }
    };
    let b = match unsafe { CStr::from_ptr(profile_b) }.to_str() {
        Ok(s) => s,
        Err(e) => {
            set_last_error(e.to_string());
            return ptr::null_mut();
        }
    };

    match profile::diff_profiles(a, b) {
        Ok(diff) => match CString::new(diff) {
            Ok(c_str) => c_str.into_raw(),
            Err(e) => {
                set_last_error(e.to_string());
                ptr::null_mut()
            }
        }
        Err(e) => {
            set_last_error(e.to_string());
            ptr::null_mut()
        }
    }
}

/// FFI wrapper for getting profile components
#[no_mangle]
pub extern "C" fn kde_theme_core_profile_get_components(
    profile_name: *const c_char,
) -> *mut c_char {
    let name = match unsafe { CStr::from_ptr(profile_name) }.to_str() {
        Ok(s) => s,
        Err(e) => {
            set_last_error(e.to_string());
            return ptr::null_mut();
        }
    };

    match profile::get_profile_components(name) {
        Ok(comps) => match serde_json::to_string(&comps) {
            Ok(json) => match CString::new(json) {
                Ok(c_str) => c_str.into_raw(),
                Err(e) => {
                    set_last_error(e.to_string());
                    ptr::null_mut()
                }
            }
            Err(e) => {
                set_last_error(e.to_string());
                ptr::null_mut()
            }
        }
        Err(e) => {
            set_last_error(e.to_string());
            ptr::null_mut()
        }
    }
}

/// FFI wrapper for WallpaperCore - pick wallpaper
#[no_mangle]
pub extern "C" fn kde_theme_core_wallpaper_pick() -> *mut c_char {
    match wallpaper::pick_wallpaper() {
        Ok(path) => match CString::new(path) {
            Ok(c_str) => c_str.into_raw(),
            Err(e) => {
                set_last_error(e.to_string());
                ptr::null_mut()
            }
        }
        Err(e) => {
            set_last_error(e.to_string());
            ptr::null_mut()
        }
    }
}

/// FFI wrapper for WallpaperCore - next wallpaper
#[no_mangle]
pub extern "C" fn kde_theme_core_wallpaper_next() -> c_int {
    match wallpaper::next_wallpaper() {
        Ok(_) => 0,
        Err(e) => {
            set_last_error(e.to_string());
            -1
        }
    }
}

/// FFI wrapper for WallpaperCore - prev wallpaper
#[no_mangle]
pub extern "C" fn kde_theme_core_wallpaper_prev() -> c_int {
    match wallpaper::prev_wallpaper() {
        Ok(_) => 0,
        Err(e) => {
            set_last_error(e.to_string());
            -1
        }
    }
}

/// FFI wrapper for WallpaperCore - current wallpaper
#[no_mangle]
pub extern "C" fn kde_theme_core_wallpaper_current() -> *mut c_char {
    match wallpaper::current_wallpaper() {
        Ok(path) => match CString::new(path) {
            Ok(c_str) => c_str.into_raw(),
            Err(e) => {
                set_last_error(e.to_string());
                ptr::null_mut()
            }
        }
        Err(e) => {
            set_last_error(e.to_string());
            ptr::null_mut()
        }
    }
}

/// FFI wrapper for WallpaperCore - list wallpapers
#[no_mangle]
pub extern "C" fn kde_theme_core_wallpaper_list() -> *mut c_char {
    match wallpaper::list_wallpapers() {
        Ok(paths) => match serde_json::to_string(&paths) {
            Ok(json) => match CString::new(json) {
                Ok(c_str) => c_str.into_raw(),
                Err(e) => {
                    set_last_error(e.to_string());
                    ptr::null_mut()
                }
            }
            Err(e) => {
                set_last_error(e.to_string());
                ptr::null_mut()
            }
        }
        Err(e) => {
            set_last_error(e.to_string());
            ptr::null_mut()
        }
    }
}

/// FFI wrapper for WallpaperCore - set wallpaper
#[no_mangle]
pub extern "C" fn kde_theme_core_wallpaper_set(path: *const c_char) -> c_int {
    let p = match unsafe { CStr::from_ptr(path) }.to_str() {
        Ok(s) => s,
        Err(e) => {
            set_last_error(e.to_string());
            return -1;
        }
    };

    match wallpaper::set_wallpaper(p) {
        Ok(_) => 0,
        Err(e) => {
            set_last_error(e.to_string());
            -1
        }
    }
}

/// FFI wrapper for WallpaperCore - override the listing directory
///
/// The application reads `wallpaper_directory` from its settings; the Rust core
/// has to be told about it explicitly (empty string resets to the default).
#[no_mangle]
pub extern "C" fn kde_theme_core_wallpaper_set_dir(dir: *const c_char) -> c_int {
    if dir.is_null() {
        wallpaper::set_wallpaper_dir("");
        return 0;
    }

    match unsafe { CStr::from_ptr(dir) }.to_str() {
        Ok(s) => {
            wallpaper::set_wallpaper_dir(s);
            0
        }
        Err(e) => {
            set_last_error(e.to_string());
            -1
        }
    }
}

/// FFI wrapper for TrackedAppsCore - detect all apps
#[no_mangle]
pub extern "C" fn kde_theme_core_apps_detect_all() -> *mut c_char {
    match tracked_apps::detect_all_apps() {
        Ok(apps) => match serde_json::to_string(&apps) {
            Ok(json) => match CString::new(json) {
                Ok(c_str) => c_str.into_raw(),
                Err(e) => {
                    set_last_error(e.to_string());
                    ptr::null_mut()
                }
            }
            Err(e) => {
                set_last_error(e.to_string());
                ptr::null_mut()
            }
        }
        Err(e) => {
            set_last_error(e.to_string());
            ptr::null_mut()
        }
    }
}

/// FFI wrapper for TrackedAppsCore - get categories
#[no_mangle]
pub extern "C" fn kde_theme_core_apps_get_categories() -> *mut c_char {
    match tracked_apps::get_categories() {
        Ok(cats) => match serde_json::to_string(&cats) {
            Ok(json) => match CString::new(json) {
                Ok(c_str) => c_str.into_raw(),
                Err(e) => {
                    set_last_error(e.to_string());
                    ptr::null_mut()
                }
            }
            Err(e) => {
                set_last_error(e.to_string());
                ptr::null_mut()
            }
        }
        Err(e) => {
            set_last_error(e.to_string());
            ptr::null_mut()
        }
    }
}

/// FFI wrapper for TrackedAppsCore - get components by category
#[no_mangle]
pub extern "C" fn kde_theme_core_apps_get_by_category(category: *const c_char) -> *mut c_char {
    let cat = match unsafe { CStr::from_ptr(category) }.to_str() {
        Ok(s) => s,
        Err(e) => {
            set_last_error(e.to_string());
            return ptr::null_mut();
        }
    };

    match tracked_apps::get_components_by_category(cat) {
        Ok(comps) => match serde_json::to_string(&comps) {
            Ok(json) => match CString::new(json) {
                Ok(c_str) => c_str.into_raw(),
                Err(e) => {
                    set_last_error(e.to_string());
                    ptr::null_mut()
                }
            }
            Err(e) => {
                set_last_error(e.to_string());
                ptr::null_mut()
            }
        }
        Err(e) => {
            set_last_error(e.to_string());
            ptr::null_mut()
        }
    }
}

/// FFI wrapper for TrackedAppsCore - get all components
#[no_mangle]
pub extern "C" fn kde_theme_core_apps_get_all() -> *mut c_char {
    match tracked_apps::get_all_components() {
        Ok(comps) => match serde_json::to_string(&comps) {
            Ok(json) => match CString::new(json) {
                Ok(c_str) => c_str.into_raw(),
                Err(e) => {
                    set_last_error(e.to_string());
                    ptr::null_mut()
                }
            }
            Err(e) => {
                set_last_error(e.to_string());
                ptr::null_mut()
            }
        }
        Err(e) => {
            set_last_error(e.to_string());
            ptr::null_mut()
        }
    }
}

/// FFI wrapper for TrackedAppsCore - refresh
#[no_mangle]
pub extern "C" fn kde_theme_core_apps_refresh() -> *mut c_char {
    match tracked_apps::refresh() {
        Ok(apps) => match serde_json::to_string(&apps) {
            Ok(json) => match CString::new(json) {
                Ok(c_str) => c_str.into_raw(),
                Err(e) => {
                    set_last_error(e.to_string());
                    ptr::null_mut()
                }
            }
            Err(e) => {
                set_last_error(e.to_string());
                ptr::null_mut()
            }
        }
        Err(e) => {
            set_last_error(e.to_string());
            ptr::null_mut()
        }
    }
}

/// FFI wrapper for SettingsCore - load settings
#[no_mangle]
pub extern "C" fn kde_theme_core_settings_load() -> *mut c_char {
    match settings::load_settings() {
        Ok(s) => match serde_json::to_string(&s) {
            Ok(json) => match CString::new(json) {
                Ok(c_str) => c_str.into_raw(),
                Err(e) => {
                    set_last_error(e.to_string());
                    ptr::null_mut()
                }
            }
            Err(e) => {
                set_last_error(e.to_string());
                ptr::null_mut()
            }
        }
        Err(e) => {
            set_last_error(e.to_string());
            ptr::null_mut()
        }
    }
}

/// FFI wrapper for SettingsCore - save settings
#[no_mangle]
pub extern "C" fn kde_theme_core_settings_save(settings_json: *const c_char) -> c_int {
    let json_str = match unsafe { CStr::from_ptr(settings_json) }.to_str() {
        Ok(s) => s,
        Err(e) => {
            set_last_error(e.to_string());
            return -1;
        }
    };

    let settings: AppSettings = match serde_json::from_str(json_str) {
        Ok(s) => s,
        Err(e) => {
            set_last_error(e.to_string());
            return -1;
        }
    };

    match settings::save_settings(settings) {
        Ok(_) => 0,
        Err(e) => {
            set_last_error(e.to_string());
            -1
        }
    }
}

/// FFI wrapper for SettingsCore - get defaults
#[no_mangle]
pub extern "C" fn kde_theme_core_settings_get_defaults() -> *mut c_char {
    let defaults = settings::get_defaults();
    match serde_json::to_string(&defaults) {
        Ok(json) => match CString::new(json) {
            Ok(c_str) => c_str.into_raw(),
            Err(e) => {
                set_last_error(e.to_string());
                ptr::null_mut()
            }
        }
        Err(e) => {
            set_last_error(e.to_string());
            ptr::null_mut()
        }
    }
}