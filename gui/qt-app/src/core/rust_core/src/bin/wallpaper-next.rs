//! `wallpaper-next` — Rust CLI (replaces the bash script removed in 0.5.0).
//!
//! Contract: step relative to the wallpaper Plasma actually shows (the cached
//! index is only a fallback), write the new index to the state file, and apply
//! with `plasma-apply-wallpaperimage`. `WALLPAPER_DRY_RUN=1` reports the file
//! instead of applying it (used by the tests).

use std::path::PathBuf;
use std::process::{Command, ExitCode};

use kde_theme_core::paths::{cache_home, config_home, home_dir};
use kde_theme_core::wallpaper::{
    anchor_index, list_wallpapers_in, write_cache_index,
};

fn env_or(key: &str, default: PathBuf) -> PathBuf {
    std::env::var_os(key)
        .map(PathBuf::from)
        .unwrap_or(default)
}

fn main() -> ExitCode {
    let dir = env_or(
        "WALLPAPER_DIR",
        home_dir().join("Изображения/Wallpaper"),
    );
    let state = env_or("WALLPAPER_STATE", cache_home().join("wallpaper_index"));
    let plasma = env_or(
        "PLASMA_APPLETSRC",
        config_home().join("plasma-org.kde.plasma.desktop-appletsrc"),
    );

    let files = match list_wallpapers_in(&dir) {
        Ok(files) => files,
        Err(e) => {
            eprintln!("wallpaper-next: {e}");
            return ExitCode::from(1);
        }
    };
    if files.is_empty() {
        return ExitCode::from(1);
    }

    let anchor = anchor_index(&files, &state, Some(&plasma));
    let index = (anchor + 1) % files.len();
    if let Err(e) = write_cache_index(&state, index) {
        eprintln!("wallpaper-next: {e}");
        return ExitCode::from(1);
    }

    if std::env::var_os("WALLPAPER_DRY_RUN").is_some() {
        println!("{}", files[index]);
        ExitCode::SUCCESS
    } else {
        match Command::new("plasma-apply-wallpaperimage").arg(&files[index]).status() {
            Ok(s) if s.success() => ExitCode::SUCCESS,
            _ => ExitCode::from(1),
        }
    }
}