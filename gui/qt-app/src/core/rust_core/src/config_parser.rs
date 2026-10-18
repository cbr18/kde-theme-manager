//! Config Parser Utilities
//!
//! Parsers for various config formats used by tracked applications.

use std::path::Path;
use std::fs;
use anyhow::{Result, Context};
use serde::{Deserialize, Serialize};
use configparser::ini::Ini;
use toml;

/// Parse INI file (kwinrc, kdeglobals, gtk settings.ini)
pub fn parse_ini(path: &Path) -> Result<Ini> {
    let mut ini = Ini::new();
    ini.load(path)
        .map_err(|e| anyhow::anyhow!("Failed to parse INI file {}: {}", path.display(), e))?;
    Ok(ini)
}

/// Parse TOML file (alacritty.toml)
pub fn parse_toml(path: &Path) -> Result<toml::Value> {
    let content = fs::read_to_string(path)
        .context(format!("Failed to read TOML file: {}", path.display()))?;
    let value = toml::from_str(&content)
        .context(format!("Failed to parse TOML: {}", path.display()))?;
    Ok(value)
}

/// Parse JSON/JSONC file (vscode, zed, fastfetch)
pub fn parse_json(path: &Path) -> Result<serde_json::Value> {
    let content = fs::read_to_string(path)
        .context(format!("Failed to read JSON file: {}", path.display()))?;
    
    // Handle JSONC (JSON with comments) - strip comments
    let content = strip_json_comments(&content);
    
    let value = serde_json::from_str(&content)
        .context(format!("Failed to parse JSON: {}", path.display()))?;
    Ok(value)
}

/// Strip JSONC comments
fn strip_json_comments(content: &str) -> String {
    let mut result = String::new();
    let mut in_string = false;
    let mut escape_next = false;
    let mut chars = content.chars().peekable();
    
    while let Some(c) = chars.next() {
        if in_string {
            result.push(c);
            if escape_next {
                escape_next = false;
            } else if c == '\\' {
                escape_next = true;
            } else if c == '"' {
                in_string = false;
            }
        } else {
            if c == '/' && chars.peek() == Some(&'/') {
                // Single-line comment - skip to end of line
                chars.next(); // consume second /
                for c in chars.by_ref() {
                    if c == '\n' {
                        result.push(c);
                        break;
                    }
                }
            } else if c == '/' && chars.peek() == Some(&'*') {
                // Multi-line comment - skip until */
                chars.next(); // consume *
                let mut prev = '\0';
                for c in chars.by_ref() {
                    if prev == '*' && c == '/' {
                        break;
                    }
                    prev = c;
                }
            } else {
                if c == '"' {
                    in_string = true;
                }
                result.push(c);
            }
        }
    }
    result
}

/// Parse CSS file (gtk.css, wofi style.css)
pub fn parse_css(path: &Path) -> Result<String> {
    let content = fs::read_to_string(path)
        .context(format!("Failed to read CSS file: {}", path.display()))?;
    Ok(content)
}

/// Parse user.js (Zen Browser)
pub fn parse_user_js(path: &Path) -> Result<Vec<(String, String)>> {
    let content = fs::read_to_string(path)
        .context(format!("Failed to read user.js: {}", path.display()))?;
    
    let mut prefs = Vec::new();
    for line in content.lines() {
        let line = line.trim();
        if line.starts_with("user_pref(") {
            // Parse: user_pref("key", value);
            if let Some(start) = line.find('"') {
                if let Some(end) = line[start+1..].find('"') {
                    let key = line[start+1..start+1+end].to_string();
                    let value_part = &line[start+1+end+2..]; // skip ", "
                    if let Some(value_end) = value_part.rfind(')') {
                        let value = value_part[..value_end].trim().to_string();
                        prefs.push((key, value));
                    }
                }
            }
        }
    }
    Ok(prefs)
}

/// Extract specific value from INI
pub fn get_ini_value(ini: &Ini, section: &str, key: &str) -> Option<String> {
    ini.get(section, key)
}

/// Extract specific value from TOML
pub fn get_toml_value(value: &toml::Value, key: &str) -> Option<String> {
    value.get(key).and_then(|v| v.as_str().map(|s| s.to_string()))
}

/// Extract specific value from JSON
pub fn get_json_value(value: &serde_json::Value, key: &str) -> Option<String> {
    value.get(key).and_then(|v| v.as_str().map(|s| s.to_string()))
}