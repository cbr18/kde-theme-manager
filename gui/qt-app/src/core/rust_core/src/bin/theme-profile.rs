//! `theme-profile` — Rust CLI (replaces the bash script removed in 0.5.0).
//!
//! Keeps the historical CLI contract: same commands, same exit-code semantics
//! (`--help` → 0, invalid names / missing profiles → 1, unknown command → 1)
//! and the same stdout shapes (`status` key=value lines, `Saved profile:` /
//! `Applied profile:` messages, unified diff text).

use std::process::ExitCode;

use kde_theme_core::paths::validate_profile_name;
use kde_theme_core::profile::{
    apply_profile_cli, delete_profile, diff_profiles, list_profiles, save_profile_cli,
};
use kde_theme_core::status::status;

const USAGE: &str = "\
Usage:
  theme-profile status
  theme-profile list
  theme-profile save NAME [--components=comp1,comp2]
  theme-profile apply NAME [--components=comp1,comp2]
  theme-profile diff A B
  theme-profile delete NAME

Components: kwin, plasma_shell, kdeglobals, gtk3, gtk4, qt5ct,
            klassy, kvantum, alacritty, kitty, wofi, btop,
            fastfetch, zed, vscode, cursor, zen, obsidian,
            color_schemes, look_and_feel

Use --components=all for all (default).

Profiles live in $XDG_CONFIG_HOME/theme-profile/profiles
(default: ~/.config/theme-profile/profiles).
";

/// Pull `--components=...` out of the arguments, returning
/// (positional args, raw component spec).
fn parse_args(args: &[String]) -> (Vec<&str>, Option<String>) {
    let mut positional = Vec::new();
    let mut components: Option<String> = None;
    for arg in args {
        if let Some(rest) = arg.strip_prefix("--components=") {
            components = Some(rest.to_string());
        } else {
            positional.push(arg.as_str());
        }
    }
    (positional, components)
}

/// Split the raw component spec the way the bash CLI did:
/// `all`/absent → everything, otherwise comma-separated ids (unknown → warn).
fn components_for_cli(raw: Option<&str>) -> Result<(Option<Vec<String>>, Option<String>), String> {
    match raw {
        None => Ok((None, None)),
        Some("all") => Ok((None, Some("all".to_string()))),
        Some(spec) => {
            if spec.is_empty() {
                return Err("No components selected".to_string());
            }
            let ids: Vec<String> = spec
                .split(',')
                .map(|c| c.trim().to_string())
                .filter(|c| !c.is_empty())
                .collect();
            if ids.is_empty() {
                return Err("No components selected".to_string());
            }
            Ok((Some(ids), Some(spec.to_string())))
        }
    }
}

fn component_suffix(raw: Option<&str>) -> String {
    match raw {
        Some(spec) => format!(" (components: {spec})"),
        None => String::new(),
    }
}

fn fail(msg: impl std::fmt::Display) -> ExitCode {
    eprintln!("{msg}");
    ExitCode::from(1)
}

fn main() -> ExitCode {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let cmd = args.first().map(String::as_str).unwrap_or("");

    match cmd {
        "status" => {
            print!("{}", status());
            ExitCode::SUCCESS
        }
        "list" => match list_profiles() {
            Ok(profiles) => {
                for p in profiles {
                    println!("{}", p.name);
                }
                ExitCode::SUCCESS
            }
            Err(e) => fail(e),
        },
        "save" => {
            let (positional, raw) = parse_args(&args[1..]);
            let Some(name) = positional.first().copied() else {
                eprint!("{USAGE}");
                return fail("Usage error: save requires a profile name");
            };
            if positional.len() != 1 {
                return fail("Expected exactly one profile name");
            }
            if validate_profile_name(name).is_err() {
                return fail(format!(
                    "Invalid profile name: {name} (must match [A-Za-z0-9][A-Za-z0-9._-]{{0,63}})"
                ));
            }
            let (components, raw) = match components_for_cli(raw.as_deref()) {
                Ok(v) => v,
                Err(e) => return fail(e),
            };
            match save_profile_cli(name, components) {
                Ok(()) => {
                    println!("Saved profile: {name}{}", component_suffix(raw.as_deref()));
                    ExitCode::SUCCESS
                }
                Err(e) => fail(e),
            }
        }
        "apply" => {
            let (positional, raw) = parse_args(&args[1..]);
            let Some(name) = positional.first().copied() else {
                eprint!("{USAGE}");
                return fail("Usage error: apply requires a profile name");
            };
            if positional.len() != 1 {
                return fail("Expected exactly one profile name");
            }
            if validate_profile_name(name).is_err() {
                return fail(format!(
                    "Invalid profile name: {name} (must match [A-Za-z0-9][A-Za-z0-9._-]{{0,63}})"
                ));
            }
            let (components, raw) = match components_for_cli(raw.as_deref()) {
                Ok(v) => v,
                Err(e) => return fail(e),
            };
            match apply_profile_cli(name, components) {
                Ok(backup) => {
                    println!("Applied profile: {name}{}", component_suffix(raw.as_deref()));
                    println!("Pre-apply backup: {}", backup.display());
                    ExitCode::SUCCESS
                }
                Err(e) => fail(e),
            }
        }
        "diff" => {
            let a = args.get(1).map(String::as_str).unwrap_or("");
            let b = args.get(2).map(String::as_str).unwrap_or("");
            if a.is_empty() || b.is_empty() {
                eprint!("{USAGE}");
                return fail("Usage error: diff requires two profile names");
            }
            match diff_profiles(a, b) {
                Ok(text) => {
                    print!("{text}");
                    ExitCode::SUCCESS
                }
                Err(e) => fail(e),
            }
        }
        "delete" => {
            let Some(name) = args.get(1).map(String::as_str) else {
                eprint!("{USAGE}");
                return fail("Usage error: delete requires a profile name");
            };
            match delete_profile(name) {
                Ok(()) => {
                    println!("Deleted profile: {name}");
                    ExitCode::SUCCESS
                }
                Err(e) => fail(e),
            }
        }
        "--help" | "-h" => {
            print!("{USAGE}");
            ExitCode::SUCCESS
        }
        "--version" => {
            println!("theme-profile 0.5.0");
            ExitCode::SUCCESS
        }
        _ => {
            eprint!("{USAGE}");
            ExitCode::from(1)
        }
    }
}