//! Small unit tests for the FFI boundary and shared path helpers.

use super::*;
use std::ffi::CString;
use std::ptr;

#[test]
fn read_cstr_rejects_null() {
    let result = read_cstr(ptr::null(), "profile_name");
    assert!(result.is_err());
    assert!(result.unwrap_err().contains("null"));
}

#[test]
fn read_cstr_reads_utf8() {
    let value = CString::new("glass").unwrap();
    assert_eq!(read_cstr(value.as_ptr(), "profile_name").unwrap(), "glass");
}

#[test]
fn profile_delete_rejects_traversal_before_touching_disk() {
    assert!(profile::delete_profile("../etc").is_err());
    assert!(profile::delete_profile(".").is_err());
    assert!(profile::delete_profile("a/b").is_err());
}

#[test]
fn profile_functions_reject_empty_components() {
    assert!(profile::apply_profile_impl("glass", Some(vec![])).is_err());
    // Validation happens before the script is executed, so no profile needs
    // to exist for this assertion.
    assert!(profile::save_profile_impl("glass", Some(vec![])).is_err());
}
