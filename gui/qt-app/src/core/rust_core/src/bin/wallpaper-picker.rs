//! `wallpaper-picker` — Rust CLI (replaces the bash script removed in 0.5.0).
//!
//! wofi grid with generated thumbnails; wofi's `--define dmenu-print_line_num`
//! prints the *0-based* line of the selected entry, which maps directly onto
//! the displayed list. The cached index is the position of the chosen file in
//! the *full* enumeration (the displayed list can be a subset when a thumbnail
//! failed to render), exactly like the historical bash script.

use std::io::Write;
use std::path::{Path, PathBuf};
use std::process::{Command, ExitCode, Stdio};

use kde_theme_core::paths::{cache_home, config_home, home_dir};
use kde_theme_core::wallpaper::{list_wallpapers_in, write_cache_index};

const COLUMNS: &str = "4";
const IMAGE_SIZE: &str = "210";
const THUMB_WIDTH: &str = "420";
const THUMB_HEIGHT: &str = "260";
const THUMB_RADIUS: u32 = 18;
const THUMB_VERSION: &str = "rounded-v1";

fn env_or(key: &str, default: PathBuf) -> PathBuf {
    std::env::var_os(key)
        .map(PathBuf::from)
        .unwrap_or(default)
}

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
    thumb_dir.join(format!("{:016x}.png", fnv1a64(&key)))
}

fn make_thumb(file: &str, thumb: &std::path::Path) -> bool {
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
            "roundrectangle 0,0,{},{} ,{},{}",
            THUMB_WIDTH.parse::<u32>().unwrap_or(0).saturating_sub(1),
            THUMB_HEIGHT.parse::<u32>().unwrap_or(0).saturating_sub(1),
            THUMB_RADIUS,
            THUMB_RADIUS
        ))
        .arg(")")
        .args(["-alpha", "set", "-compose", "DstIn", "-composite", thumb.to_string_lossy().as_ref()])
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .status();

    status.map(|s| s.success()).unwrap_or(false)
}

fn file_newer_than(file: &str, thumb: &std::path::Path) -> bool {
    let file_mtime = std::fs::metadata(file)
        .and_then(|m| m.modified())
        .ok();
    let thumb_mtime = std::fs::metadata(thumb)
        .and_then(|m| m.modified())
        .ok();
    match (file_mtime, thumb_mtime) {
        (Some(f), Some(t)) => f > t,
        _ => true,
    }
}

fn main() -> ExitCode {
    let dir = env_or("WALLPAPER_DIR", home_dir().join("Изображения/Wallpaper"));
    let state = env_or("WALLPAPER_STATE", cache_home().join("wallpaper_index"));
    let thumb_dir = env_or("WALLPAPER_THUMB_DIR", cache_home().join("wallpaper-picker"));
    let style = config_home().join("wofi/wallpaper.css");

    let files = match list_wallpapers_in(&dir) {
        Ok(files) => files,
        Err(e) => {
            eprintln!("wallpaper-picker: {e}");
            return ExitCode::from(1);
        }
    };
    if files.is_empty() {
        return ExitCode::from(1);
    }

    if let Err(e) = std::fs::create_dir_all(&thumb_dir) {
        eprintln!("wallpaper-picker: {e}");
        return ExitCode::from(1);
    }

    let mut entries = String::new();
    let mut displayed: Vec<String> = Vec::new();

    for file in &files {
        let name = std::path::Path::new(file)
            .file_name()
            .map(|n| n.to_string_lossy().to_string())
            .unwrap_or_else(|| file.clone());
        let thumb = thumb_path(&thumb_dir, file);

        if (!thumb.is_file() || file_newer_than(file, &thumb)) && !make_thumb(file, &thumb) {
            let _ = std::fs::remove_file(&thumb);
            continue;
        }

        displayed.push(file.clone());
        entries.push_str(&format!("img:{}:text:{}\n", thumb.display(), name));
    }

    if displayed.is_empty() {
        return ExitCode::from(1);
    }

    let mut wofi = match Command::new("wofi")
        .args([
            "--dmenu",
            "--allow-images",
            "--insensitive",
            "--width",
            "40%",
            "--height",
            "60%",
            "--columns",
            COLUMNS,
            "--define",
            &format!("image_size={IMAGE_SIZE}"),
            "--define",
            "content_halign=center",
            "--define",
            "dmenu-print_line_num=true",
            "--style",
            style.to_string_lossy().as_ref(),
        ])
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .spawn()
    {
        Ok(child) => child,
        Err(e) => {
            eprintln!("wallpaper-picker: could not start wofi: {e}");
            return ExitCode::from(1);
        }
    };

    if let Some(mut stdin) = wofi.stdin.take() {
        let _ = stdin.write_all(entries.as_bytes());
    }

    let output = match wofi.wait_with_output() {
        Ok(out) => out,
        Err(_) => return ExitCode::from(1),
    };
    let selection = String::from_utf8_lossy(&output.stdout).trim().to_string();
    if selection.is_empty() {
        return ExitCode::SUCCESS;
    }
    if !selection.bytes().all(|b| b.is_ascii_digit()) {
        // A typed custom entry is not a position.
        return ExitCode::from(1);
    }
    let index: usize = match selection.parse() {
        Ok(i) => i,
        Err(_) => return ExitCode::from(1),
    };
    let Some(selected_file) = displayed.get(index) else {
        return ExitCode::from(1);
    };

    // Position in the FULL enumeration (the displayed list may be a subset).
    let full_index = files.iter().position(|f| f == selected_file);
    if let Some(full_index) = full_index {
        if let Err(e) = write_cache_index(&state, full_index) {
            eprintln!("wallpaper-picker: {e}");
            return ExitCode::from(1);
        }
    }

    if std::env::var_os("WALLPAPER_DRY_RUN").is_some() {
        println!("{selected_file}");
        ExitCode::SUCCESS
    } else {
        match Command::new("plasma-apply-wallpaperimage").arg(selected_file).status() {
            Ok(s) if s.success() => ExitCode::SUCCESS,
            _ => ExitCode::from(1),
        }
    }
}