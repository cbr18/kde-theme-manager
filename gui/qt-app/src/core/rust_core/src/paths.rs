//! XDG-aware paths and profile-name validation.
//!
//! Profiles keep the historical `.config/...` layout, but the live files they
//! mirror must follow `XDG_CONFIG_HOME`/`XDG_DATA_HOME`.  `theme_root()` prefers
//! the XDG location and falls back to `~/.config/theme-profile` only when that
//! legacy directory already exists, mirroring the bash and Python layers.

use std::path::{Path, PathBuf};

use anyhow::{anyhow, Result};

pub fn home_dir() -> PathBuf {
    dirs::home_dir().unwrap_or_else(|| PathBuf::from("."))
}

pub fn config_home() -> PathBuf {
    dirs::config_dir().unwrap_or_else(|| home_dir().join(".config"))
}

pub fn cache_home() -> PathBuf {
    dirs::cache_dir().unwrap_or_else(|| home_dir().join(".cache"))
}

pub fn data_home() -> PathBuf {
    dirs::data_dir().unwrap_or_else(|| home_dir().join(".local/share"))
}

pub fn theme_root() -> PathBuf {
    let preferred = config_home().join("theme-profile");
    let legacy = home_dir().join(".config").join("theme-profile");
    if preferred.exists() {
        preferred
    } else if legacy.exists() {
        legacy
    } else {
        preferred
    }
}

pub fn profiles_dir() -> PathBuf {
    theme_root().join("profiles")
}

pub fn active_file() -> PathBuf {
    theme_root().join("active-profile")
}

pub fn settings_file() -> PathBuf {
    theme_root().join("app-preferences.json")
}

/// Resolve a profile-relative live path through the XDG base directories.
pub fn live_path(relative: &str) -> PathBuf {
    let path = Path::new(relative);
    if path.is_absolute() {
        return path.to_path_buf();
    }
    let parts: Vec<&std::ffi::OsStr> = path.iter().collect();
    let push_rest = |base: PathBuf, skip: usize| {
        let mut out = base;
        for part in &parts[skip..] {
            out.push(part);
        }
        out
    };
    if parts.first().map(|p| *p == ".config").unwrap_or(false) {
        return push_rest(config_home(), 1);
    }
    if parts.len() >= 2 && parts[0] == ".local" && parts[1] == "share" {
        return push_rest(data_home(), 2);
    }
    if parts.first().map(|p| *p == ".cache").unwrap_or(false) {
        return push_rest(cache_home(), 1);
    }
    home_dir().join(path)
}

/// A profile name is a single path component: no separators, no leading dot.
pub fn is_valid_profile_name(name: &str) -> bool {
    let bytes = name.as_bytes();
    if bytes.is_empty() || bytes.len() > 64 {
        return false;
    }
    if !bytes[0].is_ascii_alphanumeric() {
        return false;
    }
    bytes[1..]
        .iter()
        .all(|b| b.is_ascii_alphanumeric() || *b == b'.' || *b == b'_' || *b == b'-')
}

pub fn validate_profile_name(name: &str) -> Result<()> {
    if is_valid_profile_name(name) {
        Ok(())
    } else {
        Err(anyhow!(
            "Invalid profile name: must match [A-Za-z0-9][A-Za-z0-9._-]{{0,63}}"
        ))
    }
}

pub fn profile_dir(name: &str) -> Result<PathBuf> {
    validate_profile_name(name)?;
    Ok(profiles_dir().join(name))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn accepts_normal_names() {
        for name in ["glass", "paper", "my.theme_2", "A1"] {
            assert!(is_valid_profile_name(name), "{name}");
        }
    }

    #[test]
    fn rejects_traversal_and_separators() {
        for name in ["", ".", "..", "../x", "a/b", ".hidden", "a b", "a\\b"] {
            assert!(!is_valid_profile_name(name), "{name}");
        }
    }

    #[test]
    fn profile_dir_stays_under_profiles() {
        let dir = profile_dir("glass").unwrap();
        assert_eq!(dir.parent(), Some(profiles_dir().as_path()));
        assert!(profile_dir("../etc").is_err());
    }
}
